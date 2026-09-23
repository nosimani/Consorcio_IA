import streamlit as st
import pandas as pd
import random
from datetime import datetime

# =====================================================================
# CONFIGURACIÓN HIGH-END DE LA INTERFAZ (UI/UX FUTURISTA AZUL METALIZADO Y ORO)
# =====================================================================
st.set_page_config(
    page_title="Resilia Condominios - Enterprise Swarm OS",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilización avanzada mediante inyección de CSS de Alta Gama (Cyberpunk-Executive Style)
st.markdown("""
    <style>
        /* Desactivar márgenes nativos para un layout inmersivo */
        .block-container { padding-top: 2rem !important; padding-bottom: 2rem !important; }
        
        /* Fondo General de la Plataforma: Azul Metalizado Premium Oscuro */
        .main { 
            background: radial-gradient(circle at 50% 10%, #112240 0%, #060d1a 100%) !important;
        }
        
        /* Tipografías e Impacto de Títulos con Gradientes Luminosos */
        h1 {
            background: linear-gradient(90deg, #FFFFFF 0%, #38bdf8 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-family: 'Inter', -apple-system, sans-serif;
            font-weight: 900 !important;
            letter-spacing: -1.5px !important;
            padding-bottom: 10px;
        }
        h2, h3 { 
            color: #38bdf8 !important; 
            font-family: 'Inter', sans-serif; 
            font-weight: 800 !important;
            letter-spacing: -0.5px;
        }
        .stMarkdown p { color: #94a3b8 !important; font-size: 1.05rem; }

        /* Paneles de Métricas Holográficos en Oro Real y Brillo Neón */
        div[data-testid="stMetric"] {
            background: linear-gradient(135deg, rgba(212, 175, 55, 0.15) 0%, rgba(170, 124, 17, 0.05) 100%) !important;
            backdrop-filter: blur(12px) !important;
            -webkit-backdrop-filter: blur(12px) !important;
            padding: 24px !important;
            border-radius: 20px !important;
            box-shadow: 0 8px 32px 0 rgba(214, 175, 55, 0.08), inset 0 0 0 1px rgba(214, 175, 55, 0.2) !important;
            border: none !important;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
        }
        div[data-testid="stMetric"]:hover { 
            transform: translateY(-6px) scale(1.02);
            box-shadow: 0 12px 40px 0 rgba(214, 175, 55, 0.18), inset 0 0 0 1.5px rgba(214, 175, 55, 0.4) !important;
        }
        div[data-testid="stMetric"] label { 
            color: #fef08a !important; 
            font-weight: 700 !important; 
            text-transform: uppercase; 
            letter-spacing: 1px;
            font-size: 0.85rem !important;
        }
        div[data-testid="stMetric"] [data-testid="stMetricValue"] { 
            color: #FFFFFF !important; 
            font-weight: 900 !important; 
            font-size: 2.2rem !important;
            text-shadow: 0 2px 10px rgba(255, 255, 255, 0.2);
        }

        /* Estilización Estética para Solapas Principales en Acero Pulido */
        .stTabs [data-baseweb="tab-list"] { 
            gap: 10px; 
            background-color: rgba(30, 41, 59, 0.7); 
            padding: 8px; 
            border-radius: 16px; 
            border: 1px solid rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(8px);
        }
        .stTabs [data-baseweb="tab"] { 
            background-color: transparent; 
            border: none !important; 
            padding: 14px 28px; 
            border-radius: 12px; 
            font-weight: 700; 
            color: #64748b; 
            transition: all 0.25s ease;
        }
        .stTabs [aria-selected="true"] { 
            background: linear-gradient(135deg, #0284c7 0%, #0369a1 100%) !important; 
            color: #FFFFFF !important; 
            box-shadow: 0 4px 20px rgba(2, 132, 199, 0.4);
        }

        /* Solapas Celestes Secundarias para Órdenes de Trabajo */
        .celeste-tabs [data-baseweb="tab-list"] { 
            background-color: rgba(15, 23, 42, 0.8) !important; 
            border: 1px solid rgba(56, 189, 248, 0.3) !important; 
        }
        .celeste-tabs [data-baseweb="tab"] { color: #7dd3fc !important; }
        .celeste-tabs [aria-selected="true"] { 
            background: linear-gradient(135deg, #38bdf8 0%, #0ea5e9 100%) !important; 
            color: #0f172a !important; 
            font-weight: 800 !important; 
            box-shadow: 0 4px 15px rgba(56, 189, 248, 0.3);
        }

        /* Tarjetas de Contenedores de Agentes Inteligentes */
        .agent-card { 
            background: linear-gradient(135deg, rgba(30, 41, 59, 0.7) 0%, rgba(15, 23, 42, 0.7) 100%);
            padding: 24px; 
            border-radius: 18px; 
            border-left: 6px solid #38bdf8; 
            margin-bottom: 20px; 
            color: #e2e8f0;
            box-shadow: 0 4px 20px rgba(0,0,0,0.2);
            border-top: 1px solid rgba(255,255,255,0.03);
        }
        .agent-title { font-size: 1.15rem; font-weight: 800; color: #ffffff; margin-bottom: 6px; letter-spacing: 0.3px; }
        
        /* Contenedores de Tablas Interactivas Estilizadas */
        .stDataFrame, .stTable { 
            background-color: rgba(30, 41, 59, 0.4); 
            border-radius: 16px; 
            padding: 8px; 
            border: 1px solid rgba(255,255,255,0.03);
        }
        
        /* Diseño Personalizado de Controles de Formularios */
        .stButton>button {
            background: linear-gradient(135deg, #38bdf8 0%, #0284c7 100%) !important;
            color: #0f172a !important;
            font-weight: 800 !important;
            border-radius: 14px !important;
            border: none !important;
            box-shadow: 0 4px 15px rgba(2, 132, 199, 0.25) !important;
            transition: all 0.25s ease !important;
        }
        .stButton>button:hover {
            transform: translateY(-2px) !important;
            box-shadow: 0 6px 25px rgba(56, 189, 248, 0.45) !important;
        }
    </style>
""", unsafe_allow_html=True)

# =====================================================================
# BASE DE DATOS GLOBAL DE EDIFICIOS Y RUBROS DE EXCEL
# =====================================================================
if 'data_consorcios' not in st.session_state:
    st.session_state.data_consorcios = {
        "Av. Corrientes 1234, CABA": {
            "reserva": 450000.0,
            "libro_diario": [{"Fecha": "2026-09-01", "Concepto": "Abono Ascensores S.A.", "Monto": 45000.0, "Tipo": "Ordinario"}],
            "unidades": ["1A", "3J", "4K", "5M", "6P"],
            "saldos": {"1A": 1500.0, "3J": 0.0, "4K": -500.0, "5M": 12000.0, "6P": 0.0}
        },
        "Larrea 435, CABA": {
            "reserva": 380000.0,
            "libro_diario": [{"Fecha": "2026-09-02", "Concepto": "Abono Empresa de Limpieza", "Monto": 80000.0, "Tipo": "Ordinario"}],
            "unidades": ["1A", "3J", "4K", "5M", "6P"],
            "saldos": {"1A": 0.0, "3J": 8500.0, "4K": 0.0, "5M": -1200.0, "6P": 4300.0}
        },
        "Montevideo 891, CABA": {
            "reserva": 620000.0,
            "libro_diario": [{"Fecha": "2026-09-04", "Concepto": "Mantenimiento de Portón Eléctrico", "Monto": 22000.0, "Tipo": "Ordinario"}],
            "unidades": ["1A", "3J", "4K", "5M", "6P"],
            "saldos": {"1A": -300.0, "3J": 0.0, "4K": 15000.0, "5M": 0.0, "6P": 9100.0}
        },
        "San Jose 1111, CABA": {
            "reserva": 290000.0,
            "libro_diario": [{"Fecha": "2026-09-03", "Concepto": "Service Técnico Bombas de Agua", "Monto": 41000.0, "Tipo": "Ordinario"}],
            "unidades": ["1A", "3J", "4K", "5M", "6P"],
            "saldos": {"1A": 0.0, "3J": 0.0, "4K": -2500.0, "5M": 34000.0, "6P": 0.0}
        },
        "Guayaquil 399, CABA": {
            "reserva": 850000.0,
            "libro_diario": [{"Fecha": "2026-09-01", "Concepto": "Abono Servicio Grupo Electrógeno", "Monto": 65000.0, "Tipo": "Ordinario"}],
            "unidades": ["1A", "3J", "4K", "5M", "6P"],
            "saldos": {"1A": -50000.0, "3J": 0.0, "4K": 12000.0, "5M": 0.0, "6P": 0.0}
        }
    }

if 'ordenes_globales' not in st.session_state:
    st.session_state.ordenes_globales = [
        {"Edificio": "Av. Corrientes 1234, CABA", "UF": "1A", "Tipo de Trabajo": "Plomería", "Detalle": "Filtración en caño central de agua", "Estado": "Trabajos Solicitados"},
        {"Edificio": "Av. Corrientes 1234, CABA", "UF": "3J", "Tipo de Trabajo": "Cerrajería", "Detalle": "Cambio de combinación cerradura de entrada", "Estado": "Trabajos en Proceso"},
        {"Edificio": "Larrea 435, CABA", "UF": "3J", "Tipo de Trabajo": "Electricidad", "Detalle": "Falla de fase en disyuntor", "Estado": "Trabajos Solicitados"},
        {"Edificio": "Larrea 435, CABA", "UF": "6P", "Tipo de Trabajo": "Gas", "Detalle": "Revisión técnica de estufa reglamentaria", "Estado": "Trabajos Pendientes"},
        {"Edificio": "Montevideo 891, CABA", "UF": "4K", "Tipo de Trabajo": "Plomería", "Detalle": "Pintura de cochera común", "Estado": "Trabajos en Proceso"}
    ]

CARTILLA_PROVEEDORES = {
    "Cerrajería": [
        "Seleccione un prestador...",
        "🔑 Llave - Tel: 111111111 (CUIT: 2222222222) - Domicilio: xxx",
        "🔑 Cerradura - Tel: 222222222 (CUIT: 2222222222) - Domicilio: xxx",
        "🔑 Manojo - Tel: 333333333 (CUIT: 2222222222) - Domicilio: xxx",
        "🔑 Traba - Tel: 444444444 (CUIT: 2222222222) - Domicilio: xxx",
        "🔑 Pasador - Tel: 555555555 (CUIT: 2222222222) - Domicilio: xxx"
    ],
    "Electricidad": [
        "Seleccione un prestador...",
        "⚡ El Fusible - Tel: 666666666 (CUIT: 2222222222) - Domicilio: x",
        "⚡ Cablecito - Tel: 777777777 (CUIT: 2222222222) - Domicilio: x",
        "⚡ Patada - Tel: 333333333 (CUIT: 2222222222) - Domicilio: x",
