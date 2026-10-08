import streamlit as st
import pandas as pd
import numpy as np

# ==========================================
# CONFIGURACIÓN DE PÁGINA
# ==========================================
st.set_page_config(
    page_title="Consorcio IA - Gestión Inteligente",
    page_icon="🏢",
    layout="wide"
)

st.title("🏢 Consorcio IA - Sistema de Gestión")

# ==========================================
# MENÚ LATERAL DE NAVEGACIÓN
# ==========================================
opcion = st.sidebar.selectbox(
    "Seleccionar Módulo:",
    [
        "1. Panel de Ratios y Aging",
        "2. Alertas de Desvíos y Facturas Duplicadas",
        "3. Proyección y Simulador de Escenarios",
        "4. Lectura Automática de Facturas (OCR)",
        "5. Predicción de Mora",
        "6. Hoja de Ruta y Análisis Competitivo"
    ]
)

st.sidebar.divider()
st.sidebar.info("💡 **Consorcio IA**: Plataforma de análisis e inteligencia de datos.")

# ==========================================
# DATOS DE SIMULACIÓN / DEMO
# ==========================================
@st.cache_data
def generar_datos():
    np.random.seed(42)
    unidades = [f"UF {i:02d}" for i in range(1, 21)]
    deuda_al_dia = np.random.choice([0, 0, 15000, 25000], size=20)
    deuda_30 = np.random.choice([0, 0, 0, 35000], size=20)
    deuda_60 = np.random.choice([0, 0, 0, 50000], size=20)
    deuda_90 = np.random.choice([0, 0, 0, 100000], size=20)
    
    df_aging = pd.DataFrame({
        'Unidad': unidades,
        'Al Día ($)': deuda_al_dia,
        '30 Días ($)': deuda_30,
        '60 Días ($)': deuda_60,
        '90+ Días ($)': deuda_90
    })
    df_aging['Total Deuda ($)'] = df_aging[['Al Día ($)', '30 Días ($)', '60 Días ($)', '90+ Días ($)']].sum(axis=1)
    
    rubros = ['Ascensores', 'Limpieza', 'Seguridad', 'Servicios Públicos', 'Mantenimiento General', 'Honorarios']
    presupuesto = [250000, 180000, 650000, 210000, 150000, 200000]
    ejecutado = [380000, 185000, 650000, 290000, 140000, 200000]
    
    df_gastos = pd.DataFrame({
        'Rubro': rubros,
        'Presupuestado ($)': presupuesto,
        'Ejecutado ($)': ejecutado
    })
    df_gastos['Desvío ($)'] = df_gastos['Ejecutado ($)'] - df_gastos['Presupuestado ($)']
    df_gastos['Desvío (%)'] = (df_gastos['Desvío ($)'] / df_gastos['Presupuestado ($)']) * 100
    
    return df_aging, df_gastos

df_aging, df_gastos = generar_datos()

# ==========================================
# MÓDULO 1: RATIOS Y AGING
# ==========================================
if opcion == "1. Panel de Ratios y Aging":
    st.header("📊 Panel de Ratios Financieros y Aging de Deuda")
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Cobrabilidad del Mes", "86.0%", "+2.3%")
    col2.metric("Morosidad Tasa", "14.0%", "-2.3%")
    col3.metric("Fondo de Reserva Total", "$5.400.000")
    col4.metric("Fondo en Meses de Cobertura", "3.0 meses", "Meta >= 2")
    
    st.divider()
    st.subheader("📉 Deuda Acumulada por Tramo de Antigüedad ($)")
    totales = {
        'Al Día': df_aging['Al Día ($)'].sum(),
        '30 Días': df_aging['30 Días ($)'].sum(),
        '60 Días': df_aging['60 Días ($)'].sum(),
        '90+ Días': df_aging['90+ Días ($)'].sum()
    }
    df_totales = pd.DataFrame(list(totales.items()), columns=['Tramo de Antigüedad', 'Monto ($)']).set_index('Tramo de Antigüedad')
    st.bar_chart(df_totales)
    
    st.subheader("📋 Detalle Morosidad por Unidad")
    st.dataframe(df_aging, use_container_width=True)

# ==========================================
# MÓDULO 2: ALERTAS DE DESVÍOS Y DUPLICADOS
# ==========================================
elif opcion == "2. Alertas de Desvíos y Facturas Duplicadas":
    st.header("🚨 Alertas de Desvíos en Gastos y Duplicados")
    
    for idx, row in df_gastos[df_gastos['Desvío (%)'] > 15].iterrows():
        st.warning(f"⚠️ **Desvío en {row['Rubro']}**: Superó el presupuesto en un **{row['Desvío (%)']:.1f}%** (${row['Desvío ($)']:,.0f} de sobrecosto).")
        
    st.divider()
    st.subheader("📊 Comparativo Presupuestado vs Ejecutado")
    st.bar_chart(df_gastos.set_index('Rubro')[['Presupuestado ($)', 'Ejecutado ($)']])
    
    st.subheader("🔍 Control de Facturas Duplicadas")
    st.error("⚠️ Factura Duplicada Detectada: Proveedor 'Elevadores SRL' — Monto: $190.000 — Fecha: 05/09/2026")

# ==========================================
# MÓDULO 3: PROYECCIÓN Y SIMULADOR
# ==========================================
elif opcion == "3. Proyección y Simulador de Escenarios":
    st.header("📈 Proyección de Gastos y Simulador de Escenarios")
    
    col_s1, col_s2 = st.columns(2)
    with col_s1:
        inflacion = st.slider("Inflación Mensual Estimada (%)", 0.0, 15.0, 4.0, 0.5)
        aumento_expensas = st.slider("Aumento de Expensas (%)", 0.0, 30.0, 5.0, 1.0)
    with col_s2:
        meses = st.selectbox("Plazo de Proyección (Meses)", [3, 6, 12], index=1)
    
    gastos_p = []
    ingresos_p = []
    g_act = 1800000
    i_act = 2150000
    
    for _ in range(meses):
        g_act *= (1 + inflacion / 100)
        i_act *= (1 + aumento_expensas / 100)
        gastos_p.append(g_act)
        ingresos_p.append(i_act)
        
    df_sim = pd.DataFrame({
        'Mes': [f"Mes {i+1}" for i in range(meses)],
        'Ingresos Proyectados ($)': ingresos_p,
        'Gastos Proyectados ($)': gastos_p
    }).set_index('Mes')
    
    st.line_chart(df_sim)

# ==========================================
# MÓDULO 4: LECTURA AUTOMÁTICA DE FACTURAS (OCR)
# ==========================================
elif opcion == "4. Lectura Automática de Facturas (OCR)":
    st.header("📄 Lectura Automática de Facturas (OCR)")
    archivo = st.file_uploader("Cargar comprobante o factura (PDF / PNG / JPG)", type=['pdf', 'png', 'jpg', 'jpeg'])
    
    if archivo:
        st.success(f"Archivo recibido: {archivo.name}")
    
    if st.button("🚀 Simular Extracción de Datos OCR"):
        st.write("---")
        st.write("**Proveedor Extraído:** Ascensores y Servicios SRL")
        st.write("**CUIT:** 30-71889900-4")
        st.write("**Monto Total:** $215.000,00")
        st.write("**Rubro Asignado:** Mantenimiento Ascensores")
        st.success("✅ Datos parseados y validados correctamente.")

# ==========================================
# MÓDULO 5: PREDICCIÓN DE MORA
# ==========================================
elif opcion == "5. Predicción de Mora":
    st.header("🔮 Predicción Preventiva de Mora")
    st.info("Algoritmo predictivo de riesgo de retraso en el pago de expensas por unidad para el próximo período.")
    
    df_mora = df_aging[['Unidad', 'Total Deuda ($)']].copy()
    np.random.seed(101)
    df_mora['Riesgo de Mora (%)'] = np.random.randint(5, 85, size=len(df_mora))
    df_mora = df_mora.sort_values(by='Riesgo de Mora (%)', ascending=False)
    
    st.dataframe(df_mora, use_container_width=True)
    st.bar_chart(df_mora.set_index('Unidad')[['Riesgo de Mora (%)']])

# ==========================================
# MÓDULO 6: HOJA DE RUTA Y ANÁLISIS COMPETITIVO
# ==========================================
elif opcion == "6. Hoja de Ruta y Análisis Competitivo":
    st.header("📌 Hoja de Ruta Sugerida y Análisis Competitivo")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🚀 Prioridad de Implementación Recomendada")
        st.markdown("""
        1. **Panel de ratios y aging**:  
           *(cobrabilidad, morosidad, fondo de reserva en meses)* — **Máximo impacto inmediato** con los datos ya estructurados.
        2. **Alertas de desvíos en gastos y facturas duplicadas**.
        3. **Proyección de gastos y simulador de escenarios**.
        4. **Lectura automática de facturas (OCR)**.
        5. **Predicción de mora** *(una vez que exista suficiente historial)*.
        """)
        
    with col2:
        st.subheader("⚠️ Ámbitos sin Ventaja Competitiva Actual")
        st.warning("""
        **Donde las plataformas establecidas llevan años de ventaja:**
        
        * **Integración bancaria y cobros automáticos:** Requiere un servidor dedicado e independiente para escuchar *webhooks* en tiempo real.
        * **Experiencia del propietario:** Portal/App interactiva donde el vecino consulta su saldo deudor, historial y descarga recibos de pago.
        """)

# ==========================================
# PIE DE PÁGINA
# ==========================================
st.divider()
st.caption("🏢 **Consorcio IA** — Sistema de Análisis y Gestión Inteligente de Consorcios")
