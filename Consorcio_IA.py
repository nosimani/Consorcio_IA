import streamlit as st
import pandas as pd
import random
from datetime import datetime

st.set_page_config(page_title="Resilia_Condominios", page_icon="🏢", layout="wide", initial_sidebar_state="expanded")

# Inyección de CSS de Vanguardia Estética con Letras Ultra Agrandadas
st.markdown("""
    <style>
        .main { background: radial-gradient(circle at top right, #0d1e3d 0%, #071126 100%); }
        h1 { color: #ffffff; font-family: sans-serif; font-weight: 900; font-size: 2.8rem !important; text-shadow: 0 0 20px rgba(56, 189, 248, 0.4); }
        h2, h3 { color: #38bdf8; font-family: sans-serif; font-weight: 700; font-size: 2rem !important; }
        .stMarkdown p, p, label, .stRadio label { color: #e2e8f0; font-size: 1.3rem !important; line-height: 1.6 !important; }
        .stDataFrame td, .stDataFrame div, table, td, tr { font-size: 1.5rem !important; font-weight: 600 !important; color: #ffffff !important; }
        th, .stDataFrame th div { font-weight: 800 !important; color: #38bdf8 !important; font-size: 1.4rem !important; }
        div[data-testid="stMetric"] { background: linear-gradient(135deg, #d4af37 0%, #aa7c11 100%) !important; border-radius: 20px !important; padding: 22px !important; box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.6); border: 1px solid rgba(255, 255, 255, 0.2) !important; }
        div[data-testid="stMetric"] label { color: #0f172a !important; font-weight: 800 !important; font-size: 1.1rem !important; }
        div[data-testid="stMetric"] [data-testid="stMetricValue"] { color: #0b192c !important; font-weight: 900 !important; font-size: 2.4rem !important; }
        .stTabs [data-baseweb="tab-list"] { gap: 12px; background-color: #1e293b; padding: 8px; border-radius: 12px; }
        .stTabs [data-baseweb="tab"] { background-color: transparent; border: none !important; padding: 14px 28px; border-radius: 8px; font-weight: 800; color: #94a3b8; font-size: 1.3rem !important; }
        .stTabs [aria-selected="true"] { background: linear-gradient(135deg, #0284c7 0%, #0369a1 100%) !important; color: #FFFFFF !important; box-shadow: 0 0 15px rgba(56, 189, 248, 0.4); }
        .agent-card { background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%); padding: 24px; border-radius: 16px; border-left: 6px solid #38bdf8; margin-bottom: 20px; color: #f1f5f9; }
        .agent-title { font-size: 1.3rem; font-weight: 900; color: #ffffff; text-transform: uppercase; }
        .stDataFrame, .stTable { background-color: rgba(30, 41, 59, 0.5); border-radius: 16px; padding: 10px; }
    </style>
""", unsafe_allow_html=True)

if "tasas_mora" not in st.session_state:
    st.session_state.tasas_mora = {"Av. Corrientes 1234, CABA": 4.5, "Larrea 435, CABA": 5.0, "Montevideo 891, CABA": 6.2, "San Jose 1111, CABA": 3.8, "Guayaquil 399, CABA": 7.5}

ESTADISTICAS_EDIFICIOS = {
    "Av. Corrientes 1234, CABA": {"reserva": 450000.0, "factor": 1.0, "mora": "1"},
    "Larrea 435, CABA": {"reserva": 380000.0, "factor": 0.6, "mora": "2"},
    "Montevideo 891, CABA": {"reserva": 620000.0, "factor": 0.8, "mora": "2"},
    "San Jose 1111, CABA": {"reserva": 290000.0, "factor": 0.5, "mora": "1"},
    "Guayaquil 399, CABA": {"reserva": 850000.0, "factor": 1.5, "mora": "1"}
}

# LISTADO FICTICIO COMPLETO Y EXCLUSIVO REQUERIDO POR EL USUARIO SEPARADO POR RUBROS
DATOS_CARTILLA_PROVEEDORES = [
    {"Rubro": "Plomería", "Prestador": "🚰 Caños y Sanitarios Express", "CUIT": "30-55489712-4", "Teléfono": "11-4895-1234", "Zona de Atención": "CABA Centro"},
    {"Rubro": "Plomería", "Prestador": "🚰 Ingeniería Hidráulica Sur", "CUIT": "33-66985214-9", "Teléfono": "11-3564-9871", "Zona de Atención": "CABA Norte"},
    {"Rubro": "Electricidad", "Prestador": "⚡ El Fusible Matriculado", "CUIT": "20-14896532-1", "Teléfono": "11-5478-6532", "Zona de Atención": "Toda CABA"},
    {"Rubro": "Electricidad", "Prestador": "⚡ Conexiones Seguras Palermo", "CUIT": "27-33659874-2", "Teléfono": "11-6985-3214", "Zona de Atención": "CABA Norte"},
    {"Rubro": "Cerrajería", "Prestador": "🔑 Llaves Fénix 24hs", "CUIT": "23-45896521-8", "Teléfono": "11-2365-9847", "Zona de Atención": "Urgencias CABA"},
    {"Rubro": "Cerrajería", "Prestador": "🔑 Blindajes y Cerraduras Pro", "CUIT": "30-71458962-3", "Teléfono": "11-4125-3698", "Zona de Atención": "CABA Oeste"},
    {"Rubro": "Albañilería", "Prestador": "🧱 Constructora San José", "CUIT": "30-88547612-5", "Teléfono": "11-5541-2369", "Zona de Atención": "Toda CABA"},
    {"Rubro": "Albañilería", "Prestador": "🧱 Refacciones Integrales Baires", "CUIT": "20-99653214-7", "Teléfono": "11-3254-7896", "Zona de Atención": "CABA Sur"}
]

TABLA_SOLICITADA_OT = [
    {"Edificio": "Avda. Corrientes 1234", "UF": "1A", "Trabajo": "Plomería", "Presupuesto Aprobado": "$ 250.000.-", "Fecha_Inicio": "01/05/26", "Fecha_Finaliz": "01/05/26"},
    {"Edificio": "Larrea 435", "UF": "3J", "Trabajo": "Albañilería", "Presupuesto Aprobado": "$ 390.000.-", "Fecha_Inicio": "07/06/26", "Fecha_Finaliz": "12/06/26"},
    {"Edificio": "Montevideo 891", "UF": "4K", "Trabajo": "Plomería", "Presupuesto Aprobado": "$ 120.000.-", "Fecha_Inicio": "08/09/26", "Fecha_Finaliz": "09/09/26"},
    {"Edificio": "San José 1111", "UF": "5M", "Trabajo": "Electricidad", "Presupuesto Aprobado": "$ 95.000.-", "Fecha_Inicio": "12/07/26", "Fecha_Finaliz": "12/07/26"},
    {"Edificio": "Guayaquil 399", "UF": "6P", "Trabajo": "Cerrajería", "Presupuesto Aprobado": "$ 180.000.-", "Fecha_Inicio": "15/08/26", "Fecha_Finaliz": "15/08/26"}
]

if 'ordenes_simuladas' not in st.session_state: st.session_state.ordenes_simuladas = []

with st.sidebar:
    st.image("https://imgbox.com", use_container_width=True)
    st.title("Resilia_Condominios")
    st.caption("AI Swarm ERP Platform v2.6")
    st.markdown("---")
    pantalla_activa = st.radio("Seleccione Vista:", ["Panel General por Edificio", "Abrir Ordenes de Trabajo"], index=0)
    st.markdown("---")
    edificio_seleccionado = st.selectbox("Edificio Activo de Control", list(ESTADISTICAS_EDIFICIOS.keys()))
    st.markdown("---")
    st.info("CUIT: 30-11111111-9\n\nJurisdicción: Ley 941 CABA")
    
    st.markdown("<br><br>", unsafe_allow_html=True)
    if st.button("⚠️ Resetear Historial Simulador IA", use_container_width=True):
        st.session_state.ordenes_simuladas = []
        st.rerun()

consorcio_actual = ESTADISTICAS_EDIFICIOS[edificio_seleccionado]
f_cal = consorcio_actual["factor"]
tasa_act = st.session_state.tasas_mora[edificio_seleccionado]

ingresos_lista = [
    {"Ingresos": "ingresos por expensas", "Monto ($)": 320000.0 * f_cal},
    {"Ingresos": "alquileres de locales", "Monto ($)": 85000.0 * (1.0 if f_cal >= 0.8 else 0.0)},
    {"Ingresos": "intereses por colocacion a plazo fijo", "Monto ($)": 14000.0 * f_cal * (tasa_act / 5.0)}
]
gastos_lista = [
    {"Gastos": "reparaciones", "Monto ($)": 45000.0 * f_cal},
    {"Gastos": "honorarios de administración", "Monto ($)": 35000.0 * f_cal},
    {"Gastos": "sueldo de encargado", "Monto ($)": 250000.0 * (1.0 if f_cal >= 0.7 else 0.0)},
    {"Gastos": "compra de articulos de limpieza", "Monto ($)": 12000.0 * f_cal},
    {"Gastos": "pagos luz", "Monto ($)": 18000.0 * f_cal},
    {"Gastos": "otros gastos", "Monto ($)": 7000.0 * f_cal}
]

total_i_calc = sum(x['Monto ($)'] for x in ingresos_lista)
total_g_calc = sum(x['Monto ($)'] for x in gastos_lista)
balance_neto = total_i_calc - total_g_calc

if pantalla_activa == "Panel General por Edificio":
    st.title("🏢 Resilia_Condominios")
    st.markdown(f"Monitoreo analítico activo sobre el consorcio: **{edificio_seleccionado}**")

    m1, m2, m3, m4 = st.columns(4)
    with m1: st.metric(label="Total gastos del periodo", value=f"${total_g_calc:,.2f}")
    with m2: st.metric(label="Fondos de reserva", value=f"${consorcio_actual['reserva']:,.2f}")
    with m3: st.metric(label="UF en Mora", value=consorcio_actual['mora'])
    with m4: st.metric(label="Ordenes de trabajo", value=str(len(TABLA_SOLICITADA_OT) + len(st.session_state.ordenes_simuladas)))

    st.markdown("<br>", unsafe_allow_html=True)
    tab_atencion, tab_contable, tab_prov = st.tabs(["Centro de Atencion Multicanal", "Cuadro de Ingresos y Gastos", "Cartilla de Proveedores"])

    with tab_atencion:
        st.subheader("📥 Recepción Automatizada Multicanal")
        uf_sel = st.selectbox("Unidad Funcional Emisora", ["1A", "3J", "4K", "5M", "6P"])
        canal_sel = st.radio("Canal de Ingreso", ["WhatsApp", "Portal Web", "Correo Electrónico"], horizontal=True)
        tipo_incidente = st.selectbox("Tipo de Incidencia Semántica:", ["Plomería", "Cerrajería", "Electricidad", "Gas"])
        mensaje_custom = st.text_area("Cuerpo del Requerimiento:", value=f"Se desperfectó {tipo_incidente.lower()} en la UF {uf_sel}.", key="atencion_text")
        if st.button("🚀 Desplegar Enjambre de IA", use_container_width=True):
            st.markdown(f'''<div class="agent-card"><div class="agent-title">🤖 Front-Desk</div>Mensaje recibido por <b>{canal_sel}</b>.</div>''', unsafe_allow_html=True)
            costo_s = round(random.uniform(9000, 25000), 2)
            st.session_state.ordenes_simuladas.append({"Edificio": str(edificio_seleccionado), "UF": uf_sel, "Trabajo": tipo_incidente, "Presupuesto Aprobado": f"$ {costo_s:,.2f}", "Fecha_Inicio": datetime.now().strftime("%d/%m/%y"), "Fecha_Finaliz": datetime.now().strftime("%d/%m/%y")})
            st.success("¡Base de datos sincronizada!")

    with tab_contable:
        st.subheader("📊 Cuadro de Ingresos y Gastos")
        tasa_seleccionada = st.slider("Ajustar Tasa de Interés por Mora Consorcial (% Mensual):", 0.0, 15.0, float(tasa_act), 0.5)
        st.session_state.tasas_mora[edificio_seleccionado] = tasa_seleccionada
        
        st.markdown("### 📥 Flujo de Ingresos Percibidos")
        st.dataframe(pd.DataFrame(ingresos_lista), use_container_width=True, hide_index=True)
        
        st.markdown("### 📤 Flujo de Gastos Devengados")
