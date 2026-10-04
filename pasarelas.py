"""
pasarelas.py — Verificación de firma y normalización de pagos electrónicos.
Sin dependencias web: se puede probar sin levantar el servidor.
"""
from __future__ import annotations

import hashlib
import hmac
from typing import Optional

from modulo_cobranzas import MedioPago

MP_PAYMENTS_URL = "https://api.mercadopago.com/v1/payments/{}"

# payment_type_id de Mercado Pago -> medio interno
MP_MEDIOS = {
    "credit_card": MedioPago.TARJETA_CREDITO,
    "debit_card": MedioPago.TARJETA_DEBITO,
    "account_money": MedioPago.BILLETERA,
    "bank_transfer": MedioPago.TRANSFERENCIA,
    "ticket": MedioPago.OTRO,          # cupón pagado en Rapipago / Pago Fácil, etc.
    "prepaid_card": MedioPago.OTRO,
}
MP_ESTADOS_REVERSION = {"refunded", "charged_back", "cancelled"}


def verificar_firma_mercadopago(x_signature: Optional[str], x_request_id: Optional[str],
                                data_id: Optional[str], secreto: str) -> bool:
    """Header x-signature = 'ts=...,v1=...'. Manifest firmado con HMAC-SHA256 (hex):
    'id:<data.id>;request-id:<x-request-id>;ts:<ts>;'  (data.id viene en la query string)."""
    if not (x_signature and x_request_id and data_id and secreto):
        return False
    partes = dict(p.strip().split("=", 1) for p in x_signature.split(",") if "=" in p)
    ts, v1 = partes.get("ts"), partes.get("v1")
    if not ts or not v1:
        return False
    manifest = f"id:{data_id.lower()};request-id:{x_request_id};ts:{ts};"  # id alfanumérico -> minúsculas
    esperado = hmac.new(secreto.encode(), manifest.encode(), hashlib.sha256).hexdigest()
    return hmac.compare_digest(esperado, v1)


def verificar_firma_generica(cuerpo: bytes, firma_hex: Optional[str], secreto: str) -> bool:
    """Para integraciones propias o agregadores: X-Signature = HMAC-SHA256 hex del cuerpo crudo."""
    if not (firma_hex and secreto):
        return False
    esperado = hmac.new(secreto.encode(), cuerpo, hashlib.sha256).hexdigest()
    return hmac.compare_digest(esperado, firma_hex)


def obtener_pago_mercadopago(payment_id: str, access_token: str, timeout: int = 10) -> dict:
    """La notificación solo trae el id: el detalle (monto, estado, referencia) se consulta a la API.
    Así el dato real viene de Mercado Pago y no del cuerpo recibido."""
    import requests
    r = requests.get(MP_PAYMENTS_URL.format(payment_id),
                     headers={"Authorization": f"Bearer {access_token}"}, timeout=timeout)
    r.raise_for_status()
    return r.json()


def normalizar_pago_mercadopago(pago: dict) -> dict:
    """Devuelve el dict que consume modulo_cobranzas.procesar_pago_normalizado,
    más 'estado_mp' para decidir si es alta o reversión."""
    fecha = pago.get("date_approved") or pago.get("date_created") or ""
    return {
        "estado_mp": pago.get("status", ""),
        "external_reference": pago.get("external_reference") or "",
        "monto": pago.get("transaction_amount", 0),
        "medio": MP_MEDIOS.get(pago.get("payment_type_id"), MedioPago.OTRO).value,
        "entidad": f"MercadoPago/{pago.get('payment_method_id', '')}".rstrip("/"),
        "referencia": str(pago.get("id", "")),
        "fecha": fecha[:10],
    }
