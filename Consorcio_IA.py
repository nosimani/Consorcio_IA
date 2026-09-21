import streamlit as st
import sqlite3
import datetime
import pandas as pd

# Configuración inicial estética
st.set_page_config(page_title="ConsorcioAI Enterprise Dash", page_icon="🤖", layout="wide")

st.title("🏢 ConsorcioAI Core - Panel de Control del Enjambre")
st.markdown("Bienvenido al sistema de automatización de Propiedad Horizontal basado en agentes de IA.")

# --- BASE DE DATOS LOCAL ---
DB_NAME = "consorcio_ai_demo.db"
def init_db():
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS copropietarios 
            (unidad TEXT PRIMARY KEY, propietario TEXT, telefono TEXT, porcentual REAL)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS tickets 
            (id INTEGER PRIMARY KEY, fecha TEXT, unidad TEXT, categoria TEXT, dictamen TEXT, impacto REAL)''')
        
        cursor.execute("SELECT COUNT(*) FROM copropietarios")
        if cursor.fetchone() == 0:
            cursor.executemany("INSERT INTO copropietarios VALUES (?,?,?,?)", [
                ("1° A", "Juan Pérez", "+5491144445555", 0.085),
                ("4° B", "María Rodriguez", "+5491155556666", 0.120),
                ("7° C", "Carlos Gómez", "+5491166667777", 0.075)
            ])
        conn.commit()

init_db()

# --- DISEÑO DE LA INTERFAZ CON SOLAPAS (TABS) ---
tab_ingreso, tab_front, tab_legal, tab_proveedores, tab_contable = st.tabs([
    "📥 Ingreso de Reclamo", 
    "💁‍♂️ 1. Front Desk", 
    "⚖️ 2. Agente Legal", 
    "🛠️ 3. Gestor de Gremios", 
    "📊 4. Liquidación Contable"
])

# --- SOLAPA: INGRESO DE DATOS ---
with tab_ingreso:
    st.subheader("Simulador de Mensaje del Vecino")
    st.info("Use esta solapa para ingresar un problema real y ver cómo reacciona el enjambre.")
    
    unidad_seleccionada = st.selectbox("Seleccione la Unidad Afectada:", ["1° A", "4° B", "7° C"])
    mensaje_vecino = st.text_area("Mensaje de WhatsApp/Portal:", 
        "Hola, se rompió un caño interno de la pared de mi baño y me está inundando el piso.")
    
    botón_procesar = st.button("🚀 Disparar Flujo del Enjambre")

# --- PROCESAMIENTO HEURÍSTICO PARA LA DEMO ---
es_plomeria = any(w in mensaje_vecino.lower() for w in ["agua", "caño", "filtracion", "baño", "cocina"])
categoria_detectada = "Mantenimiento_Plomería" if es_plomeria else "Administrativo"
dictamen_legal = "Gasto Consorcial Común (Art. 2041 CCyCN)" if es_plomeria else "Trámite Particular (Art. 2043 CCyCN)"
costo_total = 48000.00 if es_plomeria else 0.0

with sqlite3.connect(DB_NAME) as conn:
    cursor = conn.cursor()
    cursor.execute("SELECT unidad, propietario, telefono, porcentual FROM copropietarios WHERE unidad = ?", (unidad_seleccionada,))
    vecino_data = cursor.fetchone()
    
    cursor.execute("SELECT unidad, propietario, porcentual FROM copropietarios")
    todos_los_vecinos = cursor.fetchall()

# Mapeo numérico seguro de posiciones en la tupla SQL de vecino_data:
# 0: unidad, 1: propietario, 2: telefono, 3: porcentual
propietario_nombre = vecino_data[1]
propietario_telefono = vecino_data[2]
porcentual_valor = vecino_data[3]

impacto_individual = costo_total * porcentual_valor

if botón_procesar:
    st.success(f"¡Flujo activado para la unidad {unidad_seleccionada}! Navegue por las solapas de arriba para ver el trabajo de cada agente.")

# --- SOLAPA 1: FRONT DESK ---
with tab_front:
    st.subheader("Agente de Atención al Vecino")
    st.markdown("**Rol:** Clasificar reclamos semánticamente.")
    st.code(f"Inputs recibidos:\n- Unidad: {unidad_seleccionada}\n- Texto: '{mensaje_vecino}'")
    
    if botón_procesar:
        st.metric(label="Categoría Semántica Detectada", value=categoria_detectada)
        st.write("✅ **Análisis de IA:** El reclamo requiere asistencia técnica urgente de gremios.")

# --- SOLAPA 2: LEGAL ---
with tab_legal:
    st.subheader("Agente Abogado PH")
    st.markdown("**Rol:** Validar marcos regulatorios del Código Civil y Comercial de la Nación.")
    
    if botón_procesar:
        st.info(f"📜 **Dictamen Emitido:** {dictamen_legal}")
        st.markdown(f"""
        **Fundamentación Jurídica:**
        Se analiza la unidad **{unidad_seleccionada}** bajo la titularidad de *{propietario_nombre}*.
        Al tratarse de una anomalía en un caño estructural/interno, la responsabilidad recae sobre el consorcio según las normativas vigentes de Propiedad Horizontal en Argentina (Art. 2041).
        """)

# --- SOLAPA 3: PROVEEDORES ---
with tab_proveedores:
    st.subheader("Agente Gestor de Gremios")
    st.markdown("**Rol:** Buscar proveedores homologados y emitir Órdenes de Trabajo.")
    
    if botón_procesar:
        if es_plomeria:
            st.json({
                "proveedor_asignado": "Plomería Express SRL (Homologado)",
                "id_proveedor": "PROV-9982",
                "orden_trabajo_nro": "OT-2026-0041",
                "presupuesto_estimado_ars": costo_total,
                "estado_envio": "Notificado vía API"
            })
        else:
            st.write("No se requiere contratación de gremios de emergencia para este tipo de trámite.")

# --- SOLAPA 4: CONTABLE ---
with tab_contable:
    st.subheader("Agente de Liquidación de Expensas")
    st.markdown("**Rol:** Prorratear gastos de forma equitativa e impactar el balance.")
    
    if botón_procesar:
        col1, col2, col3 = st.columns(3)
        col1.metric("Costo Total Arreglo", f"${costo_total:,.2f}")
        col2.metric(f"Porcentual ({unidad_seleccionada})", f"{porcentual_valor * 100}%")
        col3.metric("Impacto en su Expensa", f"${impacto_individual:,.2f}")
        
        st.write("### 📊 Prorrateo General del Edificio")
        st.markdown("Visualización del impacto del gasto distribuido entre todas las unidades:")
        
        data_grafico = []
        for v in todos_los_vecinos:
            data_grafico.append({
                "Unidad/Vecino": f"{v[0]} - {v[1]}",
                "Impacto ARS ($)": costo_total * v[2]
            })
        df = pd.DataFrame(data_grafico)
        
        st.bar_chart(data=df, x="Unidad/Vecino", y="Impacto ARS ($)", use_container_width=True)
        
        st.success(f"📲 **Simulación de WhatsApp enviada a {propietario_nombre} ({propietario_telefono}):**")
        st.chat_message("assistant").write(
            f"Estimado/a {propietario_nombre}, su reclamo ha sido procesado. "
            f"Dictamen: {dictamen_legal}. Impacto estimado en sus próximas expensas: ${impacto_individual:,.2f}."
        )
