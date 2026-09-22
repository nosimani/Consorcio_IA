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

# Inyección de CSS Avanzado para fondo azul metalizado oscuro, paneles dorados y sub-solapas celestes
st.markdown("""
    <style>
        .main { background-color: #0b192c; }
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

        /* Solapas Celestes Secundarias */
        .celeste-tabs [data-baseweb="tab-list"] { background-color: #0f172a !important; border: 1px solid #38bdf8 !important; }
        .celeste-tabs [data-baseweb="tab"] { color: #bae6fd !important; }
        .celeste-tabs [aria-selected="true"] { background-color: #38bdf8 !important; color: #0f172a !important; font-weight: 800 !important; }

        /* Tarjetas de los Agentes */
        .agent-card { background-color: #1e293b; padding: 24px; border-radius: 16px; border-left: 6px solid #38bdf8; margin-bottom: 18px; color: #f1f5f9; }
        .agent-title { font-size: 1.1rem; font-weight: 800; color: #ffffff; margin-bottom: 8px; }
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
    
    for nombre, datos in st.session_state.data_consorcios.items():
        datos["unidades"] = {uf: {"propietario": f"Propietario {uf}", "porcentaje": 0.20, "saldo": 12000.0 if uf in datos["mora_uf"] else 0.0} for uf in lista_ufs}
        datos["libro_diario"] = [{"Fecha": "2026-09-10", "Concepto": "Gastos Centrales Generales", "Monto": datos["gasto_base"], "Tipo": "Ordinario"}]

if 'ordenes_globales' not in st.session_state:
    st.session_state.ordenes_globales = [
        {"Edificio": "Av. Corrientes 1234, CABA", "UF": "1A", "Tipo de Trabajo": "Plomería", "Detalle": "Filtración en caño central de agua", "Estado": "Trabajos Solicitados"},
        {"Edificio": "Av. Corrientes 1234, CABA", "UF": "3J", "Tipo de Trabajo": "Albañilería", "Detalle": "Arreglo de revoques en patio", "Estado": "Trabajos en Proceso"},
        {"Edificio": "Larrea 435, CABA", "UF": "3J", "Tipo de Trabajo": "Electricidad", "Detalle": "Falla de fase en disyuntor", "Estado": "Trabajos Solicitados"},
        {"Edificio": "Larrea 435, CABA", "UF": "6P", "Tipo de Trabajo": "Plomería", "Detalle": "Revisión de colector pluvial", "Estado": "Trabajos Pendientes"}
    ]

# CARTILLA COMPLETA DE 5 PRESTADORES FICTICIOS PARA CADA UNO DE LOS 5 RUBROS SOLICITADOS
CARTILLA_PROVEEDORES = {
    "Electricistas": [
        "Seleccione un prestador...",
        "⚡ Electricidad Voltio - Tel: 11-7777-8888 (Ing. Carlos Benítez)",
        "⚡ Serviluz Express - Tel: 11-5555-9991 (Téc. Claudio Rossi)",
        "⚡ Electro-San Telmo - Tel: 11-4444-2222 (Inst. Darío Gómez)",
        "⚡ Lumina S.A. - Tel: 11-6666-4444 (Urgencias 24hs Consorcios)",
        "⚡ Instalaciones Alfa - Tel: 11-2222-1111 (Téc. Walter White)"
    ],
    "Plomeros": [
        "Seleccione un prestador...",
        "🚰 Plomería Gas-An - Tel: 11-4444-5555 (Mtro. Ángel López)",
        "🚰 Destapaciones Express - Tel: 11-3333-9999 (Juan Carlos)",
        "🚰 Hidro-Fix Palermo - Tel: 11-2222-8888 (Téc. Marcelo Díaz)",
        "🚰 Sanitarios Norte - Tel: 11-8888-1111 (Columnas y Colectores)",
        "🚰 AquaForce CABA - Tel: 11-7777-3333 (Bombas de Agua y Presión)"
    ],
    "Gasistas": [
        "Seleccione un prestador...",
        "🔥 Gasistas Matriculados Almagro - Tel: 11-2222-3333 (Mat. 45211)",
        "🔥 Sigas Soluciones - Tel: 11-6666-7777 (Pruebas de Hermeticidad)",
        "🔥 Artefactos Gas Hogar - Tel: 11-5555-4444 (Instalador Matriculado)",
        "🔥 Metrogas Certificados - Tel: 11-9999-8888 (Ing. Daniel Rossi)",
        "🔥 TermoControl Técnico - Tel: 11-3333-2222 (Calderas Centrales)"
    ],
    "Albañiles": [
        "Seleccione un prestador...",
        "🧱 Construcciones R&M - Tel: 11-3333-4444 (Mtro. Rubén Castro)",
        "🧱 Albañilería El Progreso - Tel: 11-5555-6666 (Of. Pedro Picapiedra)",
        "🧱 Estructuras Fuertes - Tel: 11-7777-2222 (Fachadas y Revoques)",
        "🧱 Revestimientos CABA - Tel: 11-8888-9999 (Colocación de Cerámicos)",
        "🧱 Soluciones en Mampostería - Tel: 11-4444-8888 (Of. Luis Herrera)"
    ],
    "Pintores": [
        "Seleccione un prestador...",
        "🎨 Pintores Asociados - Tel: 11-6666-1111 (Línea Consorcios Premium)",
        "🎨 FlexColor Revestimientos - Tel: 11-2222-5555 (Pintura de Altura)",
        "🎨 Pinceladas CABA - Tel: 11-4444-3333 (Of. Marcos Juárez)",
        "🎨 TodoObra Pinturas - Tel: 11-9999-7777 (Impermeabilización de Medianeras)",
        "🎨 ColorExpress - Tel: 11-8888-4444 (Interiores y Palieres Rápidos)"
    ],
    "Techistas": [
        "Seleccione un prestador...",
        "🏠 Techados Mar del Plata - Tel: 11-5555-2222 (Especialista en Tejas/Chapas)",
        "🏠 Membranas e Impermeabilizaciones - Tel: 11-7777-6666 (Soluciones Filtración)",
        "🏠 Cubiertas Protegidas - Tel: 11-3333-5555 (Ing. Néstor Kirchner)",
        "🏠 Techistas de Guardia CABA - Tel: 11-4444-9999 (Arreglos Post-Tormenta)",
        "🏠 Altura Confort - Tel: 11-2222-7777 (Limpieza y Zinguería de Canaletas)"
    ]
}

# =====================================================================
# PANEL LATERAL (SIDEBAR DE CONTROL AUTOMATIZADO)
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
        ot_edificio = sum(1 for o in st.session_state.ordenes_globales if o["Edificio"] == edificio_seleccionado)
        st.metric(label="Ordenes de trabajo", value=str(ot_edificio))

    st.markdown("<br>", unsafe_allow_html=True)

    tab_atencion, tab_contable, tab_prov = st.tabs([




