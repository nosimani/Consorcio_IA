import streamlit as st
import pandas as pd
import random
from datetime import datetime

# =====================================================================
# CONFIGURACIÓN HIGH-END DE LA INTERFAZ (LETRAS ULTRA AGRANDADAS)
# =====================================================================
st.set_page_config(
    page_title="Resilia_Condominios",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inyección de CSS de Vanguardia Estética con Modificadores de Tamaño de Letra Críticos
st.markdown("""
    <style>
        .main { background: radial-gradient(circle at top right, #0d1e3d 0%, #071126 100%); }
        h1 { color: #ffffff; font-family: sans-serif; font-weight: 900; letter-spacing: -1px; text-shadow: 0 0 20px rgba(56, 189, 248, 0.4); font-size: 2.8rem !important; }
        h2 { color: #38bdf8; font-family: sans-serif; font-weight: 700; font-size: 2.2rem !important; }
        h3 { color: #38bdf8; font-family: sans-serif; font-weight: 700; font-size: 1.9rem !important; }
        
        /* Agrandamos el texto general de la aplicación */
        .stMarkdown p, p, label, .stRadio label { 
            color: #e2e8f0; 
            font-size: 1.3rem !important; 
            line-height: 1.6 !important;
        }

        /* FORCE TOTAL: Agrandamos la letra de las descripciones internas de las tablas a tamaño GIGANTE */
        .stDataFrame td, .stDataFrame div, table, td, tr { 
            font-size: 1.5rem !important; 
            font-weight: 600 !important;
            color: #ffffff !important;
        }
        
        /* Modificador para los encabezados de columnas de las tablas */
        th, .stDataFrame th div {
            font-weight: 800 !important;
            color: #38bdf8 !important;
            font-size: 1.4rem !important;
        }

        /* Paneles de Métricas en Oro Líquido Flotante */
        div[data-testid="stMetric"] {
            background: linear-gradient(135deg, #d4af37 0%, #aa7c11 100%) !important;
            border-radius: 20px !important;
            padding: 22px !important;
            box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.6);
            border: 1px solid rgba(255, 255, 255, 0.2) !important;
            transition: transform 0.2s;
        }
        div[data-testid="stMetric"]:hover { transform: translateY(-5px); }
        div[data-testid="stMetric"] label { color: #0f172a !important; font-weight: 800 !important; text-transform: uppercase; letter-spacing: 0.5px; font-size: 1.1rem !important; }
        div[data-testid="stMetric"] [data-testid="stMetricValue"] { color: #0b192c !important; font-weight: 900 !important; font-size: 2.4rem !important; }

        /* Menú de Solapas Estilo Neón */
        .stTabs [data-baseweb="tab-list"] { gap: 12px; background-color: #1e293b; padding: 8px; border-radius: 12px; }
        .stTabs [data-baseweb="tab"] { background-color: transparent; border: none !important; padding: 12px 24px; border-radius: 8px; font-weight: 800; color: #94a3b8; transition: all 0.3s; font-size: 1.3rem !important; }
        .stTabs [aria-selected="true"] { background: linear-gradient(135deg, #0284c7 0%, #0369a1 100%) !important; color: #FFFFFF !important; box-shadow: 0 0 15px rgba(56, 189, 248, 0.4); }

        /* Tarjetas de Agentes e Inputs */
        .agent-card { background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%); padding: 24px; border-radius: 16px; border-left: 6px solid #38bdf8; margin-bottom: 20px; color: #f1f5f9; }
        .agent-title { font-size: 1.3rem; font-weight: 900; color: #ffffff; text-transform: uppercase; }
        .stDataFrame, .stTable { background-color: rgba(30, 41, 59, 0.5); border-radius: 16px; padding: 10px; }
        
        .stAlert div { font-size: 1.3rem !important; }
    </style>
""", unsafe_allow_html=True)

# =====================================================================
# BASE DE DATOS GLOBAL DE CONDOMINIOS
# =====================================================================
ESTADISTICAS_EDIFICIOS = {
    "Av. Corrientes 1234, CABA": {"reserva": 450000.0, "factor": 1.0, "mora": "1", "ots": "2"},
    "Larrea 435, CABA": {"reserva": 380000.0, "factor": 0.6, "mora": "2", "ots": "1"},
    "Montevideo 891, CABA": {"reserva": 620000.0, "factor": 0.8, "mora": "2", "ots": "1"},
    "San Jose 1111, CABA": {"reserva": 290000.0, "factor": 0.5, "mora": "1", "ots": "1"},
    "Guayaquil 399, CABA": {"reserva": 850000.0, "factor": 1.5, "mora": "1", "ots": "1"}
}

# MATRIZ HISTÓRICA COMPLETA DE PRESTADORES DEL EXCEL RESTAURADA
DATOS_EXCEL_PROVEEDORES = [
    {"Rubro": "Cerrajería", "Proveedor": "Llave", "CUIT": "2222222222", "Teléfono": "111111111", "Domicilio": "xxx"},
    {"Rubro": "Cerrajería", "Proveedor": "Cerradura", "CUIT": "2222222222", "Teléfono": "222222222", "Domicilio": "xxx"},
    {"Rubro": "Cerrajería", "Proveedor": "Manojo", "CUIT": "2222222222", "Teléfono": "333333333", "Domicilio": "xxx"},
    {"Rubro": "Cerrajería", "Proveedor": "Traba", "CUIT": "2222222222", "Teléfono": "444444444", "Domicilio": "xxx"},
    {"Rubro": "Cerrajería", "Proveedor": "Pasador", "CUIT": "2222222222", "Teléfono": "555555555", "Domicilio": "xxx"},
    {"Rubro": "Electricidad", "Proveedor": "El Fusible", "CUIT": "2222222222", "Teléfono": "666666666", "Domicilio": "x"},
    {"Rubro": "Electricidad", "Proveedor": "Cablecito", "CUIT": "2222222222", "Teléfono": "777777777", "Domicilio": "x"},
    {"Rubro": "Electricidad", "Proveedor": "Patada", "CUIT": "2222222222", "Teléfono": "333333333", "Domicilio": "x"},
    {"Rubro": "Electricidad", "Proveedor": "Cortocircuito", "CUIT": "2222222222", "Teléfono": "444444444", "Domicilio": "x"},
    {"Rubro": "Electricidad", "Proveedor": "Disyuntor", "CUIT": "2222222222", "Teléfono": "555555555", "Domicilio": "x"},
    {"Rubro": "Gas", "Proveedor": "Pum", "CUIT": "2222222222", "Teléfono": "666666666", "Domicilio": "x"},
    {"Rubro": "Gas", "Proveedor": "Garrafa", "CUIT": "2222222222", "Teléfono": "777777777", "Domicilio": "x"},
    {"Rubro": "Gas", "Proveedor": "Hornalla", "CUIT": "2222222222", "Teléfono": "111111111", "Domicilio": "xxx"},
    {"Rubro": "Gas", "Proveedor": "Calefonete", "CUIT": "2222222222", "Teléfono": "222222222", "Domicilio": "xxx"},
    {"Rubro": "Gas", "Proveedor": "Estufeta", "CUIT": "2222222222", "Teléfono": "333333333", "Domicilio": "xxx"},
    {"Rubro": "Plomería", "Proveedor": "Caño", "CUIT": "2222222222", "Teléfono": "444444444", "Domicilio": "xxx"},
    {"Rubro": "Plomería", "Proveedor": "Cañito", "CUIT": "2222222222", "Teléfono": "555555555", "Domicilio": "xxx"},
    {"Rubro": "Plomería", "Proveedor": "Cañete", "CUIT": "2222222222", "Teléfono": "666666666", "Domicilio": "xxxx"},
    {"Rubro": "Plomería", "Proveedor": "Canilla", "CUIT": "2222222222", "Teléfono": "777777777", "Domicilio": "xxx"},
    {"Rubro": "Plomería", "Proveedor": "Rejilla", "CUIT": "2222222222", "Teléfono": "222222222", "Domicilio": "xxx"}
]

# MATRIZ HISTÓRICA INTEGRADA DE ÓRDENES DE TRABAJO SOLICITADA VÍA CAPTURA
TABLA_SOLICITADA_OT = [
    {"Edificio": "Avda. Corrientes 1234", "UF": "1A", "Trabajo": "Plomería", "Presupuesto Aprobado": "$ 250.000.-", "Fecha_Inicio": "01/05/26", "Fecha_Finaliz": "01/05/26"},
    {"Edificio": "Larrea 435", "UF": "3J", "Trabajo": "Albañilería", "Presupuesto Aprobado": "$ 390.000.-", "Fecha_Inicio": "07/06/26", "Fecha_Finaliz": "12/06/26"},
    {"Edificio": "Montevideo 891", "UF": "4K", "Trabajo": "Plomería", "Presupuesto Aprobado": "$ 120.000.-", "Fecha_Inicio": "08/09/26", "Fecha_Finaliz": "09/09/26"},
    {"Edificio": "San José 1111", "UF": "5M", "Trabajo": "Electricidad", "Presupuesto Aprobado": "$ 95.000.-", "Fecha_Inicio": "12/07/26", "Fecha_Finaliz": "12/07/26"},
    {"Edificio": "Guayaquil 399", "UF": "6P", "Trabajo": "Cerrajería", "Presupuesto Aprobado": "$ 180.000.-", "Fecha_Inicio": "15/08/26", "Fecha_Finaliz": "15/08/26"}
]

if 'ordenes_globales' not in st.session_state:
    st.session_state.ordenes_globales = [
        {"Edificio": "Av. Corrientes 1234, CABA", "UF": "1A", "Tipo de Trabajo": "Plomería", "Detalle": "Filtración en caño central de agua", "Estado": "Trabajos Solicitados"},
        {"Edificio": "Larrea 435, CABA", "UF": "3J", "Tipo de Trabajo": "Electricidad", "Detalle": "Falla de fase en disyuntor", "Estado": "Trabajos Solicitados"}
    ]

# =====================================================================
# PANEL LATERAL (SIDEBAR DE CONTROL CON TU LOGO OFICIAL FÉNIX)
# =====================================================================
with st.sidebar:
    st.image("https://imgbox.com", use_container_width=True)
    st.title("Resilia_Condominios")
    st.caption("AI Swarm ERP Platform v2.6")
    st.markdown("---")
    pantalla_activa = st.radio("Seleccione Vista:", ["Panel General por Edificio", "Abrir Ordenes de Trabajo"], index=0)
    st.markdown("---")
    edificio_seleccionado = st.selectbox("Edificio Activo de Control", list(ESTADISTICAS_EDIFICIOS.keys()))
    st.markdown("---")
    csv_data = pd.DataFrame(st.session_state.ordenes_globales).to_csv(index=False).encode('utf-8')
    st.download_button(label="Descargar Historial OT (CSV)", data=csv_data, file_name=f"Reporte_Resilia.csv", mime="text/csv", use_container_width=True)
    st.markdown("---")
    st.info("CUIT: 30-11111111-9\n\nJurisdicción: Ley 941 CABA")

consorcio_actual = ESTADISTICAS_EDIFICIOS[edificio_seleccionado]
f_cal = consorcio_actual["factor"]

# Listados financieros generados de forma robusta y cerrados perfectamente
ingresos_lista = [
    {"Ingresos": "ingresos por expensas", "Monto ($)": 320000.0 * f_cal},
    {"Ingresos": "alquileres de locales", "Monto ($)": 85000.0 * (1.0 if f_cal >= 0.8 else 0.0)},
    {"Ingresos": "intereses por colocacion a plazo fijo", "Monto ($)": 14000.0 * f_cal}
]
gastos_lista = [
    {"Gastos": "reparaciones", "Monto ($)": 45000.0 * f_cal},
    {"Gastos": "honorarios de administración", "Monto ($)": 35000.0 * f_cal},
