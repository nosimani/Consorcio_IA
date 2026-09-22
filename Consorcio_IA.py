import streamlit as st
import pandas as pd
import random
from datetime import datetime

# =====================================================================
# CONFIGURACIÓN PREMIUM DE LA INTERFAZ (LOOK & FEEL AZUL METALIZADO Y DORADO)
# =====================================================================
st.set_page_config(
    page_title="Resilia_Condominios",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inyección de CSS Avanzado para forzar el fondo azul metalizado oscuro, paneles dorados y sub-solapas celestes
st.markdown("""
    <style>
        /* Fondo general de la plataforma: Azul Metalizado Oscuro Profundo */
        .main { background-color: #0b192c; }
        
        /* Títulos e identificadores sobre el fondo oscuro */
        h1 { color: #FFFFFF; font-family: sans-serif; font-weight: 900; letter-spacing: -1px; }
        h2, h3 { color: #38bdf8; font-family: sans-serif; font-weight: 700; }
        .stMarkdown p { color: #e2e8f0; }

        /* Paneles de Métricas Ejecutivas en Dorado Premium */
        div[data-testid="stMetric"] {
            background: linear-gradient(135deg, #d4af37 0%, #aa7c11 100%) !important;
            color: #0b192c !important;
            padding: 22px !important;
            border-radius: 16px !important;
            box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.6);
            border: 1px solid rgba(255, 255, 255, 0.2);
            transition: transform 0.2s;
        }
        div[data-testid="stMetric"]:hover { transform: translateY(-5px); }
        div[data-testid="stMetric"] label { color: #0f172a !important; font-weight: 800 !important; text-transform: uppercase; letter-spacing: 0.5px; }
        div[data-testid="stMetric"] [data-testid="stMetricValue"] { color: #0b192c !important; font-weight: 900 !important; font-size: 1.9rem !important; }

        /* Solapas Principales */
        .stTabs [data-baseweb="tab-list"] { gap: 12px; background-color: #1e293b; padding: 8px; border-radius: 12px; border: 1px solid rgba(255, 255, 255, 0.1); }
        .stTabs [data-baseweb="tab"] { background-color: transparent; border: none !important; padding: 12px 24px; border-radius: 8px; font-weight: 700; color: #94a3b8; transition: all 0.3s; }
        .stTabs [aria-selected="true"] { background-color: #0284c7 !important; color: #FFFFFF !important; }

        /* Solapas Celestes Secundarias para Órdenes de Trabajo */
        .celeste-tabs [data-baseweb="tab-list"] { background-color: #0f172a !important; border: 1px solid #38bdf8 !important; }
        .celeste-tabs [data-baseweb="tab"] { color: #bae6fd !important; }
        .celeste-tabs [aria-selected="true"] { background-color: #38bdf8 !important; color: #0f172a !important; font-weight: 800 !important; }

        /* Tarjetas de los Agentes */
        .agent-card { background-color: #1e293b; padding: 24px; border-radius: 16px; border-left: 6px solid #38bdf8; margin-bottom: 18px; color: #f1f5f9; }
        .agent-title { font-size: 1.1rem; font-weight: 800; color: #ffffff; margin-bottom: 8px; }
        
        /* Ajuste estético para tablas y dataframes sobre el fondo oscuro */
        .stDataFrame, .stTable { background-color: #1e293b; border-radius: 12px; padding: 5px; }
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

# Repositorio Dinámico de Órdenes de Trabajo Persistente
if 'ordenes_globales' not in st.session_state:
    st.session_state.ordenes_globales = [
        {"Edificio": "Av. Corrientes 1234, CABA", "UF": "1A", "Tipo de Trabajo": "Plomería", "Detalle": "Filtración en caño central de agua", "Estado": "Trabajos Solicitados"},
        {"Edificio": "Av. Corrientes 1234, CABA", "UF": "3J", "Tipo de Trabajo": "Cerrajería", "Detalle": "Cambio de combinación cerradura de entrada", "Estado": "Trabajos en Proceso"},
        {"Edificio": "Larrea 435, CABA", "UF": "3J", "Tipo de Trabajo": "Electricidad", "Detalle": "Falla de fase en disyuntor", "Estado": "Trabajos Solicitados"},
        {"Edificio": "Larrea 435, CABA", "UF": "6P", "Tipo de Trabajo": "Gas", "Detalle": "Revisión técnica de estufa reglamentaria", "Estado": "Trabajos Pendientes"}
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
# PANEL LATERAL (SIDEBAR DE CONTROL AUTOMATIZADO CON EXPORTADOR INHERENTE)
# =====================================================================
with st.sidebar:
    st.image("https://imgbox.com", use_container_width=True)
    st.title("Resilia_Condominios")
    st.caption("AI Swarm ERP Administration")
    st.markdown("---")
    
    st.markdown("🎮 **Navegación del Sistema:**")
    pantalla_activa = st.radio("Seleccione Vista:", ["🏠 Panel General por Edificio", "🛠️ Abrir Órdenes de Trabajo"], index=0)
    
    st.markdown("---")
    edificio_seleccionado = st.selectbox("Edificio Activo de Control", list(st.session_state.data_consorcios.keys()))
    
    st.markdown("---")
    # REFACTORIZACIÓN COMPATIBLE: EXPORTADOR CSV COMPATIBLE CON EXCEL DIRECTO (SIN LIBRERÍAS EXTERNAS)
    st.markdown("📥 **Reportería y Auditoría:**")
    df_download = pd.DataFrame(st.session_state.ordenes_globales)
    csv_data = df_download.to_csv(index=False).encode('utf-8')
    
    st.download_button(
        label="📊 Descargar Historial OT (Excel)",
        data=csv_data,
        file_name=f"Resilia_Reporte_OT_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv",
        use_container_width=True
    )
    st.markdown("---")
    st.info("CUIT: 30-11111111-9\n\nJurisdicción: Ley 941 CABA")

consorcio_actual = st.session_state.data_consorcios[edificio_seleccionado]
unidades_actuales = consorcio_actual["unidades"]
libro_diario_actual = consorcio_actual["libro_diario"]

# =====================================================================
# PANTALLA 1: DASHBOARD GENERAL DEL EDIFICIO ACTIVO
# =====================================================================
if pantalla_activa == "🏠 Panel General por Edificio":
    st.title("🏢 Resilia_Condominios")
    st.markdown(f"Monitoreo activo sobre el consorcio: **{edificio_seleccionado}**")

    # CUATRO INDICADORES DORADOS PREMIUM

