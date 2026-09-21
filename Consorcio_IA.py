import streamlit as st
import pandas as pd

# Configuración inicial de la página con diseño optimizado
st.set_page_config(
    page_title="ConsorcioAI Enterprise Dash", 
    page_icon="🏢", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Estilos CSS personalizados para inyectar un diseño premium
st.markdown("""
    <style>
    /* Estilo del título principal y subtítulo */
    .main-title { font-size: 32px; font-weight: 800; color: #1E3A8A; margin-bottom: 5px; }
    .sub-title { font-size: 16px; color: #4B5563; margin-bottom: 25px; }
    
    /* Contenedores tipo tarjeta para los agentes */
    .agent-card {
        background-color: #F8FAFC;
        padding: 20px;
        border-radius: 12px;
        border-left: 5px solid #2563EB;
        margin-bottom: 20px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    .legal-card { border-left-color: #10B981; background-color: #F0FDF4; }
    .gremio-card { border-left-color: #F59E0B; background-color: #FEF3C7; }
    
    /* Badges o etiquetas de estado */
    .badge {
        padding: 4px 10px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 600;
        display: inline-block;
    }
    .badge-blue { background-color: #DBEAFE; color: #1E40AF; }
    .badge-green { background-color: #D1FAE5; color: #065F46; }
    </style>
""", unsafe_allow_html=True)

# Encabezado Corporativo
st.markdown('<div class="main-title">🏢 ConsorcioAI Core v2.0</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Plataforma Autónoma de Operaciones y Gestión de Propiedad Horizontal basada en IA</div>', unsafe_allow_html=True)

# --- DATOS MATRICIALES FIJOS ---
datos_consorcio = {
    "1° A": {"propietario": "Juan Pérez", "telefono": "+5491144445555", "porcentual": 0.085},
    "4° B": {"propietario": "María Rodriguez", "telefono": "+5491155556666", "porcentual": 0.120},
    "7° C": {"propietario": "Carlos Gómez", "telefono": "+5491166667777", "porcentual": 0.075}
}

# --- SOLAPAS CON DISEÑO LIMPIO ---
tab_ingreso, tab_front, tab_legal, tab_proveedores, tab_contable = st.tabs([
    "📥 Panel de Entrada", 
    "💁‍♂️ 1. Front Desk Agent", 
    "⚖️ 2. Legal Analyst", 
    "🛠️ 3. Operations Agent", 
    "📊 4. Financial Engine"
])

# --- SOLAPA: INGRESO DE DATOS ---
with tab_ingreso:
    st.markdown("### 📥 Recepción de Incidentes")
    
    col_izq, col_der = st.columns([1, 2])
    
    with col_izq:
        st.markdown("**Configuración del Evento**")
        unidad_seleccionada = st.selectbox("Unidad de Origen:", ["1° A", "4° B", "7° C"])
        botón_procesar = st.button("🚀 Iniciar Flujo de Agentes", use_container_width=True)
        
    with col_der:
        st.markdown("**Simulador de Entrada de Comunicación (WhatsApp/Portal)**")
        mensaje_vecino = st.text_area(
            label="Mensaje recibido:",
            value="Hola, se rompió un caño interno de la pared de mi baño y me está inundando el piso.",
            height=115
        )

# --- PROCESAMIENTO INTERNO ---
es_plomeria = any(w in mensaje_vecino.lower() for w in ["agua", "caño", "filtracion", "baño", "cocina"])
categoria_detectada = "Mantenimiento: Plomería de Emergencia" if es_plomeria else "Trámite General / Administrativo"
dictamen_legal = "Responsabilidad Consorcial Común (Art. 2041 CCyCN)" if es_plomeria else "Gasto Particular de la Unidad (Art. 2043 CCyCN)"
costo_total = 48000.00 if es_plomeria else 0.0

vecino = datos_consorcio[unidad_seleccionada]
propietario_nombre = vecino["propietario"]
propietario_telefono = vecino["telefono"]
porcentual_valor = vecino["porcentual"]
impacto_individual = costo_total * porcentual_valor

if botón_procesar:
    st.toast("Enjambre activado con éxito", icon="⚙️")
    st.success(f"⚡ **Flujo transaccional en ejecución para {unidad_seleccionada}.** Los agentes han procesado el caso. Revise las siguientes solapas para auditar las acciones.")

# --- SOLAPA 1: FRONT DESK ---
with tab_front:
    st.markdown("### 💁‍♂️ Clasificación Semántica de Entradas")
    if botón_procesar:
        st.markdown(f"""
        <div class="agent-card">
            <h4>🤖 Agente Front Desk</h4>
            <p><strong>Log de Entrada:</strong> <i>"{mensaje_vecino}"</i></p>
            <span class="badge badge-blue">Clasificación: {categoria_detectada}</span>
            <p style='margin-top:10px;'><b>Acción:</b> Análisis contextual completado. Se deriva la orden al Agente de Legales para encuadre normativo.</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.warning("Active el flujo en la primera pestaña para visualizar el log del Agente.")

# --- SOLAPA 2: LEGAL ---
with tab_legal:
    st.markdown("### ⚖️ Encuadre Jurídico Automático")
    if botón_procesar:
        st.markdown(f"""
        <div class="agent-card legal-card">
            <h4>📜 Agente Legal - Propiedad Horizontal</h4>
            <p><strong>Dictamen Emitido:</strong> {dictamen_legal}</p>
            <p><b>Fundamentación:</b> Evaluada la unidad <b>{unidad_seleccionada}</b> ({propietario_nombre}). El origen del incidente afecta a elementos estructurales o conductos internos del edificio, encuadrando de forma taxativa en las obligaciones del Consorcio de Propietarios.</p>
            <span class="badge badge-green">Estatus: Aprobado para Liquidación Común</span>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.warning("Active el flujo en la primera pestaña.")

# --- SOLAPA 3: PROVEEDORES ---
with tab_proveedores:
    st.markdown("### 🛠️ Gestión de Gremios y Logística Técnica")
    if botón_procesar:
        if es_plomeria:
            st.markdown("""
            <div class="agent-card gremio-card">
                <h4>🔧 Agente Operativo de Gremios</h4>
                <p><b>Acción:</b> Despacho automático de contratista homologado.</p>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("**Orden de Trabajo Emitida (JSON oficial despachado al proveedor):**")
            st.json({
                "proveedor_asignado": "Plomería Express SRL",
                "id_proveedor_homologado": "PROV-9982",
                "orden_trabajo_nro": "OT-2026-0041",
                "presupuesto_ars": costo_total,
                "prioridad": "CRÍTICA"
            })
        else:
            st.info("El incidente actual está catalogado como Administrativo. No requiere intervención ni asignación de gremios técnicos.")
    else:
        st.warning("Active el flujo en la primera pestaña.")

# --- SOLAPA 4: CONTABLE ---
with tab_contable:
    st.markdown("### 📊 Prorrateo e Impacto Financiero")
    if botón_procesar:
        # Métricas destacadas en tarjetas limpias
        c1, c2, c3 = st.columns(3)
        c1.metric("Costo Total de Obra", f"${costo_total:,.2f}")
        c2.metric(f"Porcentual {unidad_seleccionada}", f"{porcentual_valor * 100}%")
        c3.metric("Impacto Neto en Expensa", f"${impacto_individual:,.2f}")
        
        st.markdown("---")
        st.markdown("#### 📈 Distribución Equitativa del Gasto")
        
        data_grafico = []
        for uni, v in datos_consorcio.items():
            data_grafico.append({
                "Unidad - Copropietario": f"{uni} - {v['propietario']}",
                "Impacto ARS ($)": costo_total * v['porcentual']
            })
        df = pd.DataFrame(data_grafico)
        
        st.bar_chart(data=df, x="Unidad - Copropietario", y="Impacto ARS ($)", use_container_width=True)
        
        # Notificación simulada premium
        st.markdown("#### 📲 Notificación Push Automatizada (WhatsApp Gateway)")
        st.chat_message("assistant", avatar="💬").write(
            f"**Destinatario:** {propietario_nombre} ({propietario_telefono})  \n"
            f"**Mensaje Despachado:** \"Estimado/a {propietario_nombre}, su reclamo sobre '{mensaje_vecino}' "
            f"ha sido procesado de forma autónoma. Dictamen: {dictamen_legal}. "
            f"Se ha asignado al técnico y el impacto estimado en sus próximas expensas es de ${impacto_individual:,.2f}. ConsorcioAI.\""
        )
    else:
        st.warning("Active el flujo en la primera pestaña.")

