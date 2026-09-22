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
# BASE DE DATOS GLOBAL CENTRALIZADA (CONTROL DE CONTEXTO REPOSITORIO)
# =====================================================================
if 'data_consorcios' not in st.session_state:
    lista_ufs = ["1A", "3J", "4K", "5M", "6P"]
    st.session_state.data_consorcios = {
        "Av. Corrientes 1234, CABA": {"reserva": 450000.0, "gasto_base": 295000.0, "mora_uf": ["5M"]},
        "Larrea 435, CABA": {"reserva": 380000.0, "gasto_base": 115000.0, "mora_uf": ["3J", "6P"]},
        "Montevideo 891, CABA": {"reserva": 620000.0, "gasto_base": 117000.0, "mora_uf": ["4K", "6P"]},
        "San Jose 1111, CABA": {"reserva": 290000.0, "gasto_base": 59000.0, "mora_uf": ["5M"]},
        "Guayaquil 399, CABA": {"reserva": 850000.0, "gasto_base": 515000.0, "mora_uf": ["4K"]}
    }
    
    # Construcción automatizada de las variables y UFs específicas
    for nombre, datos in st.session_state.data_consorcios.items():
        datos["unidades"] = {uf: {"propietario": f"Propietario {uf}", "porcentaje": 0.20, "saldo": 12000.0 if uf in datos["mora_uf"] else 0.0} for uf in lista_ufs}
        datos["libro_diario"] = [{"Fecha": "2026-09-10", "Concepto": "Gastos Centrales Generales", "Monto": datos["gasto_base"], "Tipo": "Ordinario"}]

# Repositorio Histórico Global de Órdenes de Trabajo para permitir filtrado cruzado por Pantallas
if 'ordenes_globales' not in st.session_state:
    st.session_state.ordenes_globales = [
        {"Edificio": "Av. Corrientes 1234, CABA", "UF": "1A", "Tipo de Trabajo": "Plomería", "Detalle": "Filtración en caño central de agua", "Estado": "Solicitado"},
        {"Edificio": "Av. Corrientes 1234, CABA", "UF": "3J", "Tipo de Trabajo": "Albañilería", "Detalle": "Arreglo de revoques en patio", "Estado": "En Proceso"},
        {"Edificio": "Larrea 435, CABA", "UF": "3J", "Tipo de Trabajo": "Electricidad", "Detalle": "Falla de fase en disyuntor", "Estado": "Solicitado"},
        {"Edificio": "Larrea 435, CABA", "UF": "6P", "Tipo de Trabajo": "Plomería", "Detalle": "Revisión de colector pluvial", "Estado": "Pendiente"},
        {"Edificio": "Montevideo 891, CABA", "UF": "4K", "Tipo de Trabajo": "Albañilería", "Detalle": "Pintura de cochera común", "Estado": "En Proceso"},
        {"Edificio": "San Jose 1111, CABA", "UF": "5M", "Tipo de Trabajo": "Albañilería", "Detalle": "Fijación de baranda de balcón", "Estado": "Solicitado"},
        {"Edificio": "Guayaquil 399, CABA", "UF": "4K", "Tipo de Trabajo": "Electricidad", "Detalle": "Instalación de tablero de cocheras", "Estado": "En Proceso"},
        {"Edificio": "Guayaquil 399, CABA", "UF": "3J", "Tipo de Trabajo": "Plomería", "Detalle": "Filtración en losa radiante", "Estado": "Pendiente"}
    ]

PROVEEDORES = {"plomeria": [{"nombre": "Plomería Gas-An", "tel": "1144445555"}]}

# =====================================================================
# PANEL LATERAL (SIDEBAR DE CONTROL AUTOMATIZADO)
# =====================================================================
with st.sidebar:
    st.image("https://imgbox.com", use_container_width=True)
    st.title("Resilia_Condominios")
    st.caption("AI Swarm ERP Administration")
    st.markdown("---")
    
    # Control de Navegación de Pantallas del Negocio
    st.markdown("🎮 **Navegación del Sistema:**")
    pantalla_activa = st.radio("Seleccione Vista:", ["🏠 Panel General por Edificio", "🛠️ Abrir Órdenes de Trabajo"], index=0)
    
    st.markdown("---")
    # Selector Interactivo de Edificios (Aplica para la vista general)
    edificio_seleccionado = st.selectbox("Edificio Activo de Control", list(st.session_state.data_consorcios.keys()))
    st.info("CUIT: 30-11111111-9\n\nJurisdicción: Ley 941 CABA")

# Extracción reactiva indexada
consorcio_actual = st.session_state.data_consorcios[edificio_seleccionado]
unidades_actuales = consorcio_actual["unidades"]
libro_diario_actual = consorcio_actual["libro_diario"]

# =====================================================================
# PANTALLA 1: DASHBOARD GENERAL DEL EDIFICIO ACTIVO
# =====================================================================
if pantalla_activa == "🏠 Panel General por Edificio":
    st.title("🏢 Resilia_Condominios")
    st.markdown(f"Monitoreo activo sobre el consorcio: **{edificio_seleccionado}**")

    # MÓDULO DE INDICADORES DORADOS
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
        # Cuenta cuántas órdenes corresponden exclusivamente a este edificio activo
        ot_edificio = sum(1 for o in st.session_state.ordenes_globales if o["Edificio"] == edificio_seleccionado)
        st.metric(label="Ordenes de trabajo", value=str(ot_edificio))

    st.markdown("<br>", unsafe_allow_html=True)

    # SOLAPAS DEL CORE ADMINISTRATIVO
    tab_atencion, tab_contable, tab_prov = st.tabs([
        "💬 Centro de Atención Multicanal", 
        "📊 Prorrateo, Finanzas y Libro Diario", 
        "📋 Cartilla de Proveedores"
    ])

    with tab_atencion:
        st.subheader("📥 Recepción Automatizada de Mensajes (Ecosistema Multicanal)")
        col_input, col_output = st.columns([1, 1.2])
        with col_input:
            uf_sel = st.selectbox("Unidad Funcional Emisora", list(unidades_actuales.keys()))
            canal_sel = st.radio("Canal de Ingreso (Multicanal)", ["WhatsApp", "Portal Web", "Correo Electrónico"], horizontal=True)
            mensaje_custom = st.text_area("Cuerpo del Requerimiento:", value="Tengo una filtración en el baño, pierde un caño de agua.")
            procesar = st.button("🚀 Desplegar Enjambre de IA", use_container_width=True)
        with col_output:
            st.markdown("### ⚙️ Trazabilidad de Decisiones")
            if procesar:
                st.markdown(f'''<div class="agent-card"><div class="agent-title">🤖 Agente Front-Desk</div>Mensaje recibido por <b>{canal_sel}</b> de la UF {uf_sel}.</div>''', unsafe_allow_html=True)
                st.success("Orden procesada correctamente por el ecosistema de IA.")

    with tab_contable:


