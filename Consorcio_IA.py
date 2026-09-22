import streamlit as st
import pandas as pd
import random
from datetime import datetime

# =====================================================================
# CONFIGURACIÓN DE LA PÁGINA (LOOK & FEEL PRÉMIUM)
# =====================================================================
st.set_page_config(
    page_title="ConsorcioIA - Multi-Agent Management",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inyección de CSS Avanzado para mejorar la paleta de colores y componentes
st.markdown("""
    <style>
        /* Paleta corporativa moderna (Azul Profundo, Gris Claro y Acentos) */
        :root {
            --primary-color: #1E3A8A;
            --background-color: #F8FAFC;
        }
        .main {
            background-color: #F8FAFC;
        }
        h1 {
            color: #0F172A;
            font-family: 'Helvetica Neue', sans-serif;
            font-weight: 800;
        }
        h2, h3 {
            color: #1E3A8A;
            font-family: 'Helvetica Neue', sans-serif;
        }
        /* Tarjetas estilizadas para logs y respuestas */
        .agent-card {
            background-color: #FFFFFF;
            padding: 20px;
            border-radius: 12px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03);
            border-left: 5px solid #3B82F6;
            margin-bottom: 15px;
        }
        .agent-legal { border-left-color: #EF4444; }
        .agent-contable { border-left-color: #10B981; }
        .agent-operativo { border-left-color: #F59E0B; }
        
        .agent-title {
            font-weight: bold;
            color: #1E293B;
            margin-bottom: 5px;
            display: flex;
            align-items: center;
            gap: 8px;
        }
    </style>
""", unsafe_allow_html=True)

# =====================================================================
# ESTADO DE LA APLICACIÓN (PERSISTENCIA DE DATOS DE SIMULACIÓN)
# =====================================================================
if 'libro_diario' not in st.session_state:
    st.session_state.libro_diario = [
        {"Fecha": "2026-09-01", "Concepto": "Abono Ascensores S.A.", "Monto": 45000.0, "Tipo": "Gasto Ordinario"},
        {"Fecha": "2026-09-05", "Concepto": "Sueldo Encargado + Cargas SUTERH", "Monto": 250000.0, "Tipo": "Gasto Ordinario"},
        {"Fecha": "2026-09-10", "Concepto": "Factura Luz Edesur", "Monto": 35000.0, "Tipo": "Gasto Ordinario"}
    ]

if 'unidades' not in st.session_state:
    st.session_state.unidades = {
        "101": {"propietario": "Juan Pérez", "porcentaje": 0.10, "saldo": 1500.0},
        "102": {"propietario": "María Rodriguez", "porcentaje": 0.15, "saldo": 0.0},
        "201": {"propietario": "Carlos López", "porcentaje": 0.12, "saldo": -500.0},
        "202": {"propietario": "Ana Martínez", "porcentaje": 0.18, "saldo": 12000.0},
        "301": {"propietario": "Luis Gomez", "porcentaje": 0.25, "saldo": 0.0},
        "302": {"propietario": "Sofía Rossi", "porcentaje": 0.20, "saldo": -1500.0}
    }

if 'reclamos' not in st.session_state:
    st.session_state.reclamos = []

# Proveedores del sistema operativo
PROVEEDORES = {
    "plomeria": [
        {"nombre": "Plomería Gas-An", "tel": "1144445555"},
        {"nombre": "Destapaciones Express", "tel": "1133339999"}
    ],
    "electricidad": [
        {"nombre": "Electricidad Voltio", "tel": "1177778888"}
    ],
    "cerrajeria": [
        {"nombre": "Cerrajería El Llavero", "tel": "1122228888"}
    ]
}

# =====================================================================
# SIDEBAR CONTROL PRINCIPAL
# =====================================================================
with st.sidebar:
    st.image("https://flaticon.com", width=80)
    st.title("ConsorcioIA")
    st.subheader("Panel de Control")
    st.markdown("---")
    st.markdown("**Consorcio Seleccionado:**")
    consorcio_act = st.selectbox("Edificio Activo", ["Av. Corrientes 1234, CABA", "Calle Florida 450, CABA"])
    st.info("CUIT: 30-11111111-9\n\nNormativa: Ley 941 CABA & CCyCN Argentina")

# =====================================================================
# HEADER PRINCIPAL
# =====================================================================
st.title("🏢 Ecosistema de Agentes Autónomos Consorciales")
st.caption("Control operativo, contable, legal y de atención omnicanal automatizado mediante IA.")

# MÓDULO DE MÉTRICAS VISUALES RÁPIDAS
m1, m2, m3, m4 = st.columns(4)
with m1:
    st.metric("Total Gastos del Mes", f"${sum(x['Monto'] for x in st.session_state.libro_diario):,.2f}")
with m2:
    st.metric("Fondo de Reserva", "$450,000.00", "+$25,000.00")
with m3:
    uf_morosas = sum(1 for u in st.session_state.unidades.values() if u['saldo'] > 0)
    st.metric("UFs en Mora", uf_morosas, delta=f"{uf_morosas/len(st.session_state.unidades)*100:.1f}% del total", delta_color="inverse")
with m4:
    st.metric("Tickets Activos de IA", len(st.session_state.reclamos))

st.markdown("<br>", unsafe_allow_html=True)

# =====================================================================
# ESTRUCTURACIÓN DE PESTAÑAS (SOLAPAS VISTOSAS)
# =====================================================================
tab_atencion, tab_contable, tab_operaciones, tab_config = st.tabs([
    "💬 Centro de Atención Omnicanal", 
    "📊 Liquidación y Contabilidad", 
    "🔧 Gestión Operativa y Proveedores",
    "⚙️ Configuración del Enjambre"
])

# ---------------------------------------------------------------------
# PESTAÑA 1: ATENCIÓN OMNICANAL
# ---------------------------------------------------------------------
with tab_atencion:
    st.header("📥 Recepción de Mensajes de Propietarios")
    st.write("Simulá la entrada de un mensaje vía WhatsApp, Web o Mail para observar cómo interactúa el Enjambre de agentes de manera autónoma.")
    
    col_input, col_output = st.columns([1, 1.2])
    
    with col_input:
        st.subheader("Enviar Simulación de Mensaje")
        uf_sel = st.selectbox("Unidad Funcional Emisora", list(st.session_state.unidades.keys()))
        canal_sel = st.radio("Canal de Entrada", ["WhatsApp", "Portal Web", "Correo Electrónico"], horizontal=True)
        
        mensaje_sugerido = st.selectbox("Sugerencias de Mensajes comunes:", [
            "Tengo una filtración en el baño, pierde un caño de agua.",
            "Hola, ¿cuánto debo de expensas?",
            "Se rompió la cerradura de la puerta de entrada al edificio.",
            "Necesito saber si entró mi pago del mes pasado."
        ])
        
        mensaje_custom = st.text_area("O escribí un mensaje personalizado:", value=mensaje_sugerido)
        procesar = st.button("🚀 Procesar Mensaje con IA", use_container_width=True)
        
    with col_output:
        st.subheader("⚙️ Trazabilidad del Enjambre de IA (Logs)")
        
        if procesar:
            msg_lower = mensaje_custom.lower()
            
            # --- LOG DE FRONT DESK ---
            st.markdown(f"""
            <div class="agent-card">
                <div class="agent-title">🤖 Agente Atención Al Cliente (Front-Desk)</div>
                <p>Mensaje interceptado en canal <b>{canal_sel}</b> perteneciente a la UF {uf_sel} ({st.session_state.unidades[uf_sel]['propietario']}).</p>
                <p><i>Análisis semántico completado de forma autónoma.</i></p>
            </div>
            """, unsafe_allow_html=True)
            
            # --- RUTEO CONTABLE ---
            if "expensa" in msg_lower or "pago" in msg_lower or "debo" in msg_lower:
                saldo = st.session_state.unidades[uf_sel]['saldo']
                estado = "Deudor" if saldo > 0 else ("Al día" if saldo == 0 else "Saldo a Favor")
                
                st.markdown(f"""
                <div class="agent-card agent-contable">
                    <div class="agent-title">📈 Agente Contador (Finanzas y Liquidación)</div>
                    <p><b>Acción:</b> Consulta de Estado de Cuenta.</p>
                    <p><b>Resultado:</b> El propietario {st.session_state.unidades[uf_sel]['propietario']} posee un saldo de <b>${abs(saldo):,.2f}</b> ({estado}).</p>
                </div>
                """, unsafe_allow_html=True)
                
                st.success(f"**Respuesta Automática enviada al propietario:** Hola {st.session_state.unidades[uf_sel]['propietario']}, tu saldo para la UF {uf_sel} es de ${abs(saldo):,.2f} ({estado}).")
                
            # --- RUTEO OPERATIVO ---
            elif any(w in msg_lower for w in ["pierde", "caño", "luz", "corto", "rompió", "filtración", "agua", "cerradura"]):
                rubro = "plomeria" if any(w in msg_lower for w in ["agua", "caño", "pierde", "filtración"]) else ("electricidad" if any(w in msg_lower for w in ["luz", "corto"]) else "cerrajeria")
                
                st.markdown(f"""
                <div class="agent-card agent-operativo">
                    <div class="agent-title">🔧 Agente Operativo (Mantenimiento e Ingeniería)</div>
                    <p><b>Incidencia Detectada:</b> Rubro <b>{rubro.upper()}</b>.</p>
                    <p><b>Acción:</b> Generando compulsa de precios automatizada vía API con los proveedores en cartilla...</p>
                </div>
                """, unsafe_allow_html=True)
                
                provs = PROVEEDORES.get(rubro, [])
                cotizaciones = []
                for p in provs:
                    precio = round(random.uniform(8000, 26000), 2)
                    cotizaciones.append({"proveedor": p['nombre'], "precio": precio})
                    st.caption(f"↳ _Presupuesto recibido de {p['nombre']}:_ ${precio:,.2f}")
                
                mejor_opcion = min(cotizaciones, key=lambda x: x['precio'])
                
                # --- RUTEO LEGAL / AUDITORÍA DE UMBRALES ---
                umbral = 20000.0

