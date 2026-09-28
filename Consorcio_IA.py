# -*- coding: utf-8 -*-
import streamlit as st
import os
import random
from crewai import Agent, Crew, Process, Task

# Configuración de página de Streamlit
st.set_page_config(page_title="Consorcio IA - Multiagente", layout="wide")

st.title("🏢 Consorcio IA: Sistema Multiagente de Administración")
st.subheader("Consultoría de Propiedad Horizontal Automatizada")

# Tomar la API Key de los Secrets de Streamlit de forma segura
if "GEMINI_API_KEY" in st.secrets:
    os.environ["GEMINI_API_KEY"] = st.secrets["GEMINI_API_KEY"]
    os.environ["OPENAI_API_BASE"] = "https://googleapis.com"
    os.environ["OPENAI_MODEL_NAME"] = "gemini-1.5-flash"
    os.environ["OPENAI_API_KEY"] = st.secrets["GEMINI_API_KEY"]
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
        with st.spinner("Los agentes están debatiendo y resolviendo el caso técnico/legal..."):
            
            # DEFINICIÓN DE AGENTES
            agente_atencion = Agent(
                role="Especialista en Atención al Copropietario",
                goal="Recibir mensajes de propietarios de edificios en Argentina, empatizar, extraer la UF y determinar la urgencia técnica.",
                backstory="Sos asistente virtual de un consorcio en Buenos Aires. Clasificás rubros (Plomería, Gas, Electricidad, Ascensores) y urgencias.",
                verbose=True, allow_delegation=False
            )

            agente_legal_contable = Agent(
                role="Auditor Legal y Contador de Propiedad Horizontal",
                goal="Garantizar que cualquier gasto cumpla con el Art. 2067 del CCyC y la Ley 941 de CABA.",
                backstory="Abogado y contador experto en consorcios. Determinás si el gasto le corresponde al consorcio (bienes comunes) o al propietario.",
                verbose=True, allow_delegation=False
            )

            agente_proveedores = Agent(
                role="Coordinador de Mantenimiento y Gremios",
                goal="Simular la compulsa de precios y redactar un correo formal de solicitud de presupuesto a los proveedores matriculados.",
                backstory="Conocés plomeros, electricistas y techistas matriculados de la zona. Creás órdenes de inspección técnicas de urgencia.",
                verbose=True, allow_delegation=False
            )

            # DEFINICIÓN DE TAREAS
            tarea_analisis = Task(
                description=f"Analizá el siguiente mensaje: '{mensaje_vecino}'. Identificá la UF, el rubro y la urgencia.",
                expected_output="Informe breve con: UF, Rubro, Nivel de Urgencia y respuesta empática para el vecino.",
                agent=agente_atencion
            )

            tarea_legal = Task(
                description="Tomá el informe y determiná si el consorcio debe hacerse cargo (Art. 2041/2042 CCyC) o si es un gasto privado.",
                expected_output="Dictamen legal y contable de 1 párrafo indicando obligación e imputación en expensas ordinarias.",
                agent=agente_legal_contable
            )

            tarea_proveedor = Task(
                description="Generá una orden de trabajo formal dirigida a un plomero o especialista matriculado para resolver el siniestro.",
                expected_output="Plantilla de comunicación formal para el proveedor detallando el problema.",
                agent=agente_proveedores
            )

            # ORQUESTACIÓN
            enjambre = Crew(
                agents=[agente_atencion, agente_legal_contable, agente_proveedores],
                tasks=[tarea_analisis, tarea_legal, tarea_proveedor],
                process=Process.sequential, verbose=True
            )

            # Ejecutar y capturar salida
            resultado = enjambre.kickoff()
            
            # Mostrar resultados de forma ordenada en la interfaz web
            st.success("¡Resolución del Enjambre de Agentes completada!")
            st.write("### 📋 Dictamen y Acciones Automatizadas del Sistema:")
            st.markdown(resultado)
