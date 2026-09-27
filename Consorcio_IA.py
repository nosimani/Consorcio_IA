import streamlit as st
import pandas as pd
from datetime import datetime

# CONFIGURACIÓN HIGH-END DE LA INTERFAZ
st.set_page_config(
    page_title="Resilia_Condominios",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inyección de CSS de Alta Visibilidad (Garantiza contraste absoluto s/ fondo negro)
st.markdown("""
    <style>
        /* Fondo Negro Absolute en toda la aplicación */
        .main, [data-testid="stAppViewContainer"], [data-testid="stHeader"] { 
            background-color: #000000 !important; 
            background: #000000 !important;
        }
        
        /* Forzar letras enteramente visibles en el Sidebar Izquierdo */
        [data-testid="stSidebar"], [data-testid="stSidebar"] div, [data-testid="stSidebar"] span, [data-testid="stSidebar"] label {
            color: #ffffff !important;
            font-size: 1.2rem !important;
        }
        [data-testid="stSidebar"] p {
            color: #38bdf8 !important;
            font-weight: 700 !important;
        }
        
        /* Contraste estricto para títulos principales */
        h1 { color: #ffffff !important; font-family: sans-serif; font-weight: 900; letter-spacing: -1px; text-shadow: 0 0 20px rgba(56, 189, 248, 0.4); font-size: 2.8rem !important; }
        h2 { color: #38bdf8 !important; font-family: sans-serif; font-weight: 700; font-size: 2.2rem !important; text-shadow: 0 0 10px rgba(56, 189, 248, 0.2); }
        h3 { color: #ffffff !important; font-family: sans-serif; font-weight: 700; font-size: 1.8rem !important; }
        
        /* Textos informativos de párrafos y etiquetas */
        .stMarkdown p, p, label, .stRadio label, span { 
            color: #ffffff !important; 
            font-size: 1.3rem !important; 
            line-height: 1.6 !important; 
        }
        
        /* Forzado de tamaño de letra GIGANTE para el contenido interno de todas las tablas */
        .stDataFrame td, .stDataFrame div, table, td, tr { 
            font-size: 1.5rem !important; 
            font-weight: 600 !important;
            color: #ffffff !important;
        }
        th, .stDataFrame th div { font-weight: 800 !important; color: #38bdf8 !important; font-size: 1.4rem !important; }

        /* Paneles de Métricas en Oro Líquido Flotante */
        div[data-testid="stMetric"] {
            background: linear-gradient(135deg, #d4af37 0%, #aa7c11 100%) !important;
            border-radius: 20px !important;
            padding: 22px !important;
            box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.9);
            border: 1px solid rgba(255, 255, 255, 0.3) !important;
        }
        div[data-testid="stMetric"] label { color: #0f172a !important; font-weight: 800 !important; font-size: 1.1rem !important; }
        div[data-testid="stMetric"] [data-testid="stMetricValue"] { color: #0b192c !important; font-weight: 900 !important; font-size: 2.4rem !important; }
        
        /* Contenedor de tablas adaptado al fondo negro */
        .stDataFrame, .stTable { background-color: rgba(20, 20, 20, 0.8) !important; border-radius: 16px; padding: 10px; border: 1px solid #2d3748; }
    </style>
""", unsafe_allow_html=True)

# BASE DE DATOS GLOBAL DE CONDOMINIOS ESTÁTICA
ESTADISTICAS_EDIFICIOS = {
    "Av. Corrientes 1234, CABA": {"reserva": 450000.0, "factor": 1.0, "mora": "1", "tasa": 4.5, "ots": "5"},
    "Larrea 435, CABA": {"reserva": 380000.0, "factor": 0.6, "mora": "2", "tasa": 5.0, "ots": "5"},
    "Montevideo 891, CABA": {"reserva": 620000.0, "factor": 0.8, "mora": "2", "tasa": 6.2, "ots": "5"},
    "San Jose 1111, CABA": {"reserva": 290000.0, "factor": 0.5, "mora": "1", "tasa": 3.8, "ots": "5"},
    "Guayaquil 399, CABA": {"reserva": 850000.0, "factor": 1.5, "mora": "1", "tasa": 7.5, "ots": "5"}
}

# CARTILLA REQUERIDA DE PROVEEDORES FICTICIOS ORGANIZADOS POR RUBRO
DATOS_CARTILLA_PROVEEDORES = [
    {"Rubro": "Plomería", "Prestador": "🚰 Caños y Sanitarios Express", "CUIT": "30-55489712-4", "Teléfono": "11-4895-1234", "Zona de Atención": "CABA Centro"},
    {"Rubro": "Plomería", "Prestador": "🚰 Ingeniería Hidráulica Sur", "CUIT": "33-66985214-9", "Teléfono": "11-3564-9871", "Zona de Atención": "CABA Norte"},
    {"Rubro": "Electricidad", "Prestador": "⚡ El Fusible Matriculado", "CUIT": "20-14896532-1", "Teléfono": "11-5478-6532", "Zona de Atención": "Toda CABA"},
    {"Rubro": "Electricidad", "Prestador": "⚡ Conexiones Seguras Palermo", "CUIT": "27-33659874-2", "Teléfono": "11-6985-3214", "Zona de Atención": "CABA Norte"},
    {"Rubro": "Cerrajería", "Prestador": "🔑 Llaves Fénix 24hs", "CUIT": "23-45896521-8", "Teléfono": "11-2365-9847", "Zona de Atención": "Urgencias CABA"},
    {"Rubro": "Cerrajería", "Prestador": "🔑 Blindajes y Cerraduras Pro", "CUIT": "30-71458962-3", "Teléfono": "11-4125-3698", "Zona de Atención": "CABA Oeste"},
    {"Rubro": "Albañilería", "Prestador": "🧱 Constructora San José", "CUIT": "30-88547612-5", "Teléfono": "11-5541-2369", "Zona de Atención": "Toda CABA"},
    {"Rubro": "Albañilería", "Prestador": "🧱 Refacciones Integrales Baires", "CUIT": "20-99653214-7", "Teléfono": "11-3254-7896", "Zona de Atención": "CABA Sur"}
]

# INICIALIZACIÓN DE ÓRDENES DE TRABAJO EN ESTADO DE SESIÓN CON DIRECCIONES COINCIDENTES
if "historico_ot" not in st.session_state:
    st.session_state.historico_ot = [
        {"Edificio": "Av. Corrientes 1234, CABA", "UF": "UF 01", "Trabajo": "Plomería", "Presupuesto Aprobado": "$ 250.000.-", "Fecha_Inicio": "01/05/26", "Fecha_Finaliz": "01/05/26", "Estado": "Realizado"},
        {"Edificio": "Larrea 435, CABA", "UF": "UF 03", "Trabajo": "Albañilería", "Presupuesto Aprobado": "$ 390.000.-", "Fecha_Inicio": "07/06/26", "Fecha_Finaliz": "12/06/26", "Estado": "En Proceso"},
        {"Edificio": "Montevideo 891, CABA", "UF": "UF 04", "Trabajo": "Plomería", "Presupuesto Aprobado": "$ 120.000.-", "Fecha_Inicio": "08/09/26", "Fecha_Finaliz": "09/09/26", "Estado": "Realizado"},
        {"Edificio": "San Jose 1111, CABA", "UF": "UF 05", "Trabajo": "Electricidad", "Presupuesto Aprobado": "$ 95.000.-", "Fecha_Inicio": "12/07/26", "Fecha_Finaliz": "12/07/26", "Estado": "Presupuestado"},
        {"Edificio": "Guayaquil 399, CABA", "UF": "UF 02", "Trabajo": "Cerrajería", "Presupuesto Aprobado": "$ 180.000.-", "Fecha_Inicio": "15/08/26", "Fecha_Finaliz": "15/08/26", "Estado": "En Proceso"}
    ]

# INTERFAZ LATERAL DE CONTROL CORPORATIVO UNIFICADA
with st.sidebar:
    st.image("Resilia.jfif", use_container_width=True)
    st.title("Resilia_Condominios")
    st.caption("AI Swarm ERP Platform v2.6")
    st.markdown("---")
    edificio_seleccionado = st.selectbox("Edificio Activo de Control", list(ESTADISTICAS_EDIFICIOS.keys()))
    st.markdown("---")
    st.info("CUIT: 30-11111111-9\n\nJurisdicción: Ley 941 CABA")

consorcio_actual = ESTADISTICAS_EDIFICIOS[edificio_seleccionado]
f_cal = consorcio_actual["factor"]
tasa_act = consorcio_actual["tasa"]

# ====== CÁLCULOS SALARIALES SUTERH OBLIGATORIOS EXIGIDOS ======
neto_encargado = 1500000.0
bruto_referencial = neto_encargado / 0.805
aportes_suterh = bruto_referencial * 0.195
contribuciones_patronales = bruto_referencial * 0.255
total_cargas_sociales = aportes_suterh + contribuciones_patronales

# Listados financieros estructurados con los valores fijos requeridos
ingresos_lista = [
    {"Ingresos": "ingresos por expensas", "Monto ($)": 5320000.0},
    {"Ingresos": "alquileres de locales", "Monto ($)": 3000000.0},
    {"Ingresos": "intereses por colocacion a plazo fijo", "Monto ($)": 14000.0 * f_cal * (tasa_act / 5.0)}
]

gastos_lista = [
    {"Gastos": "reparaciones", "Monto ($)": 45000.0 * f_cal},
    {"Gastos": "honorarios de administración", "Monto ($)": 35000.0 * f_cal},
    {"Gastos": "sueldo de encargado (NETO A COBRAR)", "Monto ($)": neto_encargado},
    {"Gastos": "Cargas Sociales SUTERH (Aportes 19.5% y Contribuciones 25.5%)", "Monto ($)": total_cargas_sociales},
    {"Gastos": "compra de articulos de limpieza", "Monto ($)": 12000.0 * f_cal},
    {"Gastos": "pagos luz", "Monto ($)": 18000.0 * f_cal},
    {"Gastos": "otros gastos", "Monto ($)": 7000.0 * f_cal}
]

total_i_calc = sum(x['Monto ($)'] for x in ingresos_lista)
total_g_calc = sum(x['Monto ($)'] for x in gastos_lista)
balance_neto = total_i_calc - total_g_calc

# REGLA ESTRUCTURAL DE COPROPIEDAD
unidades_reglamento = [
    {"UF": "UF 01", "Piso": "1° A", "Coeficiente": 0.35, "Deuda_Base": 0.0},
    {"UF": "UF 02", "Piso": "1° B", "Coeficiente": 0.25, "Deuda_Base": 180000.0 if consorcio_actual["mora"] >= "1" else 0.0},
    {"UF": "UF 03", "Piso": "2° A", "Coeficiente": 0.18, "Deuda_Base": 220000.0 if consorcio_actual["mora"] == "2" else 0.0},
    {"UF": "UF 04", "Piso": "2° B", "Coeficiente": 0.12, "Deuda_Base": 0.0},
    {"UF": "UF 05", "Piso": "3° A", "Coeficiente": 0.10, "Deuda_Base": 0.0}
]

# Filtrado dinámico de OTs del edificio seleccionado para las tarjetas y contadores
ots_edificio_activo = [ot for ot in st.session_state.historico_ot if ot["Edificio"] == edificio_seleccionado]

# =========================================================================================
# VISTA GENERAL COMPLETA, CONTINUA Y MAESTRA (TODO SE MUESTRA AL MISMO TIEMPO EN LA WEB)
# =========================================================================================
st.title("🏢 Resilia_Condominios - Panel de Control Integral")
st.markdown(f"Consorcio de Propiedad Horizontal Activo: **{edificio_seleccionado}**")

# 1. PANELES DE MÉTRICAS SUPERIORES
m1, m2, m3, m4 = st.columns(4)
with m1: st.metric(label="Total gastos del periodo", value=f"${total_g_calc:,.2f}")
with m2: st.metric(label="Fondos de reserva", value=f"${consorcio_actual['reserva']:,.2f}")
with m3: st.metric(label="UF en Mora", value=consorcio_actual["mora"])
with m4: st.metric(label="Ordenes de trabajo", value=str(len(ots_edificio_activo)))

st.markdown("---")

# 2. CUADRO DE INGRESOS Y GASTOS MÁSTER
st.header("📊 Módulo Contable: Cuadro de Ingresos y Gastos")
