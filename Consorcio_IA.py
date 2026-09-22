import streamlit as st
import pandas as pd
import random
from datetime import datetime

# =====================================================================
# CONFIGURACIÓN PREMIUM DE LA INTERFAZ (LOOK & FEEL AZUL METALIZADO OSCURO Y DORADO)
# =====================================================================
st.set_page_config(
    page_title="Resilia_Condominios",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inyección de CSS para forzar el fondo azul metalizado oscuro, paneles dorados y sub-solapas celestes
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
        div[data-testid="stMetric"]:hover {
            transform: translateY(-5px);
        }
        
        /* Modificadores de color interno para el texto dentro del panel dorado */
        div[data-testid="stMetric"] label { 
            color: #0f172a !important; 
            font-weight: 800 !important; 
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        div[data-testid="stMetric"] [data-testid="stMetricValue"] { 
            color: #0b192c !important; 
            font-weight: 900 !important; 
            font-size: 1.9rem !important;
        }

        /* Solapas Principales */
        .stTabs [data-baseweb="tab-list"] { gap: 12px; background-color: #1e293b; padding: 8px; border-radius: 12px; border: 1px solid rgba(255, 255, 255, 0.1); }
        .stTabs [data-baseweb="tab"] { background-color: transparent; border: none !important; padding: 12px 24px; border-radius: 8px; font-weight: 700; color: #94a3b8; }
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

# Instancia de datos en memoria para la demostración
if 'libro_diario' not in st.session_state:
    st.session_state.libro_diario = [
        {"Fecha": "2026-09-01", "Concepto": "Abono Ascensores S.A.", "Monto": 45000.0, "Tipo": "Gasto Ordinario"},
        {"Fecha": "2026-09-05", "Concepto": "Sueldo Encargado + Cargas SUTERH", "Monto": 250000.0, "Tipo": "Gasto Ordinario"}
    ]

if 'unidades' not in st.session_state:
    st.session_state.unidades = {
        "101": {"propietario": "Juan Pérez", "porcentaje": 0.10, "saldo": 1500.0},
        "102": {"propietario": "María Rodriguez", "porcentaje": 0.15, "saldo": 0.0}
    }

if 'reclamos' not in st.session_state:
    st.session_state.reclamos = [
        {"UF": "102", "Detalle": "Reparación de filtración", "Proveedor": "Plomería Gas-An", "Costo": 14500.0, "Estado": "Finalizada"}
    ]

PROVEEDORES = {"plomeria": [{"nombre": "Plomería Gas-An", "tel": "1144445555"}]}

# PANEL LATERAL CON EL LOGO REAL CORPORATIVO
with st.sidebar:
    st.image("https://imgbox.com", use_container_width=True)
    st.title("Resilia_Condominios")
    st.caption("AI Swarm ERP Administration")
    st.markdown("---")
    consorcio_act = st.selectbox("Edificio Monitoreado", ["Av. Corrientes 1234, CABA"])
    st.info("CUIT: 30-11111111-9\n\nJurisdicción: Ley 941 CABA")

# TÍTULO PRINCIPAL
st.title("🏢 Resilia_Condominios")
st.markdown("Plataforma avanzada de inteligencia artificial para la gestión y automatización integral de la propiedad horizontal.")

# INDICADORES PRINCIPALES (CUADROS EN DORADO PREMIUM)
m1, m2, m3, m4 = st.columns(4)
with m1:
    st.metric(label="Total gastos del periodo", value=f"${sum(x['Monto'] for x in st.session_state.libro_diario):,.2f}")
with m2:
    st.metric(label="Fondos de reserva", value="$450,000.00")
with m3:
    uf_morosas = sum(1 for u in st.session_state.unidades.values() if u['saldo'] > 0)
    st.metric(label="UF en Mora", value=str(uf_morosas))
with m4:
    st.metric(label="Ordenes de trabajo", value=str(len(st.session_state.reclamos)))

st.markdown("<br>", unsafe_allow_html=True)

# SOLAPAS PRINCIPALES (MULTICANAL)
tab_atencion, tab_contable, tab_operaciones = st.tabs([
    "💬 Centro de Atención Multicanal", 
    "📊 Prorrateo, Finanzas y Libro Diario", 
    "🔧 Logística Operativa y Proveedores"
])

with tab_atencion:
    st.subheader("📥 Recepción Automatizada de Mensajes (Multicanal)")
    col_input, col_output = st.columns([1, 1.2])
    with col_input:
        uf_sel = st.selectbox("Unidad Funcional Emisora", list(st.session_state.unidades.keys()))
        canal_sel = st.radio("Canal de Ingreso (Multicanal)", ["WhatsApp", "Portal Web", "Correo Electrónico"], horizontal=True)
        mensaje_custom = st.text_area("Cuerpo del Requerimiento:", value="Tengo una filtración en el baño, pierde un caño de agua.")
        procesar = st.button("🚀 Desplegar Enjambre de IA", use_container_width=True)
    with col_output:
        st.markdown("### ⚙️ Trazabilidad de Decisiones")
        if procesar:
            st.markdown(f'''<div class="agent-card"><div class="agent-title">🤖 Agente Front-Desk</div>Mensaje recibido por canal <b>{canal_sel}</b> de la UF {uf_sel}.</div>''', unsafe_allow_html=True)
            st.success("Orden procesada correctamente por el ecosistema de IA.")

with tab_contable:
    st.subheader("📊 Libro Diario del Consorcio")
    st.dataframe(pd.DataFrame(st.session_state.libro_diario), use_container_width=True, hide_index=True)

with tab_operaciones:
    st.subheader("🔧 Control de Mantenimiento y Cartilla de Servicios")
    
    # SUB-SOLAPAS CELESTES SOLICITADAS
    st.markdown('<div class="celeste-tabs">', unsafe_allow_html=True)
    subtab_activas, subtab_finalizadas, subtab_pendientes = st.tabs([
        "🔹 Ordenes de trabajo activas", 
        "🔹 Ordenes de trabajo finalizadas", 
        "🔹 Ordenes de trabajo Pendientes"
    ])
    st.markdown('</div>', unsafe_allow_html=True)
    
    df_all = pd.DataFrame(st.session_state.reclamos)
    with subtab_activas:
        st.info("No se registran órdenes de trabajo activas en este momento.")
    with subtab_finalizadas:
        st.dataframe(df_all[df_all['Estado'] == 'Finalizada'], use_container_width=True, hide_index=True)
    with subtab_pendientes:
        st.info("No hay órdenes de trabajo pendientes de aprobación.")







