"""
recibos.py — Recibos de pago y estados de cuenta en PDF (reportlab).

* El recibo se emite solo para pagos ACREDITADOS / CONCILIADOS (nunca pendientes ni anulados).
* Al emitirlo se guarda una FOTO de la imputación (intereses / capital por período) en la
  tabla `recibos`: reimprimirlo siempre da el mismo documento, aunque después cambie la mora.
* Cada recibo lleva un código de verificación (HMAC) que se puede comprobar con
  `verificar_recibo`. Definí la variable de entorno RECIBOS_SECRET con una clave propia.
"""
from __future__ import annotations

import hashlib
import hmac
import io
import json
import os
import zipfile
from datetime import date, datetime
from typing import Optional
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from modulo_cobranzas import ESTADOS_COBRADOS, _auditar, consorcio_pertenece
from mora import cuenta_corriente, fmt_ars, imputacion_de_pago, obtener_config_mora

AZUL = colors.HexColor("#0d1e3d")
GRIS = colors.HexColor("#f1f5f9")
_ss = getSampleStyleSheet()
ST = {
    "n": ParagraphStyle("n", parent=_ss["Normal"], fontSize=9.5, leading=13),
    "chico": ParagraphStyle("chico", parent=_ss["Normal"], fontSize=7.5, leading=10, textColor=colors.grey),
    "titulo": ParagraphStyle("titulo", parent=_ss["Title"], fontSize=17, textColor=AZUL, spaceAfter=2),
    "der": ParagraphStyle("der", parent=_ss["Normal"], fontSize=9.5, leading=13, alignment=2),
    "total": ParagraphStyle("total", parent=_ss["Normal"], fontSize=14, leading=18, alignment=2, textColor=AZUL),
}


def _p(txt, estilo="n"):
    return Paragraph(escape(str(txt)), ST[estilo])


def _m(centavos: int) -> str:
    return fmt_ars(centavos / 100)


def _tabla(filas, anchos, encabezado=True, derecha_desde=1, total=False):
    t = Table(filas, colWidths=anchos, repeatRows=1 if encabezado else 0)
    est = [("FONTSIZE", (0, 0), (-1, -1), 9), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
           ("ALIGN", (derecha_desde, 0), (-1, -1), "RIGHT"),
           ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, GRIS]),
           ("LINEBELOW", (0, 0), (-1, -1), 0.25, colors.HexColor("#cbd5e1")),
           ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5)]
    if encabezado:
        est += [("BACKGROUND", (0, 0), (-1, 0), AZUL), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold")]
    if total:
        est += [("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"), ("LINEABOVE", (0, -1), (-1, -1), 1, AZUL)]
    t.setStyle(TableStyle(est))
    return t


def _info(pares):
    t = Table([[_p(k, "chico"), _p(v)] for k, v in pares], colWidths=[42 * mm, 128 * mm])
    t.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("TOPPADDING", (0, 0), (-1, -1), 2),
                           ("BOTTOMPADDING", (0, 0), (-1, -1), 2)]))
    return t


def _encabezado(titulo, derecha, admin_info):
    nombre = (admin_info or {}).get("nombre", "")
    extra = " · ".join(f"{k} {v}" for k, v in (admin_info or {}).items() if k != "nombre" and v)
    izq = [_p(nombre or "Administración de consorcios"), _p(extra, "chico")]
    t = Table([[izq, [_p(derecha[0], "der"), _p(derecha[1], "chico")]]], colWidths=[100 * mm, 70 * mm])
    t.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("LINEBELOW", (0, 0), (-1, 0), 1.2, AZUL),
                           ("BOTTOMPADDING", (0, 0), (-1, 0), 8)]))
    return [t, Spacer(1, 8), Paragraph(escape(titulo), ST["titulo"]), Spacer(1, 6)]


def _construir(story, titulo_doc) -> bytes:
    buf = io.BytesIO()
    SimpleDocTemplate(buf, pagesize=A4, leftMargin=20 * mm, rightMargin=20 * mm, topMargin=18 * mm,
                      bottomMargin=18 * mm, title=titulo_doc, author="Consorcio_IA").build(story)
    return buf.getvalue()


# ───────────────────────── código de verificación ─────────────────────────
def codigo_verificacion(nro: str, pago_id: int, monto_centavos: int, uf: str, fecha: str) -> str:
    clave = os.getenv("RECIBOS_SECRET", "cambiar-esta-clave").encode()
    msg = f"{nro}|{pago_id}|{monto_centavos}|{uf}|{fecha}".encode()
    return hmac.new(clave, msg, hashlib.sha256).hexdigest()[:12].upper()


def verificar_recibo(conn, nro_recibo: str, codigo: str) -> bool:
    r = conn.execute("""SELECT r.codigo, r.nro_recibo, p.id, p.monto_centavos, p.fecha_pago, u.uf, p.estado
                        FROM recibos r JOIN pagos p ON p.id=r.pago_id JOIN unidades u ON u.id=p.unidad_id
                        WHERE r.nro_recibo=?""", (nro_recibo.strip(),)).fetchone()
    if not r or r["estado"] not in ESTADOS_COBRADOS:
        return False
    esperado = codigo_verificacion(r["nro_recibo"], r["id"], r["monto_centavos"], r["uf"], r["fecha_pago"])
    return hmac.compare_digest(esperado, (codigo or "").strip().upper())


# ───────────────────────── recibo de pago ─────────────────────────
def emitir_recibo(conn, pago_id: int, usuario: str, administrador: Optional[str] = None) -> dict:
    """Crea (o recupera) la foto del recibo. Si pasás `administrador`, verifica que el pago
    sea de un consorcio suyo."""
    p = conn.execute(
        """SELECT p.*, c.nombre AS consorcio, c.direccion, c.administrador, u.uf, u.propietario, u.piso
           FROM pagos p JOIN consorcios c ON c.id=p.consorcio_id JOIN unidades u ON u.id=p.unidad_id
           WHERE p.id=?""", (pago_id,)).fetchone()
    if not p:
        raise ValueError("Pago inexistente.")
    if administrador is not None and not consorcio_pertenece(conn, p["consorcio_id"], administrador):
        raise ValueError("Ese pago no pertenece a tus consorcios.")
    if p["estado"] not in ESTADOS_COBRADOS:
        raise ValueError("Solo se emiten recibos de pagos acreditados (este está "
                         f"'{p['estado']}').")

    previo = conn.execute("SELECT * FROM recibos WHERE pago_id=?", (pago_id,)).fetchone()
    if previo:
        d = json.loads(previo["desglose_json"])
        d["codigo"] = previo["codigo"]
        return d

    nro = p["nro_recibo"] or f"R-{p['consorcio_id']:03d}-{p['id']:08d}"
    imp = imputacion_de_pago(conn, pago_id)
    d = {"nro_recibo": nro, "emitido_en": datetime.now().isoformat(timespec="seconds"),
         "consorcio": p["consorcio"], "direccion": p["direccion"], "administrador": p["administrador"],
         "uf": p["uf"], "piso": p["piso"], "propietario": p["propietario"], "periodo": p["periodo"],
         "fecha_pago": p["fecha_pago"], "monto": p["monto_centavos"], "medio": p["medio"],
         "entidad": p["entidad"], "referencia": p["referencia"], **imp}
    codigo = codigo_verificacion(nro, pago_id, p["monto_centavos"], p["uf"], p["fecha_pago"])
    conn.execute("INSERT INTO recibos (pago_id, nro_recibo, emitido_en, emitido_por, desglose_json, codigo) "
                 "VALUES (?,?,?,?,?,?)", (pago_id, nro, d["emitido_en"], usuario, json.dumps(d), codigo))
    conn.execute("UPDATE pagos SET nro_recibo=? WHERE id=? AND nro_recibo IS NULL", (nro, pago_id))
    _auditar(conn, pago_id, "RECIBO", usuario, nro)
    conn.commit()
    d["codigo"] = codigo
    return d


def generar_recibo_pdf(conn, pago_id: int, usuario: str, admin_info: Optional[dict] = None,
                       administrador: Optional[str] = None) -> bytes:
    d = emitir_recibo(conn, pago_id, usuario, administrador)
    fecha = date.fromisoformat(d["fecha_pago"]).strftime("%d/%m/%Y")
    info = admin_info or {"nombre": d["administrador"]}
    story = _encabezado("RECIBO DE PAGO DE EXPENSAS",
                        (f"N° {d['nro_recibo']}", f"Emitido el {d['emitido_en'][:10]}"), info)
    medio = d["medio"] + (f" — {d['entidad']}" if d["entidad"] else "")
    story += [_info([("Consorcio", d["consorcio"]), ("Dirección", d["direccion"] or "—"),
                     ("Unidad funcional", f"{d['uf']}" + (f" (piso {d['piso']})" if d["piso"] else "")),
                     ("Propietario", d["propietario"] or "—"), ("Fecha de pago", fecha),
                     ("Medio de pago", medio), ("N° de operación", d["referencia"] or "—")]),
              Spacer(1, 10), _p("Imputación del pago", "n")]

    filas = [["Período", "Intereses punitorios", "Capital", "Subtotal"]]
    for ln in d["lineas"]:
        filas.append([ln["periodo"], _m(ln["interes"]), _m(ln["capital"]), _m(ln["interes"] + ln["capital"])])
    if d["a_favor_generado"] > 0:
        filas.append(["Saldo a favor generado", "", "", _m(d["a_favor_generado"])])
    filas.append(["TOTAL", _m(d["interes"]), _m(d["capital"] + d["a_favor_generado"]), _m(d["monto"])])
    story += [_tabla(filas, [55 * mm, 40 * mm, 40 * mm, 35 * mm], total=True), Spacer(1, 12),
              Paragraph(f"TOTAL RECIBIDO: <b>{escape(_m(d['monto']))}</b>", ST["total"]), Spacer(1, 8),
              _info([("Saldo adeudado luego de este pago", _m(d["saldo_posterior"])),
                     ("Saldo a favor de la unidad", _m(d["saldo_a_favor"]))]),
              Spacer(1, 18),
              _p(f"Código de verificación: {d['codigo']}  ·  Recibo {d['nro_recibo']}. "
                 "Comprobante emitido por el sistema de administración a partir de un pago registrado "
                 "y acreditado. Conservelo como constancia de pago.", "chico")]
    return _construir(story, f"Recibo {d['nro_recibo']}")


# ───────────────────────── estado de cuenta / aviso de deuda ─────────────────────────
def generar_estado_cuenta_pdf(conn, consorcio_id: int, uf: str, hoy: Optional[date] = None,
                              admin_info: Optional[dict] = None) -> bytes:
    hoy = hoy or date.today()
    uf = uf.strip().upper()
    res, det = cuenta_corriente(conn, consorcio_id, hoy)
    fila = res[res["UF"] == uf]
    if fila.empty:
        raise ValueError(f"La UF {uf} no existe en ese consorcio.")
    r = fila.iloc[0]
    cons = conn.execute("SELECT nombre, direccion, administrador FROM consorcios WHERE id=?",
                        (consorcio_id,)).fetchone()
    tasa, gracia = obtener_config_mora(conn, consorcio_id)
    info = admin_info or {"nombre": cons["administrador"]}
    story = _encabezado("ESTADO DE CUENTA", ("Estado de cuenta", f"al {hoy:%d/%m/%Y}"), info)
    story += [_info([("Consorcio", cons["nombre"]), ("Dirección", cons["direccion"] or "—"),
                     ("Unidad funcional", uf), ("Propietario", r["Propietario"] or "—"),
                     ("Interés punitorio", f"{tasa * 100:.2f} % mensual, devengado por día"
                      + (f" (gracia: {gracia} días)" if gracia else ""))]), Spacer(1, 10)]

    d = det[det["UF"] == uf] if not det.empty else det
    if d.empty:
        story.append(_p("La unidad no registra deuda a la fecha."))
        if r["Saldo a favor"] > 0:
            story.append(_p(f"Saldo a favor: {fmt_ars(r['Saldo a favor'])}"))
    else:
        filas = [["Período", "Vencimiento", "Días", "Capital", "Interés", "Total"]]
        for x in d.to_dict("records"):
            filas.append([x["Período"], date.fromisoformat(x["Vencimiento"]).strftime("%d/%m/%Y"),
                          str(x["Días de mora"]), fmt_ars(x["Capital adeudado"]),
                          fmt_ars(x["Interés adeudado"]), fmt_ars(x["Capital adeudado"] + x["Interés adeudado"])])
        filas.append(["TOTAL", "", "", fmt_ars(r["Capital adeudado"]), fmt_ars(r["Interés punitorio"]),
                      fmt_ars(r["Total adeudado"])])
        story += [_tabla(filas, [24 * mm, 28 * mm, 14 * mm, 36 * mm, 34 * mm, 34 * mm], derecha_desde=2,
                         total=True), Spacer(1, 10),
                  Paragraph(f"TOTAL ADEUDADO: <b>{escape(fmt_ars(r['Total adeudado']))}</b>", ST["total"]),
                  Spacer(1, 8),
                  _p("Los intereses continúan devengándose diariamente hasta la cancelación de la deuda. "
                     "Si ya abonó, envíe el comprobante a la administración para su registro.", "chico")]
    return _construir(story, f"Estado de cuenta UF {uf}")


def generar_estados_cuenta_zip(conn, consorcio_id: int, hoy: Optional[date] = None,
                               admin_info: Optional[dict] = None) -> tuple[bytes, int]:
    """Un PDF por cada UF con deuda, en un .zip listo para enviar. Devuelve (zip, cantidad)."""
    hoy = hoy or date.today()
    res, _ = cuenta_corriente(conn, consorcio_id, hoy)
    deudoras = res[res["Total adeudado"] > 0]["UF"].tolist()
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for uf in deudoras:
            z.writestr(f"estado_cuenta_UF_{uf}.pdf", generar_estado_cuenta_pdf(conn, consorcio_id, uf, hoy, admin_info))
    return buf.getvalue(), len(deudoras)
