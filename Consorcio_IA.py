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
# BASE DE DATOS OPTIMIZADA POR EDIFICIO CON SUS RESPECTIVAS 5 UFs
# =====================================================================
if 'data_consorcios' not in st.session_state:
    # Definimos la lista fija de las 5 UFs requeridas
    lista_ufs = ["1A", "3J", "4K", "5M", "6P"]
    
    # Inicializamos la estructura de los 5 edificios solicitados de forma segura
    st.session_state.data_consorcios = {
        "Av. Corrientes 1234, CABA": {"reserva": 450000.0, "gasto_base": 295000.0, "mora_uf": ["5M"]},
        "Larrea 435, CABA": {"reserva": 380000.0, "gasto_base": 115000.0, "mora_uf": ["3J", "6P"]},
        "Montevideo 891, CABA": {"reserva": 620000.0, "gasto_base": 117000.0, "mora_uf": ["4K", "6P"]},
        "San Jose 1111, CABA": {"reserva": 290000.0, "gasto_base": 59000.0, "mora_uf": ["5M"]},
        "Guayaquil 399, CABA": {"reserva": 850000.0, "gasto_base": 515000.0, "mora_uf": ["4K"]}
    }
    
    # Armamos dinámicamente las subtablas para evitar recortes de código por límite de caracteres
    for nombre, datos in st.session_state.data_consorcios.items():
        datos["unidades"] = {uf: {"propietario": f"Propietario {uf}", "porcentaje": 0.20, "saldo": 12000.0 if uf in datos["mora_uf"] else 0.0} for uf in lista_ufs}
        datos["libro_diario"] = [{"Fecha": "2026-09-10", "Concepto": "Gastos Centrales Auditados", "Monto": datos["gasto_base"], "Tipo": "Ordinario"}]
        datos["trabajos_solicitados"] = [{"UF": "1A", "Rubro": "Plomería", "Detalle": "Filtración detectada en cañería principal", "Fecha": "2026-09-22"}]
        datos["trabajos_en_proceso"] = [{"UF": "3J", "Rubro": "Albañilería", "Detalle": "Reparación de revoques en patio", "Proveedor": "Construcciones R&M"}]
        datos["trabajos_pendientes"] = [{"UF": "5M", "Rubro": "Electricidad", "Detalle": "Revisión técnica de térmicas", "Motivo": "Espera materiales"}]

PROVEEDORES = {"plomeria": [{"nombre": "Plomería Gas-An", "tel": "1144445555"}]}

# =====================================================================
# PANEL LATERAL (SIDEBAR DE CONTROL CON LOGO INTEGRADO VÍA ENLACE)
# =====================================================================
with st.sidebar:
    st.image("https://imgbox.com", use_container_width=True)
    st.title("Resilia_Condominios")
    st.caption("AI Swarm ERP Administration")
    st.markdown("---")
    
    # Selector Interactivo de Edificios Monitoreados
    edificio_seleccionado = st.selectbox("Edificios Monitoreados", list(st.session_state.data_consorcios.keys()))
    st.info("CUIT: 30-11111111-9\n\nJurisdicción: Ley 941 CABA")

# Extracción reactiva de los datos del edificio activo seleccionado
consorcio_actual = st.session_state.data_consorcios[edificio_seleccionado]
unidades_actuales = consorcio_actual["unidades"]
libro_diario_actual = consorcio_actual["libro_diario"]

# =====================================================================
# DASHBOARD CENTRAL INTERACTIVO
# =====================================================================
st.title("🏢 Resilia_Condominios")
st.markdown(f"Monitoreo corporativo activo sobre el consorcio de: **{edificio_seleccionado}**")

# CUATRO PANELES EJECUTIVOS TOTALMENTE EN DORADO PREMIUM
m1, m2, m3, m4 = st.columns(4)
with m1:
    total_gastos = sum(x['Monto'] for x in libro_diario_actual)
    st.metric(label="Total gastos del periodo", value=f"${total_gastos:,.2f}")
with m2:
    st.metric(label="Fondos de reserva", value=f"${consorcio_actual['reserva']:,.2f}")
with m3:
    uf_mora = sum(1 for u in unidades_actuales.values() if u['saldo'] > 0)
    st.metric(label="UF en Mora", value=str(uf_mora))
with m4:
    total_ot = len(consorcio_actual["trabajos_solicitados"]) + len(consorcio_actual["trabajos_en_proceso"]) + len(consorcio_actual["trabajos_pendientes"])
    st.metric(label="Ordenes de trabajo", value=str(total_ot))

st.markdown("<br>", unsafe_allow_html=True)

# CONFIGURACIÓN DE SOLAPAS PRINCIPALES (ENTORNO MULTICANAL VINCULADO)
tab_atencion, tab_contable, tab_operaciones = st.tabs([
    "💬 Centro de Atención Multicanal", 
    "📊 Prorrateo, Finanzas y Libro Diario", 
    "🔧 Logística Operativa y Proveedores"
])

# ---------------------------------------------------------------------
# SOLAPA 1: CENTRO DE ATENCIÓN MULTICANAL
# ---------------------------------------------------------------------
with tab_atencion:
    st.subheader("📥 Recepción Automatizada de Mensajes (Ecosistema Multicanal)")
    st.write("Simulá la entrada de un requerimiento. El menú desplegable muestra exclusivamente las 5 UFs (1A, 3J, 4K, 5M, 6P) de este edificio.")
    
    col_input, col_output = st.columns([1, 1.2])
    with col_input:
        st.markdown("### Consola de Entrada")
        uf_sel = st.selectbox("Unidad Funcional Emisora", list(unidades_actuales.keys()))
        canal_sel = st.radio("Canal de Ingreso (Multicanal)", ["WhatsApp", "Portal Web", "Correo Electrónico"], horizontal=True)
        mensaje_custom = st.text_area("Cuerpo del Requerimiento:", value="Tengo una filtración en el baño, pierde un caño de agua.")
        procesar = st.button("🚀 Desplegar Enjambre de IA", use_container_width=True)
    with col_output:
        st.markdown("### ⚙️ Trazabilidad de Decisiones")
        if procesar:
            msg_lower = mensaje_custom.lower()
            st.markdown(f'''<div class="agent-card"><div class="agent-title">🤖 Agente Front-Desk</div>Mensaje interceptado vía <b>{canal_sel}</b> de la UF {uf_sel} (Propietario: {unidades_actuales[uf_sel]['propietario']}).</div>''', unsafe_allow_html=True)
            
            if "expensa" in msg_lower or "pago" in msg_lower or "debo" in msg_lower:
                saldo = unidades_actuales[uf_sel]['saldo']
                estado = "Deudor" if saldo > 0 else ("Al día" if saldo == 0 else "Saldo a Favor")
                st.markdown(f'''<div class="agent-card agent-contable"><div class="agent-title">📈 Agente Contador</div>Auditoría de cuenta corriente procesada. Saldo UF {uf_sel}: <b>${abs(saldo):,.2f}</b> ({estado}).</div>''', unsafe_allow_html=True)
            else:
                st.markdown('''<div class="agent-card agent-operativo"><div class="agent-title">🔧 Agente Operativo</div>Incidencia técnica clasificada. Activando compulsa digital con la cartilla de prestadores homologados.</div>''', unsafe_allow_html=True)
