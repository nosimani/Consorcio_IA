"""
mora.py — Cuenta corriente por UF, interés punitorio automático y tramos de morosidad.

Método (todo en centavos enteros, Decimal para el cálculo):
  * Cada expensa liquidada es un CARGO con fecha de emisión y vencimiento.
  * El interés se devenga por día sobre el capital impago, DESPUÉS de
    vencimiento + días de gracia:   interés = capital × tasa_mensual × días / 30
    (interés simple sobre capital: no se capitalizan intereses).
  * Los pagos se imputan en orden cronológico: por cada cargo, del más antiguo al más
    nuevo, primero a los intereses acumulados y luego al capital. Lo que sobra queda
    como saldo a favor y se aplica a los próximos cargos.
  * La mora no se guarda: se recalcula al vuelo desde cargos y pagos, así siempre es
    consistente y auditable (si se anula un pago, la deuda se recalcula sola).

La tasa y el método deben surgir de tu reglamento de copropiedad / lo resuelto en
asamblea: este módulo solo aplica los parámetros que cargues en `configurar_mora`.
"""
from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional

import pandas as pd

from modulo_cobranzas import ESTADOS_COBRADOS, _auditar, _validar_periodo, a_centavos


def _redondeo(x: Decimal) -> int:
    return int(x.quantize(Decimal("1"), rounding=ROUND_HALF_UP))


# ───────────────────────── configuración ─────────────────────────
def configurar_mora(conn, consorcio_id: int, tasa_mensual_pct, dias_gracia: int = 0) -> None:
    """tasa_mensual_pct: porcentaje mensual (ej. 3 = 3 % mensual)."""
    tasa = Decimal(str(tasa_mensual_pct)) / 100
    if not (0 <= tasa <= 1):
        raise ValueError("La tasa mensual debe estar entre 0 % y 100 %.")
    if dias_gracia < 0:
        raise ValueError("Los días de gracia no pueden ser negativos.")
    conn.execute(
        """INSERT INTO config_mora (consorcio_id, tasa_mensual, dias_gracia) VALUES (?,?,?)
           ON CONFLICT(consorcio_id) DO UPDATE SET
             tasa_mensual=excluded.tasa_mensual, dias_gracia=excluded.dias_gracia""",
        (consorcio_id, str(tasa), int(dias_gracia)))
    conn.commit()


def obtener_config_mora(conn, consorcio_id: int) -> tuple[Decimal, int]:
    r = conn.execute("SELECT tasa_mensual, dias_gracia FROM config_mora WHERE consorcio_id=?",
                     (consorcio_id,)).fetchone()
    return (Decimal(r["tasa_mensual"]), r["dias_gracia"]) if r else (Decimal("0"), 0)


# ───────────────────────── emisión de cargos ─────────────────────────
def emitir_cargos(conn, consorcio_id: int, periodo: str, expensas_por_uf: dict,
                  vencimiento: date, usuario: str, concepto: str = "Expensa ordinaria",
                  fecha_emision: Optional[date] = None) -> dict:
    """Convierte la liquidación (liquidacion.expensas_por_uf) en cargos exigibles.
    Es idempotente: una UF que ya tiene cargo para ese período/concepto no se toca."""
    _validar_periodo(periodo)
    emision = fecha_emision or date.today()
    if vencimiento < emision:
        raise ValueError("El vencimiento no puede ser anterior a la emisión.")
    res = {"creados": 0, "existentes": 0, "sin_unidad": []}
    for uf, monto in expensas_por_uf.items():
        cent = a_centavos(monto)
        u = conn.execute("SELECT id FROM unidades WHERE consorcio_id=? AND uf=?",
                         (consorcio_id, str(uf).strip().upper())).fetchone()
        if not u:
            res["sin_unidad"].append(uf)
            continue
        if cent <= 0:
            continue
        ya = conn.execute("SELECT 1 FROM cargos WHERE unidad_id=? AND periodo=? AND concepto=?",
                          (u["id"], periodo, concepto)).fetchone()
        if ya:
            res["existentes"] += 1
            continue
        conn.execute(
            """INSERT INTO cargos (consorcio_id, unidad_id, periodo, concepto, monto_centavos,
                   fecha_emision, vencimiento, creado_por, creado_en) VALUES (?,?,?,?,?,?,?,?,?)""",
            (consorcio_id, u["id"], periodo, concepto, cent, emision.isoformat(),
             vencimiento.isoformat(), usuario, datetime.now().isoformat(timespec="seconds")))
        res["creados"] += 1
    _auditar(conn, None, "EMISION_CARGOS", usuario,
             f"consorcio {consorcio_id} {periodo}: {res['creados']} creados, {res['existentes']} existentes")
    conn.commit()
    return res


# ───────────────────────── motor de cálculo ─────────────────────────
def simular_cuenta(cargos: list[dict], pagos: list[dict], tasa: Decimal,
                   gracia: int, hoy: date) -> tuple[list[dict], int, list[dict]]:
    """cargos: {id, periodo, concepto, emision(date), vencimiento(date), monto}
       pagos : {id, fecha(date), monto}   (centavos)
       Devuelve (estado de cada cargo, saldo a favor, aplicaciones de pagos)."""
    from datetime import timedelta
    est = {c["id"]: {"id": c["id"], "periodo": c["periodo"], "concepto": c["concepto"],
                     "vencimiento": c["vencimiento"], "original": c["monto"], "capital": 0,
                     "interes": 0, "emitido": False,
                     "desde": max(c["vencimiento"] + timedelta(days=gracia), c["emision"])}
           for c in cargos}
    eventos = [(c["emision"], 0, c["id"], "cargo", c) for c in cargos if c["emision"] <= hoy]
    eventos += [(p["fecha"], 1, p["id"], "pago", p) for p in pagos if p["fecha"] <= hoy]
    eventos.sort(key=lambda e: (e[0], e[1], e[2]))

    credito, aplic = 0, []

    def devengar(hasta: date) -> None:
        for e in est.values():
            if e["emitido"] and e["capital"] > 0 and hasta > e["desde"]:
                dias = (hasta - e["desde"]).days
                e["interes"] += _redondeo(Decimal(e["capital"]) * tasa * dias / 30)
                e["desde"] = hasta

    for fecha, _, _, tipo, ev in eventos:
        devengar(fecha)
        if tipo == "cargo":
            e = est[ev["id"]]
            e["emitido"], e["capital"] = True, ev["monto"]
            usar = min(credito, e["capital"])
            if usar:
                e["capital"] -= usar
                credito -= usar
                aplic.append({"pago_id": None, "fecha": fecha, "cargo_id": e["id"],
                              "periodo": e["periodo"], "interes": 0, "capital": usar})
        else:
            resto = ev["monto"]
            for e in sorted((x for x in est.values() if x["emitido"]),
                            key=lambda x: (x["vencimiento"], x["id"])):
                if resto <= 0:
                    break
                pi = min(resto, e["interes"])
                pc = min(resto - pi, e["capital"])
                if pi or pc:
                    e["interes"] -= pi
                    e["capital"] -= pc
                    resto -= pi + pc
                    aplic.append({"pago_id": ev["id"], "fecha": fecha, "cargo_id": e["id"],
                                  "periodo": e["periodo"], "interes": pi, "capital": pc})
            credito += resto
    devengar(hoy)
    return [e for e in est.values() if e["emitido"]], credito, aplic


def _cargar(conn, consorcio_id: int, unidad_id: Optional[int] = None):
    filtro, params = ("AND unidad_id=?", [unidad_id]) if unidad_id else ("", [])
    cargos = conn.execute(
        f"""SELECT id, unidad_id, periodo, concepto, monto_centavos, fecha_emision, vencimiento
            FROM cargos WHERE consorcio_id=? {filtro}""", [consorcio_id, *params]).fetchall()
    pagos = conn.execute(
        f"""SELECT id, unidad_id, fecha_pago, monto_centavos FROM pagos
            WHERE consorcio_id=? {filtro} AND estado IN ({",".join("?" * len(ESTADOS_COBRADOS))})""",
        [consorcio_id, *params, *ESTADOS_COBRADOS]).fetchall()
    por_u: dict[int, dict] = {}
    for c in cargos:
        por_u.setdefault(c["unidad_id"], {"cargos": [], "pagos": []})["cargos"].append(
            {"id": c["id"], "periodo": c["periodo"], "concepto": c["concepto"],
             "monto": c["monto_centavos"], "emision": date.fromisoformat(c["fecha_emision"]),
             "vencimiento": date.fromisoformat(c["vencimiento"])})
    for p in pagos:
        por_u.setdefault(p["unidad_id"], {"cargos": [], "pagos": []})["pagos"].append(
            {"id": p["id"], "fecha": date.fromisoformat(p["fecha_pago"]), "monto": p["monto_centavos"]})
    return por_u


def tramo_morosidad(dias: int, hay_deuda: bool) -> str:
    if not hay_deuda:
        return "Al día"
    if dias <= 0:
        return "A vencer"
    if dias <= 30:
        return "1-30 días"
    if dias <= 60:
        return "31-60 días"
    if dias <= 90:
        return "61-90 días"
    return "Más de 90 días"


# ───────────────────────── consultas ─────────────────────────
def cuenta_corriente(conn, consorcio_id: int, hoy: Optional[date] = None
                     ) -> tuple[pd.DataFrame, pd.DataFrame]:
    """(resumen por UF, detalle por cargo impago) a la fecha `hoy`."""
    hoy = hoy or date.today()
    tasa, gracia = obtener_config_mora(conn, consorcio_id)
    datos = _cargar(conn, consorcio_id)
    resumen, detalle = [], []
    for u in conn.execute("SELECT id, uf, propietario, contacto FROM unidades WHERE consorcio_id=? ORDER BY uf",
                          (consorcio_id,)):
        d = datos.get(u["id"], {"cargos": [], "pagos": []})
        estado, credito, _ = simular_cuenta(d["cargos"], d["pagos"], tasa, gracia, hoy)
        impagos = [e for e in estado if e["capital"] > 0 or e["interes"] > 0]
        capital = sum(e["capital"] for e in impagos)
        interes = sum(e["interes"] for e in impagos)
        dias = max([(hoy - e["vencimiento"]).days for e in impagos if e["capital"] > 0], default=0)
        for e in sorted(impagos, key=lambda x: x["vencimiento"]):
            detalle.append({"UF": u["uf"], "Período": e["periodo"], "Concepto": e["concepto"],
                            "Vencimiento": e["vencimiento"].isoformat(), "Original": e["original"] / 100,
                            "Capital adeudado": e["capital"] / 100, "Interés adeudado": e["interes"] / 100,
                            "Días de mora": max(0, (hoy - e["vencimiento"]).days) if e["capital"] > 0 else 0})
        resumen.append({"UF": u["uf"], "Propietario": u["propietario"], "Contacto": u["contacto"],
                        "Cargos impagos": sum(1 for e in impagos if e["capital"] > 0),
                        "Capital adeudado": capital / 100, "Interés punitorio": interes / 100,
                        "Total adeudado": (capital + interes) / 100, "Saldo a favor": credito / 100,
                        "Días de mora": max(dias, 0),
                        "Tramo": tramo_morosidad(dias, capital + interes > 0)})
    return pd.DataFrame(resumen), pd.DataFrame(detalle)


def imputacion_de_pago(conn, pago_id: int) -> dict:
    """Cómo se aplicó un pago (intereses / capital por período) y qué deuda quedó después."""
    p = conn.execute("SELECT consorcio_id, unidad_id, fecha_pago, monto_centavos FROM pagos WHERE id=?",
                     (pago_id,)).fetchone()
    if not p:
        raise ValueError("Pago inexistente.")
    fecha = date.fromisoformat(p["fecha_pago"])
    tasa, gracia = obtener_config_mora(conn, p["consorcio_id"])
    d = _cargar(conn, p["consorcio_id"], p["unidad_id"]).get(p["unidad_id"], {"cargos": [], "pagos": []})
    estado, credito, aplic = simular_cuenta(d["cargos"], d["pagos"], tasa, gracia, fecha)
    mias = [a for a in aplic if a["pago_id"] == pago_id]
    aplicado = sum(a["interes"] + a["capital"] for a in mias)
    return {
        "lineas": [{"periodo": a["periodo"], "interes": a["interes"], "capital": a["capital"]} for a in mias],
        "interes": sum(a["interes"] for a in mias),
        "capital": sum(a["capital"] for a in mias),
        "a_favor_generado": p["monto_centavos"] - aplicado,
        "saldo_posterior": sum(e["capital"] + e["interes"] for e in estado),
        "saldo_a_favor": credito,
    }


def intereses_cobrados(conn, consorcio_id: int, desde: date, hasta: date) -> float:
    """Intereses punitorios efectivamente cobrados en el rango: es un ingreso del consorcio
    (se puede cargar como RegistroIngreso en la liquidación)."""
    tasa, gracia = obtener_config_mora(conn, consorcio_id)
    total = 0
    for d in _cargar(conn, consorcio_id).values():
        _, _, aplic = simular_cuenta(d["cargos"], d["pagos"], tasa, gracia, hasta)
        total += sum(a["interes"] for a in aplic if desde <= a["fecha"] <= hasta)
    return total / 100


def fmt_ars(monto: float) -> str:
    """1234.5 -> '$ 1.234,50' (formato argentino)."""
    return "$ " + f"{monto:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def redactar_aviso(fila: dict, consorcio: str, hoy: Optional[date] = None) -> str:
    """Texto listo para copiar y enviar por WhatsApp o email."""
    hoy = hoy or date.today()
    return (f"Hola {fila.get('Propietario') or ''}, te escribimos de la administración de {consorcio}. "
            f"A la fecha ({hoy:%d/%m/%Y}) la UF {fila['UF']} registra expensas impagas por "
            f"{fmt_ars(fila['Capital adeudado'])} más intereses punitorios por "
            f"{fmt_ars(fila['Interés punitorio'])} (total {fmt_ars(fila['Total adeudado'])}). "
            f"Los intereses siguen devengándose hasta la cancelación. Si ya abonaste, enviá el "
            f"comprobante para registrarlo. ¡Gracias!")
