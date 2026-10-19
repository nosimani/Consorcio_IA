"""
analitica.py — Indicadores de gestión de cobranza por consorcio.

Todo se calcula al vuelo desde `cargos` y `pagos` (los mismos datos que usa la mora), con el mismo
motor de imputación (`mora.simular_cuenta`): así los indicadores nunca contradicen la cuenta corriente.

Definiciones (todas en pesos, calculadas sobre capital salvo que se aclare):
  * Emitido            : suma de cargos con fecha de emisión <= hoy.
  * Cobrado            : capital de los cargos efectivamente pagado a la fecha (sin intereses).
  * Deuda vencida      : capital impago de cargos cuyo vencimiento ya pasó.
  * Índice de morosidad: deuda vencida / emitido de cargos ya vencidos.
  * Cobrabilidad       : capital cobrado / emitido (por período y total).
  * Cobrabilidad en término: parte del cargo pagada hasta vencimiento + días de gracia.
  * Días de pago       : promedio ponderado por capital de (fecha de pago - vencimiento).
                         Negativo = se pagó antes de vencer.
  * Antigüedad         : deuda (capital + interés) por tramos de días de mora.
  * Concentración      : porcentaje de la deuda que explican las 5 unidades que más deben.
No usa machine learning: son cálculos exactos y auditables.
"""
from __future__ import annotations

from datetime import date
from typing import Optional

import pandas as pd

from mora import _cargar, obtener_config_mora, simular_cuenta, tramo_morosidad

TRAMOS = ["A vencer", "1-30 días", "31-60 días", "61-90 días", "Más de 90 días"]

# Umbrales orientativos del semáforo: son una convención de trabajo, no una norma. Ajustalos a tu criterio.
UMBRALES_MOROSIDAD = (10.0, 20.0)       # % : por debajo = bien, hasta el segundo = atención, más = crítico
UMBRALES_COBRABILIDAD = (90.0, 80.0)    # % : por encima = bien, hasta el segundo = atención, menos = crítico


def semaforo_morosidad(pct: float) -> str:
    bajo, alto = UMBRALES_MOROSIDAD
    return "🟢 Bajo control" if pct < bajo else ("🟡 Atención" if pct <= alto else "🔴 Crítico")


def semaforo_cobrabilidad(pct: float) -> str:
    alto, bajo = UMBRALES_COBRABILIDAD
    return "🟢 Bueno" if pct >= alto else ("🟡 Atención" if pct >= bajo else "🔴 Crítico")


def _pesos(centavos) -> float:
    return round(float(centavos) / 100.0, 2)


def _pct(num, den) -> float:
    return round(100.0 * num / den, 2) if den else 0.0


def meses_de_reserva(saldo_fondo: float, gasto_mensual: float) -> Optional[float]:
    """Cuántos meses de gastos cubre el fondo de reserva. None si no hay gasto de referencia."""
    return round(saldo_fondo / gasto_mensual, 1) if gasto_mensual and gasto_mensual > 0 else None


def calcular_indicadores(conn, consorcio_id: int, hoy: Optional[date] = None) -> dict:
    """Devuelve un diccionario con los indicadores y varias tablas (DataFrame) listas para mostrar."""
    from datetime import timedelta

    hoy = hoy or date.today()
    tasa, gracia = obtener_config_mora(conn, consorcio_id)
    datos = _cargar(conn, consorcio_id)
    unidades = {u["id"]: u["uf"] for u in conn.execute(
        "SELECT id, uf FROM unidades WHERE consorcio_id=?", (consorcio_id,))}
    medios = conn.execute(
        """SELECT medio, COUNT(*) AS n, SUM(monto_centavos) AS total FROM pagos
           WHERE consorcio_id=? AND estado IN ('Acreditado','Conciliado') AND fecha_pago<=?
           GROUP BY medio""", (consorcio_id, hoy.isoformat())).fetchall()

    emitido = vencido_emitido = cobrado = deuda_vencida = deuda_a_vencer = interes = 0
    dias_pond = capital_pagado_pond = pagado_termino = medible_termino = 0
    por_periodo: dict[str, dict] = {}
    aging = {t: {"capital": 0, "interes": 0, "unidades": set()} for t in TRAMOS}
    deuda_uf: dict[str, int] = {}
    ufs_en_mora = set()

    for uid, d in datos.items():
        uf = unidades.get(uid)
        if uf is None:
            continue
        estado, _, aplic = simular_cuenta(d["cargos"], d["pagos"], tasa, gracia, hoy)
        por_id = {e["id"]: e for e in estado}
        venc_de = {c["id"]: c["vencimiento"] for c in d["cargos"]}

        # Cobrabilidad en término: estado de cada cargo en su fecha límite (vencimiento + gracia)
        limites = {venc + timedelta(days=gracia) for cid, venc in venc_de.items()
                   if venc + timedelta(days=gracia) <= hoy}
        a_limite = {lim: {e["id"]: e for e in simular_cuenta(d["cargos"], d["pagos"], tasa, gracia, lim)[0]}
                    for lim in limites}

        for e in estado:
            c_orig = e["original"]
            capital_pago = c_orig - e["capital"]
            emitido += c_orig
            cobrado += capital_pago
            p = por_periodo.setdefault(e["periodo"], {"emitido": 0, "cobrado": 0, "vencido": 0,
                                                       "vencido_emitido": 0, "termino": 0, "medible": 0})
            p["emitido"] += c_orig
            p["cobrado"] += capital_pago
            if e["vencimiento"] < hoy:
                vencido_emitido += c_orig
                deuda_vencida += e["capital"]
                p["vencido_emitido"] += c_orig
                p["vencido"] += e["capital"]
            else:
                deuda_a_vencer += e["capital"]
            interes += e["interes"]

            lim = e["vencimiento"] + timedelta(days=gracia)
            if lim in a_limite and e["id"] in a_limite[lim]:
                en_t = c_orig - a_limite[lim][e["id"]]["capital"]
                pagado_termino += en_t
                medible_termino += c_orig
                p["termino"] += en_t
                p["medible"] += c_orig

            if e["capital"] > 0 or e["interes"] > 0:
                dias = max(0, (hoy - e["vencimiento"]).days)
                tramo = tramo_morosidad(dias, True)
                if tramo in aging:
                    aging[tramo]["capital"] += e["capital"]
                    aging[tramo]["interes"] += e["interes"]
                    aging[tramo]["unidades"].add(uf)
                deuda_uf[uf] = deuda_uf.get(uf, 0) + e["capital"] + e["interes"]
                if e["capital"] > 0 and e["vencimiento"] < hoy:
                    ufs_en_mora.add(uf)

        for a in aplic:
            if a["capital"] > 0 and a["cargo_id"] in venc_de:
                dias_pond += (a["fecha"] - venc_de[a["cargo_id"]]).days * a["capital"]
                capital_pagado_pond += a["capital"]

    total_deuda = sum(deuda_uf.values())
    top5 = sum(sorted(deuda_uf.values(), reverse=True)[:5])
    n_uf = len(unidades)
    total_medios = sum(m["total"] for m in medios)
    electronico = sum(m["total"] for m in medios if m["medio"] != "Efectivo")

    filas_periodo = []
    for per in sorted(por_periodo):
        p = por_periodo[per]
        filas_periodo.append({
            "Período": per, "Emitido": _pesos(p["emitido"]), "Cobrado": _pesos(p["cobrado"]),
            "Cobrabilidad %": _pct(p["cobrado"], p["emitido"]),
            "En término %": _pct(p["termino"], p["medible"]) if p["medible"] else None,
            "Deuda vencida": _pesos(p["vencido"]),
            "Morosidad %": _pct(p["vencido"], p["vencido_emitido"]) if p["vencido_emitido"] else None})

    filas_aging = [{"Tramo": t, "Capital": _pesos(aging[t]["capital"]), "Interés": _pesos(aging[t]["interes"]),
                    "Total": _pesos(aging[t]["capital"] + aging[t]["interes"]),
                    "% de la deuda": _pct(aging[t]["capital"] + aging[t]["interes"], total_deuda),
                    "Unidades": len(aging[t]["unidades"])} for t in TRAMOS]

    filas_medios = sorted(({"Medio de pago": m["medio"], "Pagos": m["n"], "Total": _pesos(m["total"]),
                            "% del cobrado": _pct(m["total"], total_medios)} for m in medios),
                          key=lambda x: -x["Total"])

    morosidad = _pct(deuda_vencida, vencido_emitido)
    cobrabilidad = _pct(cobrado, emitido)
    return {
        "hay_datos": emitido > 0,
        "fecha": hoy,
        "emitido": _pesos(emitido), "cobrado": _pesos(cobrado),
        "deuda_vencida": _pesos(deuda_vencida), "deuda_a_vencer": _pesos(deuda_a_vencer),
        "interes_adeudado": _pesos(interes), "deuda_total": _pesos(total_deuda),
        "morosidad_pct": morosidad, "cobrabilidad_pct": cobrabilidad,
        "en_termino_pct": _pct(pagado_termino, medible_termino) if medible_termino else None,
        "dias_promedio_pago": round(dias_pond / capital_pagado_pond, 1) if capital_pagado_pond else None,
        "unidades": n_uf, "unidades_en_mora": len(ufs_en_mora),
        "unidades_en_mora_pct": _pct(len(ufs_en_mora), n_uf),
        "concentracion_top5_pct": _pct(top5, total_deuda),
        "pagos_electronicos_pct": _pct(electronico, total_medios),
        "gasto_mensual_referencia": _pesos(
            sum(p["emitido"] for per, p in sorted(por_periodo.items())[-3:]) / max(1, len(sorted(por_periodo)[-3:]))
        ) if por_periodo else 0.0,
        "semaforo_morosidad": semaforo_morosidad(morosidad),
        "semaforo_cobrabilidad": semaforo_cobrabilidad(cobrabilidad),
        "por_periodo": pd.DataFrame(filas_periodo),
        "aging": pd.DataFrame(filas_aging),
        "medios": pd.DataFrame(filas_medios),
        "deuda_por_uf": pd.DataFrame(
            sorted(({"UF": uf, "Deuda total": _pesos(v)} for uf, v in deuda_uf.items()),
                   key=lambda x: -x["Deuda total"])),
    }


def lecturas(ind: dict) -> list[str]:
    """Frases en lenguaje llano que resumen lo más importante. Solo afirma lo que los números sostienen."""
    if not ind["hay_datos"]:
        return []
    out = []
    if ind["deuda_vencida"] <= 0:
        out.append("No hay deuda vencida a la fecha.")
    else:
        out.append(f"{ind['unidades_en_mora']} de {ind['unidades']} unidades "
                   f"({ind['unidades_en_mora_pct']:.0f} %) tienen deuda vencida; el índice de morosidad es "
                   f"{ind['morosidad_pct']:.1f} %.")
        if ind["unidades_en_mora"] > 5 and ind["concentracion_top5_pct"] >= 60:
            out.append(f"Las 5 unidades que más deben concentran el {ind['concentracion_top5_pct']:.0f} % "
                       "de la deuda: conviene gestionar primero esos casos.")
        elif ind["unidades_en_mora"] <= 5 and ind["unidades_en_mora"] > 0:
            out.append("La deuda está en pocas unidades: la gestión caso por caso es viable.")
    mas90 = ind["aging"].loc[ind["aging"]["Tramo"] == "Más de 90 días"]
    if not mas90.empty and mas90.iloc[0]["Total"] > 0:
        out.append(f"Hay {mas90.iloc[0]['Unidades']} unidad(es) con más de 90 días de mora "
                   f"($ {mas90.iloc[0]['Total']:,.2f}). Es la deuda más difícil de recuperar: "
                   "evaluá un plan de pagos o la vía legal.")
    if ind["dias_promedio_pago"] is not None:
        d = ind["dias_promedio_pago"]
        out.append("En promedio se paga " + (f"{abs(d):.0f} días antes del vencimiento." if d < 0 else
                   (f"{d:.0f} días después del vencimiento." if d > 0 else "el día del vencimiento.")))
    return out


# ───────────────────────── presentación (Streamlit se recibe como argumento) ─────────────────────────
def render_panel_indicadores(st, ind: dict, clave: str = "ind") -> None:
    """Dibuja el panel de indicadores. `clave` evita choques de widgets si se muestra en dos pantallas."""
    from mora import fmt_ars

    if not ind or not ind.get("hay_datos"):
        st.info("Todavía no hay cargos emitidos para este edificio. Cuando emitas las expensas en "
                "💵 Cobranzas, Mora y Recibos, acá aparecen los indicadores.")
        return

    f1 = st.columns(4)
    f1[0].metric("Índice de morosidad", f"{ind['morosidad_pct']:.1f} %", ind["semaforo_morosidad"], delta_color="off")
    f1[1].metric("Cobrabilidad", f"{ind['cobrabilidad_pct']:.1f} %", ind["semaforo_cobrabilidad"], delta_color="off")
    f1[2].metric("Cobrado en término",
                 f"{ind['en_termino_pct']:.1f} %" if ind["en_termino_pct"] is not None else "—")
    d = ind["dias_promedio_pago"]
    f1[3].metric("Días promedio de pago", "—" if d is None else f"{d:+.1f}",
                 "respecto del vencimiento", delta_color="off")
    f2 = st.columns(4)
    f2[0].metric("Deuda total", fmt_ars(ind["deuda_total"]))
    f2[1].metric("Deuda vencida (capital)", fmt_ars(ind["deuda_vencida"]))
    f2[2].metric("Intereses adeudados", fmt_ars(ind["interes_adeudado"]))
    f2[3].metric("Unidades en mora", f"{ind['unidades_en_mora']} de {ind['unidades']}")

    for frase in lecturas(ind):
        st.markdown(f"- {frase}")

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("##### Antigüedad de la deuda")
        st.bar_chart(ind["aging"].set_index("Tramo")["Total"], use_container_width=True)
        st.dataframe(ind["aging"], use_container_width=True, hide_index=True)
    with c2:
        st.markdown("##### Evolución por período")
        pp = ind["por_periodo"]
        if len(pp) >= 2:
            st.line_chart(pp.set_index("Período")[["Cobrabilidad %", "En término %"]], use_container_width=True)
        st.dataframe(pp, use_container_width=True, hide_index=True)

    c3, c4 = st.columns(2)
    with c3:
        st.markdown("##### Cobrado por medio de pago")
        if ind["medios"].empty:
            st.caption("Todavía no hay pagos acreditados.")
        else:
            st.dataframe(ind["medios"], use_container_width=True, hide_index=True)
            st.caption(f"Pagos no efectivos: {ind['pagos_electronicos_pct']:.0f} % de lo cobrado.")
    with c4:
        st.markdown("##### Unidades que más deben")
        if ind["deuda_por_uf"].empty:
            st.caption("Ninguna unidad registra deuda.")
        else:
            st.dataframe(ind["deuda_por_uf"].head(5), use_container_width=True, hide_index=True)
            st.caption(f"Estas 5 concentran el {ind['concentracion_top5_pct']:.0f} % de la deuda.")

    with st.expander("🛟 Fondo de reserva: ¿para cuántos meses alcanza?"):
        gasto = st.number_input("Gasto mensual de referencia ($)", min_value=0.0,
                                value=float(ind["gasto_mensual_referencia"]), step=1000.0, key=f"{clave}_gasto")
        saldo = st.number_input("Saldo actual del fondo de reserva ($)", min_value=0.0, value=0.0,
                                step=1000.0, key=f"{clave}_fondo")
        st.caption("El gasto de referencia propuesto es el promedio de lo emitido en los últimos 3 períodos "
                   "(aproximación a los gastos reales; corregilo si tenés el dato exacto).")
        meses = meses_de_reserva(saldo, gasto)
        if meses is not None and saldo > 0:
            st.metric("El fondo cubre", f"{meses:.1f} meses de gastos")

    st.caption(f"Datos al {ind['fecha']:%d/%m/%Y}. Cobrabilidad y morosidad se calculan sobre capital, sin "
               "intereses. Los umbrales del semáforo (morosidad: bajo 10 %, crítico sobre 20 %; cobrabilidad: "
               "buena desde 90 %, crítica bajo 80 %) son una referencia orientativa, no una norma.")
