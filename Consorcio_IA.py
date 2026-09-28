# -*- coding: utf-8 -*-
import streamlit as st
import os
import google.generativeai as genai

# Configuración de página de Streamlit
st.set_page_config(page_title="Consorcio IA - Enjambre Nativo", layout="wide")

st.title("🏢 Consorcio IA: Sistema Multiagente de Administración")
st.subheader("Consultoría de Propiedad Horizontal y Automatización Contable-Legal")

# Validar API Key desde los Secrets de Streamlit
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
else:
    st.warning("⚠️ Falta configurar la GEMINI_API_KEY en los Secrets de la App.")

# Formulario en la web para ingresar el reclamo del propietario
st.write("### 📩 Mesa de Entradas Digital (Reclamos de Propietarios)")
mensaje_vecino = st.text_area(
    "Ingresá el mensaje del propietario o consorcista:",
    value="Hola, soy Juan de la UF 4B de Corrientes 1500. Estoy desesperado, me está saliendo agua a lo pavote de la pared del baño y me está arruinando el parqué. ¡Mandame a alguien urgente porque se me inunda el departamento!"
)

if st.button("🚀 Ejecutar Enjambre de Agentes"):
    if "GEMINI_API_KEY" not in st.secrets:
        st.error("No se puede iniciar el enjambre sin la API Key configurada.")
    else:
        with st.spinner("El enjambre está operando..."):
            try:
                # Inicializar el modelo base gratuito y potente
                model = genai.GenerativeModel('gemini-1.5-flash')

                # --- AGENTE 1: ATENCIÓN AL COPROPIETARIO ---
                prompt_atencion = f"""
                Sos el Agente Especialista en Atención al Copropietario de una administración en Argentina.
                Tu meta es analizar el mensaje del vecino, extraer la UF, el rubro técnico (Plomería, Electricidad, Gas, Ascensores) y la urgencia.
                Mensaje del vecino: "{mensaje_vecino}"
                Devuelve un informe estructurado con UF, Rubro, Nivel de Urgencia y un saludo empático de respuesta.
                """
                respuesta_atencion = model.generate_content(prompt_atencion).text

                # --- AGENTE 2: LEGAL Y COMPLIANCE CONTABLE ---
                prompt_legal = f"""
                Sos el Agente Auditor Legal y Contador de Propiedad Horizontal en Argentina.
                Basándote en el siguiente informe de mantenimiento:
                "{respuesta_atencion}"
                Aplica el Código Civil y Comercial de la Nación (Art. 2041, 2042 y 2067) y determina si el gasto corresponde al Consorcio (bien común/cañería interna) o al Propietario (bien privado/gasto exclusivo). Indica si se imputará en Expensas Ordinarias o Extraordinarias de forma resumida en un párrafo contundente.
                """
                respuesta_legal = model.generate_content(prompt_legal).text

                # --- AGENTE 3: COORDINADOR DE PROVEEDORES ---
                prompt_proveedores = f"""
                Sos el Agente Coordinador de Mantenimiento y Gremios Matriculados.
                Tomando en cuenta la resolución legal:
                "{respuesta_legal}"
                Si corresponde al consorcio, redacta un mensaje formal e institucional por WhatsApp/Mail dirigido a un prestador matriculado del rubro detectado para solicitarle presupuesto urgente y visita técnica a la locación. Si no corresponde, redacta una respuesta formal denegando el servicio al propietario con fundamentos.
                """
                respuesta_proveedores = model.generate_content(prompt_proveedores).text

                # --- RENDERIZADO VISUAL EN LA APP ---
                st.success("¡Procesamiento del enjambre completado de forma segura!")
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.info("👤 **Agente Atención**")
                    st.write(respuesta_atencion)
                    
                with col2:
                    st.warning("⚖️ **Agente Legal/Contable**")
                    st.write(respuesta_legal)
                    
                with col3:
                    st.success("🛠️ **Agente Proveedores**")
                    st.write(respuesta_proveedores)

            except Exception as e:
                st.error(f"Error en la ejecución de los agentes: {e}")
