import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

# ==========================================
# CONFIGURACIÓN GENERAL DE LA PÁGINA
# ==========================================
st.set_page_config(
    page_title="Consorcio IA - Gestión Inteligente",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos CSS personalizados
st.markdown("""
<style>
    .main-title {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1E3A8A;
        margin-bottom: 0.5rem;
    }
    .sub-title {
        font-size: 1.1rem;
        color: #4B5563;
        margin-bottom: 1.5rem;
    }
    .metric-card {
        background-color: #F3F4F6;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #2563EB;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# DATOS DE PRUEBA / SIMULACIÓN
# ==========================================
@st.cache_data
def cargar_datos_demo():
    np.random.seed(42)
    unidades = [f"U.F. {i:02d} - Dpto {1+(i//4)}{(chr(65+i%4))}" for i in range(1, 21)]
    propietarios = [f"Propietario {i}" for i in range(1, 21)]
    
    deuda_al_dia = np.random.choice([0, 0, 0, 15000, 25000], size=20)
    deuda_30 = np.random.choice([0, 0, 0, 0, 35000, 42000], size=20)
    deuda_60 = np.random.choice([0, 0, 0, 0, 0, 55000], size=20)
    deuda_90_mas = np.random.choice([0, 0, 0, 0, 0, 120000], size=20)
    
    df_aging = pd.DataFrame({
        'Unidad': unidades,
        'Propietario': propietarios,
        'Al Día ($)': deuda_al_dia,
        '30 Días ($)': deuda_30,
        '60 Días ($)': deuda_60,
        '90+ Días ($)': deuda_90_mas,
    })
    df_aging['Total Deuda ($)'] = df_aging[['Al Día ($)', '30 Días ($)', '60 Días ($)', '90+ Días ($)']].sum(axis=1)
    
    rubros = ['Mantenimiento Ascensores', 'Limpieza y Sum.', 'Seguridad / Portería', 'Servicios Públicos (Luz/Agua)', 'Reparaciones Estructurales', 'Honorarios Admin']
    presupuesto_mes = [250000, 180000, 650000, 210000, 150000, 200000]
    gastos_reales = [380000, 185000, 650000, 290000, 140000, 200000]
    
    df_gastos = pd.DataFrame({
        'Rubro': rubros,
        'Presupuestado ($)': presupuesto_mes,
        'Ejecutado ($)': gastos_reales,
    })
    df_gastos['Desvío ($)'] = df_gastos['Ejecutado ($)'] - df_gastos['Presupuestado ($)']
    df_gastos['Desvío (%)'] = (df_gastos['Desvío ($)'] / df_gastos['Presupuestado ($)']) * 100
    
    df_facturas = pd.DataFrame([
        {'ID': 'FAC-1001', 'Proveedor': 'Elevadores SRL', 'CUIT': '30-11223344-5', 'Monto ($)': 190000, 'Fecha': '2026-09-05', 'Rubro': 'Mantenimiento Ascensores', 'Estado': 'Normal'},
        {'ID': 'FAC-1002', 'Proveedor': 'Elevadores SRL', 'CUIT': '30-11223344-5', 'Monto ($)': 190000, 'Fecha': '2026-09-05', 'Rubro': 'Mantenimiento Ascensores', 'Estado': 'DUPLICADO DETECTADO'},
        {'ID': 'FAC-1003', 'Proveedor': 'Luz y Fuerza SA', 'CUIT': '30-99887766-1', 'Monto ($)': 290000, 'Fecha': '2026-09-10', 'Rubro': 'Servicios Públicos (Luz/Agua)', 'Estado': 'Normal'},
        {'ID': 'FAC-1004', 'Proveedor': 'Limpieza Total', 'CUIT': '30-55443322-9', 'Monto ($)': 185000, 'Fecha': '2026-09-12', 'Rubro': 'Limpieza y Sum.', 'Estado': 'Normal'},
    ])
    
    return df_aging, df_gastos, df_facturas

df_aging, df_gastos, df_facturas = cargar_datos_demo()

# ==========================================
# BARRA LATERAL (NAVEGACIÓN)
# ==========================================
st.sidebar.title("🏢 Consorcio IA")
st.sidebar.caption("Plataforma Inteligente de Administración")

opcion_menu = st.sidebar.radio(
    "Seleccione un Módulo:",
    [
        "1. Panel de Ratios y Aging",
        "2. Alertas de Desvíos y Duplicados",
        "3. Proyección y Simulador de Escenarios",
        "4. Lectura Automática de Facturas (OCR)",
        "5. Predicción de Mora",
        "6. Hoja de Ruta y Análisis Competitivo"
    ]
)

st.sidebar.divider()
st.sidebar.info("💡 **Demo Interactiva**: Módulo cargado con datos de demostración.")

# ==========================================
# MÓDULO 1: RATIOS Y AGING
# ==========================================
if opcion_menu == "1. Panel de Ratios y Aging":
    st.markdown('<p class="main-title">📊 Panel de Ratios Financieros y Aging de Deuda</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-title">Indicadores clave de cobrabilidad, morosidad y cobertura de reserva del consorcio.</p>', unsafe_allow_html=True)
    
    expensas_totales_emitidas = 2500000
    total_recaudado = 2150000
    cobrabilidad_pct = (total_recaudado / expensas_totales_emitidas) * 100
    morosidad_pct = 100 - cobrabilidad_pct
    
    fondo_reserva_actual = 5400000
    gasto_promedio_mensual = 1800000
    meses_fondo_reserva = fondo_reserva_actual / gasto_promedio_mensual
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Cobrabilidad del Mes", f"{cobrabilidad_pct:.1f}%", "+2.3% vs mes anterior")
    with col2:
        st.metric("Tasa de Morosidad", f"{morosidad_pct:.1f}%", "-2.3% mejora", delta_color="normal")
    with col3:
        st.metric("Fondo de Reserva", f"${fondo_reserva_actual:,.0f}")
    with col4:
        st.metric("Fondo en Cobertura", f"{meses_fondo_reserva:.1f} meses", "Meta: >= 2.0 meses")
    
    st.divider()
    
    col_g1, col_g2 = st.columns([1, 1])
    
    with col_g1:
        st.subheader("📌 Composición del Aging de Deuda")
        totales_aging = {
            'Al Día': df_aging['Al Día ($)'].sum(),
            '30 Días': df_aging['30 Días ($)'].sum(),
            '60 Días': df_aging['60 Días ($)'].sum(),
            '90+ Días': df_aging['90+ Días ($)'].sum()
        }
        fig_pie = px.pie(
            names=list(totales_aging.keys()),
            values=list(totales_aging.values()),
            hole=0.4,
            color_discrete_sequence=px.colors.qualitative.Set2
        )
        st.plotly_chart(fig_pie, use_container_width=True)
        
    with col_g2:
        st.subheader("📉 Deuda Acumulada por Tramo ($)")
        df_tramo = pd.DataFrame(list(totales_aging.items()), columns=['Tramo', 'Monto ($)'])
        fig_bar = px.bar(df_tramo, x='Tramo', y='Monto ($)', color='Tramo', text_auto=',.0f')
        st.plotly_chart(fig_bar, use_container_width=True)
        
    st.subheader("📋 Detalle de Unidades Morosas")
    df_morosos = df_aging[df_aging['Total Deuda ($)'] > 0]
    st.dataframe(df_morosos, use_container_width=True)

# ==========================================
# MÓDULO 2: ALERTAS DE DESVÍOS Y DUPLICADOS
# ==========================================
elif opcion_menu == "2. Alertas de Desvíos y Duplicados":
    st.markdown('<p class="main-title">🚨 Alertas de Desvíos en Gastos y Duplicados</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-title">Monitoreo automático de sobrecostos presupuestarios y comprobantes repetidos.</p>', unsafe_allow_html=True)
    
    desvios_criticos = df_gastos[df_gastos['Desvío (%)'] > 15]
    if not desvios_criticos.empty:
        for idx, row in desvios_criticos.iterrows():
            st.warning(f"⚠️ **Alerta de Sobrecosto en '{row['Rubro']}'**: El gasto superó lo presupuestado en un **{row['Desvío (%)']:.1f}%** (${row['Desvío ($)']:,.0f} de exceso).")
    
    st.divider()
    
    col1, col2 = st.columns([1.2, 1])
    
    with col1:
        st.subheader("📊 Comparativo Presupuesto vs Ejecutado")
        fig_gastos = go.Figure(data=[
            go.Bar(name='Presupuestado', x=df_gastos['Rubro'], y=df_gastos['Presupuestado ($)'], marker_color='#93C5FD'),
            go.Bar(name='Ejecutado', x=df_gastos['Rubro'], y=df_gastos['Ejecutado ($)'], marker_color='#1E40AF')
        ])
        fig_gastos.update_layout(barmode='group', xaxis_tickangle=-30)
        st.plotly_chart(fig_gastos, use_container_width=True)
        
    with col2:
        st.subheader("🔍 Facturas Duplicadas Detectadas")
        facturas_dup = df_facturas[df_facturas['Estado'] == 'DUPLICADO DETECTADO']
        if not facturas_dup.empty:
            st.error(f"Se han encontrado {len(facturas_dup)} comprobante(s) duplicado(s):")
            st.dataframe(facturas_dup[['ID', 'Proveedor', 'CUIT', 'Monto ($)', 'Fecha']], use_container_width=True)
        else:
            st.success("No se detectaron facturas duplicadas.")

# ==========================================
# MÓDULO 3: PROYECCIÓN Y SIMULADOR
# ==========================================
elif opcion_menu == "3. Proyección y Simulador de Escenarios":
    st.markdown('<p class="main-title">📈 Proyección de Gastos y Simulador de Escenarios</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-title">Simulación del impacto de la inflación y cuotas extraordinarias en la reserva.</p>', unsafe_allow_html=True)
    
    col_sim, col_res = st.columns([1, 1.2])
    
    with col_sim:
        st.subheader("⚙️ Parámetros del Escenario")
        inflacion_mensual = st.slider("Inflación Estimada Mensual (%)", 0.0, 15.0, 4.0, 0.5)
        aumento_expensas = st.slider("Aumento Programado de Expensas (%)", 0.0, 30.0, 5.0, 1.0)
        meses_proyeccion = st.selectbox("Plazo de Proyección (Meses)", [3, 6, 12], index=1)
        cuota_extraordinaria = st.number_input("Cuota Extraordinaria por Unidad ($)", value=0, step=5000)
        
    meses = [f"Mes {i+1}" for i in range(meses_proyeccion)]
    gasto_base = 1800000
    ingreso_base = 2150000 + (cuota_extraordinaria * 20)
    
    gastos_proyectados = []
    ingresos_proyectados = []
    fondo_reserva_proyectado = []
    
    fondo_acum = 5400000
    g_act = gasto_base
    i_act = ingreso_base
    
    for _ in range(meses_proyeccion):
        g_act *= (1 + inflacion_mensual / 100)
        i_act *= (1 + aumento_expensas / 100)
        superavit = i_act - g_act
        fondo_acum += superavit
        
        gastos_proyectados.append(g_act)
        ingresos_proyectados.append(i_act)
        fondo_reserva_proyectado.append(fondo_acum)
        
    with col_res:
        st.subheader("📉 Evolución del Fondo de Reserva")
        df_proy = pd.DataFrame({
            'Mes': meses,
            'Ingresos Proyectados ($)': ingresos_proyectados,
            'Gastos Proyectados ($)': gastos_proyectados,
            'Fondo Reserva ($)': fondo_reserva_proyectado
        })
        
        fig_proy = px.line(df_proy, x='Mes', y=['Ingresos Proyectados ($)', 'Gastos Proyectados ($)', 'Fondo Reserva ($)'], markers=True)
        st.plotly_chart(fig_proy, use_container_width=True)
        
    st.divider()
    if fondo_reserva_proyectado[-1] < 0:
        st.error("⚠️ **ADVERTENCIA**: Con estos parámetros, el fondo de reserva resultará **DEFICITARIO** en el plazo estimado.")
    else:
        st.success(f"✅ Fondo de Reserva estimado al finalizar el período: **${fondo_reserva_proyectado[-1]:,.0f}**.")

# ==========================================
# MÓDULO 4: LECTURA AUTOMÁTICA DE FACTURAS (OCR)
# ==========================================
elif opcion_menu == "4. Lectura Automática de Facturas (OCR)":
    st.markdown('<p class="main-title">📄 Lectura Automática de Facturas (OCR con IA)</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-title">Carga y extracción automática de datos desde facturas digitalizadas.</p>', unsafe_allow_html=True)
    
    uploaded_file = st.file_uploader("Arrastre o seleccione la factura (PDF / PNG / JPG)", type=['pdf', 'png', 'jpg', 'jpeg'])
    
    col_up, col_ocr = st.columns([1, 1])
    
    with col_up:
        if uploaded_file is not None:
            st.success(f"Archivo subido: **{uploaded_file.name}**")
        else:
            st.info("👆 Cargue un archivo o ejecute la simulación de prueba.")
            
        if st.button("🚀 Simular Procesamiento OCR"):
            st.session_state['ocr_demo'] = True
            
    with col_ocr:
        if st.session_state.get('ocr_demo', False) or uploaded_file is not None:
            st.subheader("🤖 Datos Extraídos por IA:")
            
            factura_extraida = {
                "Proveedor": "Ascensores y Servicios SRL",
                "CUIT": "30-71889900-4",
                "Tipo Comprobante": "Factura B",
                "Nro Comprobante": "0004-00012894",
                "Fecha Emisión": "2026-10-02",
                "Monto Total ($)": 215000.00,
                "Rubro Asignado": "Mantenimiento Ascensores",
                "Confianza IA": "98.4%"
            }
            
            for k, v in factura_extraida.items():
                st.write(f"**{k}:** {v}")
                
            if st.button("✅ Confirmar e Ingresar a Gastos"):
                st.success("¡Comprobante contabilizado con éxito!")

# ==========================================
# MÓDULO 5: PREDICCIÓN DE MORA
# ==========================================
elif opcion_menu == "5. Predicción de Mora":
    st.markdown('<p class="main-title">🔮 Predicción Preventiva de Mora</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-title">Scoring predictivo de riesgo de atraso en expensas por unidad.</p>', unsafe_allow_html=True)
    
    df_pred = df_aging[['Unidad', 'Propietario', 'Total Deuda ($)']].copy()
    np.random.seed(101)
    df_pred['Probabilidad de Mora Próximo Mes (%)'] = np.random.randint(5, 85, size=len(df_pred))
    
    def nivel_riesgo(pct):
        if pct > 60:
            return 'Alto 🔴'
        elif pct > 30:
            return 'Medio 🟡'
        return 'Bajo 🟢'
        
    df_pred['Nivel de Riesgo'] = df_pred['Probabilidad de Mora Próximo Mes (%)'].apply(nivel_riesgo)
    df_pred = df_pred.sort_values(by='Probabilidad de Mora Próximo Mes (%)', ascending=False)
    
    st.subheader("🎯 Scoring Preventivo por Unidad")
    st.dataframe(df_pred, use_container_width=True)
    
    fig_risk = px.histogram(df_pred, x='Nivel de Riesgo', color='Nivel de Riesgo', title="Distribución de Riesgo de Mora")
    st.plotly_chart(fig_risk, use_container_width=True)

# ==========================================
# MÓDULO 6: HOJA DE RUTA Y ANÁLISIS COMPETITIVO
# ==========================================
elif opcion_menu == "6. Hoja de Ruta y Análisis Competitivo":
    st.markdown('<p class="main-title">📌 Hoja de Ruta y Posicionamiento Competitivo</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-title">Priorización del desarrollo y ventajas frente a plataformas tradicionales.</p>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([1.2, 1])
    
    with col1:
        st.subheader("🚀 Orden Recomendado de Desarrollo")
        st.markdown("""
        1. **Panel de ratios y aging**:  
           *Cobrabilidad, morosidad y fondo de reserva en meses.*  
           👉 **Máximo impacto inmediato** con los datos estructurados disponibles.
           
        2. **Alertas de desvíos en gastos y facturas duplicadas**:  
           👉 Detección proactiva de inconsistencias operativas y sobrecostos.
           
        3. **Proyección de gastos y simulador de escenarios**:  
           👉 Herramienta para la toma de decisiones financieras en asambleas.
           
        4. **Lectura automática de facturas (OCR)**:  
           👉 Automatización del procesamiento e ingesta de comprobantes.
           
        5. **Predicción de mora**:  
           👉 Modelado predictivo cuando se acumule mayor historial de datos.
        """)

    with col2:
        st.subheader("⚠️ Brecha respecto a Plataformas Tradicionales")
        st.warning("""
        **Ámbitos donde el sistema aún no posee ventaja competitiva directa:**
        
        * **Integración bancaria y cobros automáticos:**  
          Requiere servidor dedicado para la gestión y escucha de *webhooks* en tiempo real con pasarelas de pago y bancos.
          
        * **Experiencia del propietario (Portal de autogestión):**  
          Portal/App donde el vecino consulta su saldo deudor, historial de liquidaciones y descarga sus recibos de pago.
        """)

# ==========================================
# PIE DE PÁGINA
# ==========================================
st.divider()
st.caption("🏢 **Consorcio IA** — Sistema Inteligente de Gestión de Consorcios | Streamlit & Python")
