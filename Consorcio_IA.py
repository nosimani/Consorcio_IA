import streamlit as st
import pandas as pd
import random
from datetime import datetime

# =====================================================================
# CONFIGURACIÓN PREMIUM DE LA INTERFAZ (LOOK & FEEL CORPORATIVO)
# =====================================================================
st.set_page_config(
    page_title="ConsorcioIA - Enterprise Swarm OS",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inyección de CSS Avanzado para diseño ejecutivo de alto impacto
st.markdown("""
    <style>
        /* Fondo general de la plataforma */
        .main {
            background-color: #F1F5F9;
        }
        
        /* Tipografías institucionales */
        h1 {
            color: #0F172A;
            font-family: 'Inter', -apple-system, sans-serif;
            font-weight: 900;
            letter-spacing: -1px;
        }
        h2, h3 {
            color: #1E3A8A;
            font-family: 'Inter', sans-serif;
            font-weight: 700;
        }

        /* Tarjetas de Métricas Ejecutivas (Glassmorphism Oscuro) */
        div[data-testid="stMetric"] {
            background: linear-gradient(135deg, #1E3A8A 0%, #0F172A 100%);
            color: white !important;
            padding: 25px !important;
            border-radius: 16px !important;
            box-shadow: 0 10px 15px -3px rgba(15, 23, 42, 0.15);
            border: 1px solid rgba(255, 255, 255, 0.1);
            transition: transform 0.2s;
        }
        div[data-testid="stMetric"]:hover {
            transform: translateY(-5px);
        }
        div[data-testid="stMetric"] label {
            color: #93C5FD !important;
            font-weight: 600 !important;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        div[data-testid="stMetric"] [data-testid="stMetricValue"] {
            color: #FFFFFF !important;
            font-weight: 800 !important;
            font-size: 2rem !important;
        }

        /* Menú de Navegación por Solapas Avanzadas */
        .stTabs [data-baseweb="tab-list"] {
            gap: 12px;
            background-color: #E2E8F0;
            padding: 8px;
            border-radius: 12px;
        }
        .stTabs [data-baseweb="tab"] {
            background-color: transparent;
            border: none !important;
            padding: 12px 24px;
            border-radius: 8px;
            font-weight: 700;
            color: #475569;
            transition: all 0.3s;
        }
        .stTabs [aria-selected="true"] {
            background-color: #FFFFFF !important;
            color: #1E3A8A !important;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        }

        /* Reportes de la Inteligencia Artificial (Logs del Enjambre) */
        .agent-card {
            background-color: #FFFFFF;
            padding: 24px;
            border-radius: 16px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
            border-left: 6px solid #3B82F6;
            margin-bottom: 18px;
        }
        .agent-legal { border-left-color: #EF4444; background: linear-gradient(to right, #FFF5F5, #FFFFFF); }
        .agent-contable { border-left-color: #10B981; background: linear-gradient(to right, #F0FDF4, #FFFFFF); }
        .agent-operativo { border-left-color: #F59E0B; background: linear-gradient(to right, #FFFBEB, #FFFFFF); }
        
        .agent-title {
            font-size: 1.1rem;
            font-weight: 800;
            color: #1E293B;
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

if 'reclamos' not in st.session_state:
    st.session_state.reclamos = []

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
    # Integración directa del logo corporativo sin imágenes rotas
    st.image("https://imgbox.com", use_container_width=True)
    st.title("ConsorcioIA")
    st.caption("AI Swarm ERP para Administración")
    st.markdown("---")
    st.markdown("💡 **Variables de Entorno:**")
    consorcio_act = st.selectbox("Edificio Monitoreado", ["Av. Corrientes 1234, CABA", "Calle Florida 450, CABA"])
    st.info("CUIT: 30-11111111-9\n\nNormativa: Ley 941 CABA & CCyCN Argentina")

# =====================================================================
# CUERPO PRINCIPAL / DASHBOARD CENTRAL
# =====================================================================
st.title("🏢 Sistema de Enjambre Multiagente Consorcial")
st.markdown("Automatización integral de reclamos operativos, liquidación contable por coeficientes y auditoría legal.")

# Fila superior de Indicadores de Alto Impacto
m1, m2, m3, m4 = st.columns(4)
with m1:
    st.metric(label="Total Gastos del Periodo", value=f"${sum(x['Monto'] for x in st.session_state.libro_diario):,.2f}")
with m2:
    st.metric(label="Fondo de Reserva Consorcial", value="$450,000.00")
with m3:
    uf_morosas = sum(1 for u in st.session_state.unidades.values() if u['saldo'] > 0)
    st.metric(label="UFs en Estado de Mora", value=str(uf_morosas))
with m4:
    st.metric(label="Órdenes de Trabajo Activas", value=str(len(st.session_state.reclamos)))

st.markdown("<br>", unsafe_allow_html=True)

# Estructura de Navegación por Solapas
tab_atencion, tab_contable, tab_operaciones = st.tabs([
    "💬 Centro de Atención Omnicanal", 
    "📊 Prorrateo, Finanzas y Libro Diario", 
    "🔧 Logística Operativa y Proveedores"
])

# ---------------------------------------------------------------------
# SOLAPA 1: CENTRO DE ATENCIÓN OMNICANAL (RECLAMOS)
# ---------------------------------------------------------------------
with tab_atencion:
    st.subheader("📥 Recepción Automatizada de Mensajes")
    st.write("Simulá la entrada de un requerimiento para verificar el ruteo inteligente del enjambre.")
    
    col_input, col_output = st.columns([1, 1.2])
    
    with col_input:
        st.markdown("### Consola de Entrada")
        uf_sel = st.selectbox("Unidad Funcional Emisora", list(st.session_state.unidades.keys()))
        canal_sel = st.radio("Canal de Ingreso", ["WhatsApp", "Portal Web", "Correo Electrónico"], horizontal=True)
        
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
            msg_lower = mensaje_custom.lower()
            
            # 1. Ejecución del Agente de Front-Desk
            st.markdown(f'''<div class="agent-card"><div class="agent-title">🤖 Agente Atención (Front-Desk)</div>Mensaje recibido por <b>{canal_sel}</b> de la UF {uf_sel} ({st.session_state.unidades[uf_sel]['propietario']}). Clasificando intención...</div>''', unsafe_allow_html=True)
            
            # Ruteo Contable
            if "expensa" in msg_lower or "pago" in msg_lower or "debo" in msg_lower:
                saldo = st.session_state.unidades[uf_sel]['saldo']
                estado = "Deudor" if saldo > 0 else ("Al día" if saldo == 0 else "Saldo a Favor")
                st.markdown(f'''<div class="agent-card agent-contable"><div class="agent-title">📈 Agente Contador (Finanzas)</div>Consulta de cuenta procesada. Saldo actual de la UF: <b>${abs(saldo):,.2f}</b> ({estado}). Generando respuesta automática saliente...</div>''', unsafe_allow_html=True)
                st.success(f"Respuesta enviada: Estimado copropietario, su saldo es de ${abs(saldo):,.2f} ({estado}).")
            
            # Ruteo Operativo de Mantenimiento

