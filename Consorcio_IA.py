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
                /* Reducir el tamaño del título en el sidebar */
        [data-testid="stSidebar"] h1 {
            font-size: 1.6rem !important;
            text-align: center !important;
            margin-top: 5px !important;
        }
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
    st.image("Resilia.jfif", width=150)
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
st.markdown("""
    <div style="display: flex; align-items: center; gap: 15px; margin-top: 10px; margin-bottom: 15px;">
        <!-- ICONO INSTITUCIONAL DE ADMINISTRACIÓN (DIRECCIÓN DE IMAGEN CONTROLADA) -->
        <img src="https://icons8.com" width="50" style="filter: drop-shadow(0 0 10px rgba(212,175,55,0.8));">
        
        <!-- TEXTO FORZADO EN ROJO FUEGO CON CONTORNO Y RELIEVE EN ORO LÍQUIDO -->
        <span style="
            margin: 0;
            font-size: 2.6rem !important;
            font-weight: 900 !important;
            font-family: sans-serif;
            letter-spacing: -1px;
            color: #ff3b30 !important;
            -webkit-text-fill-color: #ff3b30 !important;
            text-shadow: 0 0 12px rgba(212, 175, 55, 0.9), 2px 2px 0px #aa7c11, -1px -1px 0px #aa7c11, 1px -1px 0px #aa7c11, -1px 1px 0px #aa7c11;
        ">RESIL_IA CONDOMINIOS</span>
    </div>
""", unsafe_allow_html=True)
""", unsafe_allow_html=True)
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

    # =========================================================================================
# LÓGICA DE CONTROL CONTINUA: SEPARACIÓN DE PANTALLAS SEGÚN EL SIDEBAR
# =========================================================================================

# NOTA: Para que este bloque funcione con tu estructura actual, buscá más arriba en tu archivo
# donde definiste las tablas de "ingresos_lista" y "gastos_lista" y envolvelas bajo este condicional IF:
# (Si preferís dejarlo simple y que todo cargue junto sin condicionales, pegá esto directo abajo de la línea 159):

st.markdown("---")
st.header("🔧 Sección Operativa: Control de Órdenes de Trabajo")
st.markdown(f"Monitoreo de incidentes activos y prestadores asignados para el consorcio seleccionado.")

# 1. CUADROS INDIVIDUALES SEGMENTADOS POR UNIDAD FUNCIONAL (NATIVOS Y ULTRA-ESTABLES)
st.subheader("🏢 Estado Operativo por Unidad Funcional")

# Filtramos las órdenes de trabajo para que solo aparezcan las que corresponden al edificio activo
# Buscamos coincidencias de texto simples para evitar errores de escritura en las variables
ots_filtradas = [
    ot for ot in TABLA_SOLICITADA_OT 
    if edificio_seleccionado.split(",")[0].strip().lower() in ot["Edificio"].lower()
]

if ots_filtradas:
    # Creamos 3 columnas nativas para distribuir los cuadros en la pantalla sin colapsar el CSS
    columnas_uf = st.columns(3)
    for idx, ot in enumerate(ots_filtradas):
        with columnas_uf[idx % 3]:
            # Contenedor con borde nativo para simular el cuadro de cada departamento
            with st.container(border=True):
                st.markdown(f"### 🏢 Departamento: {ot['UF']}")
                st.markdown(f"**Trabajo Requerido:** {ot['Trabajo']}")
                st.markdown(f"**Presupuesto:** {ot['Presupuesto Aprobado']}")
                st.markdown(f"**Plazo Inicial:** {ot['Fecha_Inicio']} | **Fin:** {ot['Fecha_Finaliz']}")
                
                # Asignamos un estado visual dinámico según el rubro para control interno
                if "Plomería" in ot["Trabajo"]:
                    st.success("🟢 Estado: Realizado / Terminado")
                elif "Albañilería" in ot["Trabajo"]:
                    st.info("🔵 Estado: En Proceso de Ejecución")
                else:
                    st.warning("🟡 Estado: Presupuestado / Pendiente")
else:
    st.info("No se registran Órdenes de Trabajo (OT) activas para este consorcio en el periodo corriente.")

st.markdown("---")

# 2. CARTILLA OBLIGATORIA DE PROVEEDORES HOMOLOGADOS
st.subheader("📜 Cartilla de Prestadores de Servicio Matriculados")
st.markdown("Nómina autorizada de profesionales independientes con CUIT validado para el ingreso a los edificios:")
st.dataframe(pd.DataFrame(DATOS_CARTILLA_PROVEEDORES), use_container_width=True, hide_index=True)

st.markdown("---")

# 3. PLANILLA DE AUDITORÍA GENERAL (HISTÓRICO COMPLETO)
st.subheader("📋 Registro Central de Órdenes de Trabajo (Histórico)")
st.markdown("Bitácora contable de todas las reparaciones liquidadas en la plataforma:")
st.dataframe(pd.DataFrame(TABLA_SOLICITADA_OT), use_container_width=True, hide_index=True)
