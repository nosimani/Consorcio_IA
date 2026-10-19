"""
portal_propietario.py — Acceso de solo lectura para que cada propietario consulte SU deuda y descargue
SUS recibos y estado de cuenta, sin ver nada de otras unidades ni de otros consorcios.

Cómo funciona:
  * El administrador genera un código por unidad (pestaña "Portal propietarios" de Cobranzas).
    El código se muestra UNA sola vez; en la base solo queda su hash PBKDF2 (no se puede recuperar).
    Generar uno nuevo invalida el anterior.
  * El propietario entra a la dirección de la app agregando  ?portal=1  y escribe su código.
  * Tras 5 intentos fallidos, esa unidad queda bloqueada 15 minutos. El contador vive en la base
    (no en la sesión), así que abrir otra pestaña no permite seguir probando códigos.
  * Toda consulta del portal filtra por la unidad autenticada.
"""
from __future__ import annotations

import hashlib
import hmac
import os
import secrets
from datetime import date, datetime, timedelta
from typing import Optional

from mora import cuenta_corriente, fmt_ars
from modulo_cobranzas import ESTADOS_COBRADOS, _auditar
from recibos import generar_estado_cuenta_pdf, generar_recibo_pdf

ALFABETO = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"      # sin 0/O/1/I/L para que no se confundan al dictarlo
LARGO_SECRETO = 10                                 # 32^10 ≈ 1,1 × 10^15 combinaciones
MAX_INTENTOS = 5
BLOQUEO_MIN = 15
ITERACIONES = 200_000


def _hash(secreto: str, salt_hex: Optional[str] = None, iteraciones: int = ITERACIONES) -> str:
    salt = bytes.fromhex(salt_hex) if salt_hex else os.urandom(16)
    dk = hashlib.pbkdf2_hmac("sha256", secreto.encode("utf-8"), salt, iteraciones)
    return f"pbkdf2${iteraciones}${salt.hex()}${dk.hex()}"


_HASH_FALSO = _hash("x", "00" * 16, 1000)


def _verificar(secreto: str, registro: str) -> bool:
    try:
        _, it, salt_hex, hash_hex = registro.split("$")
        return hmac.compare_digest(_hash(secreto, salt_hex, int(it)).split("$")[3], hash_hex)
    except Exception:
        return False


def _formatear(unidad_id: int, secreto: str) -> str:
    grupos = "-".join(secreto[i:i + 4] for i in range(0, len(secreto), 4))
    return f"{unidad_id}-{grupos}"


def _parsear(codigo: str) -> Optional[tuple[int, str]]:
    limpio = (codigo or "").strip().upper().replace(" ", "")
    if "-" not in limpio:
        return None
    primero, resto = limpio.split("-", 1)
    secreto = resto.replace("-", "")
    if not primero.isdigit() or len(secreto) != LARGO_SECRETO or any(c not in ALFABETO for c in secreto):
        return None
    return int(primero), secreto


# ───────────────────────── administración de accesos ─────────────────────────
def generar_acceso(conn, unidad_id: int, usuario: str) -> str:
    """Crea (o reemplaza) el acceso de una unidad y devuelve el código para entregarle al propietario."""
    secreto = "".join(secrets.choice(ALFABETO) for _ in range(LARGO_SECRETO))
    ahora = datetime.now().isoformat(timespec="seconds")
    conn.execute(
        """INSERT INTO accesos_propietario (unidad_id, hash_clave, creado_por, creado_en)
           VALUES (?,?,?,?)
           ON CONFLICT(unidad_id) DO UPDATE SET hash_clave=excluded.hash_clave,
             creado_por=excluded.creado_por, creado_en=excluded.creado_en,
             intentos_fallidos=0, bloqueado_hasta=''""",
        (unidad_id, _hash(secreto), usuario, ahora))
    _auditar(conn, None, "ACCESO_PORTAL_GENERADO", usuario, f"unidad {unidad_id}")
    conn.commit()
    return _formatear(unidad_id, secreto)


def revocar_acceso(conn, unidad_id: int, usuario: str) -> None:
    conn.execute("DELETE FROM accesos_propietario WHERE unidad_id=?", (unidad_id,))
    _auditar(conn, None, "ACCESO_PORTAL_REVOCADO", usuario, f"unidad {unidad_id}")
    conn.commit()


def accesos_de_consorcio(conn, consorcio_id: int):
    """UF del consorcio con la fecha en que se generó su acceso (vacío = sin acceso)."""
    return conn.df(
        """SELECT u.id AS unidad_id, u.uf AS "UF", u.propietario AS "Propietario",
                  COALESCE(a.creado_en, '') AS "Acceso generado", COALESCE(a.bloqueado_hasta, '') AS "Bloqueado hasta"
           FROM unidades u LEFT JOIN accesos_propietario a ON a.unidad_id = u.id
           WHERE u.consorcio_id=? ORDER BY u.uf""", [consorcio_id])


# ───────────────────────── ingreso del propietario ─────────────────────────
MENSAJE_ERROR = "Código incorrecto o acceso no disponible. Revisalo o pedile uno nuevo a tu administración."


def verificar_acceso(conn, codigo: str, ahora: Optional[datetime] = None) -> Optional[dict]:
    """Devuelve los datos de la unidad si el código es correcto; si no, None.
    No distingue entre 'unidad inexistente', 'código malo' y 'bloqueada' hacia afuera."""
    ahora = ahora or datetime.now()
    parsed = _parsear(codigo)
    if not parsed:
        _verificar("x", _HASH_FALSO)                       # tiempo parecido en todos los caminos
        return None
    unidad_id, secreto = parsed
    acc = conn.execute("SELECT * FROM accesos_propietario WHERE unidad_id=?", (unidad_id,)).fetchone()
    if not acc:
        _verificar(secreto, _HASH_FALSO)
        return None
    if acc["bloqueado_hasta"] and datetime.fromisoformat(acc["bloqueado_hasta"]) > ahora:
        return None
    if not _verificar(secreto, acc["hash_clave"]):
        intentos = acc["intentos_fallidos"] + 1
        bloqueo = ""
        if intentos >= MAX_INTENTOS:
            bloqueo = (ahora + timedelta(minutes=BLOQUEO_MIN)).isoformat(timespec="seconds")
            intentos = 0
        conn.execute("UPDATE accesos_propietario SET intentos_fallidos=?, bloqueado_hasta=? WHERE unidad_id=?",
                     (intentos, bloqueo, unidad_id))
        conn.commit()
        return None
    conn.execute("UPDATE accesos_propietario SET intentos_fallidos=0, bloqueado_hasta='' WHERE unidad_id=?",
                 (unidad_id,))
    conn.commit()
    u = conn.execute(
        """SELECT u.id AS unidad_id, u.uf, u.propietario, u.piso, c.id AS consorcio_id,
                  c.nombre AS consorcio, c.direccion, c.administrador
           FROM unidades u JOIN consorcios c ON c.id = u.consorcio_id WHERE u.id=?""", (unidad_id,)).fetchone()
    return dict(u) if u else None


def datos_de_la_unidad(conn, sesion: dict, hoy: Optional[date] = None) -> dict:
    """Todo lo que ve el propietario. Solo consulta por la unidad autenticada."""
    hoy = hoy or date.today()
    uf, cid, uid = sesion["uf"], sesion["consorcio_id"], sesion["unidad_id"]
    resumen, detalle = cuenta_corriente(conn, cid, hoy)
    fila = resumen[resumen["UF"] == uf]
    r = fila.iloc[0].to_dict() if not fila.empty else {}
    det = detalle[detalle["UF"] == uf] if not detalle.empty else detalle
    marks = ",".join("?" * len(ESTADOS_COBRADOS))
    pagos = conn.df(
        f"""SELECT id, fecha_pago AS "Fecha", periodo AS "Período", medio AS "Medio",
                   CAST(monto_centavos AS DOUBLE PRECISION) / 100.0 AS "Monto", estado AS "Estado"
            FROM pagos WHERE unidad_id=? AND estado IN ({marks})
            ORDER BY fecha_pago DESC, id DESC LIMIT 36""", [uid, *ESTADOS_COBRADOS])
    return {"resumen": r, "detalle": det, "pagos": pagos}


def pdf_recibo(conn, sesion: dict, pago_id: int) -> bytes:
    """Recibo de un pago de ESTA unidad (si el id es de otra, se rechaza)."""
    ok = conn.execute("SELECT 1 FROM pagos WHERE id=? AND unidad_id=?", (pago_id, sesion["unidad_id"])).fetchone()
    if not ok:
        raise ValueError("Ese pago no corresponde a tu unidad.")
    return generar_recibo_pdf(conn, pago_id, usuario=f"portal UF {sesion['uf']}")


def pdf_estado_cuenta(conn, sesion: dict) -> bytes:
    return generar_estado_cuenta_pdf(conn, sesion["consorcio_id"], sesion["uf"])


# ───────────────────────── pantalla ─────────────────────────
def modo_portal(st) -> bool:
    """True si la app se abrió con ?portal=1 (acceso de propietarios)."""
    try:
        valor = st.query_params.get("portal")
    except Exception:
        try:
            valor = (st.experimental_get_query_params().get("portal") or [None])[0]
        except Exception:
            return False
    if isinstance(valor, (list, tuple)):
        valor = valor[0] if valor else None
    return isinstance(valor, str) and valor.strip() == "1"


def render_portal(st, get_conn, init_db, encabezado=None) -> None:
    if encabezado:
        encabezado("Portal del propietario", "Consulta de deuda y recibos")
    sesion = st.session_state.get("portal_sesion")

    if not sesion:
        st.markdown("### Ingresá con el código que te dio tu administración")
        st.caption("Con tu código podés ver tu deuda, tus pagos y bajar tus recibos. "
                   "Cada código sirve solo para tu unidad.")
        if st.session_state.get("portal_intentos", 0) >= 10:
            st.error("Demasiados intentos en esta sesión. Cerrá y volvé a abrir la página.")
            return
        with st.form("form_portal"):
            codigo = st.text_input("Código de acceso", type="password", placeholder="Ej.: 57-K7M2-9QXA-TH")
            if st.form_submit_button("Ingresar"):
                conn = get_conn()
                try:
                    init_db(conn)
                    encontrada = verificar_acceso(conn, codigo)
                finally:
                    conn.close()
                if encontrada:
                    st.session_state["portal_sesion"] = encontrada
                    st.session_state["portal_intentos"] = 0
                    st.rerun()
                st.session_state["portal_intentos"] = st.session_state.get("portal_intentos", 0) + 1
                st.error(MENSAJE_ERROR)
        return

    c1, c2 = st.columns([4, 1])
    c1.success(f"🏠 {sesion['consorcio']} · Unidad {sesion['uf']}"
               + (f" · {sesion['propietario']}" if sesion.get("propietario") else ""))
    if c2.button("Salir"):
        st.session_state.pop("portal_sesion", None)
        st.rerun()

    conn = get_conn()
    try:
        init_db(conn)
        datos = datos_de_la_unidad(conn, sesion)
        r = datos["resumen"]
        m1, m2, m3 = st.columns(3)
        m1.metric("Total adeudado", fmt_ars(r.get("Total adeudado", 0.0)))
        m2.metric("Capital", fmt_ars(r.get("Capital adeudado", 0.0)))
        m3.metric("Intereses punitorios", fmt_ars(r.get("Interés punitorio", 0.0)))
        if r.get("Saldo a favor", 0) > 0:
            st.info(f"Tenés un saldo a favor de {fmt_ars(r['Saldo a favor'])}, que se aplica a tus próximas expensas.")
        if r.get("Total adeudado", 0) <= 0:
            st.success("Tu unidad no registra deuda a la fecha. ¡Gracias!")
        else:
            st.markdown("#### Detalle de lo adeudado")
            st.dataframe(datos["detalle"].drop(columns=["UF"], errors="ignore"),
                         use_container_width=True, hide_index=True)
            st.caption("Los intereses siguen devengándose por día hasta la cancelación. "
                       "Si ya pagaste, enviá el comprobante a tu administración.")
        try:
            st.download_button("📄 Descargar mi estado de cuenta (PDF)", pdf_estado_cuenta(conn, sesion),
                               f"estado_de_cuenta_UF_{sesion['uf']}.pdf", "application/pdf")
        except ValueError as e:
            st.warning(str(e))

        st.markdown("#### Mis pagos")
        pagos = datos["pagos"]
        if pagos.empty:
            st.caption("Todavía no hay pagos registrados para tu unidad.")
        else:
            for p in pagos.to_dict("records"):
                a, b = st.columns([4, 1])
                a.markdown(f"**{p['Fecha']}** · período {p['Período']} · {fmt_ars(p['Monto'])} · {p['Medio']}")
                clave = f"portal_pdf_{p['id']}"
                if st.session_state.get(clave):
                    b.download_button("Descargar", st.session_state[clave],
                                      f"recibo_UF_{sesion['uf']}_{p['id']}.pdf", "application/pdf",
                                      key=f"dl_{p['id']}")
                elif b.button("Preparar recibo", key=f"prep_{p['id']}"):
                    try:
                        st.session_state[clave] = pdf_recibo(conn, sesion, int(p["id"]))
                        st.rerun()
                    except ValueError as e:
                        st.warning(str(e))
    finally:
        conn.close()
