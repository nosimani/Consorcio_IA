import streamlit as st
import pandas as pd
import random
from datetime import datetime

# =====================================================================
# CONFIGURACIÓN HIGH-END DE LA INTERFAZ (CYBERPUNK CORPORATIVO)
# =====================================================================
st.set_page_config(
    page_title="Resilia_Condominios",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inyección de CSS de Vanguardia Estética (Fondo Metalizado Oscuro, Neón y Oro)
st.markdown("""
    <style>
        .main { background: radial-gradient(circle at top right, #0d1e3d 0%, #071126 100%); }
        h1 { color: #ffffff; font-family: sans-serif; font-weight: 900; letter-spacing: -1.5px; text-shadow: 0 0 20px rgba(56, 189, 248, 0.4); }
        h2, h3 { color: #38bdf8; font-family: sans-serif; font-weight: 700; }
        .stMarkdown p { color: #e2e8f0; }

        /* Paneles de Métricas en Oro Líquido Flotante */
        div[data-testid="stMetric"] {
            background: linear-gradient(135deg, #d4af37 0%, #aa7c11 100%) !important;
            border-radius: 20px !important;
            padding: 24px !important;
            box-shadow: 0 15px 35px -5px rgba(0, 0, 0, 0.5);
            border: 1px solid rgba(255, 255, 255, 0.15) !important;
            transition: all 0.3s ease;
        }
        div[data-testid="stMetric"]:hover { transform: translateY(-8px); }
        div[data-testid="stMetric"] label { color: #071126 !important; font-weight: 800 !important; text-transform: uppercase; letter-spacing: 1px; }
        div[data-testid="stMetric"] [data-testid="stMetricValue"] { color: #071126 !important; font-weight: 900 !important; font-size: 2.1rem !important; }

        /* Menú de Solapas Estilo Neón */
        .stTabs [data-baseweb="tab-list"] { gap: 15px; background-color: rgba(30, 41, 59, 0.7); padding: 10px; border-radius: 16px; backdrop-filter: blur(10px); }
        .stTabs [data-baseweb="tab"] { background-color: transparent; border: none !important; padding: 14px 28px; border-radius: 8px; font-weight: 800; color: #94a3b8; transition: all 0.3s; }
        .stTabs [aria-selected="true"] { background: linear-gradient(135deg, #0284c7 0%, #0369a1 100%) !important; color: #FFFFFF !important; box-shadow: 0 0 15px rgba(56, 189, 248, 0.4); }

        /* Solapas Celestes Secundarias */
        .celeste-tabs [data-baseweb="tab-list"] { background-color: #071126 !important; border: 1px solid #38bdf8 !important; }
        .celeste-tabs [data-baseweb="tab"] { color: #bae6fd !important; }
        .celeste-tabs [aria-selected="true"] { background: #38bdf8 !important; color: #071126 !important; font-weight: 900 !important; }

        /* Tarjetas de Agentes e Inputs */
        .agent-card { background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%); padding: 24px; border-radius: 16px; border-left: 6px solid #38bdf8; margin-bottom: 20px; color: #f1f5f9; }
        .agent-title { font-size: 1.1rem; font-weight: 900; color: #ffffff; text-transform: uppercase; }
        .stDataFrame, .stTable { background-color: rgba(30, 41, 59, 0.5); border-radius: 16px; padding: 10px; }
    </style>
""", unsafe_allow_html=True)

# =====================================================================
# CORE DE DATOS CONTABLES DEL SISTEMA POR EDIFICIO (INGRESOS Y GASTOS)
# =====================================================================
if 'data_consorcios' not in st.session_state:
    st.session_state.data_consorcios = {
        "Av. Corrientes 1234, CABA": {
            "reserva": 450000.0, "mora": "1", "ots": "2",
            "ingresos": [
                {"Concepto": "Cobro de Expensas Ordinarias/Extraordinarias", "Monto": 320000.0},
                {"Concepto": "Alquileres de Locales Comerciales PB", "Monto": 85000.0},
                {"Concepto": "Intereses por colocaciones a Plazo Fijo", "Monto": 14000.0}
            ],
            "gastos": [
                {"Concepto": "Gastos por Reparaciones e Infraestructura", "Monto": 45000.0},
                {"Concepto": "Honorarios de Administración", "Monto": 35000.0},
                {"Concepto": "Sueldo de Encargado + Cargas SUTERH", "Monto": 250000.0},
                {"Concepto": "Compra de artículos de limpieza", "Monto": 12000.0},
                {"Concepto": "Pagos de luz (Edesur/Edenor Central)", "Monto": 18000.0},
                {"Concepto": "Otros gastos generales y bancarios", "Monto": 7000.0}
            ]
        },
        "Larrea 435, CABA": {
            "reserva": 380000.0, "mora": "2", "ots": "1",
            "ingresos": [
                {"Concepto": "Cobro de Expensas Ordinarias/Extraordinarias", "Monto": 190000.0},
                {"Concepto": "Alquileres de Locales Comerciales PB", "Monto": 0.0},
                {"Concepto": "Intereses por colocaciones a Plazo Fijo", "Monto": 9500.0}
            ],
            "gastos": [
                {"Concepto": "Gastos por Reparaciones e Infraestructura", "Monto": 35000.0},
                {"Concepto": "Honorarios de Administración", "Monto": 28000.0},
                {"Concepto": "Sueldo de Encargado + Cargas SUTERH", "Monto": 0.0}, # Personal tercerizado
                {"Concepto": "Compra de artículos de limpieza", "Monto": 14000.0},
                {"Concepto": "Pagos de luz (Edesur/Edenor Central)", "Monto": 22000.0},
                {"Concepto": "Otros gastos generales y bancarios", "Monto": 5500.0}
            ]
        },
        "Montevideo 891, CABA": {
            "reserva": 620000.0, "mora": "2", "ots": "1",
            "ingresos": [
                {"Concepto": "Cobro de Expensas Ordinarias/Extraordinarias", "Monto": 280000.0},
                {"Concepto": "Alquileres de Locales Comerciales PB", "Monto": 110000.0},
                {"Concepto": "Intereses por colocaciones a Plazo Fijo", "Monto": 21000.0}
            ],
            "gastos": [
                {"Concepto": "Gastos por Reparaciones e Infraestructura", "Monto": 22000.0},
                {"Concepto": "Honorarios de Administración", "Monto": 32000.0},
                {"Concepto": "Sueldo de Encargado + Cargas SUTERH", "Monto": 230000.0},
                {"Concepto": "Compra de artículos de limpieza", "Monto": 9000.0},
                {"Concepto": "Pagos de luz (Edesur/Edenor Central)", "Monto": 16000.0},
                {"Concepto": "Otros gastos generales y bancarios", "Monto": 8000.0}
            ]
        },
        "San Jose 1111, CABA": {
            "reserva": 290000.0, "mora": "1", "ots": "1",
            "ingresos": [
                {"Concepto": "Cobro de Expensas Ordinarias/Extraordinarias", "Monto": 145000.0},
                {"Concepto": "Alquileres de Locales Comerciales PB", "Monto": 45000.0},
                {"Concepto": "Intereses por colocaciones a Plazo Fijo", "Monto": 5000.0}
            ],
            "gastos": [
                {"Concepto": "Gastos por Reparaciones e Infraestructura", "Monto": 41000.0},
                {"Concepto": "Honorarios de Administración", "Monto": 25000.0},
                {"Concepto": "Sueldo de Encargado + Cargas SUTERH", "Monto": 180000.0},
                {"Concepto": "Compra de artículos de limpieza", "Monto": 6500.0},
                {"Concepto": "Pagos de luz (Edesur/Edenor Central)", "Monto": 11500.0},
                {"Concepto": "Otros gastos generales y bancarios", "Monto": 4000.0}
            ]
        },
        "Guayaquil 399, CABA": {
            "reserva": 850000.0, "mora": "1", "ots": "1",
            "ingresos": [
                {"Concepto": "Cobro de Expensas Ordinarias/Extraordinarias", "Monto": 540000.0},
                {"Concepto": "Alquileres de Locales Comerciales PB", "Monto": 160000.0},
                {"Concepto": "Intereses por colocaciones a Plazo Fijo", "Monto": 35000.0}
            ],
            "gastos": [
                {"Concepto": "Gastos por Reparaciones e Infraestructura", "Monto": 65000.0},
                {"Concepto": "Honorarios de Administración", "Monto": 48000.0},
                {"Concepto": "Sueldo de Encargado + Cargas SUTERH", "Monto": 450000.0},
                {"Concepto": "Compra de artículos de limpieza", "Monto": 24000.0},
                {"Concepto": "Pagos de luz (Edesur/Edenor Central)", "Monto": 38000.0},
                {"Concepto": "Otros gastos generales y bancarios", "Monto": 12000.0}
            ]
        }
    }

if 'ordenes_globales' not in st.session_state:
    st.session_state.ordenes_globales = [
        {"Edificio": "Av. Corrientes 1234, CABA", "UF": "1A", "Tipo de Trabajo": "Plomería", "Detalle": "Filtración en caño central de agua", "Estado": "Trabajos Solicitados"},
        {"Edificio": "Av. Corrientes 1234, CABA", "UF": "3J", "Tipo de Trabajo": "Cerrajería", "Detalle": "Cambio de combinación cerradura", "Estado": "Trabajos en Proceso"},
        {"Edificio": "Larrea 435, CABA", "UF": "3J", "Tipo de Trabajo": "Electricidad", "Detalle": "Falla de fase en disyuntor", "Estado": "Trabajos Solicitados"},
        {"Edificio": "Larrea 435, CABA", "UF": "6P", "Tipo de Trabajo": "Gas", "Detalle": "Revisión técnica de estufa reglamentaria", "Estado": "Trabajos Pendientes"},
        {"Edificio": "Montevideo 891, CABA", "UF": "4K", "Tipo de Trabajo": "Plomería", "Detalle": "Pintura de cochera común", "Estado": "Trabajos en Proceso"}
    ]

CARTILLA_PROVEEDORES = {
    "Cerrajería": ["Seleccione un prestador...", "🔑 Llave - Tel: 111111111 (CUIT: 2222222222)", "🔑 Cerradura - Tel: 222222222", "🔑 Manojo - Tel: 333333333", "🔑 Traba - Tel: 444444444", "🔑 Pasador - Tel: 555555555"],
    "Electricidad": ["Seleccione un prestador...", "⚡ El Fusible - Tel: 666666666 (CUIT: 2222222222)", "⚡ Cablecito - Tel: 777777777", "⚡ Patada - Tel: 333333333", "⚡ Cortocircuito - Tel: 444444444", "⚡ Disyuntor - Tel: 555555555"],
