import streamlit as st
import pandas as pd
import random
from datetime import datetime

# =====================================================================
# CONFIGURACIÓN PREMIUM DE LA INTERFAZ (LOOK & FEEL CORPO AZUL / CELESTE)
# =====================================================================
st.set_page_config(
    page_title="Resilia_Condominios - Enterprise Swarm OS",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inyección de CSS Avanzado para diseño corporativo azul y celeste de alto impacto
st.markdown("""
    <style>
        /* Fondo general de la plataforma: Paleta Azul Institucional */
        .main {
            background-color: #0c2340;
        }
        
        /* Títulos e identificadores en Blanco/Celeste sobre el fondo azul */
        h1 {
            color: #FFFFFF;
            font-family: 'Inter', -apple-system, sans-serif;
            font-weight: 900;
            letter-spacing: -1px;
        }
        h2, h3 {
            color: #38bdf8;
            font-family: 'Inter', sans-serif;
            font-weight: 700;
        }
        
        /* Texto de ayuda/captions en gris claro para contraste */
        .stMarkdown p {
            color: #cbd5e1;
        }

        /* Paneles de Métricas Ejecutivas (Diseño Vidrio Premium) */
        div[data-testid="stMetric"] {
            background: linear-gradient(135deg, #1e3a8a 0%, #1e40af 100%);
            color: white !important;
            padding: 22px !important;
            border-radius: 16px !important;
            box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.3);
            border: 1px solid rgba(255, 255, 255, 0.1);
            transition: transform 0.2s;
        }
        div[data-testid="stMetric"]:hover {
            transform: translateY(-5px);
        }
        div[data-testid="stMetric"] label {
            color: #38bdf8 !important;
            font-weight: 700 !important;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        div[data-testid="stMetric"] [data-testid="stMetricValue"] {
            color: #FFFFFF !important;
            font-weight: 800 !important;
            font-size: 1.8rem !important;
        }

        /* Estilo para las pestañas de navegación principales */
        .stTabs [data-baseweb="tab-list"] {
            gap: 12px;
            background-color: #1e293b;
            padding: 8px;
            border-radius: 12px;
            border: 1px solid rgba(255, 255, 255, 0.1);
        }
        .stTabs [data-baseweb="tab"] {
            background-color: transparent;
            border: none !important;
            padding: 12px 24px;
            border-radius: 8px;
            font-weight: 700;
            color: #94a3b8;
            transition: all 0.3s;
        }
        .stTabs [aria-selected="true"] {
            background-color: #0284c7 !important;
            color: #FFFFFF !important;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.2);
        }

        /* Estilo específico para las SOLAPAS CELESTES de Órdenes de Trabajo */
        .celeste-tabs [data-baseweb="tab-list"] {
            background-color: #0f172a !important;
            border: 1px solid #38bdf8 !important;
        }
        .celeste-tabs [data-baseweb="tab"] {
            color: #bae6fd !important;
        }
        .celeste-tabs [aria-selected="true"] {
            background-color: #38bdf8 !important;
            color: #0f172a !important;
            font-weight: 800 !important;
        }

        /* Reportes de la Inteligencia Artificial (Logs del Enjambre) */
        .agent-card {
            background-color: #1e293b;
            padding: 24px;
            border-radius: 16px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.2);
            border-left: 6px solid #38bdf8;
            margin-bottom: 18px;
            color: #f1f5f9;
        }
        .agent-card b { color: #38bdf8; }
        .agent-legal { border-left-color: #ef4444; background: linear-gradient(to right, #2d1f1f, #1e293b); }
        .agent-contable { border-left-color: #10b981; background: linear-gradient(to right, #192c24, #1e293b); }
        .agent-operativo { border-left-color: #f59e0b; background: linear-gradient(to right, #2c2519, #1e293b); }
        
        .agent-title {
            font-size: 1.1rem;
            font-weight: 800;
            color: #ffffff;
            margin-bottom: 8px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
    </style>
""", unsafe_allow_html=True)

# =====================================================================
# CORE DE NEGOCIO Y MODELO DE DATOS DE SIMULACIÓN
# =====================================================================
if 'libro_diario' not in st.session_state:
    st.session_state.libro_diario = [
        {"Fecha": "2026-09-01", "Concepto": "Abono Ascensores S.A.", "Monto": 45000.0, "Tipo": "Gasto Ordinario"},
        {"Fecha": "2026-09-05", "Concepto": "Sueldo Encargado + Cargas SUTERH", "Monto": 250000.0, "Tipo": "Gasto Ordinario"},
        {"Fecha": "2026-09-10", "Concepto": "Factura Luz Edesur", "Monto": 35000.0, "Tipo": "Gasto Ordinario"}
    ]

if 'unidades' not in st.session_state:
    st.session_state.unidades = {
        "101": {"propietario": "Juan Pérez", "porcentaje": 0.10, "saldo": 1500.0},
        "102": {"propietario": "María Rodriguez", "porcentaje": 0.15, "saldo": 0.0},
        "201": {"propietario": "Carlos López", "porcentaje": 0.12, "saldo": -500.0},
        "202": {"propietario": "Ana Martínez", "porcentaje": 0.18, "saldo": 12000.0},
        "301": {"propietario": "Luis Gomez", "porcentaje": 0.25, "saldo": 0.0},
        "302": {"propietario": "Sofía Rossi", "porcentaje": 0.20, "saldo": -1500.0}
    }

# Historial base de órdenes con estados distribuidos
if 'reclamos' not in st.session_state:
    st.session_state.reclamos = [
        {"UF": "102", "Detalle": "Reparación de filtración de cocina antigua", "Proveedor Asignado": "Plomería Gas-An", "Costo Cotizado": 14500.0, "Estado": "Finalizada"},
        {"UF": "301", "Detalle": "Cambio de térmicas generales palier b", "Proveedor Asignado": "Electricidad Voltio", "Costo Cotizado": 19000.0, "Estado": "Activa"}
    ]

PROVEEDORES = {
    "plomeria": [
        {"nombre": "Plomería Gas-An", "tel": "1144445555", "email": "gas-an@plomeros.com"},
        {"nombre": "Destapaciones Express", "tel": "1133339999", "email": "express@destapaciones.com"}
    ],
    "electricidad": [
        {"nombre": "Electricidad Voltio", "tel": "1177778888", "email": "voltio@electricistas.com"}
    ],
    "cerrajeria": [
        {"nombre": "Cerrajería El Llavero", "tel": "1122228888", "email": "contacto@elllavero.com"}
    ]
}

# =====================================================================
# PANEL LATERAL (SIDEBAR CON LOGO OFICIAL DE RESILIA AGENCY)
# =====================================================================
with st.sidebar:
    st.image("https://imgbox.com", use_container_width=True)
    st.title("Resilia_Condominios")
    st.caption("AI Swarm ERP Administration")
    st.markdown("---")
    st.markdown("💡 **Variables de Entorno:**")
    consorcio_act = st.selectbox("Edificio Monitoreado", ["Av. Corrientes 1234, CABA", "Calle Florida 450, CABA"])
    st.info("CUIT: 30-11111111-9\n\nNormativa: Ley 941 CABA & CCyCN Argentina")

# =====================================================================
# CUERPO PRINCIPAL / DASHBOARD CENTRAL
# =====================================================================
st.title("🏢 Resilia_Condominios")
st.markdown("Plataforma avanzada de inteligencia artificial para la gestión y automatización integral de la propiedad horizontal.")

# PANELES / CUATRO TARJETAS INCLUYENDO "ORDENES DE TRABAJO"
m1, m2, m3, m4 = st.columns(4)
with m1:
    st.metric(label="Total Gastos del Periodo", value=f"${sum(x['Monto'] for x in st.session_state.libro_diario):,.2f}")
with m2:
    st.metric(label="Fondo de Reserva Consorcial", value="$450,000.00")
with m3:
    uf_morosas = sum(1 for u in st.session_state.unidades.values() if u['saldo'] > 0)
    st.metric(label="UFs en Estado de Mora", value=str(uf_morosas))
with m4:
    st.metric(label="Ordenes de Trabajo", value=str(len(st.session_state.reclamos)))

st.markdown("<br>", unsafe_allow_html=True)

# Estructura de Navegación por Solapas Principales
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
    st.write("Simulá la entrada de un requerimiento para verificar el ruteo inteligente del enjambre.")
    
    col_input, col_output = st.columns([1, 1.2])
    
    with col_input:
        st.markdown("### Consola de Entrada")
        uf_sel = st.selectbox("Unidad Funcional Emisora", list(st.session_state.unidades.keys()))
        canal_sel = st.radio("Canal de Ingreso (Multicanal)", ["WhatsApp", "Portal Web", "Correo Electrónico"], horizontal=True)
        
        mensaje_sugerido = st.selectbox("Mensajes Frecuentes:", [
            "Tengo una filtración en el baño, pierde un caño de agua.",
            "Hola, ¿cuánto debo de expensas?",
            "Se rompió la cerradura de la puerta de entrada al edificio.",
            "Necesito saber si entró mi pago del mes pasado."
        ])
        
        mensaje_custom = st.text_area("Cuerpo del Requerimiento:", value=mensaje_sugerido)
        procesar = st.button("🚀 Desplegar Enjambre de IA", use_container_width=True)
        
    with col_output:
        st.markdown("### ⚙️ Trazabilidad de Decisiones Automatizadas (Logs)")
        if procesar:


