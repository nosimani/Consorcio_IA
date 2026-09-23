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
        h1 { color: #ffffff; font-family: sans-serif; font-weight: 900; letter-spacing: -1px; text-shadow: 0 0 20px rgba(56, 189, 248, 0.4); }
        h2, h3 { color: #38bdf8; font-family: sans-serif; font-weight: 700; }
        .stMarkdown p { color: #e2e8f0; }

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
        div[data-testid="stMetric"] label { color: #0f172a !important; font-weight: 800 !important; text-transform: uppercase; letter-spacing: 0.5px; }
        div[data-testid="stMetric"] [data-testid="stMetricValue"] { color: #0b192c !important; font-weight: 900 !important; font-size: 1.9rem !important; }

        /* Menú de Solapas Estilo Neón */
        .stTabs [data-baseweb="tab-list"] { gap: 12px; background-color: #1e293b; padding: 8px; border-radius: 12px; }
        .stTabs [data-baseweb="tab"] { background-color: transparent; border: none !important; padding: 12px 24px; border-radius: 8px; font-weight: 800; color: #94a3b8; transition: all 0.3s; }
        .stTabs [aria-selected="true"] { background: linear-gradient(135deg, #0284c7 0%, #0369a1 100%) !important; color: #FFFFFF !important; box-shadow: 0 0 15px rgba(56, 189, 248, 0.4); }

        /* Solapas Celestes Secundarias */
        .celeste-tabs [data-baseweb="tab-list"] { background-color: #0f172a !important; border: 1px solid #38bdf8 !important; }
        .celeste-tabs [data-baseweb="tab"] { color: #bae6fd !important; }
        .celeste-tabs [aria-selected="true"] { background: #38bdf8 !important; color: #0f172a !important; font-weight: 800 !important; }

        /* Tarjetas de Agentes e Inputs */
        .agent-card { background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%); padding: 24px; border-radius: 16px; border-left: 6px solid #38bdf8; margin-bottom: 20px; color: #f1f5f9; }
        .agent-title { font-size: 1.1rem; font-weight: 900; color: #ffffff; text-transform: uppercase; }
        .stDataFrame, .stTable { background-color: rgba(30, 41, 59, 0.5); border-radius: 16px; padding: 10px; }
    </style>
""", unsafe_allow_html=True)

# =====================================================================
# BASE DE DATOS GLOBAL DE CONDOMINIOS
# =====================================================================
if 'data_consorcios' not in st.session_state:
    st.session_state.data_consorcios = {
        "Av. Corrientes 1234, CABA": {"reserva": 450000.0, "factor": 1.0, "mora": "1", "ots": "2"},
        "Larrea 435, CABA": {"reserva": 380000.0, "factor": 0.6, "mora": "2", "ots": "1"},
        "Montevideo 891, CABA": {"reserva": 620000.0, "factor": 0.8, "mora": "2", "ots": "1"},
        "San Jose 1111, CABA": {"reserva": 290000.0, "factor": 0.5, "mora": "1", "ots": "1"},
        "Guayaquil 399, CABA": {"reserva": 850000.0, "factor": 1.5, "mora": "1", "ots": "1"}
    }

if 'ordenes_globales' not in st.session_state:
    st.session_state.ordenes_globales = [
        {"Edificio": "Av. Corrientes 1234, CABA", "UF": "1A", "Tipo de Trabajo": "Plomería", "Detalle": "Filtración en caño central de agua", "Estado": "Trabajos Solicitados"},
        {"Edificio": "Av. Corrientes 1234, CABA", "UF": "3J", "Tipo de Trabajo": "Cerrajería", "Detalle": "Cambio de combinación cerradura", "Estado": "Trabajos en Proceso"},
        {"Edificio": "Larrea 435, CABA", "UF": "3J", "Tipo de Trabajo": "Electricidad", "Detalle": "Falla de fase en disyuntor", "Estado": "Trabajos Solicitados"},
        {"Edificio": "Larrea 435, CABA", "UF": "6P", "Tipo de Trabajo": "Gas", "Detalle": "Revisión técnica de estufa reglamentaria", "Estado": "Trabajos Pendientes"}
    ]

# Matriz de Proveedores basada en tu Excel original
CARTILLA_PROVEEDORES = {
    "Cerrajería": ["Seleccione un prestador...", "🔑 Llave - Tel: 111111111 (CUIT: 2222222222)", "🔑 Cerradura - Tel: 222222222", "🔑 Manojo - Tel: 333333333", "🔑 Traba - Tel: 444444444", "🔑 Pasador - Tel: 555555555"],
    "Electricidad": ["Seleccione un prestador...", "⚡ El Fusible - Tel: 666666666 (CUIT: 2222222222)", "⚡ Cablecito - Tel: 777777777", "⚡ Patada - Tel: 333333333", "⚡ Cortocircuito - Tel: 444444444", "⚡ Disyuntor - Tel: 555555555"],
    "Gas": ["Seleccione un prestador...", "🔥 Pum - Tel: 666666666 (CUIT: 2222222222)", "🔥 Garrafa - Tel: 777777777", "🔥 Hornalla - Tel: 111111111", "🔥 Calefonete - Tel: 222222222", "🔥 Estufeta - Tel: 333333333"],
    "Plomería": ["Seleccione un prestador...", "🚰 Caño - Tel: 444444444 (CUIT: 2222222222)", "🚰 Cañito - Tel: 555555555", "🚰 Cañete - Tel: 666666666", "🚰 Canilla - Tel: 777777777", "🚰 Rejilla - Tel: 222222222"]
}

# =====================================================================
# PANEL LATERAL (SIDEBAR DE CONTROL)
# =====================================================================
with st.sidebar:
    st.image("https://imgbox.com", use_container_width=True)
    st.title("Resilia_Condominios")
    st.caption("AI Swarm ERP Platform v2.6")
    st.markdown("---")
    pantalla_activa = st.radio("Seleccione Vista:", ["🏠 Panel General por Edificio", "🛠️ Abrir Órdenes de Trabajo"], index=0)
    st.markdown("---")
    edificio_seleccionado = st.selectbox("Edificio Activo de Control", list(st.session_state.data_consorcios.keys()))
    st.markdown("---")
    csv_data = pd.DataFrame(st.session_state.ordenes_globales).to_csv(index=False).encode('utf-8')
    st.download_button(label="📊 Descargar Historial OT (CSV)", data=csv_data, file_name=f"Reporte_Resilia.csv", mime="text/csv", use_container_width=True)
    st.markdown("---")
    st.info("CUIT: 30-11111111-9\n\nJurisdicción: Ley 941 CABA")

# Carga de la configuración del edificio activo
consorcio_actual = st.session_state.data_consorcios[edificio_seleccionado]
f_cal = consorcio_actual["factor"]

# ALGORITMO AUTOMÁTICO COMPACTO DE INGRESOS Y GASTOS (Blindado contra límites de texto del chat)
ingresos_lista = [
    {"Concepto": "Cobro de Expensas Ordinarias/Extraordinarias", "Monto": 320000.0 * f_cal},
    {"Concepto": "Alquileres de Locales Comerciales PB", "Monto": 85000.0 * (1.0 if f_cal >= 0.8 else 0.0)},
    {"Concepto": "Intereses por colocaciones a Plazo Fijo", "Monto": 14000.0 * f_cal}
]
gastos_lista = [
    {"Concepto": "Gastos por Reparaciones e Infraestructura", "Monto": 45000.0 * f_cal},
    {"Concepto": "Honorarios de Administración", "Monto": 35000.0 * f_cal},
    {"Concepto": "Sueldo de Encargado + Cargas SUTERH", "Monto": 250000.0 * (1.0 if f_cal >= 0.7 else 0.0)},
    {"Concepto": "Compra de artículos de limpieza", "Monto": 12000.0 * f_cal},
    {"Concepto": "Pagos de luz (Edesur/Edenor Central)", "Monto": 18000.0 * f_cal},
    {"Concepto": "Otros gastos generales y bancarios", "Monto": 7000.0 * f_cal}
]

# =====================================================================
# PANTALLA 1: DASHBOARD GENERAL
# =====================================================================
if pantalla_activa == "🏠 Panel General por Edificio":
    st.title("🏢 Resilia_Condominios")
    st.markdown(f"Monitoreo analítico activo sobre el consorcio: **{edificio_seleccionado}**")

    # MÉTRICAS EN DORADO
    m1, m2, m3, m4 = st.columns(4)
    with m1: 
        total_g = sum(x['Monto'] for x in gastos_lista)
        st.metric(label="Total gastos del periodo", value=f"${total_g:,.2f}")
    with m2: st.metric(label="Fondos de reserva", value=f"${consorcio_actual['reserva']:,.2f}")
    with m3: st.metric(label="UF en Mora", value=consorcio_actual['mora'])
    with m4: st.metric(label="Ordenes de trabajo", value=consorcio_actual['ots'])

    st.markdown("<br>", unsafe_allow_html=True)
    
    # REGLA DE NOMENCLATURA SOLICITADA
    tab_atencion, tab_contable, tab_prov = st.tabs([
        "💬 Centro de Atención Multicanal", 
        "📊 Cuadro de Ingresos y Gastos", 
        "📋 Cartilla de Proveedores"
    ])

    with tab_atencion:
        st.subheader("📥 Recepción Automatizada Multicanal")
        col_input, col_output = st.columns([1, 1.2])
        with col_input:
            uf_sel = st.selectbox("Unidad Funcional Emisora", ["1A", "3J", "4K", "5M", "6P"])
            canal_sel = st.radio("Canal de Ingreso", ["WhatsApp", "Portal Web", "Correo Electrónico"], horizontal=True)
            tipo_incidente = st.selectbox("Tipo de Incidencia Semántica:", ["Plomería", "Cerrajería", "Electricidad", "Gas"])
            mensaje_custom = st.text_area("Cuerpo del Requerimiento:", value=f"Se detectó un desperfecto crítico de {tipo_incidente.lower()} en la UF {uf_sel}.")
            procesar = st.button("🚀 Desplegar Enjambre de IA", use_container_width=True)
        with col_output:
            st.markdown("### ⚙️ Trazabilidad de Decisiones")
            if procesar:
                st.markdown(f'''<div class="agent-card"><div class="agent-title">🤖 Agente Front-Desk</div>Mensaje recibido por <b>{canal_sel}</b> de la UF {uf_sel}.</div>''', unsafe_allow_html=True)
