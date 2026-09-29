import streamlit as st
import pandas as pd

# CONFIGURACIÓN HIGH-END DE LA INTERFAZ
st.set_page_config(
    page_title="Resilia_Condominios",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inyección de CSS (Fondo azul metalizado oscuro original, paneles dorados y letra gigante de tablas)
st.markdown("""
    <style>
        .main { background: radial-gradient(circle at top right, #0d1e3d 0%, #071126 100%); }
        h1 { color: #ffffff !important; font-family: sans-serif; font-weight: 900; letter-spacing: -1px; text-shadow: 0 0 20px rgba(56, 189, 248, 0.4); font-size: 2.8rem !important; }
        h2, h3 { color: #38bdf8 !important; font-family: sans-serif; font-weight: 700; font-size: 2rem !important; }
        .stMarkdown p, p, label, .stRadio label { color: #e2e8f0; font-size: 1.3rem !important; line-height: 1.6 !important; }
        
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

        /* REQUERIMIENTO: Reducir el nombre RESILIA AGENCY en la barra lateral izquierda */
        [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2 {
            font-size: 1.1rem !important;
            text-align: center !important;
            color: #ffffff !important;
            font-weight: 800 !important;
            margin-top: 5px !important;
            margin-bottom: 5px !important;
        }
    </style>
""", unsafe_allow_html=True)

# BASE DE DATOS GLOBAL DE CONDOMINIOS ESTÁTICA ORIGINAL
ESTADISTICAS_EDIFICIOS = {
    "Av. Corrientes 1234, CABA": {"reserva": 450000.0, "factor": 1.0, "mora": "1", "tasa": 4.5, "ots": "5"},
    "Larrea 435, CABA": {"reserva": 380000.0, "factor": 0.6, "mora": "2", "tasa": 5.0, "ots": "5"},
    "Montevideo 891, CABA": {"reserva": 620000.0, "factor": 0.8, "mora": "2", "tasa": 6.2, "ots": "5"},
    "San Jose 1111, CABA": {"reserva": 290000.0, "factor": 0.5, "mora": "1", "tasa": 3.8, "ots": "5"},
    "Guayaquil 399, CABA": {"reserva": 850000.0, "factor": 1.5, "mora": "1", "tasa": 7.5, "ots": "5"}
}

# CARTILLA REQUERIDA DE PROVEEDORES FICTICIOS ORGANIZADOS POR RUBRO ORIGINAL
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

# TABLA REQUERIDA DE ÓRDENES DE TRABAJO EXACTA DEL EXCEL ORIGINAL
TABLA_SOLICITADA_OT = [
    {"Edificio": "Av. Corrientes 1234, CABA", "UF": "UF 01", "Trabajo": "Plomería", "Presupuesto Aprobado": "$ 250.000.-", "Fecha_Inicio": "01/05/26", "Fecha_Finaliz": "01/05/26", "Estado": "Realizado"},
    {"Edificio": "Larrea 435, CABA", "UF": "UF 03", "Trabajo": "Albañilería", "Presupuesto Aprobado": "$ 390.000.-", "Fecha_Inicio": "07/06/26", "Fecha_Finaliz": "12/06/26", "Estado": "En Proceso"},
    {"Edificio": "Montevideo 891, CABA", "UF": "UF 04", "Trabajo": "Plomería", "Presupuesto Aprobado": "$ 120.000.-", "Fecha_Inicio": "08/09/26", "Fecha_Finaliz": "09/09/26", "Estado": "Realizado"},
    {"Edificio": "San Jose 1111, CABA", "UF": "UF 05", "Trabajo": "Electricidad", "Presupuesto Aprobado": "$ 95.000.-", "Fecha_Inicio": "12/07/26", "Fecha_Finaliz": "12/07/26", "Estado": "Presupuestado"},
    {"Edificio": "Guayaquil 399, CABA", "UF": "UF 02", "Trabajo": "Cerrajería", "Presupuesto Aprobado": "$ 180.000.-", "Fecha_Inicio": "15/08/26", "Fecha_Finaliz": "15/08/26", "Estado": "En Proceso"}
]

# INTERFAZ LATERAL (SIDEBAR CORPORATIVO CON MÓDULOS DE CONTROL)
with st.sidebar:
    # REQUERIMIENTO: Logo del panel izquierdo más chico (width=110)
    st.markdown("<div style='text-align: center; width: 100%;'><style>[data-testid='stSidebar'] [data-testid='stImage'] {display: block; margin-left: auto; margin-right: auto;}</style></div>", unsafe_allow_html=True)
    st.image("Resilia.jfif", width=110) 
    # REQUERIMIENTO: Nombre RESILIA AGENCY más pequeño (estilizado mediante CSS de arriba)
    st.caption("AI Swarm ERP Platform v2.6")
    st.markdown("---")
    pantalla_activa = st.radio("Seleccione Módulo de Control:", ["📋 Dashboard y Contabilidad", "🔧 Órdenes de Trabajo de Campo"], index=0)
    st.markdown("---")
    edificio_seleccionado = st.selectbox("Edificio Activo de Control", list(ESTADISTICAS_EDIFICIOS.keys()))
    st.markdown("---")
    st.info("CUIT: 30-11111111-9\n\nJurisdicción: Ley 941 CABA")

consorcio_actual = ESTADISTICAS_EDIFICIOS[edificio_seleccionado]
f_cal = consorcio_actual["factor"]
tasa_act = consorcio_actual["tasa"]

# ====== ENCARGADO SUTERH CON LOS CALCULOS REQUERIDOS ======
neto_encargado = 1500000.0
bruto_referencial = neto_encargado / 0.805
aportes_suterh = bruto_referencial * 0.195
contribuciones_patronales = bruto_referencial * 0.255
total_cargas = aportes_suterh + contribuciones_patronales

# Listados financieros estructurados con los MONTOS FIJOS SOLICITADOS
ingresos_lista = [
    {"Ingresos": "ingresos por expensas", "Monto ($)": 5320000.0},
    {"Ingresos": "alquileres de locales", "Monto ($)": 3000000.0},
    {"Ingresos": "intereses por colocacion a plazo fijo", "Monto ($)": 14000.0 * f_cal * (tasa_act / 5.0)}
]
gastos_lista = [
    {"Gastos": "reparaciones", "Monto ($)": 45000.0 * f_cal},
    {"Gastos": "honorarios de administración", "Monto ($)": 35000.0 * f_cal},
    {"Gastos": "sueldo de encargado (NETO A COBRAR)", "Monto ($)": neto_encargado},
    {"Gastos": "cargas sociales suterh (aportes y contribuciones)", "Monto ($)": total_cargas},
    {"Gastos": "compra de articulos de limpieza", "Monto ($)": 12000.0 * f_cal},
    {"Gastos": "pagos luz", "Monto ($)": 18000.0 * f_cal},
    {"Gastos": "otros gastos", "Monto ($)": 7000.0 * f_cal}
]

total_i_calc = sum(x['Monto ($)'] for x in ingresos_lista)
total_g_calc = sum(x['Monto ($)'] for x in gastos_lista)
balance_neto = total_i_calc - total_g_calc

# REGLA ESTRUCTURAL DE COPROPIEDAD PARA EL PRORRATEO NATIVO PANDAS (INMUNE A ERRORES DE SINTAXIS)
uf_lista = ["UF 01", "UF 02", "UF 03", "UF 04", "UF 05"]
piso_lista = ["1° A", "1° B", "2° A", "2° B", "3° A"]
coef_lista = [0.35, 0.25, 0.18, 0.12, 0.10]

deuda_base_1 = 180000.0 if consorcio_actual["mora"] >= "1" else 0.0
deuda_base_2 = 220000.0 if consorcio_actual["mora"] == "2" else 0.0
deudas_lista = [0.0, deuda_base_1, deuda_base_2, 0.0, 0.0]

gastos_puros = [total_g_calc * c for c in coef_lista]
intereses_puros = [d * (tasa_act / 100.0) for d in deudas_lista]
totales_puros = [gastos_puros[i] + deudas_lista[i] + intereses_puros[i] for i in range(5)]

# REQUERIMIENTO: TÍTULO EN EL PANEL PRINCIPAL ARRIBA DE TODO DE COLOR ROJO FUEGO SEGURO
st.markdown("<h1 style='color: #ff3b30 !important; -webkit-text-fill-color: #ff3b30 !important; font-weight: 900; margin-bottom: 15px; margin-top: 0px;'>🏢 RESIL_IA CONDOMINIOS</h1>", unsafe_allow_html=True)

# EJECUCIÓN TOTALMENTE LINEAL CONDICIONAL
if pantalla_activa == "📋 Dashboard y Contabilidad":
    st.title("Panel Principal")
    st.markdown(f"Monitoreo analítico y flujos contables para el consorcio: **{edificio_seleccionado}**")

    # Filtrado dinámico de OTs del edificio seleccionado para las tarjetas de la pantalla
    ots_edificio_activo = [ot for ot in TABLA_SOLICITADA_OT if ot["Edificio"] == edificio_seleccionado]

    m1, m2, m3, m4 = st.columns(4)
    with m1: st.metric(label="Total gastos del periodo", value=f"${total_g_calc:,.2f}")
    with m2: st.metric(label="Fondos de reserva", value=f"${consorcio_actual['reserva']:,.2f}")
    with m3: st.metric(label="UF en Mora", value=consorcio_actual['mora'])
    with m4: st.metric(label="Ordenes de trabajo", value=str(len(ots_edificio_activo)))

    st.markdown("---")
    
    # SECCIÓN 1: CUADRO DE INGRESOS Y GASTOS ORIGINAL RESTAURADO
    st.header("📊 Módulo Contable: Cuadro de Ingresos y Gastos")
    
    st.markdown("### 📥 Flujo de Ingresos Percibidos")
    st.dataframe(pd.DataFrame(ingresos_lista), use_container_width=True, hide_index=True)
