import streamlit as st
import pandas as pd

# CONFIGURACIÓN HIGH-END DE LA INTERFAZ
st.set_page_config(
    page_title="Resil_IA Condominios",
    page_icon="https://imgbox.com",
    layout="wide"
)

# Inyección de CSS para forzar el fondo azul metalizado oscuro, paneles dorados y letra gigante
st.markdown("""
    <style>
        .main { background: radial-gradient(circle at top right, #0d1e3d 0%, #071126 100%); }
        h1 { color: #ffffff; font-family: sans-serif; font-weight: 900; letter-spacing: -1px; text-shadow: 0 0 20px rgba(56, 189, 248, 0.4); font-size: 2.8rem !important; }
        h2, h3 { color: #38bdf8; font-family: sans-serif; font-weight: 700; font-size: 2rem !important; }
        .stMarkdown p, p, label, .stRadio label { color: #e2e8f0; font-size: 1.3rem !important; line-height: 1.6 !important; }
        
        /* Título de la barra lateral achicado y estilizado en degradado dorado y rojo */
        [data-testid="stSidebar"] h1 {
            font-size: 1.35rem !important;
            font-weight: 900 !important;
            text-transform: uppercase !important;
            background: linear-gradient(135deg, #d4af37 0%, #ff4d4d 100%) !important;
            -webkit-background-clip: text !important;
            -webkit-text-fill-color: transparent !important;
            letter-spacing: 0.5px !important;
            margin-top: -5px !important;
            text-shadow: none !important;
        }
        
        /* Forzado de tamaño de letra GIGANTE para el contenido interno de todas las tablas */
        .stDataFrame td, .stDataFrame div, table, td, tr { 
            font-size: 1.5rem !important; 
            font-weight: 600 !important;
            color: #ffffff !important;
        }
        th, .stDataFrame th div { font-weight: 800 !important; color: #38bdf8 !important; font-size: 1.4rem !important; }

        /* Paneles de Métricas en Oro Líquido Flotante */
        div[data-testid="stMetric"] {
            background: linear-gradient(135deg, #d4af37 0%, #aa7c11 100%) !important;
            border-radius: 20px !important;
            padding: 22px !important;
            box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.6);
            border: 1px solid rgba(255, 255, 255, 0.2) !important;
        }
        div[data-testid="stMetric"] label { color: #0f172a !important; font-weight: 800 !important; font-size: 1.1rem !important; }
        div[data-testid="stMetric"] [data-testid="stMetricValue"] { color: #0b192c !important; font-weight: 900 !important; font-size: 2.4rem !important; }
        .stDataFrame, .stTable { background-color: rgba(30, 41, 59, 0.5); border-radius: 16px; padding: 10px; }
    </style>
""", unsafe_allow_html=True)

# BASE DE DATOS GLOBAL DE CONDOMINIOS ESTÁTICA
ESTADISTICAS_EDIFICIOS = {
    "Av. Corrientes 1234, CABA": {"reserva": 450000.0, "factor": 1.0, "mora": "1", "tasa": 4.5, "ots": "5"},
    "Larrea 435, CABA": {"reserva": 380000.0, "factor": 0.6, "mora": "2", "tasa": 5.0, "ots": "5"},
    "Montevideo 891, CABA": {"reserva": 620000.0, "factor": 0.8, "mora": "2", "tasa": 6.2, "ots": "5"},
    "San Jose 1111, CABA": {"reserva": 290000.0, "factor": 0.5, "mora": "1", "tasa": 3.8, "ots": "5"},
    "Guayaquil 399, CABA": {"reserva": 850000.0, "factor": 1.5, "mora": "1", "tasa": 7.5, "ots": "5"}
}

# CARTILLA REQUERIDA DE PROVEEDORES FICTICIOS ORGANIZADOS POR RUBRO
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

# TABLA REQUERIDA DE ÓRDENES DE TRABAJO EXACTA DEL EXCEL
TABLA_SOLICITADA_OT = [
    {"Edificio": "Avda. Corrientes 1234", "UF": "1A", "Trabajo": "Plomería", "Presupuesto Aprobado": "$ 250.000.-", "Fecha_Inicio": "01/05/26", "Fecha_Finaliz": "01/05/26"},
    {"Edificio": "Larrea 435", "UF": "3J", "Trabajo": "Albañilería", "Presupuesto Aprobado": "$ 390.000.-", "Fecha_Inicio": "07/06/26", "Fecha_Finaliz": "12/06/26"},
    {"Edificio": "Montevideo 891", "UF": "4K", "Trabajo": "Plomería", "Presupuesto Aprobado": "$ 120.000.-", "Fecha_Inicio": "08/09/26", "Fecha_Finaliz": "09/09/26"},
    {"Edificio": "San José 1111", "UF": "5M", "Trabajo": "Electricidad", "Presupuesto Aprobado": "$ 95.000.-", "Fecha_Inicio": "12/07/26", "Fecha_Finaliz": "12/07/26"},
    {"Edificio": "Guayaquil 399", "UF": "6P", "Trabajo": "Cerrajería", "Presupuesto Aprobado": "$ 180.000.-", "Fecha_Inicio": "15/08/26", "Fecha_Finaliz": "15/08/26"}
]

# INTERFAZ LATERAL (SIDEBAR CORPORATIVO CON TU LOGO FÉNIX LOCAL)
with st.sidebar:
    st.image("Resilia.jfif", use_container_width=True)
    st.title("Resil_IA Condominios")
    st.caption("AI Swarm ERP Platform v2.6")
    st.markdown("---")
    # RADIO SANEADO: CONTROL TOTAL DE FLUJO EN PANTALLA
    pantalla_activa = st.radio("Seleccione Módulo de Control:", ["📋 Dashboard y Contabilidad", "🔧 Órdenes de Trabajo de Campo"], index=0)
    st.markdown("---")
    edificio_seleccionado = st.selectbox("Edificio Activo de Control", list(ESTADISTICAS_EDIFICIOS.keys()))
    st.markdown("---")
    st.info("CUIT: 30-11111111-9\n\nJurisdicción: Ley 941 CABA")

consorcio_actual = ESTADISTICAS_EDIFICIOS[edificio_seleccionado]
f_cal = consorcio_actual["factor"]
tasa_act = consorcio_actual["tasa"]

# Listados financieros estructurados con nombres solicitados en letra gigante
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

# =====================================================================
# CONDICIONAL 1: MÓDULO DE CONTABILIDAD PRINCIPAL
# =====================================================================
if pantalla_activa == "📋 Dashboard y Contabilidad":
    # Banner GIF animado premium en alta resolución
    st.image("data:image/jpeg;base64,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", use_container_width=True)
    st.title("Panel Principal")
    st.markdown(f"Monitoreo analítico y flujos contables para el consorcio: **{edificio_seleccionado}**")

    m1, m2, m3, m4 = st.columns(4)
    with m1: st.metric(label="Total gastos del periodo", value=f"${total_g_calc:,.2f}")
    with m2: st.metric(label="Fondos de reserva", value=f"${consorcio_actual['reserva']:,.2f}")
    with m3: st.metric(label="UF en Mora", value=consorcio_actual['mora'])
    with m4: st.metric(label="Ordenes de trabajo", value=consorcio_actual['ots'])

    st.markdown("---")
    
    st.header("📊 Módulo Contable: Cuadro de Ingresos y Gastos")
    st.markdown("### 📥 Flujo de Ingresos Percibidos")
    st.dataframe(pd.DataFrame(ingresos_lista), use_container_width=True, hide_index=True)
    st.info(f"**Total Ingresos Registrados:** ${total_i_calc:,.2f}")
    
    st.markdown("### 📤 Flujo de Gastos Devengados")
    st.dataframe(pd.DataFrame(gastos_lista), use_container_width=True, hide_index=True)
    st.info(f"**Total Gastos Registrados:** ${total_g_calc:,.2f}")
    
    st.markdown("### 🧮 Liquidación Prorrateada por Departamento (Cuota Parte 20% Equitativo)")
    cuota_uf = total_g_calc / 5.0
    prorrateo_data = [{"Unidad Funcional": uf, "Concepto Liquidación": "Expensas Base Prorrateadas (20%)", "Total a Pagar ($)": f"$ {cuota_uf:,.2f}"} for uf in ["1A", "3J", "4K", "5M", "6P"]]
    st.dataframe(pd.DataFrame(prorrateo_data), use_container_width=True, hide_index=True)
    
    st.markdown("---")
    st.markdown("### 📈 Balance de Ejecución Mensual Neto")
    st.markdown(f"**Saldo Neto de Caja:** ${balance_neto:,.2f}")
    
    st.markdown("### 📊 Gráfico Comparativo Analítico (Balance de Caja)")
    df_chart = pd.DataFrame({"Flujo Financiero": ["Ingresos Totales", "Gastos Totales"], "Monto Acumulado ($)": [total_i_calc, total_g_calc]})
    st.bar_chart(data=df_chart, x="Flujo Financiero", y="Monto Acumulado ($)")

    st.markdown("---")
    st.header("📋 Cartilla Homologada de Proveedores")
    st.markdown("Nómina de prestadores ficticios autorizados (Plomeros, Electricistas, Cerrajeros, Albañiles):")
