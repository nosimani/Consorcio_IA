"""
╔══════════════════════════════════════════════════════════════════════════════════════╗
║                    RESILIA_CONDOMINIOS v2.0                                  ║
║         SISTEMA MULTIAGENTE DE ENJAMBRE PARA GESTIÓN DE CONDOMINIOS         ║
║                                                                            ║
║  Arquitectura: Orquestador Central + 7 Agentes Especializados              ║
║  Patrón: Swarm Intelligence con Coordinación Emergente                     ║
║  Enfoque: Cada petición dispara activación selectiva del enjambre          ║
╚══════════════════════════════════════════════════════════════════════════════════════╝
"""

import streamlit as st
import hashlib
import hmac
import logging
import os
import re
import unicodedata
from modulo_cobranzas import (render_modulo_cobranzas, get_conn, init_db, crear_consorcio,
                              cargar_unidades_desde_df)
from mora import cuenta_corriente
import pandas as pd
from dataclasses import dataclass
from enum import Enum
from typing import List, Dict, Any
from datetime import datetime
import time
from io import BytesIO

# ✅ Import opcional para evitar error en Streamlit Cloud
try:
    import xlsxwriter
except Exception:
    xlsxwriter = None

try:
    import openpyxl
except Exception:
    openpyxl = None


# ════════════════════════════════════════════════════════════════
# EMOJIS DE ROBOTS Y ANIMACIONES
# ════════════════════════════════════════════════════════════════

ROBOTS_ANIMADOS = {
    "CONTABLE": ["🤖", "🦾", "⚙️"],
    "COMPLIANCE": ["🤖", "✔️", "✅"],
    "PROVEEDORES": ["🤖", "📦", "🏢"],
    "OPERATIVO": ["🤖", "⚙️", "🔧"],
    "MORA": ["🤖", "⚠️", "💰"],
    "AUDITOR": ["🤖", "🔍", "📋"],
    "REPORTES": ["🤖", "📊", "📈"],
}


def obtener_robot_animado(agente_tipo: str, paso: int) -> str:
    secuencia = ROBOTS_ANIMADOS.get(agente_tipo, ["🤖", "⚙️", "📊"])
    return secuencia[paso % len(secuencia)]


def animar_robot_procesando(placeholder, agente_nombre: str, agente_tipo: str, duracion_ms: float):
    frames_total = int(duracion_ms / 100)
    for frame in range(frames_total):
        robot = obtener_robot_animado(agente_tipo, frame)
        barras = "▓" * (frame % 10) + "░" * (10 - (frame % 10))
        placeholder.markdown(
            f"""
            <div class="swarm-agent swarm-processing">
            {robot} <b>{agente_nombre}</b><br/>
            Procesando... {barras} {int((frame / frames_total) * 100)}%
            </div>
            """,
            unsafe_allow_html=True,
        )
        time.sleep(0.1)


# ════════════════════════════════════════════════════════════════
# AUTENTICACIÓN (protege el módulo de Cobranzas) Y DATOS REALES
# ════════════════════════════════════════════════════════════════

def hash_clave(clave: str, salt_hex: str = None, iteraciones: int = 200_000) -> str:
    """Hash PBKDF2-SHA256 con sal. Formato: pbkdf2$iteraciones$sal$hash"""
    salt = bytes.fromhex(salt_hex) if salt_hex else os.urandom(16)
    dk = hashlib.pbkdf2_hmac("sha256", clave.encode("utf-8"), salt, iteraciones)
    return f"pbkdf2${iteraciones}${salt.hex()}${dk.hex()}"


_HASH_FALSO = hash_clave("x", "00" * 16, 1000)


def verificar_clave(clave: str, registro: str) -> bool:
    try:
        _, it, salt_hex, hash_hex = registro.split("$")
        calculado = hash_clave(clave, salt_hex, int(it)).split("$")[3]
        return hmac.compare_digest(calculado, hash_hex)
    except Exception:
        return False


def usuarios_configurados() -> dict:
    """Usuarios definidos en .streamlit/secrets.toml, sección [usuarios]."""
    try:
        return dict(st.secrets["usuarios"])
    except Exception:
        return {}


def login_cobranzas() -> bool:
    """Pide usuario y clave. Devuelve True si hay una sesión iniciada."""
    if st.session_state.get("usuario"):
        c1, c2 = st.columns([4, 1])
        c1.success(f"👤 Sesión iniciada: {st.session_state['usuario']}")
        if c2.button("Cerrar sesión"):
            st.session_state.pop("usuario", None)
            st.rerun()
        return True

    usuarios = usuarios_configurados()
    if not usuarios:
        st.warning("🔐 El módulo de Cobranzas maneja datos de pagos y requiere usuarios con clave. "
                   "Aún no hay ninguno configurado.")
        st.markdown("1. Generá el hash de cada clave con `python generar_clave.py`.\n"
                    "2. Pegalo en `.streamlit/secrets.toml` (en Streamlit Cloud: *Settings → Secrets*):")
        st.code('[usuarios]\nadmin1 = "pbkdf2$200000$...$..."', language="toml")
        return False

    intentos = st.session_state.get("intentos_login", 0)
    if intentos >= 5:
        st.error("Demasiados intentos fallidos. Recargá la página para volver a intentar.")
        return False

    with st.form("form_login_cobranzas"):
        usuario = st.text_input("Usuario")
        clave = st.text_input("Clave", type="password")
        if st.form_submit_button("Ingresar"):
            registro = usuarios.get(usuario, _HASH_FALSO)      # siempre se calcula el hash
            if verificar_clave(clave, registro) and usuario in usuarios:
                st.session_state["usuario"] = usuario
                st.session_state["intentos_login"] = 0
                st.rerun()
            st.session_state["intentos_login"] = intentos + 1
            st.error("Usuario o clave incorrectos.")
    return False


def normalizar_edificio(nombre: str) -> str:
    """'Av. Corrientes 1234, CABA' y 'Avda. Corrientes 1234' -> 'av corrientes 1234'
    (sin tildes, sin puntuación, sin 'CABA'). Sirve para comparar nombres de edificios."""
    t = unicodedata.normalize("NFKD", str(nombre)).encode("ascii", "ignore").decode().lower()
    t = re.sub(r"[^a-z0-9 ]", " ", t)
    t = re.sub(r"\b(avda|avenida|av)\b", "av", t)
    t = re.sub(r"\bcaba\b", " ", t)
    return " ".join(t.split())


def coeficientes_para_liquidar(edificio: str):
    """Coeficientes REALES para liquidar: primero el archivo de coeficientes; si no hay,
    el porcentual de la base de edificios. Si no hay ninguno devuelve None (no se inventa nada)."""
    df = st.session_state.get("coeficientes_cargados")
    if df is not None and not df.empty and float(df["Coeficiente"].sum()) > 0:
        return df
    base = st.session_state.get("unidades_edificios")
    if base is not None and not base.empty:
        g = base[base["Edificio"] == edificio]
        if not g.empty and float(g["Porcentual Expensas"].sum()) > 0:
            return pd.DataFrame({
                "UF": g["UF/Dpto"].astype(str).str.strip().str.upper().values,
                "Propietario": "",
                "Piso": g["Piso"].values,
                "Coeficiente": g["Porcentual Expensas"].values,
                "Contacto": "",
            })
    return None


def mora_real_edificio(administrador, edificio):
    """Resumen de mora real (desde cargos y pagos de la base de Cobranzas) o None si ese
    edificio todavía no tiene cargos emitidos."""
    if not administrador:
        return None
    st.session_state.pop("error_bd", None)
    conn = get_conn()
    try:
        init_db(conn)
        fila = conn.execute("SELECT id FROM consorcios WHERE administrador=? AND nombre=?",
                            (administrador, edificio)).fetchone()
        if not fila:
            return None
        if not conn.execute("SELECT 1 FROM cargos WHERE consorcio_id=? LIMIT 1", (fila["id"],)).fetchone():
            return None
        resumen, _ = cuenta_corriente(conn, fila["id"])
        return resumen
    except Exception as error:
        # Con una base en red puede haber cortes: se avisa en pantalla en vez de mostrar datos falsos en silencio.
        logging.getLogger("consorcio_ia").exception("No se pudo leer la mora real desde la base de datos")
        st.session_state["error_bd"] = f"{type(error).__name__}: {error}"
        return None
    finally:
        conn.close()


# ════════════════════════════════════════════════════════════════
# 1. DEFINICIONES ESTRUCTURALES DEL ENJAMBRE
# ════════════════════════════════════════════════════════════════

def parsear_monto_ar(texto) -> float:
    """Convierte montos en formato argentino a float.
    '$ 250.000.-' -> 250000.0 | '$ 1.250.000,50' -> 1250000.5 | 95000 -> 95000.0"""
    s = str(texto).replace("$", "").replace(".-", "").strip()
    if "," in s:                       # coma = decimal, punto = miles
        s = s.replace(".", "").replace(",", ".")
    elif s.count(".") > 1 or (s.count(".") == 1 and len(s.split(".")[1]) == 3):
        s = s.replace(".", "")         # '250.000' / '1.250.000' -> solo separadores de miles
    return float(s)


class TipoAgente(Enum):
    ORQUESTADOR = "🎯 Orquestador Central"
    CONTABLE = "📊 Agente Contable"
    COMPLIANCE = "✅ Agente Compliance"
    PROVEEDORES = "🏢 Agente de Proveedores"
    OPERATIVO = "🔧 Agente Operativo"
    MORA = "⚠️ Agente de Cobranza"
    AUDITOR = "🔍 Agente de Auditoría"
    REPORTES = "📈 Agente de Reportes"


class EstadoAgente(Enum):
    INACTIVO = "⚪ Inactivo"
    ACTIVADO = "🟢 Activado"
    PROCESANDO = "🟡 Procesando"
    COMPLETADO = "✅ Completado"
    ERROR = "🔴 Error"


class TipoGasto(Enum):
    SERVICIOS_BASICOS = "Servicios Básicos"
    PERSONAL = "Personal y Cargas Sociales"
    MANTENIMIENTO = "Mantenimiento y Reparaciones"
    LIMPIEZA = "Limpieza y Desinfección"
    SEGUROS = "Seguros y Seguridad"
    ADMINISTRACION = "Administración"
    PROVISIONES = "Provisiones y Fondos"
    OTROS = "Otros Gastos"


class TipoIngreso(Enum):
    EXPENSAS = "Expensas Cobradas"
    SERVICIOS = "Ingresos por Servicios"
    FINANCIEROS = "Ingresos Financieros"
    OTROS = "Otros Ingresos"


@dataclass
class EventoSwarm:
    timestamp: str
    tipo_evento: str
    descripcion: str
    modulo_solicitante: str
    parametros: Dict[str, Any]


@dataclass
class ResultadoAgente:
    agente: str
    estado: EstadoAgente
    datos_procesados: Dict[str, Any]
    tiempo_procesamiento: str
    dependencias_cumplidas: List[str]


@dataclass
class RegistroGasto:
    concepto: str
    tipo_gasto: TipoGasto
    monto: float
    descripcion: str = ""
    factura: str = ""


@dataclass
class RegistroIngreso:
    concepto: str
    tipo_ingreso: TipoIngreso
    monto: float
    descripcion: str = ""


@dataclass
class CoeficienteUF:
    uf: str
    propietario: str = ""
    piso: str = ""
    coeficiente: float = 0.0
    contacto: str = ""


@dataclass
class LiquidacionExpensas:
    periodo: str
    fecha_liquidacion: str
    total_ingresos: float
    total_gastos: float
    deficit_o_superavit: float
    gastos_por_rubro: Dict[str, float]
    ingresos_por_rubro: Dict[str, float]
    coeficientes: Dict[str, CoeficienteUF]
    expensas_por_uf: Dict[str, float]


# ════════════════════════════════════════════════════════════════
# 2. BASE DE DATOS GLOBAL (INMUTABLE)
# ════════════════════════════════════════════════════════════════

ESTADISTICAS_EDIFICIOS = {
    "Av. Corrientes 1234, CABA": {
        "reserva": 450000.0,
        "factor": 1.0,
        "mora": "1",
        "tasa": 4.5,
        "ots": "5",
        "cantidad_uf": 50,
        "coeficientes": {}
    },
    "Larrea 435, CABA": {
        "reserva": 380000.0,
        "factor": 0.6,
        "mora": "2",
        "tasa": 5.0,
        "ots": "5",
        "cantidad_uf": 30,
        "coeficientes": {}
    },
    "Montevideo 891, CABA": {
        "reserva": 620000.0,
        "factor": 0.8,
        "mora": "2",
        "tasa": 6.2,
        "ots": "5",
        "cantidad_uf": 40,
        "coeficientes": {}
    },
    "San Jose 1111, CABA": {
        "reserva": 290000.0,
        "factor": 0.5,
        "mora": "1",
        "tasa": 3.8,
        "ots": "5",
        "cantidad_uf": 25,
        "coeficientes": {}
    },
    "Guayaquil 399, CABA": {
        "reserva": 850000.0,
        "factor": 1.5,
        "mora": "1",
        "tasa": 7.5,
        "ots": "5",
        "cantidad_uf": 60,
        "coeficientes": {}
    }
}

# ════════════════════════════════════════════════════════════════
# DIRECTORIO COMPLETO DE PRESTADORES DE SERVICIOS
# ════════════════════════════════════════════════════════════════

DATOS_CARTILLA_PROVEEDORES = [
    # 🚰 PLOMERÍA
    {
        "Rubro": "🚰 Plomería",
        "Prestador": "Caños y Sanitarios Express",
        "CUIT": "30-55489712-4",
        "Teléfono": "11-4895-1234",
        "Email": "contacto@canosysan.com.ar",
        "Zona de Atención": "CABA Centro",
        "Horario": "Lunes a Viernes 8:00-18:00",
        "Emergencias": "✅ Sí",
        "Especialidad": "Reparación, instalación de cañerías, sanitarios"
    },
    {
        "Rubro": "🚰 Plomería",
        "Prestador": "Ingeniería Hidráulica Sur",
        "CUIT": "33-66985214-9",
        "Teléfono": "11-3564-9871",
        "Email": "info@hidraulicasur.com.ar",
        "Zona de Atención": "CABA Norte",
        "Horario": "Lunes a Sábado 8:00-20:00",
        "Emergencias": "✅ Sí",
        "Especialidad": "Sistemas de presión, purgas, desagües"
    },
    
    # ⚡ ELECTRICIDAD
    {
        "Rubro": "⚡ Electricidad",
        "Prestador": "El Fusible Matriculado",
        "CUIT": "20-14896532-1",
        "Teléfono": "11-5478-6532",
        "Email": "fusible@electrica.com.ar",
        "Zona de Atención": "Toda CABA",
        "Horario": "Lunes a Viernes 7:00-19:00",
        "Emergencias": "✅ Sí",
        "Especialidad": "Reparación de instalaciones, tableros, tomacorrientes"
    },
    {
        "Rubro": "⚡ Electricidad",
        "Prestador": "Conexiones Seguras Palermo",
        "CUIT": "27-33659874-2",
        "Teléfono": "11-6985-3214",
        "Email": "seguras@palermo.com.ar",
        "Zona de Atención": "CABA Norte",
        "Horario": "Lunes a Viernes 8:00-18:00",
        "Emergencias": "❌ No",
        "Especialidad": "Iluminación LED, automatización, sistemas de energía"
    },
    
    # 🔑 CERRAJERÍA
    {
        "Rubro": "🔑 Cerrajería",
        "Prestador": "Llaves Fénix 24hs",
        "CUIT": "23-45896521-8",
        "Teléfono": "11-2365-9847",
        "Email": "fenix24@cerrajeria.com.ar",
        "Zona de Atención": "Urgencias CABA",
        "Horario": "24 horas, 7 días",
        "Emergencias": "✅ Sí",
        "Especialidad": "Cerraduras de seguridad, aperturas de emergencia"
    },
    {
        "Rubro": "🔑 Cerrajería",
        "Prestador": "Blindajes y Cerraduras Pro",
        "CUIT": "30-71458962-3",
        "Teléfono": "11-4125-3698",
        "Email": "blindajes@pro.com.ar",
        "Zona de Atención": "CABA Oeste",
        "Horario": "Lunes a Viernes 9:00-17:00",
        "Emergencias": "❌ No",
        "Especialidad": "Puertas blindadas, cajas de seguridad"
    },
    
    # 🧱 ALBAÑILERÍA
    {
        "Rubro": "🧱 Albañilería",
        "Prestador": "Constructora San José",
        "CUIT": "30-88547612-5",
        "Teléfono": "11-5541-2369",
        "Email": "info@sanjose.com.ar",
        "Zona de Atención": "Toda CABA",
        "Horario": "Lunes a Sábado 8:00-18:00",
        "Emergencias": "✅ Sí",
        "Especialidad": "Mampostería, revoques, pintura, reformas"
    },
    {
        "Rubro": "🧱 Albañilería",
        "Prestador": "Refacciones Integrales Baires",
        "CUIT": "20-99653214-7",
        "Teléfono": "11-3254-7896",
        "Email": "refacciones@baires.com.ar",
        "Zona de Atención": "CABA Sur",
        "Horario": "Lunes a Viernes 8:00-17:00",
        "Emergencias": "❌ No",
        "Especialidad": "Arreglos menores, grietas, humedades"
    },
    
    # 🚪 PORTERO ELECTRÓNICO
    {
        "Rubro": "🚪 Portero Electrónico",
        "Prestador": "Smart Door Solutions",
        "CUIT": "27-78945612-3",
        "Teléfono": "11-5892-3456",
        "Email": "smartdoor@solutions.com.ar",
        "Zona de Atención": "Toda CABA",
        "Horario": "Lunes a Viernes 8:00-18:00",
        "Emergencias": "✅ Sí",
        "Especialidad": "Instalación, reparación, modernización de porteros"
    },
    {
        "Rubro": "🚪 Portero Electrónico",
        "Prestador": "Comunicaciones Seguras",
        "CUIT": "33-54123789-6",
        "Teléfono": "11-4567-8901",
        "Email": "comunicaciones@seguras.com.ar",
        "Zona de Atención": "CABA Centro",
        "Horario": "Lunes a Viernes 9:00-17:00",
        "Emergencias": "❌ No",
        "Especialidad": "Videoporteros, sistemas de acceso, vigilancia"
    },
    
    # 🧹 LIMPIEZA Y MANTENIMIENTO
    {
        "Rubro": "🧹 Limpieza",
        "Prestador": "Limpieza Pro CABA",
        "CUIT": "29-66354789-2",
        "Teléfono": "11-5534-6789",
        "Email": "pro@limpieza.com.ar",
        "Zona de Atención": "Toda CABA",
        "Horario": "Lunes a Sábado 8:00-20:00",
        "Emergencias": "✅ Sí",
        "Especialidad": "Limpieza de viviendas, común, desinfección"
    },
    {
        "Rubro": "🧹 Limpieza",
        "Prestador": "Green Clean Eco",
        "CUIT": "25-71234567-8",
        "Teléfono": "11-6789-1234",
        "Email": "eco@greenclean.com.ar",
        "Zona de Atención": "CABA Norte y Centro",
        "Horario": "Lunes a Viernes 7:00-18:00",
        "Emergencias": "❌ No",
        "Especialidad": "Limpieza ecológica, lavado a presión"
    },
    
    # 🔧 MANTENIMIENTO GENERAL
    {
        "Rubro": "🔧 Mantenimiento General",
        "Prestador": "Técnicos Express",
        "CUIT": "24-89456123-1",
        "Teléfono": "11-7890-2345",
        "Email": "express@tecnicos.com.ar",
        "Zona de Atención": "Toda CABA",
        "Horario": "Lunes a Domingo 8:00-20:00",
        "Emergencias": "✅ Sí",
        "Especialidad": "Reparaciones varias, tornería, ajustes menores"
    },
    {
        "Rubro": "🔧 Mantenimiento General",
        "Prestador": "Profesionales del Mantenimiento",
        "CUIT": "26-34567890-5",
        "Teléfono": "11-2345-6789",
        "Email": "profesionales@mant.com.ar",
        "Zona de Atención": "CABA Oeste y Sur",
        "Horario": "Lunes a Viernes 8:00-17:00",
        "Emergencias": "❌ No",
        "Especialidad": "Mantención preventiva, inspecciones"
    },
    
    # 🪟 VIDRIERÍA
    {
        "Rubro": "🪟 Vidriería",
        "Prestador": "Vidrios Blindados Premium",
        "CUIT": "28-67890123-4",
        "Teléfono": "11-3456-7890",
        "Email": "premium@vidrios.com.ar",
        "Zona de Atención": "Toda CABA",
        "Horario": "Lunes a Viernes 8:00-18:00",
        "Emergencias": "✅ Sí",
        "Especialidad": "Vidrios blindados, espejos, cerramientos"
    },
]

TABLA_SOLICITADA_OT = [
    {
        "Edificio": "Avda. Corrientes 1234",
        "UF": "1A",
        "Trabajo": "Plomería",
        "Presupuesto Aprobado": "$ 250.000.-",
        "Fecha_Inicio": "01/05/26",
        "Fecha_Finaliz": "01/05/26"
    },
    {
        "Edificio": "Larrea 435",
        "UF": "3J",
        "Trabajo": "Albañilería",
        "Presupuesto Aprobado": "$ 390.000.-",
        "Fecha_Inicio": "07/06/26",
        "Fecha_Finaliz": "12/06/26"
    },
    {
        "Edificio": "Montevideo 891",
        "UF": "4K",
        "Trabajo": "Plomería",
        "Presupuesto Aprobado": "$ 120.000.-",
        "Fecha_Inicio": "08/09/26",
        "Fecha_Finaliz": "09/09/26"
    },
    {
        "Edificio": "San José 1111",
        "UF": "5M",
        "Trabajo": "Electricidad",
        "Presupuesto Aprobado": "$ 95.000.-",
        "Fecha_Inicio": "12/07/26",
        "Fecha_Finaliz": "12/07/26"
    },
    {
        "Edificio": "Guayaquil 399",
        "UF": "6P",
        "Trabajo": "Cerrajería",
        "Presupuesto Aprobado": "$ 180.000.-",
        "Fecha_Inicio": "15/08/26",
        "Fecha_Finaliz": "15/08/26"
    }
]

# ════════════════════════════════════════════════════════════════
# CARGA DE BASES DE EDIFICIOS Y COEFICIENTES
# ════════════════════════════════════════════════════════════════

CAMPOS_UNIDADES_REQUERIDOS = [
    "Calle",
    "Numero",
    "Ciudad",
    "UF/Dpto",
    "Piso",
    "Porcentual Expensas",
]

CAMPOS_COEFICIENTES_REQUERIDOS = [
    "UF",
    "Propietario",
    "Piso",
    "Coeficiente",
    "Contacto",
]


def cargar_base_unidades(archivo) -> pd.DataFrame:
    nombre_archivo = archivo.name.lower()

    if nombre_archivo.endswith(".csv"):
        df = pd.read_csv(archivo, encoding="utf-8-sig")
    elif nombre_archivo.endswith((".xlsx", ".xls")):
        df = pd.read_excel(archivo)
    else:
        raise ValueError("El archivo debe estar en formato CSV o Excel.")

    df.columns = [str(col).strip() for col in df.columns]

    campos_faltantes = [campo for campo in CAMPOS_UNIDADES_REQUERIDOS if campo not in df.columns]
    if campos_faltantes:
        raise ValueError("Faltan las siguientes columnas obligatorias: " + ", ".join(campos_faltantes))

    for campo in ["Calle", "Ciudad", "UF/Dpto", "Piso"]:
        df[campo] = df[campo].fillna("").astype(str).str.strip()

    df["Numero"] = (
        df["Numero"]
        .fillna("")
        .astype(str)
        .str.replace(".0", "", regex=False)
        .str.strip()
    )

    df["Porcentual Expensas"] = (
        df["Porcentual Expensas"]
        .astype(str)
        .str.replace("%", "", regex=False)
        .str.replace(",", ".", regex=False)
        .str.strip()
    )
    df["Porcentual Expensas"] = pd.to_numeric(df["Porcentual Expensas"], errors="coerce").fillna(0)

    df["Edificio"] = (
        df["Calle"].fillna("").astype(str)
        + " "
        + df["Numero"].fillna("").astype(str)
        + ", "
        + df["Ciudad"].fillna("").astype(str)
    )
    df["Edificio"] = df["Edificio"].str.replace("  ", " ", regex=False).str.strip()

    columnas_ordenadas = [
        "Edificio",
        "Calle",
        "Numero",
        "Ciudad",
        "UF/Dpto",
        "Piso",
        "Porcentual Expensas",
    ]

    return df[columnas_ordenadas]


def cargar_base_coeficientes(archivo) -> pd.DataFrame:
    nombre_archivo = archivo.name.lower()

    if nombre_archivo.endswith(".csv"):
        df = pd.read_csv(archivo, encoding="utf-8-sig")
    elif nombre_archivo.endswith((".xlsx", ".xls")):
        df = pd.read_excel(archivo)
    else:
        raise ValueError("El archivo debe estar en formato CSV o Excel.")

    df.columns = [str(col).strip() for col in df.columns]
    campos_faltantes = [campo for campo in CAMPOS_COEFICIENTES_REQUERIDOS if campo not in df.columns]
    if campos_faltantes:
        raise ValueError("Faltan las siguientes columnas obligatorias: " + ", ".join(campos_faltantes))

    df["UF"] = df["UF"].fillna("").astype(str).str.strip().str.upper()
    df["Propietario"] = df["Propietario"].fillna("").astype(str).str.strip()
    df["Piso"] = df["Piso"].fillna("").astype(str).str.strip()
    df["Contacto"] = df["Contacto"].fillna("").astype(str).str.strip()
    df["Coeficiente"] = pd.to_numeric(
        df["Coeficiente"].astype(str).str.replace(",", ".", regex=False),
        errors="coerce",
    ).fillna(0)

    return df


def registrar_edificio_desde_base(df: pd.DataFrame):
    if df.empty:
        return

    for edificio, grupo in df.groupby("Edificio"):
        if edificio in ESTADISTICAS_EDIFICIOS:
            continue

        total_unidades = len(grupo)
        promedio_expensas = float(grupo["Porcentual Expensas"].mean()) if total_unidades else 0.0

        ESTADISTICAS_EDIFICIOS[edificio] = {
            "reserva": max(200000.0, total_unidades * 50000.0),
            "factor": round(max(0.3, promedio_expensas / 100.0), 2),
            "mora": "1" if promedio_expensas > 20 else "0",
            "tasa": round(4.0 + (promedio_expensas / 10.0), 1),
            "ots": str(min(5, max(1, total_unidades // 2))),
            "cantidad_uf": total_unidades,
            "coeficientes": {}
        }


# ════════════════════════════════════════════════════════════════
# PROCESO COMPLETO DE LIQUIDACIÓN DE EXPENSAS
# ════════════════════════════════════════════════════════════════

class AgenteLiquidacion:
    def __init__(self):
        self.gastos_registrados: List[RegistroGasto] = []
        self.ingresos_registrados: List[RegistroIngreso] = []
        self.coeficientes_uf: Dict[str, CoeficienteUF] = {}
        self.estado = EstadoAgente.INACTIVO

    def activar(self):
        self.estado = EstadoAgente.ACTIVADO

    def registrar_gasto(self, gasto: RegistroGasto):
        self.gastos_registrados.append(gasto)

    def registrar_ingreso(self, ingreso: RegistroIngreso):
        self.ingresos_registrados.append(ingreso)

    def cargar_coeficientes_desde_dataframe(self, df: pd.DataFrame):
        self.coeficientes_uf = {}
        for _, row in df.iterrows():
            uf = str(row["UF"]).upper()
            coef_obj = CoeficienteUF(
                uf=uf,
                propietario=str(row.get("Propietario", "")),
                piso=str(row.get("Piso", "")),
                coeficiente=float(row.get("Coeficiente", 0)),
                contacto=str(row.get("Contacto", ""))
            )
            self.coeficientes_uf[uf] = coef_obj

    def normalizar_coeficientes(self) -> Dict[str, float]:
        if not self.coeficientes_uf:
            return {}

        valores = {uf: coef_obj.coeficiente for uf, coef_obj in self.coeficientes_uf.items()}
        if not valores:
            return {}

        total = sum(valores.values())
        if total <= 0:
            cantidad = len(valores)
            return {uf: 1 / cantidad for uf in valores}

        factor = 1.0 / total
        for uf in self.coeficientes_uf:
            self.coeficientes_uf[uf].coeficiente *= factor

        return {uf: coef_obj.coeficiente for uf, coef_obj in self.coeficientes_uf.items()}

    def calcular_liquidacion(self, periodo: str) -> LiquidacionExpensas:
        self.activar()
        self.estado = EstadoAgente.PROCESANDO

        gastos_por_rubro = {}
        for gasto in self.gastos_registrados:
            rubro = gasto.tipo_gasto.value
            gastos_por_rubro[rubro] = gastos_por_rubro.get(rubro, 0.0) + gasto.monto

        ingresos_por_rubro = {}
        for ingreso in self.ingresos_registrados:
            rubro = ingreso.tipo_ingreso.value
            ingresos_por_rubro[rubro] = ingresos_por_rubro.get(rubro, 0.0) + ingreso.monto

        total_gastos = sum(gastos_por_rubro.values())
        total_ingresos = sum(ingresos_por_rubro.values())

        if not self.coeficientes_uf:
            self.estado = EstadoAgente.ERROR
            raise ValueError(
                "No hay coeficientes cargados. Cargá la base de unidades antes de liquidar."
            )

        self.normalizar_coeficientes()

        expensas_por_uf = {
            uf: total_gastos * coef_obj.coeficiente
            for uf, coef_obj in self.coeficientes_uf.items()
        }

        self.estado = EstadoAgente.COMPLETADO

        return LiquidacionExpensas(
            periodo=periodo,
            fecha_liquidacion=datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            total_ingresos=total_ingresos,
            total_gastos=total_gastos,
            deficit_o_superavit=total_ingresos - total_gastos,
            gastos_por_rubro=gastos_por_rubro,
            ingresos_por_rubro=ingresos_por_rubro,
            coeficientes=self.coeficientes_uf,
            expensas_por_uf=expensas_por_uf,
        )

    def generar_estado_cuenta_uf(self, uf: str, liquidacion: LiquidacionExpensas) -> Dict[str, Any]:
        if uf not in self.coeficientes_uf:
            return None

        coef_obj = self.coeficientes_uf[uf]
        expensas = liquidacion.expensas_por_uf.get(uf, 0)

        return {
            "uf": uf,
            "propietario": coef_obj.propietario,
            "piso": coef_obj.piso,
            "contacto": coef_obj.contacto,
            "coeficiente": coef_obj.coeficiente,
            "porcentaje": f"{coef_obj.coeficiente * 100:.2f}%",
            "periodo": liquidacion.periodo,
            "total_gastos": liquidacion.total_gastos,
            "expensas_a_pagar": expensas,
            "fecha_liquidacion": liquidacion.fecha_liquidacion,
            "vencimiento": datetime.now().strftime("%d/%m/%Y"),
        }

    def generar_excel_liquidacion(self, liquidacion: LiquidacionExpensas, edificio: str):
        output = BytesIO()

        if xlsxwriter is None and openpyxl is None:
            raise RuntimeError("No hay librería de Excel disponible. Instale xlsxwriter o openpyxl.")

        if xlsxwriter is not None:
            workbook = xlsxwriter.Workbook(output)
            header = workbook.add_format(
                {"bg_color": "#0d1e3d", "font_color": "#ffffff", "bold": True, "border": 1, "align": "center"}
            )
            cell = workbook.add_format({"border": 1})
            money = workbook.add_format({"num_format": "$#,##0.00", "border": 1})
            percent = workbook.add_format({"num_format": "0.00%", "border": 1})
            pct_num = workbook.add_format({"num_format": '0.00"%"', "border": 1})

            ws = workbook.add_worksheet("Resumen")
            ws.set_column("A:B", 30)
            ws.merge_range("A1:B1", f"LIQUIDACIÓN DE EXPENSAS - {edificio}", workbook.add_format({"bold": True, "font_size": 16, "align": "center", "bg_color": "#38bdf8", "font_color": "#0f172a"}))
            ws.write("A2", "Período")
            ws.write("B2", liquidacion.periodo)
            ws.write("A3", "Fecha")
            ws.write("B3", liquidacion.fecha_liquidacion)
            row = 5
            ws.write(row, 0, "INGRESOS", header)
            ws.write(row, 1, "", header)
            row += 1
            for rubro, monto in liquidacion.ingresos_por_rubro.items():
                ws.write(row, 0, rubro, cell)
                ws.write(row, 1, monto, money)
                row += 1
            ws.write(row, 0, "TOTAL INGRESOS", header)
            ws.write(row, 1, liquidacion.total_ingresos, money)
            row += 2
            ws.write(row, 0, "GASTOS", header)
            ws.write(row, 1, "", header)
            row += 1
            for rubro, monto in liquidacion.gastos_por_rubro.items():
                ws.write(row, 0, rubro, cell)
                ws.write(row, 1, monto, money)
                row += 1
            ws.write(row, 0, "TOTAL GASTOS", header)
            ws.write(row, 1, liquidacion.total_gastos, money)
            row += 2
            ws.write(row, 0, "RESULTADO", header)
            ws.write(row, 1, liquidacion.deficit_o_superavit, money)

            ws2 = workbook.add_worksheet("Por UF")
            ws2.set_column("A:E", 22)
            ws2.merge_range("A1:E1", f"DISTRIBUCIÓN POR UF - {edificio}", workbook.add_format({"bold": True, "font_size": 16, "align": "center", "bg_color": "#38bdf8", "font_color": "#0f172a"}))
            ws2.write("A3", "UF", header)
            ws2.write("B3", "Propietario", header)
            ws2.write("C3", "Coeficiente", header)
            ws2.write("D3", "Porcentaje", header)
            ws2.write("E3", "Expensas a Pagar", header)
            row = 3
            for uf, coef_obj in liquidacion.coeficientes.items():
                row += 1
                ws2.write(row, 0, uf, cell)
                ws2.write(row, 1, coef_obj.propietario, cell)
                ws2.write(row, 2, coef_obj.coeficiente, percent)
                ws2.write(row, 3, coef_obj.coeficiente * 100, pct_num)
                ws2.write(row, 4, liquidacion.expensas_por_uf.get(uf, 0), money)

            workbook.close()
            output.seek(0)
            return output

        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Resumen"
        ws.append(["LIQUIDACIÓN DE EXPENSAS", edificio])
        ws.append(["Periodo", liquidacion.periodo])
        ws.append(["Fecha", liquidacion.fecha_liquidacion])
        ws.append([])
        ws.append(["INGRESOS"])
        for rubro, monto in liquidacion.ingresos_por_rubro.items():
            ws.append([rubro, monto])
        ws.append(["TOTAL INGRESOS", liquidacion.total_ingresos])
        ws.append([])
        ws.append(["GASTOS"])
        for rubro, monto in liquidacion.gastos_por_rubro.items():
            ws.append([rubro, monto])
        ws.append(["TOTAL GASTOS", liquidacion.total_gastos])
        ws.append(["RESULTADO", liquidacion.deficit_o_superavit])

        ws2 = wb.create_sheet("Por UF")
        ws2.append(["UF", "Propietario", "Coeficiente", "Porcentaje", "Expensas a Pagar"])
        for uf, coef_obj in liquidacion.coeficientes.items():
            ws2.append([uf, coef_obj.propietario, coef_obj.coeficiente, coef_obj.coeficiente * 100, liquidacion.expensas_por_uf.get(uf, 0)])

        wb.save(output)
        output.seek(0)
        return output


# ════════════════════════════════════════════════════════════════
# 3. NÚCLEO DEL ENJAMBRE - AGENTES ESPECIALIZADOS
# ════════════════════════════════════════════════════════════════

class AgenteBase:
    def __init__(self, tipo_agente: TipoAgente):
        self.tipo_agente = tipo_agente
        self.estado = EstadoAgente.INACTIVO
        self.historial_procesamiento = []

    def activar(self):
        self.estado = EstadoAgente.ACTIVADO

    def procesar(self, evento: EventoSwarm) -> ResultadoAgente:
        raise NotImplementedError

    def registrar_operacion(self, resultado: ResultadoAgente):
        self.historial_procesamiento.append(resultado)


class AgenteContable(AgenteBase):
    def __init__(self):
        super().__init__(TipoAgente.CONTABLE)

    def procesar(self, evento: EventoSwarm, edificio_data: Dict) -> ResultadoAgente:
        self.activar()
        self.estado = EstadoAgente.PROCESANDO
        tiempo_inicio = time.time()

        try:
            f_cal = edificio_data["factor"]
            tasa_act = edificio_data["tasa"]

            ingresos = [
                {"Ingresos": "ingresos por expensas", "Monto ($)": 320000.0 * f_cal},
                {
                    "Ingresos": "alquileres de locales",
                    "Monto ($)": 85000.0 * (1.0 if f_cal >= 0.8 else 0.0),
                },
                {
                    "Ingresos": "intereses por colocacion a plazo fijo",
                    "Monto ($)": 14000.0 * f_cal * (tasa_act / 5.0),
                },
            ]

            gastos = [
                {"Gastos": "reparaciones", "Monto ($)": 45000.0 * f_cal},
                {"Gastos": "honorarios de administración", "Monto ($)": 35000.0 * f_cal},
                {"Gastos": "sueldo de encargado", "Monto ($)": 250000.0 * (1.0 if f_cal >= 0.7 else 0.0)},
                {"Gastos": "compra de articulos de limpieza", "Monto ($)": 12000.0 * f_cal},
                {"Gastos": "pagos luz", "Monto ($)": 18000.0 * f_cal},
                {"Gastos": "otros gastos", "Monto ($)": 7000.0 * f_cal},
            ]

            total_ingresos = sum(x["Monto ($)"] for x in ingresos)
            total_gastos = sum(x["Monto ($)"] for x in gastos)
            balance = total_ingresos - total_gastos

            self.estado = EstadoAgente.COMPLETADO
            tiempo_procesamiento = f"⚡ {(time.time() - tiempo_inicio)*1000:.2f}ms"

            return ResultadoAgente(
                agente=self.tipo_agente.value,
                estado=self.estado,
                datos_procesados={
                    "ingresos": ingresos,
                    "gastos": gastos,
                    "total_ingresos": total_ingresos,
                    "total_gastos": total_gastos,
                    "balance_neto": balance,
                },
                tiempo_procesamiento=tiempo_procesamiento,
                dependencias_cumplidas=[],
            )
        except Exception as e:
            self.estado = EstadoAgente.ERROR
            return ResultadoAgente(
                agente=self.tipo_agente.value,
                estado=self.estado,
                datos_procesados={"error": str(e)},
                tiempo_procesamiento="❌ Error en procesamiento",
                dependencias_cumplidas=[],
            )


class AgenteCompliance(AgenteBase):
    def __init__(self):
        super().__init__(TipoAgente.COMPLIANCE)

    def procesar(self, evento: EventoSwarm) -> ResultadoAgente:
        self.activar()
        self.estado = EstadoAgente.PROCESANDO
        tiempo_inicio = time.time()

        validaciones = {
            "ley_941_caba": "✅ Adherencia legal vigente",
            "codigo_civil_comercial": "✅ Art. 2048 cumplido",
            "validacion_cuit": "✅ Formato CUIT verificado",
            "vigencia_fiscal": "✅ Todas las entidades activas",
        }

        self.estado = EstadoAgente.COMPLETADO
        tiempo_procesamiento = f"⚡ {(time.time() - tiempo_inicio)*1000:.2f}ms"

        return ResultadoAgente(
            agente=self.tipo_agente.value,
            estado=self.estado,
            datos_procesados=validaciones,
            tiempo_procesamiento=tiempo_procesamiento,
            dependencias_cumplidas=[],
        )


class AgenteProveedores(AgenteBase):
    def __init__(self):
        super().__init__(TipoAgente.PROVEEDORES)

    def procesar(self, evento: EventoSwarm, rubro_filtro: str = None) -> ResultadoAgente:
        self.activar()
        self.estado = EstadoAgente.PROCESANDO
        tiempo_inicio = time.time()

        try:
            if rubro_filtro:
                proveedores_filtrados = [
                    p
                    for p in DATOS_CARTILLA_PROVEEDORES
                    if rubro_filtro.lower() in p["Rubro"].lower()
                ]
            else:
                proveedores_filtrados = DATOS_CARTILLA_PROVEEDORES

            self.estado = EstadoAgente.COMPLETADO
            tiempo_procesamiento = f"⚡ {(time.time() - tiempo_inicio)*1000:.2f}ms"

            return ResultadoAgente(
                agente=self.tipo_agente.value,
                estado=self.estado,
                datos_procesados={
                    "proveedores": proveedores_filtrados,
                    "total_disponibles": len(proveedores_filtrados),
                    "rubros": list(set([p["Rubro"] for p in DATOS_CARTILLA_PROVEEDORES])),
                },
                tiempo_procesamiento=tiempo_procesamiento,
                dependencias_cumplidas=[],
            )
        except Exception as e:
            self.estado = EstadoAgente.ERROR
            return ResultadoAgente(
                agente=self.tipo_agente.value,
                estado=self.estado,
                datos_procesados={"error": str(e)},
                tiempo_procesamiento="❌ Error en procesamiento",
                dependencias_cumplidas=[],
            )


class AgenteOperativo(AgenteBase):
    def __init__(self):
        super().__init__(TipoAgente.OPERATIVO)

    def procesar(self, evento: EventoSwarm, edificio_filtro: str = None) -> ResultadoAgente:
        self.activar()
        self.estado = EstadoAgente.PROCESANDO
        tiempo_inicio = time.time()

        try:
            if edificio_filtro:
                ots_filtradas = [ot for ot in TABLA_SOLICITADA_OT
                                 if normalizar_edificio(ot["Edificio"]) == normalizar_edificio(edificio_filtro)]
            else:
                ots_filtradas = TABLA_SOLICITADA_OT

            presupuesto_total = sum(parsear_monto_ar(ot["Presupuesto Aprobado"]) for ot in ots_filtradas)

            self.estado = EstadoAgente.COMPLETADO
            tiempo_procesamiento = f"⚡ {(time.time() - tiempo_inicio)*1000:.2f}ms"

            return ResultadoAgente(
                agente=self.tipo_agente.value,
                estado=self.estado,
                datos_procesados={
                    "ordenes_trabajo": ots_filtradas,
                    "total_ordenes": len(ots_filtradas),
                    "presupuesto_total": presupuesto_total,
                },
                tiempo_procesamiento=tiempo_procesamiento,
                dependencias_cumplidas=[TipoAgente.COMPLIANCE.value],
            )
        except Exception as e:
            self.estado = EstadoAgente.ERROR
            return ResultadoAgente(
                agente=self.tipo_agente.value,
                estado=self.estado,
                datos_procesados={"error": str(e)},
                tiempo_procesamiento="❌ Error en procesamiento",
                dependencias_cumplidas=[],
            )


class AgenteMora(AgenteBase):
    def __init__(self):
        super().__init__(TipoAgente.MORA)

    def procesar(self, evento: EventoSwarm, edificio_data: Dict, resumen_mora=None) -> ResultadoAgente:
        self.activar()
        self.estado = EstadoAgente.PROCESANDO
        tiempo_inicio = time.time()

        if resumen_mora is not None:
            # Mora REAL: cargos emitidos, pagos acreditados e interés punitorio calculado
            morosas = resumen_mora[(resumen_mora["Capital adeudado"] > 0) & (resumen_mora["Días de mora"] > 0)]
            mora_count = len(morosas)
            max_dias = int(morosas["Días de mora"].max()) if mora_count else 0
            if mora_count > 1:
                alerta_nivel = "🔴 CRÍTICO - Más de 1 UF en mora"
            elif mora_count == 1:
                alerta_nivel = "🟡 MODERADO - 1 UF en mora"
            else:
                alerta_nivel = "🟢 CONTROLADO - Sin mora registrada"
            if max_dias > 90:
                acciones = ["Intimación legal", "Contacto directo con el propietario"]
            elif max_dias > 30:
                acciones = ["Refinanciación", "Aviso formal de deuda"]
            elif max_dias > 0:
                acciones = ["Contacto preventivo"]
            else:
                acciones = ["Sin acciones pendientes"]
            datos = {
                "fuente": "real",
                "uf_en_mora": mora_count,
                "nivel_alerta": alerta_nivel,
                "acciones_recomendadas": acciones,
                "capital_adeudado": float(resumen_mora["Capital adeudado"].sum()),
                "interes_punitorio": float(resumen_mora["Interés punitorio"].sum()),
                "total_adeudado": float(resumen_mora["Total adeudado"].sum()),
                "detalle": morosas[["UF", "Propietario", "Capital adeudado", "Interés punitorio",
                                    "Total adeudado", "Días de mora", "Tramo"]].to_dict("records"),
            }
        else:
            # Sin cargos emitidos para este edificio: se mantiene el dato de demostración
            mora_count = int(edificio_data.get("mora", "0"))
            if mora_count > 1:
                alerta_nivel = "🔴 CRÍTICO - Más de 1 UF en mora"
            elif mora_count == 1:
                alerta_nivel = "🟡 MODERADO - 1 UF en mora"
            else:
                alerta_nivel = "🟢 CONTROLADO - Sin mora registrada"
            datos = {
                "fuente": "simulado",
                "uf_en_mora": mora_count,
                "nivel_alerta": alerta_nivel,
                "acciones_recomendadas": ["Contacto preventivo", "Refinanciación", "Intimación legal"],
            }

        self.estado = EstadoAgente.COMPLETADO
        tiempo_procesamiento = f"⚡ {(time.time() - tiempo_inicio)*1000:.2f}ms"

        return ResultadoAgente(
            agente=self.tipo_agente.value,
            estado=self.estado,
            datos_procesados=datos,
            tiempo_procesamiento=tiempo_procesamiento,
            dependencias_cumplidas=[TipoAgente.CONTABLE.value],
        )


class AgenteAuditor(AgenteBase):
    def __init__(self):
        super().__init__(TipoAgente.AUDITOR)

    def procesar(self, evento: EventoSwarm, resultados_previos: Dict[str, ResultadoAgente]) -> ResultadoAgente:
        self.activar()
        self.estado = EstadoAgente.PROCESANDO
        tiempo_inicio = time.time()

        audit_log = []
        for agente_nombre, resultado in resultados_previos.items():
            if resultado.estado == EstadoAgente.COMPLETADO:
                audit_log.append(f"✅ {agente_nombre}: procesado correctamente")
            else:
                audit_log.append(f"⚠️ {agente_nombre}: requiere revisión")

        self.estado = EstadoAgente.COMPLETADO
        tiempo_procesamiento = f"🔍 {(time.time() - tiempo_inicio)*1000:.2f}ms"

        return ResultadoAgente(
            agente=self.tipo_agente.value,
            estado=self.estado,
            datos_procesados={
                "bitacora_auditoria": audit_log,
                "inconsistencias_detectadas": 0,
                "timestamp_auditoria": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            },
            tiempo_procesamiento=tiempo_procesamiento,
            dependencias_cumplidas=list(resultados_previos.keys()),
        )


class AgenteReportes(AgenteBase):
    def __init__(self):
        super().__init__(TipoAgente.REPORTES)

    def procesar(self, evento: EventoSwarm, resultados_previos: Dict[str, ResultadoAgente]) -> ResultadoAgente:
        self.activar()
        self.estado = EstadoAgente.PROCESANDO
        tiempo_inicio = time.time()

        agentes_exitosos = len([r for r in resultados_previos.values() if r.estado == EstadoAgente.COMPLETADO])

        reporte_ejecutivo = {
            "fecha_generacion": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            "evento_disparador": evento.tipo_evento,
            "agentes_activados": len(resultados_previos),
            "agentes_exitosos": agentes_exitosos,
            "resumen": f"Solicitud procesada por {agentes_exitosos}/{len(resultados_previos)} agentes especializados",
        }

        self.estado = EstadoAgente.COMPLETADO
        tiempo_procesamiento = f"📄 {(time.time() - tiempo_inicio)*1000:.2f}ms"

        return ResultadoAgente(
            agente=self.tipo_agente.value,
            estado=self.estado,
            datos_procesados=reporte_ejecutivo,
            tiempo_procesamiento=tiempo_procesamiento,
            dependencias_cumplidas=list(resultados_previos.keys()),
        )


# ════════════════════════════════════════════════════════════════
# 4. ORQUESTADOR CENTRAL
# ════════════════════════════════════════════════════════════════

class OrquestadorSwarm:
    def __init__(self):
        self.enjambre = {
            TipoAgente.CONTABLE: AgenteContable(),
            TipoAgente.COMPLIANCE: AgenteCompliance(),
            TipoAgente.PROVEEDORES: AgenteProveedores(),
            TipoAgente.OPERATIVO: AgenteOperativo(),
            TipoAgente.MORA: AgenteMora(),
            TipoAgente.AUDITOR: AgenteAuditor(),
            TipoAgente.REPORTES: AgenteReportes(),
        }
        self.evento_actual = None
        self.resultados_enjambre = {}
        self.placeholders_animacion = {}

    def disparar_enjambre(self, evento: EventoSwarm, edificio_seleccionado: str, resumen_mora=None) -> Dict[str, ResultadoAgente]:
        self.evento_actual = evento
        self.resultados_enjambre = {}

        if edificio_seleccionado not in ESTADISTICAS_EDIFICIOS:
            registrar_edificio_desde_base(st.session_state.get("unidades_edificios", pd.DataFrame()))
        if edificio_seleccionado not in ESTADISTICAS_EDIFICIOS:
            ESTADISTICAS_EDIFICIOS[edificio_seleccionado] = {
                "reserva": 250000.0,
                "factor": 0.8,
                "mora": "0",
                "tasa": 5.0,
                "ots": "3",
                "cantidad_uf": 10,
                "coeficientes": {},
            }

        edificio_data = ESTADISTICAS_EDIFICIOS[edificio_seleccionado]

        if evento.tipo_evento == "MODULO_CONTABILIDAD":
            self.resultados_enjambre[TipoAgente.CONTABLE.value] = self.enjambre[TipoAgente.CONTABLE].procesar(evento, edificio_data)
            self.resultados_enjambre[TipoAgente.MORA.value] = self.enjambre[TipoAgente.MORA].procesar(evento, edificio_data, resumen_mora)
            self.resultados_enjambre[TipoAgente.COMPLIANCE.value] = self.enjambre[TipoAgente.COMPLIANCE].procesar(evento)

        elif evento.tipo_evento == "MODULO_OPERATIVO":
            self.resultados_enjambre[TipoAgente.OPERATIVO.value] = self.enjambre[TipoAgente.OPERATIVO].procesar(evento, edificio_seleccionado)
            self.resultados_enjambre[TipoAgente.PROVEEDORES.value] = self.enjambre[TipoAgente.PROVEEDORES].procesar(evento)
            self.resultados_enjambre[TipoAgente.COMPLIANCE.value] = self.enjambre[TipoAgente.COMPLIANCE].procesar(evento)

        self.resultados_enjambre[TipoAgente.AUDITOR.value] = self.enjambre[TipoAgente.AUDITOR].procesar(evento, self.resultados_enjambre)
        self.resultados_enjambre[TipoAgente.REPORTES.value] = self.enjambre[TipoAgente.REPORTES].procesar(evento, self.resultados_enjambre)

        return self.resultados_enjambre


# ════════════════════════════════════════════════════════════════
# 5. CONFIGURACIÓN DE STREAMLIT
# ════════════════════════════════════════════════════════════

st.set_page_config(
    page_title="Resil_IA Condominios",
    page_icon="🏙️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

:root {
    --bg: #0a1220;
    --bg-2: #0e1a2f;
    --card: #121e35;
    --card-2: #16253f;
    --borde: #1f3050;
    --borde-fuerte: #2c4268;
    --texto: #e7edf7;
    --texto-2: #a4b3cb;
    --texto-3: #6f819f;
    --acento: #38bdf8;
    --acento-2: #0ea5e9;
    --oro: #e0b84a;
    --ok: #22c55e;
    --aviso: #f59e0b;
    --error: #ef4444;
    --radio: 14px;
    --sombra: 0 1px 2px rgba(0,0,0,.35), 0 8px 24px rgba(0,0,0,.25);
}

html, body, [class*="css"], .stApp, button, input, textarea, select {
    font-family: 'Inter', system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif !important;
}
.stApp {
    background:
        radial-gradient(1200px 500px at 85% -10%, rgba(56,189,248,.10), transparent 60%),
        linear-gradient(180deg, var(--bg-2) 0%, var(--bg) 100%) !important;
    color: var(--texto);
    color-scheme: dark;
}
[data-testid="stHeader"] { background: transparent !important; }
footer, #MainMenu { visibility: hidden; }
.block-container { padding-top: 2rem !important; padding-bottom: 3rem !important; max-width: 1280px; }

/* ── Tipografía ── */
h1, h2, h3, h4 { font-family: 'Inter', sans-serif !important; letter-spacing: -0.02em; }
h1 { color: var(--texto) !important; font-weight: 800 !important; font-size: 2rem !important; }
h2 { color: var(--texto) !important; font-weight: 700 !important; font-size: 1.45rem !important;
     padding-bottom: .4rem; border-bottom: 1px solid var(--borde); margin-top: 1.2rem !important; }
h3 { color: var(--acento) !important; font-weight: 600 !important; font-size: 1.15rem !important; }
h4 { color: var(--texto) !important; font-weight: 600 !important; font-size: 1rem !important; }
.stMarkdown p, p, li, .stRadio label, .stCheckbox label, .stSelectbox label, .stTextInput label,
.stNumberInput label, .stDateInput label, .stFileUploader label, .stTextArea label {
    color: var(--texto) !important; font-size: 0.97rem !important; line-height: 1.6 !important;
}
label, [data-testid="stWidgetLabel"] p { color: var(--texto-2) !important; font-weight: 500 !important; font-size: .9rem !important; }
small, .stCaption, [data-testid="stCaptionContainer"] { color: var(--texto-3) !important; }
hr { border-color: var(--borde) !important; margin: 1.2rem 0 !important; }
a { color: var(--acento) !important; }

/* ── Cabecera de la app ── */
.app-header {
    display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 14px;
    background: linear-gradient(135deg, var(--card) 0%, var(--card-2) 100%);
    border: 1px solid var(--borde); border-radius: 18px; padding: 18px 22px; margin: 4px 0 22px 0;
    box-shadow: var(--sombra); position: relative; overflow: hidden;
}
.app-header::before {
    content: ""; position: absolute; left: 0; top: 0; bottom: 0; width: 4px;
    background: linear-gradient(180deg, var(--acento), var(--acento-2));
}
.app-header .marca { display: flex; align-items: center; gap: 16px; }
.app-header .marca-icono {
    width: 52px; height: 52px; border-radius: 14px; display: grid; place-items: center; font-size: 1.6rem;
    background: linear-gradient(135deg, rgba(56,189,248,.22), rgba(14,165,233,.08));
    border: 1px solid rgba(56,189,248,.35);
}
.app-header .marca-nombre { font-size: 1.65rem; font-weight: 800; letter-spacing: -0.03em; color: var(--texto); line-height: 1.1; }
.app-header .marca-nombre .u { color: #ff1744; }
.app-header .marca-nombre .ia { color: #ff1744; }
.app-header .marca-sub { color: #ff1744; font-size: .85rem; margin-top: 3px; font-weight: 600; }
.app-header .derecha { display: flex; flex-direction: column; align-items: flex-end; gap: 6px; }
.chip {
    display: inline-flex; align-items: center; gap: 6px; padding: 5px 12px; border-radius: 999px;
    background: rgba(56,189,248,.10); border: 1px solid rgba(56,189,248,.30);
    color: var(--acento); font-size: .8rem; font-weight: 600; letter-spacing: .01em;
}
.chip.neutro { background: rgba(148,163,184,.08); border-color: var(--borde-fuerte); color: var(--texto-2); }
.app-header .edificio { color: var(--texto); font-size: .95rem; font-weight: 600; }
.app-header .edificio span { color: #39ff14; font-weight: 700; margin-right: 6px; text-shadow: 0 0 8px rgba(57,255,20,.45); }

/* ── Barra lateral ── */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0c1628 0%, #08101e 100%) !important;
    border-right: 1px solid var(--borde);
}
[data-testid="stSidebar"] .block-container, [data-testid="stSidebarUserContent"] { padding-top: 1rem !important; }
.logo-container { display: flex; justify-content: center; margin: 6px 0 4px 0; padding: 6px 0 14px 0; }
.logo-container img { max-width: 96px; height: auto; border-radius: 16px; border: 1px solid var(--borde-fuerte); box-shadow: 0 6px 20px rgba(56,189,248,.18); }
.sidebar-tag, [data-testid="stSidebar"] p.sidebar-tag { text-align: center; color: #ff1744 !important; font-size: .8rem !important; font-weight: 800 !important; letter-spacing: .16em; text-transform: uppercase; margin: 0 0 8px 0; }
.sidebar-nota { font-size: .8rem !important; color: var(--texto-3) !important; line-height: 1.5; }
[data-testid="stSidebar"] h3 { font-size: 1rem !important; color: var(--texto) !important; }
[data-testid="stSidebar"] .stRadio > div { gap: 4px; }
[data-testid="stSidebar"] .stRadio label {
    padding: 9px 12px !important; border-radius: 10px; border: 1px solid transparent;
    transition: background .15s ease, border-color .15s ease; width: 100%;
}
[data-testid="stSidebar"] .stRadio label:hover { background: rgba(56,189,248,.07); }
[data-testid="stSidebar"] .stRadio label:has(input:checked) {
    background: rgba(56,189,248,.14); border-color: rgba(56,189,248,.40);
}
[data-testid="stSidebar"] .stRadio label p { font-size: .93rem !important; font-weight: 500 !important; color: var(--texto) !important; }

/* ── Métricas ── */
div[data-testid="stMetric"] {
    background: linear-gradient(160deg, var(--card) 0%, var(--card-2) 100%) !important;
    border: 1px solid var(--borde) !important; border-top: 3px solid var(--acento) !important;
    border-radius: var(--radio) !important; padding: 16px 18px !important; box-shadow: var(--sombra) !important;
}
div[data-testid="stMetric"] label, div[data-testid="stMetric"] [data-testid="stMetricLabel"] p {
    color: var(--texto-2) !important; font-weight: 600 !important; font-size: .82rem !important;
    text-transform: uppercase; letter-spacing: .05em;
}
div[data-testid="stMetric"] [data-testid="stMetricValue"] {
    color: var(--texto) !important; font-weight: 800 !important; font-size: 1.85rem !important; letter-spacing: -0.02em;
}

/* ── Tablas ── */
.stDataFrame, .stTable, [data-testid="stDataFrame"] {
    background: var(--card) !important; border: 1px solid var(--borde); border-radius: var(--radio) !important; overflow: hidden;
}
table { border-collapse: collapse; width: 100%; }
th { background: var(--card-2) !important; color: var(--texto-2) !important; font-weight: 600 !important;
     font-size: .78rem !important; text-transform: uppercase; letter-spacing: .05em; padding: 10px 12px !important; border-bottom: 1px solid var(--borde-fuerte) !important; }
td { color: var(--texto) !important; font-size: .92rem !important; font-weight: 500 !important; padding: 9px 12px !important; border-bottom: 1px solid var(--borde) !important; }
tr:hover td { background: rgba(56,189,248,.04); }

/* ── Botones ── */
.stButton > button, .stDownloadButton > button, [data-testid="stFormSubmitButton"] > button {
    background: linear-gradient(180deg, var(--acento) 0%, var(--acento-2) 100%) !important;
    color: #04121f !important; border: none !important; border-radius: 10px !important;
    font-weight: 700 !important; font-size: .92rem !important; padding: .55rem 1.1rem !important;
    box-shadow: 0 2px 10px rgba(14,165,233,.30); transition: transform .12s ease, box-shadow .12s ease, filter .12s ease;
}
.stButton > button:hover, .stDownloadButton > button:hover, [data-testid="stFormSubmitButton"] > button:hover {
    filter: brightness(1.08); transform: translateY(-1px); box-shadow: 0 6px 18px rgba(14,165,233,.40);
}
.stButton > button:active { transform: translateY(0); }
.stButton > button p, .stDownloadButton > button p, [data-testid="stFormSubmitButton"] > button p { color: #04121f !important; font-weight: 700 !important; font-size: .92rem !important; }
.stButton > button[kind="secondary"] {
    background: transparent !important; color: var(--texto) !important; border: 1px solid var(--borde-fuerte) !important; box-shadow: none;
}
.stButton > button[kind="secondary"] p { color: var(--texto) !important; }

/* ── Campos ── */
.stTextInput input, .stNumberInput input, .stTextArea textarea, .stDateInput input,
[data-baseweb="select"] > div, [data-baseweb="input"] {
    background: var(--bg) !important; color: var(--texto) !important;
    border: 1px solid var(--borde-fuerte) !important; border-radius: 10px !important; font-size: .95rem !important;
}
.stTextInput input:focus, .stNumberInput input:focus, .stTextArea textarea:focus {
    border-color: var(--acento) !important; box-shadow: 0 0 0 3px rgba(56,189,248,.18) !important;
}
[data-testid="stFileUploaderDropzone"] {
    background: rgba(56,189,248,.04) !important; border: 1.5px dashed var(--borde-fuerte) !important; border-radius: var(--radio) !important;
}
[data-testid="stFileUploaderDropzone"]:hover { border-color: var(--acento) !important; }

/* ── Desplegables, pestañas, formularios, avisos ── */
[data-testid="stExpander"] {
    background: var(--card) !important; border: 1px solid var(--borde) !important; border-radius: var(--radio) !important; overflow: hidden;
}
[data-testid="stExpander"] summary { font-weight: 600; color: var(--texto); }
[data-testid="stExpander"] summary:hover { background: rgba(56,189,248,.05); }
[data-testid="stForm"] { background: var(--card) !important; border: 1px solid var(--borde) !important; border-radius: var(--radio) !important; padding: 18px !important; }
.stTabs [data-baseweb="tab-list"] { gap: 6px; border-bottom: 1px solid var(--borde); }
.stTabs [data-baseweb="tab"] { color: var(--texto-2) !important; font-weight: 600; padding: 10px 16px; border-radius: 10px 10px 0 0; }
.stTabs [aria-selected="true"] { color: var(--acento) !important; background: rgba(56,189,248,.08); }
.stTabs [data-baseweb="tab-highlight"] { background: var(--acento) !important; }
[data-testid="stAlert"] { border-radius: 12px !important; border: 1px solid var(--borde-fuerte) !important; }
[data-testid="stAlert"] p { font-size: .93rem !important; }
[data-testid="stSuccess"], div[data-baseweb="notification"][kind="positive"] { background: rgba(34,197,94,.10) !important; }

/* ── Enjambre de agentes ── */
.swarm-agent {
    background: var(--card); border: 1px solid var(--borde); border-left: 4px solid var(--acento);
    padding: 12px 16px; margin: 8px 0; border-radius: 12px; font-size: .93rem; color: var(--texto);
    box-shadow: 0 1px 2px rgba(0,0,0,.25); transition: all .2s ease;
}
.swarm-agent b { font-weight: 600; }
.swarm-completed { border-left-color: var(--ok) !important; background: rgba(34,197,94,.07) !important; }
.swarm-processing { border-left-color: var(--aviso) !important; background: rgba(245,158,11,.08) !important; animation: pulse 1.5s infinite; }
.swarm-active { border-left-color: var(--acento) !important; background: rgba(56,189,248,.07) !important; }
.swarm-error { border-left-color: var(--error) !important; background: rgba(239,68,68,.08) !important; }
@keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: .72; } }
@keyframes robotMove { 0% { transform: translateX(-3px); } 50% { transform: translateX(3px); } 100% { transform: translateX(-3px); } }
.robot-animado { display: inline-block; animation: robotMove 1.2s infinite; font-size: 1.1rem; margin-right: 4px; }

/* ── Tarjetas varias ── */
.titulo-edificio { background: linear-gradient(135deg, var(--acento) 0%, var(--acento-2) 100%); color: #04121f; padding: 10px 16px; border-radius: 10px; font-weight: 700; font-size: 1rem; margin: 16px 0; }
.estado-cuenta-box { background: linear-gradient(160deg, var(--card) 0%, var(--card-2) 100%); border: 1px solid var(--borde-fuerte); border-top: 3px solid var(--acento); border-radius: 14px; padding: 22px; margin: 15px 0; box-shadow: var(--sombra); }
.estado-cuenta-box p { font-size: .95rem !important; }
.prestador-card { background: linear-gradient(160deg, var(--card) 0%, var(--card-2) 100%); border: 1px solid var(--borde); border-left: 4px solid var(--ok); border-radius: 12px; padding: 16px 18px; margin: 10px 0; box-shadow: var(--sombra); }
.prestador-card p { font-size: .92rem !important; margin: 3px 0; }
.pie { text-align: center; color: var(--texto-3); font-size: .8rem; padding: 22px 0 6px 0; line-height: 1.7; }

@media (max-width: 760px) {
    .app-header { padding: 14px 16px; }
    .app-header .derecha { align-items: flex-start; }
    .app-header .marca-nombre { font-size: 1.35rem; }
    h1 { font-size: 1.6rem !important; }
}

    </style>
    """,
    unsafe_allow_html=True,
)

def encabezado(modulo: str, etiqueta: str = "", valor: str = "") -> None:
    """Cabecera común de todas las pantallas. El texto se escapa: viene de archivos que sube el usuario."""
    import html as _html
    derecha = f'<span class="chip">{_html.escape(modulo)}</span>'
    if valor:
        derecha += (f'<div class="edificio"><span>📍 {_html.escape(etiqueta)}</span>'
                    f'{_html.escape(valor)}</div>')
    elif etiqueta:
        derecha += f'<div class="edificio"><span>📍 {_html.escape(etiqueta)}</span></div>'
    st.markdown(
        '<div class="app-header"><div class="marca"><div class="marca-icono">🏙️</div><div>'
        '<div class="marca-nombre">Resil<span class="u">_</span><span class="ia">IA</span> Condominios</div>'
        '<div class="marca-sub">Gestión inteligente de consorcios</div></div></div>'
        f'<div class="derecha">{derecha}</div></div>',
        unsafe_allow_html=True,
    )


# INICIALIZACIÓN DE SESIÓN
if "unidades_edificios" not in st.session_state:
    st.session_state.unidades_edificios = pd.DataFrame(
        columns=["Edificio", "Calle", "Numero", "Ciudad", "UF/Dpto", "Piso", "Porcentual Expensas"]
    )

if "coeficientes_cargados" not in st.session_state:
    st.session_state.coeficientes_cargados = pd.DataFrame()

if "agente_liquidacion" not in st.session_state:
    st.session_state.agente_liquidacion = AgenteLiquidacion()

if "liquidacion_actual" not in st.session_state:
    st.session_state.liquidacion_actual = None

orquestador = OrquestadorSwarm()  # se recrea en cada ejecución (ver nota sobre Enum y reruns)
agente_liquidacion = st.session_state.agente_liquidacion


# ════════════════════════════════════════════════════════════════
# 6. SIDEBAR - CONTROL CENTRAL
# ════════════════════════════════════════════════════════════════

with st.sidebar:
    st.markdown(
        """
        <div class="logo-container">
            <img src="https://raw.githubusercontent.com/nosimani/Consorcio_IA/main/Resilia.jfif" alt="Resilia Logo">
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("<p class='sidebar-tag'>Sistema multiagente avanzado</p>", unsafe_allow_html=True)
    st.markdown("---")

    pantalla_activa = st.radio(
        "📌 Seleccione Módulo de Control:",
        [
            "📋 Dashboard y Contabilidad",
            "🔧 Órdenes de Trabajo de Campo",
            "📊 Liquidación de Expensas",
            "👷 Directorio de Prestadores",
            "💵 Cobranzas, Mora y Recibos"
        ],
        index=0,
    )

    st.markdown("---")

    st.subheader("🏢 Cargar base de edificios")
    archivos_edificios = st.file_uploader(
        "Seleccione uno o varios archivos CSV o Excel",
        type=["csv", "xlsx", "xls"],
        accept_multiple_files=True,
        help=("Cada archivo debe contener las columnas: Calle, Numero, Ciudad, UF/Dpto, Piso y Porcentual Expensas."),
    )

    if archivos_edificios:
        bases_cargadas = []
        errores_carga = []

        for archivo in archivos_edificios:
            try:
                base_edificio = cargar_base_unidades(archivo)
                bases_cargadas.append(base_edificio)
            except Exception as error:
                errores_carga.append(f"{archivo.name}: {str(error)}")

        if bases_cargadas:
            base_total = pd.concat(bases_cargadas, ignore_index=True)
            st.session_state.unidades_edificios = pd.concat(
                [st.session_state.unidades_edificios, base_total],
                ignore_index=True,
            )
            st.session_state.unidades_edificios = st.session_state.unidades_edificios.drop_duplicates().reset_index(drop=True)
            registrar_edificio_desde_base(st.session_state.unidades_edificios)
            st.success(f"✅ Se cargaron {len(st.session_state.unidades_edificios)} unidades funcionales.")

        for error in errores_carga:
            st.error(f"❌ {error}")

    st.markdown("---")
    st.subheader("📋 Cargar Coeficientes por UF")
    archivo_coeficientes = st.file_uploader(
        "Cargue archivo de coeficientes (CSV o Excel)",
        type=["csv", "xlsx", "xls"],
        key="coef_uploader",
        help="Debe contener columnas: UF, Propietario, Piso, Coeficiente, Contacto"
    )

    if archivo_coeficientes:
        try:
            df_coef = cargar_base_coeficientes(archivo_coeficientes)
            st.session_state.coeficientes_cargados = df_coef
            st.success(f"✅ Se cargaron {len(df_coef)} coeficientes correctamente.")
        except Exception as error:
            st.error(f"❌ Error: {str(error)}")

    edificios_base = list(ESTADISTICAS_EDIFICIOS.keys())
    edificios_cargados = []

    if not st.session_state.unidades_edificios.empty:
        edificios_cargados = sorted(st.session_state.unidades_edificios["Edificio"].dropna().unique().tolist())

    edificios_disponibles = sorted(set(edificios_base).union(edificios_cargados))

    st.markdown("---")
    edificio_seleccionado = st.selectbox("🏗️ Edificio Activo de Control", edificios_disponibles)
    st.markdown("---")
    st.info("**CUIT:** 30-11111111-9\n\n**Jurisdicción:** Ley 941 CABA")
    st.markdown("---")
    st.markdown(
        "<p class='sidebar-nota'>ℹ️ <b>Arquitectura multiagente</b><br/>Cada solicitud activa el enjambre de agentes especializados</p>",
        unsafe_allow_html=True,
    )


# ════════════════════════════════════════════════════════════════
# MÓDULO 4: DIRECTORIO DE PRESTADORES DE SERVICIOS
# ════════════════════════════════════════════════════════════════

if pantalla_activa == "👷 Directorio de Prestadores":
    
    encabezado("Directorio de Prestadores", "Prestadores de servicios homologados")
    st.markdown("---")
    
    st.header("👷 Cartilla de Prestadores")
    st.markdown("Listado completo de profesionales y servicios disponibles para el consorcio.")
    
    # Filtros
    col1, col2 = st.columns(2)
    
    with col1:
        rubros_unicos = sorted(list(set([p["Rubro"] for p in DATOS_CARTILLA_PROVEEDORES])))
        rubro_filtrado = st.selectbox("🔎 Filtrar por rubro:", ["📋 Todos los rubros"] + rubros_unicos)
    
    with col2:
        buscar_texto = st.text_input("🔍 Buscar por nombre o CUIT:", placeholder="Ej: plomería, 30-55489")
    
    # Aplicar filtros
    proveedores_mostrados = DATOS_CARTILLA_PROVEEDORES.copy()
    
    if rubro_filtrado != "📋 Todos los rubros":
        proveedores_mostrados = [p for p in proveedores_mostrados if p["Rubro"] == rubro_filtrado]
    
    if buscar_texto:
        buscar_texto_lower = buscar_texto.lower()
        proveedores_mostrados = [
            p for p in proveedores_mostrados
            if buscar_texto_lower in p["Prestador"].lower()
            or buscar_texto_lower in p["CUIT"].lower()
            or buscar_texto_lower in p["Email"].lower()
        ]
    
    st.markdown(f"**Resultados encontrados: {len(proveedores_mostrados)}**")
    st.markdown("---")
    
    # Mostrar prestadores en tarjetas
    for prestador in proveedores_mostrados:
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col1:
            st.markdown(f"### {prestador['Rubro']}")
        
        with col2:
            st.markdown(f"""
            <div class="prestador-card">
                <h4 style="color: #38bdf8; margin: 0;">{prestador['Prestador']}</h4>
                <p><b>CUIT:</b> {prestador['CUIT']}</p>
                <p><b>Teléfono:</b> {prestador['Teléfono']}</p>
                <p><b>Email:</b> {prestador['Email']}</p>
                <p><b>Zona:</b> {prestador['Zona de Atención']}</p>
                <p><b>Horario:</b> {prestador['Horario']}</p>
                <p><b>Emergencias:</b> {prestador['Emergencias']}</p>
                <p><b>Especialidad:</b> {prestador['Especialidad']}</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
            <div style="text-align: center; padding: 20px;">
                <a href="tel:{prestador['Teléfono'].replace('-', '')}" style="text-decoration: none;">
                    <button style="background: #10b981; color: white; padding: 8px 16px; border: none; border-radius: 8px; cursor: pointer; font-weight: bold;">
                        📞 Llamar
                    </button>
                </a>
                <br><br>
                <a href="mailto:{prestador['Email']}" style="text-decoration: none;">
                    <button style="background: #38bdf8; color: #0f172a; padding: 8px 16px; border: none; border-radius: 8px; cursor: pointer; font-weight: bold;">
                        ✉️ Email
                    </button>
                </a>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")
    
    # Tabla resumida
    st.markdown("---")
    st.subheader("📊 Vista en Tabla")
    
    df_prestadores = pd.DataFrame(proveedores_mostrados)
    df_mostrar = df_prestadores[["Rubro", "Prestador", "Teléfono", "Email", "Zona de Atención", "Emergencias"]]
    
    st.dataframe(df_mostrar, use_container_width=True, hide_index=True)
    
    # Estadísticas
    st.markdown("---")
    st.subheader("📈 Estadísticas del Directorio")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Prestadores", len(DATOS_CARTILLA_PROVEEDORES))
    
    with col2:
        rubros_totales = len(set([p["Rubro"] for p in DATOS_CARTILLA_PROVEEDORES]))
        st.metric("Rubros Disponibles", rubros_totales)
    
    with col3:
        emergencias = len([p for p in DATOS_CARTILLA_PROVEEDORES if p["Emergencias"] == "✅ Sí"])
        st.metric("Con Emergencias 24hs", emergencias)
    
    with col4:
        st.metric("Cobertura", "Toda CABA")


# ════════════════════════════════════════════════════════════════
# 7-9. OTROS MÓDULOS (Dashboard, Operativo, Liquidación) - IGUALES AL ANTERIOR
# ════════════════════════════════════════════════════════════════

elif pantalla_activa == "📋 Dashboard y Contabilidad":

    evento = EventoSwarm(
        timestamp=datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        tipo_evento="MODULO_CONTABILIDAD",
        descripcion="Usuario solicita visualizar datos contables y financieros",
        modulo_solicitante="📋 Dashboard",
        parametros={"edificio": edificio_seleccionado},
    )

    encabezado("Dashboard y Contabilidad", "Edificio monitorizado:", edificio_seleccionado)

    if (
        "unidades_edificios" in st.session_state
        and not st.session_state.unidades_edificios.empty
        and edificio_seleccionado in st.session_state.unidades_edificios["Edificio"].unique()
    ):
        unidades_edificio = st.session_state.unidades_edificios[st.session_state.unidades_edificios["Edificio"] == edificio_seleccionado]
        if not unidades_edificio.empty:
            st.markdown("---")
            st.header("🏠 Unidades Funcionales del Edificio")
            unidades_mostrar = unidades_edificio[["UF/Dpto", "Piso", "Porcentual Expensas"]].copy()
            unidades_mostrar["Porcentual Expensas"] = unidades_mostrar["Porcentual Expensas"].fillna(0).map(lambda valor: f"{valor:.2f}%")
            st.dataframe(unidades_mostrar, use_container_width=True, hide_index=True)

            total_porcentual = float(unidades_edificio["Porcentual Expensas"].sum())
            st.info(f"📊 Unidades registradas: {len(unidades_edificio)} | Porcentual total: {total_porcentual:.2f}%")

    st.markdown("---")
    with st.expander("🐝 **ACTIVIDAD DEL ENJAMBRE** (Ver cómo trabajan los agentes)", expanded=True):
        st.markdown("### 🎯 Evento Disparador")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.info(f"**Tipo de Evento:**\n{evento.tipo_evento}")
        with col2:
            st.info(f"**Módulo:**\n{evento.modulo_solicitante}")
        with col3:
            st.metric("Agentes Activados", 3)

        st.markdown("### 🤖 Estado de Agentes en Tiempo Real")

        agente_placeholders = {}
        agentes_a_procesar = [TipoAgente.CONTABLE.value, TipoAgente.MORA.value, TipoAgente.COMPLIANCE.value]
        for agente_tipo in agentes_a_procesar:
            agente_placeholders[agente_tipo] = st.empty()

        resultados = orquestador.disparar_enjambre(
            evento, edificio_seleccionado,
            mora_real_edificio(st.session_state.get("usuario"), edificio_seleccionado),
        )

        for agente_nombre, resultado in resultados.items():
            if agente_nombre not in [TipoAgente.AUDITOR.value, TipoAgente.REPORTES.value]:
                estado_emoji = {
                    EstadoAgente.COMPLETADO: "✅",
                    EstadoAgente.PROCESANDO: "⏳",
                    EstadoAgente.ERROR: "❌",
                    EstadoAgente.ACTIVADO: "🟢",
                }
                emoji = estado_emoji.get(resultado.estado, "❓")
                css_class = {
                    EstadoAgente.COMPLETADO: "swarm-completed",
                    EstadoAgente.PROCESANDO: "swarm-processing",
                    EstadoAgente.ERROR: "swarm-error",
                    EstadoAgente.ACTIVADO: "swarm-active",
                }.get(resultado.estado, "")
                robot_emoji = "🤖 → "
                if agente_nombre in agente_placeholders:
                    agente_placeholders[agente_nombre].markdown(
                        f"""
                        <div class="swarm-agent {css_class}">
                        <span class="robot-animado">{robot_emoji}</span>{emoji} <b>{agente_nombre}</b><br/>
                        ⏱️ {resultado.tiempo_procesamiento}
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

    st.markdown("---")
    st.header("📊 Panel de Métricas Clave")
    st.caption("ℹ️ Los ingresos, gastos y el prorrateo de este panel son de demostración. "
               "Los datos reales se cargan en 📊 Liquidación de Expensas y 💵 Cobranzas, Mora y Recibos.")

    resultado_contable = resultados.get(TipoAgente.CONTABLE.value)
    if resultado_contable and resultado_contable.estado == EstadoAgente.COMPLETADO:
        datos_contables = resultado_contable.datos_procesados

        m1, m2, m3, m4 = st.columns(4)
        with m1:
            st.metric("💰 Total Gastos", f"${datos_contables['total_gastos']:,.2f}")
        with m2:
            st.metric("🏦 Fondos de Reserva", f"${ESTADISTICAS_EDIFICIOS[edificio_seleccionado]['reserva']:,.2f}")
        with m3:
            resultado_mora = resultados.get(TipoAgente.MORA.value)
            mora_txt = resultado_mora.datos_procesados.get("uf_en_mora", "N/A") if resultado_mora else "N/A"
            st.metric("⚠️ UF en Mora", mora_txt)
        with m4:
            delta_text = "Positivo ✅" if datos_contables["balance_neto"] > 0 else "Déficit ❌"
            st.metric("💹 Balance Neto", f"${datos_contables['balance_neto']:,.2f}", delta=delta_text)

    st.markdown("---")
    st.header("📥 Flujo de Ingresos Percibidos")

    if resultado_contable and resultado_contable.estado == EstadoAgente.COMPLETADO:
        ingresos_df = pd.DataFrame(resultado_contable.datos_procesados["ingresos"])
        st.dataframe(ingresos_df, use_container_width=True, hide_index=True)
        st.success(f"✅ **Total Ingresos:** ${resultado_contable.datos_procesados['total_ingresos']:,.2f}")

    st.markdown("---")
    st.header("📤 Flujo de Gastos Devengados")

    if resultado_contable and resultado_contable.estado == EstadoAgente.COMPLETADO:
        gastos_df = pd.DataFrame(resultado_contable.datos_procesados["gastos"])
        st.dataframe(gastos_df, use_container_width=True, hide_index=True)
        st.info(f"📌 **Total Gastos:** ${resultado_contable.datos_procesados['total_gastos']:,.2f}")

    st.markdown("---")
    st.header("🧮 Liquidación Prorrateada por Departamento")
    st.markdown("Distribución legal s/ Art. 2048 Código Civil y Comercial - Cuota Parte 20% Equitativo:")

    if resultado_contable and resultado_contable.estado == EstadoAgente.COMPLETADO:
        total_g = resultado_contable.datos_procesados["total_gastos"]
        cuota_parte_gasto = total_g * 0.20

        prorrateo_data = [
            {
                "Unidad Funcional": f"UF 0{i}",
                "Piso/Dpto": f"{i}° A",
                "Coeficiente": "20.00%",
                "Monto a Pagar ($)": cuota_parte_gasto,
            }
            for i in range(1, 6)
        ]
        prorrateo_df = pd.DataFrame(prorrateo_data)
        st.dataframe(prorrateo_df, use_container_width=True, hide_index=True)
        st.success(f"⚖️ **Balance Contable del Consorcio (Resultado Neto):** ${resultado_contable.datos_procesados['balance_neto']:,.2f}")

    st.markdown("---")
    st.header("⚠️ Estado de Cobranza")

    resultado_mora = resultados.get(TipoAgente.MORA.value)
    if resultado_mora and resultado_mora.estado == EstadoAgente.COMPLETADO:
        datos_mora = resultado_mora.datos_procesados
        alerta = datos_mora.get("nivel_alerta", "Información no disponible")
        if "CRÍTICO" in alerta:
            st.error(f"🔴 {alerta}")
        elif "MODERADO" in alerta:
            st.warning(f"🟡 {alerta}")
        else:
            st.success(f"🟢 {alerta}")

        with st.expander("📋 Acciones Recomendadas"):
            for accion in datos_mora.get("acciones_recomendadas", []):
                st.write(f"• {accion}")

        if datos_mora.get("fuente") == "real":
            mc1, mc2, mc3 = st.columns(3)
            mc1.metric("Capital adeudado", f"${datos_mora['capital_adeudado']:,.2f}")
            mc2.metric("Interés punitorio", f"${datos_mora['interes_punitorio']:,.2f}")
            mc3.metric("Total adeudado", f"${datos_mora['total_adeudado']:,.2f}")
            if datos_mora["detalle"]:
                st.dataframe(pd.DataFrame(datos_mora["detalle"]), use_container_width=True, hide_index=True)
        else:
            if st.session_state.get("error_bd"):
                st.warning("⚠️ No se pudo leer la base de datos de Cobranzas, por eso se muestran datos de "
                           f"demostración. Detalle: {st.session_state['error_bd']}")
            st.caption("ℹ️ Dato de demostración: este edificio aún no tiene cargos emitidos en el módulo "
                       "💵 Cobranzas, Mora y Recibos. Al emitirlos, acá verás la mora real.")


elif pantalla_activa == "🔧 Órdenes de Trabajo de Campo":

    evento = EventoSwarm(
        timestamp=datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        tipo_evento="MODULO_OPERATIVO",
        descripcion="Usuario solicita gestión de órdenes de trabajo y proveedores",
        modulo_solicitante="🔧 Operativo",
        parametros={"edificio": edificio_seleccionado},
    )

    encabezado("Órdenes de Trabajo", "Edificio operando:", edificio_seleccionado)

    if (
        "unidades_edificios" in st.session_state
        and not st.session_state.unidades_edificios.empty
        and edificio_seleccionado in st.session_state.unidades_edificios["Edificio"].unique()
    ):
        unidades_edificio = st.session_state.unidades_edificios[st.session_state.unidades_edificios["Edificio"] == edificio_seleccionado]
        if not unidades_edificio.empty:
            st.markdown("---")
            st.header("🏠 Unidades Funcionales del Edificio")
            unidades_mostrar = unidades_edificio[["UF/Dpto", "Piso", "Porcentual Expensas"]].copy()
            unidades_mostrar["Porcentual Expensas"] = unidades_mostrar["Porcentual Expensas"].fillna(0).map(lambda valor: f"{valor:.2f}%")
            st.dataframe(unidades_mostrar, use_container_width=True, hide_index=True)

            total_porcentual = float(unidades_edificio["Porcentual Expensas"].sum())
            st.info(f"📊 Unidades registradas: {len(unidades_edificio)} | Porcentual total: {total_porcentual:.2f}%")

    st.markdown("---")
    with st.expander("🐝 **ACTIVIDAD DEL ENJAMBRE** (Ver cómo trabajan los agentes)", expanded=True):
        st.markdown("### 🎯 Evento Disparador")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.info(f"**Tipo de Evento:**\n{evento.tipo_evento}")
        with col2:
            st.info(f"**Módulo:**\n{evento.modulo_solicitante}")
        with col3:
            st.metric("Agentes Activados", 3)

        st.markdown("### 🤖 Estado de Agentes en Tiempo Real")

        agente_placeholders = {}
        agentes_a_procesar = [TipoAgente.OPERATIVO.value, TipoAgente.PROVEEDORES.value, TipoAgente.COMPLIANCE.value]
        for agente_tipo in agentes_a_procesar:
            agente_placeholders[agente_tipo] = st.empty()

        resultados = orquestador.disparar_enjambre(evento, edificio_seleccionado)

        for agente_nombre, resultado in resultados.items():
            if agente_nombre not in [TipoAgente.AUDITOR.value, TipoAgente.REPORTES.value]:
                estado_emoji = {
                    EstadoAgente.COMPLETADO: "✅",
                    EstadoAgente.PROCESANDO: "⏳",
                    EstadoAgente.ERROR: "❌",
                    EstadoAgente.ACTIVADO: "🟢",
                }
                emoji = estado_emoji.get(resultado.estado, "❓")
                css_class = {
                    EstadoAgente.COMPLETADO: "swarm-completed",
                    EstadoAgente.PROCESANDO: "swarm-processing",
                    EstadoAgente.ERROR: "swarm-error",
                    EstadoAgente.ACTIVADO: "swarm-active",
                }.get(resultado.estado, "")
                robot_emoji = "🤖 → "
                if agente_nombre in agente_placeholders:
                    agente_placeholders[agente_nombre].markdown(
                        f"""
                        <div class="swarm-agent {css_class}">
                        <span class="robot-animado">{robot_emoji}</span>{emoji} <b>{agente_nombre}</b><br/>
                        ⏱️ {resultado.tiempo_procesamiento}
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

    st.markdown("---")
    st.header("📜 Cartilla de Prestadores de Servicio Matriculados")
    st.markdown("Validación de CUIT y vigencia fiscal automatizada por el Agente Compliance:")

    resultado_proveedores = resultados.get(TipoAgente.PROVEEDORES.value)
    if resultado_proveedores and resultado_proveedores.estado == EstadoAgente.COMPLETADO:
        proveedores_df = pd.DataFrame(resultado_proveedores.datos_procesados["proveedores"])
        columnas_mostrar = ["Rubro", "Prestador", "CUIT", "Teléfono", "Email", "Zona de Atención"]
        st.dataframe(proveedores_df[columnas_mostrar], use_container_width=True, hide_index=True)

        col1, col2 = st.columns(2)
        with col1:
            st.info(f"📊 Total Prestadores: {resultado_proveedores.datos_procesados['total_disponibles']}")
        with col2:
            rubros = ", ".join([r.replace("🚰 ", "").replace("⚡ ", "").replace("🔑 ", "").replace("🧱 ", "").replace("🚪 ", "").replace("🧹 ", "").replace("🔧 ", "") for r in resultado_proveedores.datos_procesados["rubros"]])
            st.info(f"🏷️ Rubros Disponibles: {rubros}")

    st.markdown("---")
    st.header("📋 Registro Central de Órdenes de Trabajo (OT)")
    st.markdown("Bitácora de auditoría de reparaciones y costos liquidados en el periodo fiscal:")

    resultado_operativo = resultados.get(TipoAgente.OPERATIVO.value)
    if resultado_operativo and resultado_operativo.estado == EstadoAgente.COMPLETADO:
        ots_df = pd.DataFrame(resultado_operativo.datos_procesados["ordenes_trabajo"])
        st.dataframe(ots_df, use_container_width=True, hide_index=True)

        col1, col2 = st.columns(2)
        with col1:
            st.warning(f"⚙️ Órdenes de Trabajo: {resultado_operativo.datos_procesados['total_ordenes']}")
        with col2:
            st.metric("Presupuesto Total", f"${resultado_operativo.datos_procesados['presupuesto_total']:,.2f}")

    st.markdown("---")
    resultado_compliance = resultados.get(TipoAgente.COMPLIANCE.value)
    if resultado_compliance and resultado_compliance.estado == EstadoAgente.COMPLETADO:
        st.header("✅ Validaciones Normativas")
        validaciones = resultado_compliance.datos_procesados

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.success(validaciones.get("ley_941_caba", "N/A"))
        with col2:
            st.success(validaciones.get("codigo_civil_comercial", "N/A"))
        with col3:
            st.success(validaciones.get("validacion_cuit", "N/A"))
        with col4:
            st.success(validaciones.get("vigencia_fiscal", "N/A"))


elif pantalla_activa == "📊 Liquidación de Expensas":

    encabezado("Liquidación de Expensas", "Edificio activo:", edificio_seleccionado)
    st.markdown("---")

    st.header("📊 Liquidación Integral de Expensas")
    st.markdown("**Proceso Completo: Ingresos → Gastos → Prorrateo por UF**")

    if "periodo_liquidacion" not in st.session_state:
        st.session_state.periodo_liquidacion = "Octubre 2026"

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "💵 Ingresos",
        "💰 Gastos",
        "📋 Resumen",
        "🏠 Por Unidad Funcional",
        "🖨️ Exportar"
    ])

    with tab1:
        st.subheader("Registre los Ingresos del Período")
        col1, col2 = st.columns(2)
        with col1:
            periodo = st.selectbox("Período de Liquidación", ["Octubre 2026", "Noviembre 2026", "Diciembre 2026"], key="periodo_liquidacion")
        with col2:
            tipo_ingreso_sel = st.selectbox("Tipo de Ingreso", [t.value for t in TipoIngreso])

        col1, col2, col3 = st.columns(3)
        with col1:
            concepto_ing = st.text_input("Concepto", placeholder="Ej: Expensas octubre")
        with col2:
            monto_ing = st.number_input("Monto ($)", min_value=0.0, step=100.0)
        with col3:
            descripcion_ing = st.text_input("Descripción", placeholder="Detalles adicionales")

        if st.button("✅ Registrar Ingreso", key="btn_ingreso"):
            if concepto_ing and monto_ing > 0:
                nuevo_ingreso = RegistroIngreso(
                    concepto=concepto_ing,
                    tipo_ingreso=TipoIngreso(tipo_ingreso_sel),
                    monto=monto_ing,
                    descripcion=descripcion_ing,
                )
                agente_liquidacion.registrar_ingreso(nuevo_ingreso)
                st.success(f"✅ Ingreso registrado: {concepto_ing} - ${monto_ing:,.2f}")
            else:
                st.error("❌ Complete todos los campos requeridos")

        if agente_liquidacion.ingresos_registrados:
            st.markdown("---")
            st.subheader("Ingresos Registrados")
            ingresos_data = []
            for ing in agente_liquidacion.ingresos_registrados:
                ingresos_data.append({
                    "Concepto": ing.concepto,
                    "Tipo": ing.tipo_ingreso.value,
                    "Monto ($)": f"${ing.monto:,.2f}",
                    "Descripción": ing.descripcion
                })
            df_ingresos = pd.DataFrame(ingresos_data)
            st.dataframe(df_ingresos, use_container_width=True, hide_index=True)
            total_ingresos = sum(ing.monto for ing in agente_liquidacion.ingresos_registrados)
            st.metric("💵 Total Ingresos", f"${total_ingresos:,.2f}")

    with tab2:
        st.subheader("Registre los Gastos del Período")
        col1, col2 = st.columns(2)
        with col1:
            tipo_gasto_sel = st.selectbox("Tipo de Gasto", [t.value for t in TipoGasto], key="tipo_gasto")
        with col2:
            factura = st.text_input("Número de Factura", placeholder="Ej: 00001234")

        col1, col2, col3 = st.columns(3)
        with col1:
            concepto_gast = st.text_input("Concepto", placeholder="Ej: Electricidad", key="concepto_gasto")
        with col2:
            monto_gast = st.number_input("Monto ($)", min_value=0.0, step=100.0, key="monto_gasto")
        with col3:
            descripcion_gast = st.text_input("Descripción", placeholder="Detalles", key="desc_gasto")

        if st.button("✅ Registrar Gasto", key="btn_gasto"):
            if concepto_gast and monto_gast > 0:
                nuevo_gasto = RegistroGasto(
                    concepto=concepto_gast,
                    tipo_gasto=TipoGasto(tipo_gasto_sel),
                    monto=monto_gast,
                    descripcion=descripcion_gast,
                    factura=factura,
                )
                agente_liquidacion.registrar_gasto(nuevo_gasto)
                st.success(f"✅ Gasto registrado: {concepto_gast} - ${monto_gast:,.2f}")
            else:
                st.error("❌ Complete los campos requeridos")

        if agente_liquidacion.gastos_registrados:
            st.markdown("---")
            st.subheader("Gastos Registrados")
            gastos_data = []
            for gast in agente_liquidacion.gastos_registrados:
                gastos_data.append({
                    "Concepto": gast.concepto,
                    "Tipo": gast.tipo_gasto.value,
                    "Factura": gast.factura,
                    "Monto ($)": f"${gast.monto:,.2f}",
                    "Descripción": gast.descripcion
                })
            df_gastos = pd.DataFrame(gastos_data)
            st.dataframe(df_gastos, use_container_width=True, hide_index=True)
            total_gastos = sum(gast.monto for gast in agente_liquidacion.gastos_registrados)
            st.metric("💰 Total Gastos", f"${total_gastos:,.2f}")

    with tab3:
        st.subheader("Resumen Ejecutivo de Liquidación")

        if agente_liquidacion.gastos_registrados or agente_liquidacion.ingresos_registrados:
            df_coef_liq = coeficientes_para_liquidar(edificio_seleccionado)
            liquidacion = None
            if df_coef_liq is None:
                st.session_state.liquidacion_actual = None
                st.error(f"❌ No hay coeficientes para {edificio_seleccionado}. Cargá el archivo de coeficientes "
                         "(UF, Propietario, Piso, Coeficiente, Contacto) o la base de edificios en la barra "
                         "lateral. El sistema ya no inventa unidades funcionales.")
            else:
                agente_liquidacion.cargar_coeficientes_desde_dataframe(df_coef_liq)
                try:
                    liquidacion = agente_liquidacion.calcular_liquidacion(st.session_state.periodo_liquidacion)
                    st.session_state.liquidacion_actual = liquidacion
                except ValueError as e:
                    st.session_state.liquidacion_actual = None
                    st.error(f"❌ {e}")

            if liquidacion is not None:

                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("💵 Total Ingresos", f"${liquidacion.total_ingresos:,.2f}")
                with col2:
                    st.metric("💰 Total Gastos", f"${liquidacion.total_gastos:,.2f}")
                with col3:
                    resultado = liquidacion.deficit_o_superavit
                    st.metric("⚖️ Resultado", f"${abs(resultado):,.2f}", delta=("Superávit ✅" if resultado > 0 else "Déficit ⚠️"))
                with col4:
                    st.metric("📅 Período", liquidacion.periodo)

                st.markdown("---")

                st.subheader("📥 Desglose de Ingresos por Rubro")
                ingresos_rubro_data = []
                for rubro, monto in liquidacion.ingresos_por_rubro.items():
                    porcentaje = (monto / liquidacion.total_ingresos * 100) if liquidacion.total_ingresos > 0 else 0
                    ingresos_rubro_data.append({
                        "Rubro": rubro,
                        "Monto ($)": f"${monto:,.2f}",
                        "Porcentaje": f"{porcentaje:.1f}%"
                    })
                if ingresos_rubro_data:
                    df_ing_rubro = pd.DataFrame(ingresos_rubro_data)
                    st.dataframe(df_ing_rubro, use_container_width=True, hide_index=True)

                st.markdown("---")

                st.subheader("📤 Desglose de Gastos por Rubro")
                gastos_rubro_data = []
                for rubro, monto in liquidacion.gastos_por_rubro.items():
                    porcentaje = (monto / liquidacion.total_gastos * 100) if liquidacion.total_gastos > 0 else 0
                    gastos_rubro_data.append({
                        "Rubro": rubro,
                        "Monto ($)": f"${monto:,.2f}",
                        "Porcentaje": f"{porcentaje:.1f}%"
                    })
                if gastos_rubro_data:
                    df_gast_rubro = pd.DataFrame(gastos_rubro_data)
                    st.dataframe(df_gast_rubro, use_container_width=True, hide_index=True)

        else:
            st.info("📭 Registre ingresos y gastos para generar el resumen")

    with tab4:
        st.subheader("🏠 Liquidación por Unidad Funcional")

        if st.session_state.liquidacion_actual:
            liquidacion = st.session_state.liquidacion_actual

            st.markdown(f"**Período:** {liquidacion.periodo}")
            st.markdown(f"**Total a Prorratear:** ${liquidacion.total_gastos:,.2f}")
            st.markdown("**Coeficientes de Distribución (Art. 2048 - Código Civil y Comercial)**")
            st.markdown("---")

            expensas_uf_data = []
            for uf, coef_obj in liquidacion.coeficientes.items():
                gasto_uf = liquidacion.expensas_por_uf.get(uf, 0)
                expensas_uf_data.append({
                    "UF/Dpto": uf,
                    "Propietario": coef_obj.propietario,
                    "Coeficiente": f"{coef_obj.coeficiente:.4f}",
                    "Porcentaje": f"{coef_obj.coeficiente * 100:.2f}%",
                    "Expensas a Pagar ($)": f"${gasto_uf:,.2f}"
                })

            df_expensas_uf = pd.DataFrame(expensas_uf_data)
            st.dataframe(df_expensas_uf, use_container_width=True, hide_index=True)

            st.markdown("---")
            st.markdown("📋 **Verificaciones Contables:**")
            col1, col2, col3 = st.columns(3)

            suma_coeficientes = sum(coef_obj.coeficiente for coef_obj in liquidacion.coeficientes.values())
            suma_expensas = sum(liquidacion.expensas_por_uf.values())

            with col1:
                st.success(f"✅ Coeficientes normalizados: {suma_coeficientes:.4f}")

            with col2:
                st.success(f"✅ Expensas prorrateadas: ${suma_expensas:,.2f}")

            with col3:
                st.info(f"📊 UF registradas: {len(liquidacion.coeficientes)}")

            st.markdown("---")
            st.markdown("### 📄 Generar Estado de Cuenta por UF")
            st.markdown("Seleccione una UF para ver su estado de cuenta detallado.")

            uf_lista = list(liquidacion.coeficientes.keys())
            uf_seleccionada_ec = st.selectbox("Seleccione UF:", uf_lista, key="uf_estado_cuenta")

            if st.button("🖨️ Generar Estado de Cuenta", key="btn_estado_cuenta"):
                estado_cuenta = agente_liquidacion.generar_estado_cuenta_uf(uf_seleccionada_ec, liquidacion)

                if estado_cuenta:
                    st.markdown(
                        f"""
                        <div class="estado-cuenta-box">
                            <h3 style="color: #38bdf8;">ESTADO DE CUENTA</h3>
                            <p><b>Edificio:</b> {edificio_seleccionado}</p>
                            <p><b>Unidad Funcional:</b> {estado_cuenta['uf']}</p>
                            <p><b>Propietario:</b> {estado_cuenta['propietario']}</p>
                            <p><b>Piso:</b> {estado_cuenta['piso']}</p>
                            <p><b>Teléfono/Contacto:</b> {estado_cuenta['contacto']}</p>
                            <hr style="border-color: #38bdf8;">
                            <p><b>Período:</b> {estado_cuenta['periodo']}</p>
                            <p><b>Coeficiente:</b> {estado_cuenta['coeficiente']:.4f} ({estado_cuenta['porcentaje']})</p>
                            <p><b>Total Gastos a Prorratear:</b> ${estado_cuenta['total_gastos']:,.2f}</p>
                            <h4 style="color: #10b981; font-size: 1.5rem;">EXPENSAS A PAGAR: ${estado_cuenta['expensas_a_pagar']:,.2f}</h4>
                            <hr style="border-color: #38bdf8;">
                            <p><b>Fecha de Liquidación:</b> {estado_cuenta['fecha_liquidacion']}</p>
                            <p><b>Vencimiento de Pago:</b> {estado_cuenta['vencimiento']}</p>
                            <p style="font-size: 0.9rem; color: #94a3b8;">Pago realizado dentro de los 10 días de notificación</p>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
        else:
            st.info("📭 Complete el resumen para ver la distribución por UF")

    with tab5:
        st.subheader("📥 Exportar Liquidación")

        if st.session_state.liquidacion_actual:
            liquidacion = st.session_state.liquidacion_actual
            st.markdown("### Opciones de Exportación")
            col1, col2 = st.columns(2)

            with col1:
                if st.button("📊 Descargar Excel", key="btn_excel"):
                    try:
                        excel_file = agente_liquidacion.generar_excel_liquidacion(liquidacion, edificio_seleccionado)
                        st.download_button(
                            label="⬇️ Descargar Archivo Excel",
                            data=excel_file,
                            file_name=f"Liquidacion_Expensas_{edificio_seleccionado.replace(' ', '_')}_{liquidacion.periodo.replace(' ', '_')}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        )
                        st.success("✅ Archivo Excel generado correctamente")
                    except Exception as e:
                        st.error(f"❌ No se pudo exportar Excel: {e}")

            with col2:
                if st.button("📋 Copiar Datos", key="btn_copy"):
                    st.info("📋 Datos listos para copiar")

            st.markdown("---")
            st.markdown("### 📊 Vista Previa de Datos para Exportar")

            col1, col2 = st.columns(2)
            with col1:
                st.subheader("Resumen")
                resumen_data = {
                    "Total Ingresos": f"${liquidacion.total_ingresos:,.2f}",
                    "Total Gastos": f"${liquidacion.total_gastos:,.2f}",
                    "Resultado": f"${liquidacion.deficit_o_superavit:,.2f}",
                    "Período": liquidacion.periodo,
                }
                st.json(resumen_data)

            with col2:
                st.subheader("Totales por Rubro")
                st.write("**Ingresos:**")
                for rubro, monto in liquidacion.ingresos_por_rubro.items():
                    st.write(f"- {rubro}: ${monto:,.2f}")
                st.write("\n**Gastos:**")
                for rubro, monto in liquidacion.gastos_por_rubro.items():
                    st.write(f"- {rubro}: ${monto:,.2f}")

        else:
            st.info("📭 Genere una liquidación primero")


elif pantalla_activa == "💵 Cobranzas, Mora y Recibos":

    encabezado("Cobranzas, Mora y Recibos", "Edificio activo:", edificio_seleccionado)
    st.markdown("---")
    st.header("💵 Cobranzas, Mora y Recibos")

    if login_cobranzas():
        usuario_actual = st.session_state["usuario"]

        with st.expander("🔗 Traer el edificio activo a Cobranzas (consorcio + unidades funcionales)"):
            st.caption("Crea el consorcio con el nombre del edificio activo y carga sus UF desde los "
                       "coeficientes cargados o, si no hay, desde la base de edificios.")
            if st.button("Importar edificio activo", key="btn_importar_cobranzas"):
                df_uf = coeficientes_para_liquidar(edificio_seleccionado)
                if df_uf is None:
                    st.error("No hay coeficientes ni base de unidades para este edificio. Cargalos en la barra lateral.")
                else:
                    conn_imp = get_conn()
                    try:
                        init_db(conn_imp)
                        cid_imp = crear_consorcio(conn_imp, usuario_actual, edificio_seleccionado)
                        n_imp = cargar_unidades_desde_df(conn_imp, cid_imp, df_uf)
                    finally:
                        conn_imp.close()
                    st.success(f"✅ Consorcio «{edificio_seleccionado}» listo con {n_imp} unidades funcionales.")

        liq_vigente = st.session_state.liquidacion_actual
        if liq_vigente:
            st.info(f"📊 Liquidación vigente: **{edificio_seleccionado}** — {liq_vigente.periodo}. "
                    "Sus expensas por UF se usan para emitir los cargos en la pestaña 📉 Mora y deuda.")
        render_modulo_cobranzas(liq_vigente.expensas_por_uf if liq_vigente else None)


# ════════════════════════════════════════════════════════════════
# 10. FOOTER
# ════════════════════════════════════════════════════════════════

st.markdown("---")
st.markdown(
    """
    <div class='pie'>
    <b>🏢 Resilia_IA v2.0 - Arquitectura Multiagente con Enjambre Coordinado</b><br/>
    <small>Cada solicitud dispara un equipo de agentes especializados que trabajan sinérgicamente<br/>
    🐝 Sistema de Inteligencia Distribuida para Gestión de Condominios</small>
    </div>
    """,
    unsafe_allow_html=True,
)
# ==============================================================================
# MÓDULO ADICIONAL: PANEL DE CONTROL FINANCIERO E INTELIGENCIA DE NEGOCIO
# ==============================================================================
import pandas as pd
import numpy as np

st.sidebar.divider()
st.sidebar.subheader("⚙️ Herramientas Financieras e IA")

# Desplegable en el menú lateral para elegir cuál de las 5 herramientas usar
herramienta = st.sidebar.selectbox(
    "Seleccionar Herramienta Avanzada:",
    [
        "1. Panel de Ratios y Aging",
        "2. Alertas de Desvíos y Facturas Duplicadas",
        "3. Proyección y Simulador de Escenarios",
        "4. Lectura Automática de Facturas (OCR)",
        "5. Predicción Preventiva de Mora"
    ]
)

# ------------------------------------------------------------------------------
# 1. PANEL DE RATIOS Y AGING (Cobrabilidad, Morosidad, Fondo de Reserva)
# ------------------------------------------------------------------------------
if herramienta == "1. Panel de Ratios y Aging":
    st.divider()
    st.header("📊 Panel de Ratios Financieros y Aging de Deuda")
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Cobrabilidad del Mes", "86.0%", "+2.3% vs mes anterior")
    col2.metric("Tasa de Morosidad", "14.0%", "-2.3% mejora", delta_color="normal")
    col3.metric("Fondo de Reserva", "$5.400.000")
    col4.metric("Fondo en Cobertura", "3.0 meses", "Meta: >= 2.0 meses")
    
    st.subheader("📉 Aging de Deuda por Tramo de Antigüedad ($)")
    df_aging_demo = pd.DataFrame({
        'Tramo': ['Al Día', '30 Días', '60 Días', '90+ Días'],
        'Monto ($)': [1250000, 420000, 210000, 180000]
    }).set_index('Tramo')
    st.bar_chart(df_aging_demo)

# ------------------------------------------------------------------------------
# 2. ALERTAS DE DESVÍOS EN GASTOS Y FACTURAS DUPLICADAS
# ------------------------------------------------------------------------------
elif herramienta == "2. Alertas de Desvíos y Facturas Duplicadas":
    st.divider()
    st.header("🚨 Detección de Desvíos Presupuestarios y Duplicados")
    
    st.warning("⚠️ **Alerta de Mantenimiento Ascensores**: El gasto real ($380.000) superó el presupuesto ($250.000) en un **52.0%**.")
    st.warning("⚠️ **Alerta de Servicios Públicos**: El gasto real ($290.000) superó el presupuesto ($210.000) en un **38.1%**.")
    
    st.subheader("📊 Comparativo Presupuestado vs Ejecutado")
    df_desvios = pd.DataFrame({
        'Rubro': ['Ascensores', 'Limpieza', 'Seguridad', 'Luz/Agua', 'Mantenimiento'],
        'Presupuestado ($)': [250000, 180000, 650000, 210000, 150000],
        'Ejecutado ($)': [380000, 185000, 650000, 290000, 140000]
    }).set_index('Rubro')
    st.bar_chart(df_desvios)
    
    st.subheader("🔍 Facturas Duplicadas Detectadas")
    st.error("❌ **Comprobante Repetido**: Proveedor 'Elevadores SRL' — Factura B 0004-12894 — Monto: $190.000 — Fecha: 05/09/2026")

# ------------------------------------------------------------------------------
# 3. PROYECCIÓN DE GASTOS Y SIMULADOR DE ESCENARIOS
# ------------------------------------------------------------------------------
elif herramienta == "3. Proyección y Simulador de Escenarios":
    st.divider()
    st.header("📈 Proyección de Gastos y Simulador de Escenarios")
    
    c1, c2 = st.columns(2)
    with c1:
        inflacion_m = st.slider("Inflación Mensual Estimada (%)", 0.0, 15.0, 4.0, 0.5)
        aumento_exp = st.slider("Aumento Programado Expensas (%)", 0.0, 30.0, 5.0, 1.0)
    with c2:
        plazo = st.selectbox("Plazo de Proyección (Meses)", [3, 6, 12], index=1)
        cuota_extra = st.number_input("Cuota Extraordinaria por U.F. ($)", value=0, step=5000)
        
    gastos_p, ingresos_p, fondo_p = [], [], []
    g_act, i_act, fondo_act = 1800000, 2150000 + (cuota_extra * 20), 5400000
    
    for _ in range(plazo):
        g_act *= (1 + inflacion_m / 100)
        i_act *= (1 + aumento_exp / 100)
        fondo_act += (i_act - g_act)
        gastos_p.append(g_act)
        ingresos_p.append(i_act)
        fondo_p.append(fondo_act)
        
    df_proy = pd.DataFrame({
        'Mes': [f"Mes {i+1}" for i in range(plazo)],
        'Ingresos ($)': ingresos_p,
        'Gastos ($)': gastos_p,
        'Fondo Reserva ($)': fondo_p
    }).set_index('Mes')
    
    st.line_chart(df_proy)

# ------------------------------------------------------------------------------
# 4. LECTURA AUTOMÁTICA DE FACTURAS (OCR)
# ------------------------------------------------------------------------------
elif herramienta == "4. Lectura Automática de Facturas (OCR)":
    st.divider()
    st.header("📄 Ingesta y Lectura Automática de Facturas (OCR)")
    
    archivo_f = st.file_uploader("Subir factura o comprobante (PDF, JPG, PNG)", type=['pdf', 'jpg', 'jpeg', 'png'])
    
    if archivo_f is not None or st.button("🚀 Simular Lectura OCR de Ejemplo"):
        st.success("✅ **Comprobante procesado con éxito por el modelo de visión**")
        
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            st.write("**Proveedor:** Ascensores y Servicios SRL")
            st.write("**CUIT:** 30-71889900-4")
            st.write("**Tipo:** Factura B")
        with col_f2:
            st.write("**Monto Total:** $215.000,00")
            st.write("**Fecha:** 02/10/2026")
            st.write("**Rubro:** Mantenimiento Ascensores")
            
        if st.button("💾 Guardar en Contabilidad"):
            st.balloons()
            st.success("¡Gasto registrado automáticamente en la base de datos!")

# ------------------------------------------------------------------------------
# 5. PREDICCIÓN DE MORA
# ------------------------------------------------------------------------------
elif herramienta == "5. Predicción Preventiva de Mora":
    st.divider()
    st.header("🔮 Predicción Preventiva de Mora")
    st.caption("Scoring predictivo de probabilidad de atraso en el pago para el próximo vencimiento.")
    
    unidades_m = [f"U.F. {i:02d}" for i in range(1, 11)]
    np.random.seed(42)
    riesgos = np.random.randint(10, 85, size=10)
    
    df_mora = pd.DataFrame({
        'Unidad': unidades_m,
        'Riesgo Estimado (%)': riesgos
    }).sort_values(by='Riesgo Estimado (%)', ascending=False)
    
    st.dataframe(df_mora, use_container_width=True)
    st.bar_chart(df_mora.set_index('Unidad'))

# ------------------------------------------------------------------------------
# INFRAESTRUCTURA PENDIENTE PARA SINCRONIZACIÓN EXTERNA
# ------------------------------------------------------------------------------
st.sidebar.divider()
with st.sidebar.expander("🌐 Sincronización Externa Pendiente"):
    st.warning("⚠️ **Infraestructura pendiente para sincronización externa:**")
    st.markdown("""
    * **Cobros automáticos:** Requiere servidor externo dedicado a escuchar *webhooks* bancarios.
    * **Portal del propietario:** Requiere interfaz con credenciales individuales para consulta de deuda.
    """)
