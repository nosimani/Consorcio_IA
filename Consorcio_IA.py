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
