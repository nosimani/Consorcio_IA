import streamlit as st
import pandas as pd
import random
from datetime import datetime

# =====================================================================
# CONFIGURACIÓN HIGH-END DE LA INTERFAZ (CYBERPUNK CORPORATIVO)
# =====================================================================
st.set_page_config(
    page_title="Resilia_Condominios - Swarm OS",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inyección de CSS de Vanguardia Estética (Fondo Azul Metalizado Profundo, Neón y Oro)
st.markdown("""
    <style>
        /* Fondo general de la plataforma - Azul Eléctrico de Medianoche */
        .main { 
            background: radial-gradient(circle at top right, #0d1e3d 0%, #071126 100%);
        }
        
        /* Tipografías institucionales estilizadas */
        h1 { 
            color: #ffffff; 
            font-family: 'Inter', system-ui, sans-serif; 
            font-weight: 900; 
            letter-spacing: -1.5px;
            text-shadow: 0 0 20px rgba(56, 189, 248, 0.4);
        }
        h2, h3 { 
            color: #38bdf8; 
            font-family: 'Inter', sans-serif; 
            font-weight: 800;
            letter-spacing: -0.5px;
        }
        .stMarkdown p { color: #e2e8f0; font-family: 'Inter', sans-serif; }

        /* Paneles de Métricas en Oro Líquido Flotante */
        div[data-testid="stMetric"] {
            background: linear-gradient(135deg, #f59e0b 0%, #b45309 100%) !important;
            border-radius: 20px !important;
            padding: 24px !important;
            box-shadow: 0 15px 35px -5px rgba(180, 83, 9, 0.3), inset 0 1px 1px rgba(255, 255, 255, 0.2);
            border: 1px solid rgba(255, 255, 255, 0.15) !important;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        }
        div[data-testid="stMetric"]:hover {
            transform: translateY(-8px) scale(1.02);
            box-shadow: 0 20px 40px -5px rgba(180, 83, 9, 0.5), inset 0 1px 1px rgba(255, 255, 255, 0.4);
        }
        div[data-testid="stMetric"] label { 
            color: #071126 !important; 
            font-weight: 900 !important; 
            text-transform: uppercase;
            letter-spacing: 1px;
            font-size: 0.85rem !important;
        }
        div[data-testid="stMetric"] [data-testid="stMetricValue"] { 
            color: #071126 !important; 
            font-weight: 950 !important; 
            font-size: 2.2rem !important;
            text-shadow: 0 2px 4px rgba(255, 255, 255, 0.2);
        }

        /* Menú de Solapas Estilo Neón */
        .stTabs [data-baseweb="tab-list"] { 
            gap: 15px; 
            background-color: rgba(30, 41, 59, 0.7); 
            padding: 10px; 
            border-radius: 16px; 
            border: 1px solid rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(10px);
        }
        .stTabs [data-baseweb="tab"] { 
            background-color: transparent; 
            border: none !important; 
            padding: 14px 28px; 
            border-radius: 10px; 
            font-weight: 800; 
            color: #94a3b8; 
            transition: all 0.3s ease;
        }
        .stTabs [data-baseweb="tab"]:hover {
            color: #38bdf8;
            background-color: rgba(255, 255, 255, 0.02);
        }
        .stTabs [aria-selected="true"] { 
            background: linear-gradient(135deg, #0284c7 0%, #0369a1 100%) !important;
            color: #FFFFFF !important; 
            box-shadow: 0 0 15px rgba(56, 189, 248, 0.4);
        }

        /* Solapas Celestes Secundarias (Glow Efímero) */
        .celeste-tabs [data-baseweb="tab-list"] { 
            background-color: #071126 !important; 
            border: 1px solid #38bdf8 !important; 
            box-shadow: 0 0 10px rgba(56, 189, 248, 0.2);
        }
        .celeste-tabs [data-baseweb="tab"] { color: #bae6fd !important; }
        .celeste-tabs [aria-selected="true"] { 
            background: #38bdf8 !important; 
            color: #071126 !important; 
            font-weight: 900 !important; 
        }

        /* Contenedores de Agentes Inteligentes con Respuestas */
        .agent-card { 
            background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%); 
            padding: 26px; 
            border-radius: 20px; 
            border-left: 6px solid #38bdf8; 
            margin-bottom: 20px; 
            color: #f1f5f9;
            box-shadow: 0 10px 20px rgba(0,0,0,0.2), 0 0 1px rgba(255,255,255,0.1);
        }
        .agent-title { font-size: 1.15rem; font-weight: 900; color: #ffffff; text-transform: uppercase; letter-spacing: 0.5px; }
        
        /* Controles, Inputs y Tablas Integrados Estéticamente */
        .stDataFrame, .stTable { 
            background-color: rgba(30, 41, 59, 0.5); 
            border-radius: 16px; 
            padding: 10px;
            border: 1px solid rgba(255, 255, 255, 0.05);
        }
    </style>
""", unsafe_allow_html=True)

# =====================================================================
# DATA ENGINE - CONTROL DINÁMICO REPOSITORIO
# =====================================================================
if 'data_consorcios' not in st.session_state:
    st.session_state.data_consorcios = {
        "Av. Corrientes 1234, CABA": {"reserva": 450000.0, "gastos": 295000.0, "mora": "1", "ots": "2"},
        "Larrea 435, CABA": {"reserva": 380000.0, "gastos": 115000.0, "mora": "2", "ots": "1"},
        "Montevideo 891, CABA": {"reserva": 620000.0, "gastos": 117000.0, "mora": "2", "ots": "1"},
        "San Jose 1111, CABA": {"reserva": 290000.0, "gastos": 59000.0, "mora": "1", "ots": "1"},
        "Guayaquil 399, CABA": {"reserva": 850000.0, "gastos": 515000.0, "mora": "1", "ots": "1"}
    }

if 'ordenes_globales' not in st.session_state:
    st.session_state.ordenes_globales = [
        {"Edificio": "Av. Corrientes 1234, CABA", "UF": "1A", "Tipo de Trabajo": "Plomería", "Detalle": "Filtración en caño central de agua", "Estado": "Trabajos Solicitados"},
        {"Edificio": "Av. Corrientes 1234, CABA", "UF": "3J", "Tipo de Trabajo": "Cerrajería", "Detalle": "Cambio de combinación cerradura", "Estado": "Trabajos en Proceso"},
        {"Edificio": "Larrea 435, CABA", "UF": "3J", "Tipo de Trabajo": "Electricidad", "Detalle": "Falla de fase en disyuntor", "Estado": "Trabajos Solicitados"},
        {"Edificio": "Larrea 435, CABA", "UF": "6P", "Tipo de Trabajo": "Gas", "Detalle": "Revisión técnica de estufa reglamentaria", "Estado": "Trabajos Pendientes"},
        {"Edificio": "Montevideo 891, CABA", "UF": "4K", "Tipo de Trabajo": "Plomería", "Detalle": "Pintura de cochera común", "Estado": "Trabajos en Proceso"}
    ]

# Cartilla unificada basada en los datos de tu Excel
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
        "⚡ Cortocircuito - Tel: 444444444 (CUIT: 2222222222) - Domicilio: x",
        "⚡ Disyuntor - Tel: 555555555 (CUIT: 2222222222) - Domicilio: x"
    ],
    "Gas": [
        "Seleccione un prestador...",
        "🔥 Pum - Tel: 666666666 (CUIT: 2222222222) - Domicilio: x",
        "🔥 Garrafa - Tel: 777777777 (CUIT: 2222222222) - Domicilio: x",
        "🔥 Hornalla - Tel: 111111111 (CUIT: 2222222222) - Domicilio: xxx",
        "🔥 Calefonete - Tel: 222222222 (CUIT: 2222222222) - Domicilio: xxx",
        "🔥 Estufeta - Tel: 333333333 (CUIT: 2222222222) - Domicilio: xxx"
    ],
    "Plomería": [
        "Seleccione un prestador...",
        "🚰 Caño - Tel: 444444444 (CUIT: 2222222222) - Domicilio: xxx",
        "🚰 Cañito - Tel: 555555555 (CUIT: 2222222222) - Domicilio: xxx",
        "🚰 Cañete - Tel: 666666666 (CUIT: 2222222222) - Domicilio: xxxx",
        "🚰 Canilla - Tel: 777777777 (CUIT: 2222222222) - Domicilio: xxx",
        "🚰 Rejilla - Tel: 222222222 (CUIT: 2222222222) - Domicilio: xxx"
    ]
}

# =====================================================================
# INTERFAZ LATERAL (SIDEBAR CORPORATIVO)
# =====================================================================
with st.sidebar:
    st.image("https://imgbox.com", use_container_width=True)
    st.title("Resilia_Condominios")
    st.caption("AI Swarm ERP Platform v2.4")
    st.markdown("---")
    
    st.markdown("🎮 **Navegación del Sistema:**")
    pantalla_activa = st.radio("Seleccione Vista:", ["🏠 Panel General por Edificio", "🛠️ Abrir Órdenes de Trabajo"], index=0)
    
    st.markdown("---")
    edificio_seleccionado = st.selectbox("Edificio Activo de Control", list(st.session_state.data_consorcios.keys()))
    
    st.markdown("---")
    st.markdown("📥 **Reportería y Auditoría:**")
    df_download = pd.DataFrame(st.session_state.ordenes_globales)
    csv_data = df_download.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📊 Descargar Historial OT (CSV)",
        data=csv_data,
        file_name=f"Reporte_Resilia.csv",
        mime="text/csv",
        use_container_width=True
    )
    st.markdown("---")
    st.info("CUIT: 30-11111111-9\n\nJurisdicción: Ley 941 CABA")

consorcio_actual = st.session_state.data_consorcios[edificio_seleccionado]

# =====================================================================
# PANEL GENERAL POR EDIFICIO
# =====================================================================

