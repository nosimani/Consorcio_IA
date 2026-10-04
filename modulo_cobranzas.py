"""
modulo_cobranzas.py — Registro de ingresos por pagos de expensas (multi-consorcio).

Medios: efectivo (carga manual), transferencia, tarjeta crédito/débito,
billeteras virtuales, débito automático, cheque.
- Montos en CENTAVOS (enteros): nunca float para dinero.
- Idempotencia: (medio, entidad, referencia) es único -> evita pagos duplicados.
- Nada se borra: los pagos se anulan y todo queda en `auditoria`.
- Multi-tenant: cada consorcio pertenece a un administrador (usuario logueado).
- Base de datos: PostgreSQL en producción (DATABASE_URL) o SQLite en desarrollo; ver db.py.
"""
from __future__ import annotations

import hashlib
import hmac
import json
from datetime import date, datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
from enum import Enum
from typing import Optional

import pandas as pd

from db import (DB_PATH, IntegrityError, descripcion_motor, esquema,  # noqa: F401
                get_conn, init_db, usa_postgres)

SCHEMA = esquema("sqlite")      # compatibilidad: el esquema real depende del motor (db.py)


class MedioPago(str, Enum):
    EFECTIVO = "Efectivo"
    TRANSFERENCIA = "Transferencia bancaria"
    TARJETA_CREDITO = "Tarjeta de crédito"
    TARJETA_DEBITO = "Tarjeta de débito"
    BILLETERA = "Billetera virtual"
    DEBITO_AUTOMATICO = "Débito automático (CBU)"
    CHEQUE = "Cheque"
    OTRO = "Otro"


class EstadoPago(str, Enum):
    PENDIENTE = "Pendiente de acreditación"
    ACREDITADO = "Acreditado"
    CONCILIADO = "Conciliado"
    ANULADO = "Anulado"


class PagoDuplicado(ValueError):
    """La referencia ya fue registrada (reintento de webhook o carga repetida)."""


ESTADOS_COBRADOS = (EstadoPago.ACREDITADO.value, EstadoPago.CONCILIADO.value)
MEDIOS_CONCILIABLES = (
    MedioPago.TRANSFERENCIA.value,
    MedioPago.DEBITO_AUTOMATICO.value,
    MedioPago.BILLETERA.value,
)

# ───────────────────────── utilidades ─────────────────────────
def a_centavos(monto) -> int:
    return int((Decimal(str(monto)) * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def _validar_periodo(periodo: str) -> None:
    try:
        datetime.strptime(periodo, "%Y-%m")
    except ValueError:
        raise ValueError("El período debe tener formato AAAA-MM (ej. 2026-10).")


def _auditar(conn, pago_id, accion, usuario, detalle=""):
    conn.execute(
        "INSERT INTO auditoria (pago_id, accion, usuario, detalle, ts) VALUES (?,?,?,?,?)",
        (pago_id, accion, usuario, detalle, datetime.now().isoformat(timespec="seconds")),
    )


# ───────────────────────── altas básicas ─────────────────────────
def crear_consorcio(conn, administrador: str, nombre: str, direccion: str = "") -> int:
    conn.execute(
        "INSERT INTO consorcios (administrador, nombre, direccion) VALUES (?,?,?) "
        "ON CONFLICT (administrador, nombre) DO NOTHING",
        (administrador, nombre.strip(), direccion.strip()),
    )
    conn.commit()
    return conn.execute(
        "SELECT id FROM consorcios WHERE administrador=? AND nombre=?",
        (administrador, nombre.strip()),
    ).fetchone()["id"]


def cargar_unidades_desde_df(conn, consorcio_id: int, df: pd.DataFrame) -> int:
    """df con columnas UF, Propietario, Piso, Coeficiente, Contacto (como en tu app)."""
    n = 0
    for r in df.to_dict("records"):
        conn.execute(
            """INSERT INTO unidades (consorcio_id, uf, piso, propietario, coeficiente, contacto)
               VALUES (?,?,?,?,?,?)
               ON CONFLICT(consorcio_id, uf) DO UPDATE SET
                 piso=excluded.piso, propietario=excluded.propietario,
                 coeficiente=excluded.coeficiente, contacto=excluded.contacto""",
            (consorcio_id, str(r["UF"]).strip().upper(), str(r.get("Piso", "")),
             str(r.get("Propietario", "")), float(r.get("Coeficiente", 0) or 0),
             str(r.get("Contacto", ""))),
        )
        n += 1
    conn.commit()
    return n


# ───────────────────────── registro de pagos ─────────────────────────
def registrar_pago(
    conn, *, consorcio_id: int, uf: str, periodo: str, monto, medio, usuario: str,
    fecha_pago: Optional[date] = None, entidad: str = "", referencia: str = "",
    origen: str = "manual", observaciones: str = "", confirmado: bool = False,
) -> int:
    """
    Efectivo -> queda ACREDITADO y se emite nro. de recibo.
    Resto    -> exige referencia (n° de operación) y queda PENDIENTE hasta conciliar,
                salvo confirmado=True (notificación firmada de la pasarela/billetera).
    """
    medio = MedioPago(medio)
    centavos = a_centavos(monto)
    if centavos <= 0:
        raise ValueError("El monto debe ser mayor a cero.")
    _validar_periodo(periodo)

    unidad = conn.execute(
        "SELECT id FROM unidades WHERE consorcio_id=? AND uf=?",
        (consorcio_id, uf.strip().upper()),
    ).fetchone()
    if not unidad:
        raise ValueError(f"La UF {uf} no existe en ese consorcio.")

    referencia = (referencia or "").strip()
    if medio is not MedioPago.EFECTIVO and not referencia:
        raise ValueError("Falta el número de operación / referencia del pago.")

    es_efectivo = medio is MedioPago.EFECTIVO
    estado = EstadoPago.ACREDITADO if (es_efectivo or confirmado) else EstadoPago.PENDIENTE
    entidad = entidad.strip()
    if referencia:
        # Chequeo previo: en PostgreSQL un INSERT que choca con el índice único igual consume un
        # número de la secuencia de ids, y el n.º de recibo sale del id: cada reintento de webhook
        # dejaría un hueco. El índice único sigue siendo la defensa final ante dos pedidos simultáneos.
        if conn.execute("SELECT 1 FROM pagos WHERE medio=? AND entidad=? AND referencia=?",
                        (medio.value, entidad, referencia)).fetchone():
            raise PagoDuplicado("Ya existe un pago con esa referencia: posible duplicado.")
    try:
        cur = conn.execute(
            """INSERT INTO pagos (consorcio_id, unidad_id, periodo, fecha_pago, monto_centavos,
                   medio, entidad, referencia, estado, origen, observaciones, cargado_por, creado_en)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?) RETURNING id""",
            (consorcio_id, unidad["id"], periodo, (fecha_pago or date.today()).isoformat(),
             centavos, medio.value, entidad, referencia, estado.value, origen,
             observaciones, usuario, datetime.now().isoformat(timespec="seconds")),
        )
    except IntegrityError:
        raise PagoDuplicado("Ya existe un pago con esa referencia: posible duplicado.")

    pago_id = cur.fetchone()["id"]
    if es_efectivo:
        conn.execute("UPDATE pagos SET nro_recibo=? WHERE id=?",
                     (f"R-{consorcio_id:03d}-{pago_id:08d}", pago_id))
    _auditar(conn, pago_id, "ALTA", usuario, f"{medio.value} ${centavos/100:,.2f} UF {uf}")
    conn.commit()
    return pago_id


def anular_pago(conn, pago_id: int, usuario: str, motivo: str) -> None:
    if not motivo.strip():
        raise ValueError("Indicá el motivo de la anulación.")
    conn.execute("UPDATE pagos SET estado=? WHERE id=?", (EstadoPago.ANULADO.value, pago_id))
    _auditar(conn, pago_id, "ANULACION", usuario, motivo)
    conn.commit()


# ───────────────────── pagos electrónicos (webhooks) ─────────────────────
def verificar_firma(cuerpo: bytes, firma_hex: str, secreto: str) -> bool:
    """HMAC-SHA256 genérico. Cada pasarela (Mercado Pago, etc.) define su propio
    esquema de firma: adaptá esta función a la documentación del proveedor."""
    esperado = hmac.new(secreto.encode(), cuerpo, hashlib.sha256).hexdigest()
    return hmac.compare_digest(esperado, firma_hex or "")


def parsear_referencia_externa(ref: str) -> tuple[int, str, str]:
    """Al generar el link/QR de pago, mandá external_reference='consorcio_id:UF:AAAA-MM'.
    Así cada pago que vuelve por webhook ya sabe a qué unidad pertenece."""
    try:
        consorcio_id, uf, periodo = (ref or "").split(":")
        return int(consorcio_id), uf, periodo
    except ValueError:
        raise ValueError("El pago llegó sin referencia válida (se esperaba 'consorcio:UF:AAAA-MM').")


def consorcio_pertenece(conn, consorcio_id: int, administrador: str) -> bool:
    return conn.execute("SELECT 1 FROM consorcios WHERE id=? AND administrador=?",
                        (consorcio_id, administrador)).fetchone() is not None


def registrar_desde_notificacion(conn, proveedor: str, datos: dict) -> int:
    """datos normalizados: external_reference ('consorcio:UF:AAAA-MM'), monto, medio
    (valor de MedioPago), entidad, referencia, fecha (ISO, opcional)."""
    consorcio_id, uf, periodo = parsear_referencia_externa(datos.get("external_reference") or "")
    fecha = datos.get("fecha")
    if isinstance(fecha, str) and fecha:
        fecha = date.fromisoformat(fecha[:10])
    return registrar_pago(
        conn, consorcio_id=consorcio_id, uf=uf, periodo=periodo, monto=datos["monto"],
        medio=datos["medio"], entidad=datos.get("entidad") or proveedor,
        referencia=str(datos["referencia"]), usuario=f"sistema:{proveedor}",
        origen="webhook", confirmado=True, fecha_pago=fecha or None,
    )


def anular_por_referencia(conn, referencia: str, usuario: str, motivo: str) -> int:
    """Devoluciones / contracargos que avisa la pasarela. Devuelve cantidad anulada."""
    filas = conn.execute(
        "SELECT id FROM pagos WHERE referencia=? AND origen='webhook' AND estado<>?",
        (str(referencia), EstadoPago.ANULADO.value)).fetchall()
    for f in filas:
        anular_pago(conn, f["id"], usuario, motivo)
    return len(filas)


# ───────────────────── bitácora de eventos de pasarela ─────────────────────
def evento_estado(conn, administrador: str, proveedor: str, evento_id: str) -> Optional[str]:
    r = conn.execute("SELECT estado FROM eventos_webhook WHERE administrador=? AND proveedor=? AND evento_id=?",
                     (administrador, proveedor, evento_id)).fetchone()
    return r["estado"] if r else None


def registrar_evento(conn, administrador, proveedor, evento_id, estado,
                     detalle="", datos: Optional[dict] = None, pago_id=None) -> None:
    conn.execute(
        """INSERT INTO eventos_webhook (administrador, proveedor, evento_id, estado, detalle,
               datos_json, pago_id, recibido_en) VALUES (?,?,?,?,?,?,?,?)
           ON CONFLICT(administrador, proveedor, evento_id) DO UPDATE SET
               estado=excluded.estado, detalle=excluded.detalle,
               datos_json=excluded.datos_json, pago_id=excluded.pago_id""",
        (administrador, proveedor, evento_id, estado, detalle,
         json.dumps(datos, default=str) if datos else "", pago_id,
         datetime.now().isoformat(timespec="seconds")))
    conn.commit()


def procesar_pago_normalizado(conn, administrador: str, proveedor: str,
                              evento_id: str, datos: dict) -> dict:
    """Punto único de entrada para cualquier pasarela. Idempotente y tolerante a fallas:
    lo que no se puede asignar a una UF queda como 'sin_identificar' para resolver a mano."""
    previo = evento_estado(conn, administrador, proveedor, evento_id)
    if previo and previo != "error":
        return {"resultado": "ya_procesado"}
    try:
        cid, _, _ = parsear_referencia_externa(datos.get("external_reference") or "")
        if not consorcio_pertenece(conn, cid, administrador):
            raise ValueError("La referencia apunta a un consorcio que no es de este administrador.")
        pid = registrar_desde_notificacion(conn, proveedor, datos)
        registrar_evento(conn, administrador, proveedor, evento_id, "procesado", pago_id=pid, datos=datos)
        return {"resultado": "registrado", "pago_id": pid}
    except PagoDuplicado:
        registrar_evento(conn, administrador, proveedor, evento_id, "procesado", "duplicado", datos)
        return {"resultado": "duplicado"}
    except (ValueError, KeyError) as e:
        registrar_evento(conn, administrador, proveedor, evento_id, "sin_identificar", str(e), datos)
        return {"resultado": "sin_identificar", "motivo": str(e)}


def asignar_evento(conn, evento_row_id: int, administrador: str, consorcio_id: int,
                   uf: str, periodo: str) -> int:
    """El administrador asigna a mano un pago electrónico que llegó sin referencia válida."""
    ev = conn.execute("SELECT * FROM eventos_webhook WHERE id=? AND administrador=? AND estado='sin_identificar'",
                      (evento_row_id, administrador)).fetchone()
    if not ev:
        raise ValueError("Evento inexistente o ya resuelto.")
    if not consorcio_pertenece(conn, consorcio_id, administrador):
        raise ValueError("Consorcio inválido.")
    datos = json.loads(ev["datos_json"])
    datos["external_reference"] = f"{consorcio_id}:{uf.strip().upper()}:{periodo}"
    pid = registrar_desde_notificacion(conn, ev["proveedor"], datos)
    registrar_evento(conn, administrador, ev["proveedor"], ev["evento_id"], "procesado",
                     f"asignado manualmente por {administrador}", datos, pid)
    return pid


def eventos_sin_identificar(conn, administrador: str) -> pd.DataFrame:
    return conn.df(
        """SELECT id, proveedor, evento_id, detalle, datos_json, recibido_en
           FROM eventos_webhook WHERE administrador=? AND estado='sin_identificar'
           ORDER BY id DESC""", [administrador])


# ───────────────────────── conciliación bancaria ─────────────────────────
def conciliar_extracto(conn, consorcio_id: int, extracto: pd.DataFrame, usuario: str,
                       tolerancia_dias: int = 2) -> pd.DataFrame:
    """extracto con columnas: fecha, monto, referencia (opcional), descripcion (opcional).
    1) match por referencia + monto; 2) match por monto + fecha (±tolerancia) si es único."""
    extracto = extracto.rename(columns=lambda c: str(c).strip().lower())
    if not {"fecha", "monto"} <= set(extracto.columns):
        raise ValueError("El extracto necesita al menos las columnas 'fecha' y 'monto'.")

    marks = ",".join("?" * len(MEDIOS_CONCILIABLES))
    pendientes = [dict(r) for r in conn.execute(
        f"""SELECT id, fecha_pago, monto_centavos, referencia FROM pagos
            WHERE consorcio_id=? AND estado=? AND medio IN ({marks})""",
        (consorcio_id, EstadoPago.PENDIENTE.value, *MEDIOS_CONCILIABLES),
    )]
    usados: set[int] = set()
    resultados = []

    for fila in extracto.to_dict("records"):
        cent = a_centavos(fila["monto"])
        ref = "" if pd.isna(fila.get("referencia")) else str(fila["referencia"]).strip()
        f = pd.to_datetime(fila["fecha"]).date()
        libres = [p for p in pendientes if p["id"] not in usados and p["monto_centavos"] == cent]

        match = [p for p in libres if ref and p["referencia"] == ref]
        if not match:
            match = [p for p in libres
                     if abs((date.fromisoformat(p["fecha_pago"]) - f).days) <= tolerancia_dias]

        if len(match) == 1:
            pid = match[0]["id"]
            conn.execute("UPDATE pagos SET estado=? WHERE id=?", (EstadoPago.CONCILIADO.value, pid))
            _auditar(conn, pid, "CONCILIACION", usuario, f"extracto {f} ${cent/100:,.2f}")
            usados.add(pid)
            resultados.append({**fila, "resultado": "conciliado", "pago_id": pid})
        else:
            resultados.append({**fila, "resultado": "ambiguo" if match else "sin_match", "pago_id": None})

    conn.commit()
    return pd.DataFrame(resultados)


# ───────────────────────── consultas e informes ─────────────────────────
def libro_ingresos(conn, consorcio_ids: list[int], periodo: Optional[str] = None) -> pd.DataFrame:
    if not consorcio_ids:
        return pd.DataFrame()
    marks = ",".join("?" * len(consorcio_ids))
    sql = f"""SELECT p.id, p.nro_recibo, p.fecha_pago, c.nombre AS consorcio, u.uf,
                     u.propietario, p.periodo, CAST(p.monto_centavos AS DOUBLE PRECISION) / 100.0 AS monto, p.medio,
                     p.entidad, p.referencia, p.estado, p.origen, p.cargado_por
              FROM pagos p JOIN consorcios c ON c.id=p.consorcio_id
              JOIN unidades u ON u.id=p.unidad_id
              WHERE p.consorcio_id IN ({marks})"""
    params: list = list(consorcio_ids)
    if periodo:
        sql += " AND p.periodo=?"
        params.append(periodo)
    return conn.df(sql + " ORDER BY p.fecha_pago DESC, p.id DESC", params)


def resumen_por_medio(conn, consorcio_ids: list[int], periodo: str) -> pd.DataFrame:
    df = libro_ingresos(conn, consorcio_ids, periodo)
    if df.empty:
        return df
    df = df[df["estado"] != EstadoPago.ANULADO.value]
    return (df.groupby(["consorcio", "medio", "estado"], as_index=False)
              .agg(cantidad=("id", "count"), total=("monto", "sum")))


def estado_cobranza_por_uf(conn, consorcio_id: int, periodo: str,
                           expensas_por_uf: dict[str, float]) -> pd.DataFrame:
    """Cruza lo liquidado (liquidacion.expensas_por_uf) con lo efectivamente cobrado."""
    cobrado = {r["uf"]: r["total"] for r in conn.execute(
        f"""SELECT u.uf, CAST(SUM(p.monto_centavos) AS DOUBLE PRECISION) / 100.0 AS total FROM pagos p
            JOIN unidades u ON u.id=p.unidad_id
            WHERE p.consorcio_id=? AND p.periodo=? AND p.estado IN ({",".join("?"*len(ESTADOS_COBRADOS))})
            GROUP BY u.uf""", (consorcio_id, periodo, *ESTADOS_COBRADOS))}
    filas = []
    for u in conn.execute("SELECT uf, propietario FROM unidades WHERE consorcio_id=? ORDER BY uf",
                          (consorcio_id,)):
        debe = round(float(expensas_por_uf.get(u["uf"], 0.0)), 2)
        pago = round(float(cobrado.get(u["uf"], 0.0)), 2)
        saldo = round(debe - pago, 2)
        estado = "Al día" if saldo <= 0.01 else ("Pago parcial" if pago > 0 else "Sin pago")
        filas.append({"UF": u["uf"], "Propietario": u["propietario"], "Expensa": debe,
                      "Cobrado": pago, "Saldo": saldo, "Estado": estado})
    return pd.DataFrame(filas)


def ingresos_para_liquidacion(conn, consorcio_id: int, periodo: str) -> dict[str, float]:
    """Alimenta AgenteLiquidacion:
       monto = ingresos_para_liquidacion(conn, id, '2026-10')['Expensas Cobradas']
       agente.registrar_ingreso(RegistroIngreso("Cobranzas del período", TipoIngreso.EXPENSAS, monto))"""
    total = conn.execute(
        f"""SELECT COALESCE(SUM(monto_centavos),0) FROM pagos WHERE consorcio_id=? AND periodo=?
            AND estado IN ({",".join("?"*len(ESTADOS_COBRADOS))})""",
        (consorcio_id, periodo, *ESTADOS_COBRADOS)).fetchone()[0]
    return {"Expensas Cobradas": float(total) / 100.0}


# ───────────────────────── interfaz Streamlit ─────────────────────────
def render_modulo_cobranzas(expensas_por_uf: Optional[dict] = None) -> None:
    """Llamar desde tu app: render_modulo_cobranzas(liquidacion.expensas_por_uf).
    Requiere st.session_state['usuario'] seteado por tu login."""
    import streamlit as st

    usuario = st.session_state.get("usuario")
    if not usuario:
        st.warning("Iniciá sesión para operar el módulo de cobranzas.")
        return
    conn = get_conn()                 # PostgreSQL (pool) o SQLite, según la configuración
    try:
        init_db(conn)
        _render_cobranzas(st, conn, usuario, expensas_por_uf)
    finally:
        conn.close()                  # sin esto cada clic dejaría una conexión abierta


def _render_cobranzas(st, conn, usuario, expensas_por_uf) -> None:
    st.header("💵 Cobranzas")
    if conn.motor == "sqlite":
        st.warning("🗄️ Base de datos: SQLite local. En Streamlit Cloud estos datos se pierden cuando la "
                   "app se reinicia. Para producción configurá DATABASE_URL (PostgreSQL).")
    else:
        st.caption("🗄️ Base de datos: PostgreSQL")
    with st.expander("Consorcios y unidades funcionales"):
        nuevo = st.text_input("Nuevo consorcio (nombre / dirección)")
        if st.button("Crear consorcio") and nuevo.strip():
            crear_consorcio(conn, usuario, nuevo)
            st.rerun()

    cons = conn.execute("SELECT id, nombre FROM consorcios WHERE administrador=? ORDER BY nombre",
                        (usuario,)).fetchall()
    if not cons:
        st.info("Creá tu primer consorcio para empezar.")
        return
    nombres = {c["nombre"]: c["id"] for c in cons}
    nombre_sel = st.selectbox("Consorcio", list(nombres))
    cid = nombres[nombre_sel]

    with st.expander("Cargar UF y propietarios (CSV/Excel con UF, Propietario, Piso, Coeficiente, Contacto)"):
        up = st.file_uploader("Archivo", type=["csv", "xlsx"], key="up_uf")
        if up is not None and st.button("Importar unidades"):
            df_uf = pd.read_csv(up) if up.name.lower().endswith(".csv") else pd.read_excel(up)
            st.success(f"{cargar_unidades_desde_df(conn, cid, df_uf)} unidades cargadas.")

    t1, t2, t3, t4, t5, t6 = st.tabs(["➕ Registrar pago", "📒 Libro de ingresos", "🏦 Conciliación",
                                      "📊 Resumen", "⚠️ Sin identificar", "📉 Mora y deuda"])

    with t1:
        ufs = [r["uf"] for r in conn.execute(
            "SELECT uf FROM unidades WHERE consorcio_id=? ORDER BY uf", (cid,))]
        with st.form("form_pago", clear_on_submit=True):
            uf = st.selectbox("Unidad funcional", ufs)
            periodo = st.text_input("Período (AAAA-MM)", value=date.today().strftime("%Y-%m"))
            monto = st.number_input("Monto ($)", min_value=0.0, step=100.0, format="%.2f")
            medio = st.selectbox("Medio de pago", list(MedioPago), format_func=lambda m: m.value)
            entidad = st.text_input("Banco / billetera / tarjeta (opcional)")
            referencia = st.text_input("N° de operación (obligatorio salvo efectivo)")
            fecha = st.date_input("Fecha de pago", value=date.today())
            obs = st.text_area("Observaciones")
            if st.form_submit_button("Registrar pago"):
                try:
                    pid = registrar_pago(conn, consorcio_id=cid, uf=uf, periodo=periodo, monto=monto,
                                         medio=medio, usuario=usuario, fecha_pago=fecha,
                                         entidad=entidad, referencia=referencia, observaciones=obs)
                    st.success(f"Pago #{pid} registrado.")
                except ValueError as e:
                    st.error(str(e))

    with t2:
        per = st.text_input("Filtrar por período (AAAA-MM, vacío = todos)", key="per_libro")
        libro = libro_ingresos(conn, [cid], per or None)
        st.dataframe(libro, use_container_width=True)
        if not libro.empty:
            st.download_button("Descargar CSV", libro.to_csv(index=False).encode("utf-8-sig"),
                               "libro_ingresos.csv", "text/csv")
        with st.expander("Anular un pago"):
            pid_a = st.number_input("ID del pago", min_value=1, step=1)
            motivo = st.text_input("Motivo")
            if st.button("Anular"):
                try:
                    anular_pago(conn, int(pid_a), usuario, motivo)
                    st.success("Pago anulado (queda en auditoría).")
                except ValueError as e:
                    st.error(str(e))

        with st.expander("🧾 Recibo en PDF"):
            from recibos import generar_recibo_pdf
            pid_r = st.number_input("ID del pago", min_value=1, step=1, key="pid_recibo")
            if st.button("Preparar recibo"):
                try:
                    st.session_state["_recibo_pdf"] = (int(pid_r), generar_recibo_pdf(
                        conn, int(pid_r), usuario, administrador=usuario))
                except ValueError as e:
                    st.error(str(e))
            rec = st.session_state.get("_recibo_pdf")
            if rec:
                st.download_button(f"Descargar recibo del pago #{rec[0]}", rec[1],
                                   f"recibo_{rec[0]}.pdf", "application/pdf")

    with t3:
        ext = st.file_uploader("Extracto bancario (fecha, monto, referencia)", type=["csv", "xlsx"], key="ext")
        if ext is not None and st.button("Conciliar"):
            df_ext = pd.read_csv(ext) if ext.name.lower().endswith(".csv") else pd.read_excel(ext)
            try:
                res = conciliar_extracto(conn, cid, df_ext, usuario)
                st.dataframe(res, use_container_width=True)
                st.caption("'sin_match' = depósito sin identificar: cargalo como pago asignándolo a su UF.")
            except ValueError as e:
                st.error(str(e))

    with t4:
        per_r = st.text_input("Período (AAAA-MM)", value=date.today().strftime("%Y-%m"), key="per_res")
        st.subheader("Ingresos por medio de pago")
        st.dataframe(resumen_por_medio(conn, [cid], per_r), use_container_width=True)
        if expensas_por_uf:
            st.subheader("Estado de cobranza por UF")
            st.dataframe(estado_cobranza_por_uf(conn, cid, per_r, expensas_por_uf),
                         use_container_width=True)

    with t5:
        pend = eventos_sin_identificar(conn, usuario)
        if pend.empty:
            st.success("No hay pagos electrónicos pendientes de identificar.")
        else:
            st.caption("Pagos que llegaron de la pasarela sin una referencia válida de UF.")
            st.dataframe(pend.drop(columns=["datos_json"]), use_container_width=True)
            ev_id = st.selectbox("Evento a asignar", pend["id"].tolist())
            uf_a = st.selectbox("Unidad funcional", ufs, key="uf_evento")
            per_a = st.text_input("Período (AAAA-MM)", value=date.today().strftime("%Y-%m"), key="per_evento")
            if st.button("Asignar pago a esta UF"):
                try:
                    st.success(f"Pago #{asignar_evento(conn, int(ev_id), usuario, cid, uf_a, per_a)} registrado.")
                    st.rerun()
                except ValueError as e:
                    st.error(str(e))

    with t6:
        from mora import (configurar_mora, cuenta_corriente, emitir_cargos, fmt_ars,
                          obtener_config_mora, redactar_aviso)
        from recibos import generar_estado_cuenta_pdf, generar_estados_cuenta_zip

        tasa_act, gracia_act = obtener_config_mora(conn, cid)
        with st.expander("⚙️ Parámetros de mora", expanded=(tasa_act == 0)):
            tasa_in = st.number_input("Interés punitorio mensual (%)", 0.0, 100.0, float(tasa_act * 100), 0.1)
            gracia_in = st.number_input("Días de gracia", 0, 60, int(gracia_act))
            st.caption("Aplicá lo que establezca tu reglamento de copropiedad o lo resuelto en asamblea.")
            if st.button("Guardar parámetros"):
                try:
                    configurar_mora(conn, cid, tasa_in, int(gracia_in))
                    st.success("Parámetros guardados.")
                except ValueError as e:
                    st.error(str(e))

        with st.expander("📤 Emitir cargos del período"):
            if not expensas_por_uf:
                st.info("Pasá liquidacion.expensas_por_uf a render_modulo_cobranzas para emitir los cargos.")
            else:
                per_c = st.text_input("Período (AAAA-MM)", value=date.today().strftime("%Y-%m"), key="per_cargo")
                venc = st.date_input("Vencimiento", value=date.today() + timedelta(days=10))
                if st.button("Emitir cargos"):
                    try:
                        r = emitir_cargos(conn, cid, per_c, expensas_por_uf, venc, usuario)
                        st.success(f"{r['creados']} cargos creados, {r['existentes']} ya existían.")
                        if r["sin_unidad"]:
                            st.warning("UF sin cargar en el consorcio: " + ", ".join(map(str, r["sin_unidad"])))
                    except ValueError as e:
                        st.error(str(e))

        hoy = st.date_input("Calcular deuda al", value=date.today(), key="hoy_mora")
        res, _ = cuenta_corriente(conn, cid, hoy)
        if res.empty:
            st.info("Todavía no hay unidades ni cargos para calcular.")
        else:
            c1, c2, c3 = st.columns(3)
            c1.metric("Capital adeudado", fmt_ars(res["Capital adeudado"].sum()))
            c2.metric("Interés punitorio", fmt_ars(res["Interés punitorio"].sum()))
            c3.metric("Total adeudado", fmt_ars(res["Total adeudado"].sum()))
            st.dataframe(res.drop(columns=["Contacto"]), use_container_width=True)

            morosas = res[res["Total adeudado"] > 0]
            if not morosas.empty:
                uf_m = st.selectbox("UF con deuda", morosas["UF"].tolist(), key="uf_mora")
                fila = morosas[morosas["UF"] == uf_m].iloc[0].to_dict()
                st.text_area("Aviso para copiar y enviar", redactar_aviso(fila, nombre_sel, hoy), height=130)
                st.download_button("Estado de cuenta (PDF)",
                                   generar_estado_cuenta_pdf(conn, cid, uf_m, hoy, {"nombre": usuario}),
                                   f"estado_cuenta_UF_{uf_m}.pdf", "application/pdf")
                if st.button("Preparar ZIP con todos los estados de cuenta"):
                    st.session_state["_zip_estados"] = generar_estados_cuenta_zip(conn, cid, hoy, {"nombre": usuario})
                z = st.session_state.get("_zip_estados")
                if z:
                    st.download_button(f"Descargar {z[1]} estados de cuenta (ZIP)", z[0],
                                       "estados_de_cuenta.zip", "application/zip")
