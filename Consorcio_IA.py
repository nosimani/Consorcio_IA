# -*- coding: utf-8 -*-
"""
Consorcio_IA - Módulo Multiagente Real y Gratuito
Utiliza CrewAI y Google Gemini (Capa Gratuita)
"""

import os
from crewai import Agent, Crew, Process, Task

# Configuración del entorno gratuito utilizando la API Key de Gemini
# Nota: Debes registrarte en Google AI Studio y obtener tu API key sin costo.
os.environ["GEMINI_API_KEY"] = "TU_GEMINI_API_KEY_AQUI"
os.environ["OPENAI_API_BASE"] = "https://googleapis.com"
os.environ["OPENAI_MODEL_NAME"] = "gemini-1.5-flash"  # Modelo rápido, potente y gratuito
os.environ["OPENAI_API_KEY"] = os.environ["GEMINI_API_KEY"]

# ==========================================
# DEFINICIÓN DE AGENTES (CREWAI)
# ==========================================

# 1. Agente de Atención y Clasificación de Reclamos
agente_atencion = Agent(
    role="Especialista en Atención al Copropietario",
    goal="Recibir mensajes de propietarios de edificios en Argentina, empatizar, extraer la UF y determinar la urgencia técnica.",
    backstory=(
        "Sos un asistente virtual de una administración de consorcios en Buenos Aires. "
        "Tu trabajo es leer los reclamos de los vecinos (a veces enojados o preocupados), "
        "entender qué UF (Unidad Funcional) escribe y clasificar el rubro exacto del problema (Plomería, Gas, Electricidad, Ascensores)."
    ),
    verbose=True,
    allow_delegation=False
)

# 2. Agente de Legales y Compliance Contable
agente_legal_contable = Agent(
    role="Auditor Legal y Contador de Propiedad Horizontal",
    goal="Garantizar que cualquier gasto u orden de servicio cumpla con el Art. 2067 del CCyC y la Ley 941.",
    backstory=(
        "Sos un abogado y contador experimentado en consorcios argentinos. "
        "Revisás los incidentes técnicos y determinás si el consorcio está legalmente obligado a pagarlo "
        "(ej. caños maestros de agua) o si le corresponde al propietario por ser dentro de su propiedad exclusiva. "
        "Además, verificás que el gasto se impute correctamente en las expensas ordinarias o extraordinarias."
    ),
    verbose=True,
    allow_delegation=False
)

# 3. Agente de Proveedores y Presupuestos
agente_proveedores = Agent(
    role="Coordinador de Mantenimiento y Gremios",
    goal="Simular la compulsa de precios y redactar un correo formal de solicitud de presupuesto a los proveedores matriculados.",
    backstory=(
        "Conocés a todos los plomeros, electricistas y techistas matriculados de la zona. "
        "Tu función es tomar el problema validado legalmente y redactar una orden de inspección clara, "
        "con los términos técnicos adecuados para que el prestador vaya a cotizar."
    ),
    verbose=True,
    allow_delegation=False
)

# ==========================================
# DEFINICIÓN DE TAREAS
# ==========================================

mensaje_propietario = (
    "Hola, soy Juan de la UF 4B de Corrientes 1500. Estoy desesperado, "
    "me está saliendo agua a lo pavote de la pared del baño y me está arruinando el parqué. "
    "¡Mandame a alguien urgente porque se me inunda el departamento!"
)

tarea_analisis = Task(
    description=f"Analizá el siguiente mensaje del propietario: '{mensaje_propietario}'. Identificá la UF, el rubro y el nivel de urgencia.",
    expected_output="Un informe breve que contenga: UF, Nombre del propietario, Rubro del problema, Nivel de Urgencia y un mensaje de respuesta empático para el vecino.",
    agent=agente_atencion
)

tarea_legal = Task(
    description="Tomá el informe del reclamo y determiná si el consorcio debe hacerse cargo (Art. 2041/2042 CCyC sobre bienes comunes) o si es gasto privado. Define si va a Expensas Ordinarias.",
    expected_output="Dictamen legal y contable de 1 párrafo indicando obligación (Consorcio o Propietario) e imputación del futuro gasto.",
    agent=agente_legal_contable
)

tarea_proveedor = Task(
    description="Generá una orden de trabajo formal dirigida a un plomero matriculado para resolver el siniestro reportado.",
    expected_output="Una plantilla de mail/WhatsApp formal de solicitud de urgencia técnica para el proveedor, detallando la locación y el problema.",
    agent=agente_proveedores
)

# ==========================================
# ORQUESTACIÓN DEL ENJAMBRE
# ==========================================

enjambre_consorcio = Crew(
    agents=[agente_atencion, agente_legal_contable, agente_proveedores],
    tasks=[tarea_analisis, tarea_legal, tarea_proveedor],
    process=Process.sequential,  # Los agentes trabajan en cadena (Pipeline)
    verbose=True
)

if __name__ == "__main__":
    print("Iniciando procesamiento de enjambre inteligente...")
    resultado = enjambre_consorcio.kickoff()
    print("\n================== RESULTADO FINAL DEL ENJAMBRE ==================")
    print(resultado)
