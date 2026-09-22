import streamlit as st
import pandas as pd
import random
from datetime import datetime

# =====================================================================
# CONFIGURACIÓN PREMIUM DE LA INTERFAZ (LOOK & FEEL AZUL METALIZADO Y DORADO)
# =====================================================================
st.set_page_config(
    page_title="Resilia_Condominios",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inyección de CSS para forzar el fondo azul metalizado oscuro, paneles dorados y sub-solapas celestes
st.markdown("""
    <style>
        /* Fondo general de la plataforma: Azul Metalizado Oscuro Profundo */
        .main { background-color: #0b192c; }
        
        /* Títulos e identificadores sobre el fondo oscuro */
        h1 { color: #FFFFFF; font-family: sans-serif; font-weight: 900; letter-spacing: -1px; }
        h2, h3 { color: #38bdf8; font-family: sans-serif; font-weight: 700; }
        .stMarkdown p { color: #e2e8f0; }

        /* Paneles de Métricas Ejecutivas en Dorado Premium */
        div[data-testid="stMetric"] {
            background: linear-gradient(135deg, #d4af37 0%, #aa7c11 100%) !important;
            color: #0b192c !important;
            padding: 22px !important;
            border-radius: 16px !important;
            box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.6);
            border: 1px solid rgba(255, 255, 255, 0.2);
            transition: transform 0.2s;
        }
        div[data-testid="stMetric"]:hover {
            transform: translateY(-5px);
        }
        
        /* Modificadores de color interno para el texto dentro del panel dorado */
        div[data-testid="stMetric"] label { 
            color: #0f172a !important; 
            font-weight: 800 !important; 
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        div[data-testid="stMetric"] [data-testid="stMetricValue"] { 
            color: #0b192c !important; 
            font-weight: 900 !important; 
            font-size: 1.9rem !important;
        }

        /* Solapas Principales */
        .stTabs [data-baseweb="tab-list"] { gap: 12px; background-color: #1e293b; padding: 8px; border-radius: 12px; border: 1px solid rgba(255, 255, 255, 0.1); }
        .stTabs [data-baseweb="tab"] { background-color: transparent; border: none !important; padding: 12px 24px; border-radius: 8px; font-weight: 700; color: #94a3b8; transition: all 0.3s; }
        .stTabs [aria-selected="true"] { background-color: #0284c7 !important; color: #FFFFFF !important; }

        /* Solapas Celestes Secundarias para Órdenes de Trabajo */
        .celeste-tabs [data-baseweb="tab-list"] { background-color: #0f172a !important; border: 1px solid #38bdf8 !important; }
        .celeste-tabs [data-baseweb="tab"] { color: #bae6fd !important; }
        .celeste-tabs [aria-selected="true"] { background-color: #38bdf8 !important; color: #0f172a !important; font-weight: 800 !important; }

        /* Tarjetas de los Agentes */
        .agent-card { background-color: #1e293b; padding: 24px; border-radius: 16px; border-left: 6px solid #38bdf8; margin-bottom: 18px; color: #f1f5f9; }
        .agent-title { font-size: 1.1rem; font-weight: 800; color: #ffffff; margin-bottom: 8px; }
        
        /* Ajuste estético para tablas y dataframes sobre el fondo oscuro */
        .stDataFrame, .stTable { background-color: #1e293b; border-radius: 12px; padding: 5px; }
    </style>
""", unsafe_allow_html=True)

# =====================================================================
# BASE DE DATOS ESTRUCTURADA POR EDIFICIO (CON SUS RESPECTIVAS 5 UFs)
# =====================================================================
DATA_EDIFICIOS = {
    "Av. Corrientes 1234, CABA": {
        "unidades": {
            "1A": {"propietario": "Juan Pérez", "porcentaje": 0.20, "saldo": 1500.0},
            "3J": {"propietario": "María Rodriguez", "porcentaje": 0.15, "saldo": 0.0},
            "4K": {"propietario": "Carlos López", "porcentaje": 0.25, "saldo": -500.0},
            "5M": {"propietario": "Ana Martínez", "porcentaje": 0.18, "saldo": 12000.0},
            "6P": {"propietario": "Luis Gomez", "porcentaje": 0.22, "saldo": 0.0}
        },
        "fondo_reserva": 450000.00,
        "libro_diario": [
            {"Fecha": "2026-09-01", "Concepto": "Abono Ascensores S.A.", "Monto": 45000.0, "Tipo": "Gasto Ordinario"},
            {"Fecha": "2026-09-05", "Concepto": "Sueldo Encargado SUTERH", "Monto": 250000.0, "Tipo": "Gasto Ordinario"}
        ],
        "trabajos_solicitados": [{"UF": "1A", "Rubro": "Plomería", "Detalle": "Rotura de caño de agua en baño principal", "Fecha": "2026-09-21"}],
        "trabajos_en_proceso": [{"UF": "3J", "Rubro": "Plomería", "Detalle": "Cambio de llaves de paso", "Proveedor": "Plomería Gas-An"}],
        "trabajos_pendientes": [{"UF": "4K", "Rubro": "Albañilería", "Detalle": "Revoque de patio interno", "Motivo": "Falta de materiales"}]
    },
    "Larrea 435, CABA": {
        "unidades": {
            "1A": {"propietario": "Sofía Rossi", "porcentaje": 0.20, "saldo": 0.0},
            "3J": {"propietario": "Jorge Blanco", "porcentaje": 0.15, "saldo": 8500.0},
            "4K": {"propietario": "Andrés Fernández", "porcentaje": 0.25, "saldo": 0.0},
            "5M": {"propietario": "Clara Benítez", "porcentaje": 0.18, "saldo": -1200.0},
            "6P": {"propietario": "Ricardo Darín", "porcentaje": 0.22, "saldo": 4300.0}
        },
        "fondo_reserva": 380000.00,
        "libro_diario": [
            {"Fecha": "2026-09-02", "Concepto": "Abono Empresa de Limpieza", "Monto": 80000.0, "Tipo": "Gasto Ordinario"},
            {"Fecha": "2026-09-08", "Concepto": "Destapación de Columna Cloacal", "Monto": 35000.0, "Tipo": "Gasto Ordinario"}
        ],
        "trabajos_solicitados": [{"UF": "3J", "Rubro": "Electricidad", "Detalle": "Luz parpadeante en palier", "Fecha": "2026-09-22"}],
        "trabajos_en_proceso": [],
        "trabajos_pendientes": [{"UF": "6P", "Rubro": "Albañilería", "Detalle": "Arreglo de grieta en cochera", "Motivo": "Presupuesto elevado"}]
    },
    "Montevideo 891, CABA": {
        "unidades": {
            "1A": {"propietario": "Esteban Quito", "porcentaje": 0.15, "saldo": -300.0},
            "3J": {"propietario": "Mónica Ferrari", "porcentaje": 0.25, "saldo": 0.0},
            "4K": {"propietario": "Pedro Picapiedra", "porcentaje": 0.20, "saldo": 15000.0},
            "5M": {"propietario": "Gisela Valenzuela", "porcentaje": 0.15, "saldo": 0.0},
            "6P": {"propietario": "Roberto Gómez", "porcentaje": 0.25, "saldo": 9100.0}
        },
        "fondo_reserva": 620000.00,
        "libro_diario": [
            {"Fecha": "2026-09-04", "Concepto": "Mantenimiento de Portón Eléctrico", "Monto": 22000.0, "Tipo": "Gasto Ordinario"},
            {"Fecha": "2026-09-12", "Concepto": "Seguro Integral Edificio", "Monto": 95000.0, "Tipo": "Gasto Ordinario"}
        ],
        "trabajos_solicitados": [],
        "trabajos_en_proceso": [{"UF": "4K", "Rubro": "Albañilería", "Detalle": "Pintura de fachada interna", "Proveedor": "Pintores Asociados"}],
        "trabajos_pendientes": []
    },
    "San Jose 1111, CABA": {
        "unidades": {
            "1A": {"propietario": "Facundo Cabral", "porcentaje": 0.22, "saldo": 0.0},
            "3J": {"propietario": "Lucía Galán", "porcentaje": 0.18, "saldo": 0.0},
            "4K": {"propietario": "Joaquín Sabina", "porcentaje": 0.20, "saldo": -2500.0},
            "5M": {"propietario": "Charly García", "porcentaje": 0.20, "saldo": 34000.0},
            "6P": {"propietario": "Fito Páez", "porcentaje": 0.20, "saldo": 0.0}
        },
        "fondo_reserva": 290000.00,
        "libro_diario": [
            {"Fecha": "2026-09-03", "Concepto": "Service de Bombas de Agua", "Monto": 41000.0, "Tipo": "Gasto Ordinario"},
            {"Fecha": "2026-09-15", "Concepto": "Recarga de Matafuegos Gral", "Monto": 18000.0, "Tipo": "Gasto Ordinario"}
        ],
        "trabajos_solicitados": [{"UF": "5M", "Rubro": "Plomería", "Detalle": "Pérdida en bacha de cocina", "Fecha": "2026-09-20"}],
        "trabajos_en_proceso": [],
        "trabajos_pendientes": []
    },
    "Guayaquil 399, CABA": {
        "unidades": {
            "1A": {"propietario": "Lionel Messi", "porcentaje": 0.30, "saldo": -50000.0},
            "3J": {"propietario": "Ángel Di María", "porcentaje": 0.20, "saldo": 0.0},
            "4K": {"propietario": "Rodrigo De Paul", "porcentaje": 0.15, "saldo": 1200.0},
            "5M": {"propietario": "Emiliano Martínez", "porcentaje": 0.15, "saldo": 0.0},
            "6P": {"propietario": "Lionel Scaloni", "porcentaje": 0.20, "saldo": 0.0}
        },
        "fondo_reserva": 850000.00,
        "libro_diario": [
            {"Fecha": "2026-09-01", "Concepto": "Abono Grupo Electrógeno", "Monto": 65000.0, "Tipo": "Gasto Ordinario"},
            {"Fecha": "2026-09-10", "Concepto": "Sueldo Vigilancia Privada", "Monto": 450000.0, "Tipo": "Gasto Ordinario"}
        ],
        "trabajos_solicitados": [],
        "trabajos_en_proceso": [{"UF": "4K", "Rubro": "Electricidad", "Detalle": "Instalación de luminaria LED en cocheras", "Proveedor": "Electricidad Voltio"}],
        "trabajos_pendientes": [{"UF": "3J", "Rubro": "Plomería", "Detalle": "Filtración en losa radiante", "Motivo": "Esperando cese de lluvias"}]
    }
}

PROVEEDORES = {"plomeria": [{"nombre": "Plomería Gas-An", "tel": "1144445555"}]}

# =====================================================================
# PANEL LATERAL (SIDEBAR CON LOGO INTERACTIVO Y SELECTOR DE CONSORCIO)
# =====================================================================
with st.sidebar:
    st.image("https://imgbox.com", use_container_width=True)
    st.title("Resilia_Condominios")
    st.caption("AI Swarm ERP Administration")
    st.markdown("---")
    
    # Selector Dinámico del Edificio Monitoreado









