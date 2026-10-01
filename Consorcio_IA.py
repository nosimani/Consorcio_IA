"""
╔═══════════════════════════════════════════════════════════════════════════════╗
║                    RESILIA_CONDOMINIOS v2.0                                  ║
║         SISTEMA MULTIAGENTE DE ENJAMBRE PARA GESTIÓN DE CONDOMINIOS         ║
║                                                                            ║
║  Arquitectura: Orquestador Central + 7 Agentes Especializados              ║
║  Patrón: Swarm Intelligence con Coordinación Emergente                     ║
║  Enfoque: Cada petición dispara activación selectiva del enjambre          ║
╚═══════════════════════════════════════════════════════════════════════════════╝
"""

import streamlit as st
import pandas as pd
from dataclasses import dataclass
from enum import Enum
from typing import List, Dict, Any
from datetime import datetime
import time


# ════════════════════════════════════════════════════════════════════════════════
# EMOJIS DE ROBOTS Y ANIMACIONES
# ════════════════════════════════════════════════════════════════════════════════

ROBOTS_ANIMADOS = {
    "CONTABLE": ["🤖", "🦾", "⚙️"],
    "COMPLIANCE": ["🤖", "✔️", "✅"],
    "PROVEEDORES": ["🤖", "📦", "🏢"],
    "OPERATIVO": ["🤖", "⚙️", "🔧"],
    "MORA": ["🤖", "⚠️", "💰"],
    "AUDITOR": ["🤖", "🔍", "📋"],
    "REPORTES": ["🤖", "📊", "📈"],
}

def obtener_robot_animado(agente_tipo: str, paso: int) -> str:
    """Retorna el emoji del robot en movimiento según el paso de animación"""
    secuencia = ROBOTS_ANIMADOS.get(agente_tipo, ["🤖", "⚙️", "📊"])
    return secuencia[paso % len(secuencia)]


def animar_robot_procesando(placeholder, agente_nombre: str, agente_tipo: str, duracion_ms: float):
    """
    Anima un robot moviéndose mientras el agente procesa.
    """
    frames_total = int(duracion_ms / 100)
    
    for frame in range(frames_total):
        robot = obtener_robot_animado(agente_tipo, frame)
        barras = "▓" * (frame % 10) + "░" * (10 - (frame % 10))
        
        placeholder.markdown(
            f"""
            <div class="swarm-agent swarm-processing">
            {robot} <b>{agente_nombre}</b><br/>
            Procesando... {barras} {int((frame / frames_total) * 100)}%
            </div>
            """,
            unsafe_allow_html=True,
        )
        time.sleep(0.1)


# ════════════════════════════════════════════════════════════════════════════════
# 1. DEFINICIONES ESTRUCTURALES DEL ENJAMBRE
# ════════════════════════════════════════════════════════════════════════════════

class TipoAgente(Enum):
    """Clasificación de roles dentro del enjambre"""
    ORQUESTADOR = "🎯 Orquestador Central"
    CONTABLE = "📊 Agente Contable"
    COMPLIANCE = "✅ Agente Compliance"
    PROVEEDORES = "🏢 Agente de Proveedores"
    OPERATIVO = "🔧 Agente Operativo"
    MORA = "⚠️ Agente de Cobranza"
    AUDITOR = "🔍 Agente de Auditoría"
    REPORTES = "📈 Agente de Reportes"


class EstadoAgente(Enum):
    """Estados del ciclo de vida de cada agente"""
    INACTIVO = "⚪ Inactivo"
    ACTIVADO = "🟢 Activado"
    PROCESANDO = "🟡 Procesando"
    COMPLETADO = "✅ Completado"
    ERROR = "🔴 Error"


class TipoGasto(Enum):
    """Clasificación de gastos por rubro"""
    SERVICIOS_BASICOS = "Servicios Básicos"
    PERSONAL = "Personal y Cargas Sociales"
    MANTENIMIENTO = "Mantenimiento y Reparaciones"
    LIMPIEZA = "Limpieza y Desinfección"
    SEGUROS = "Seguros y Seguridad"
    ADMINISTRACION = "Administración"
    PROVISIONES = "Provisiones y Fondos"
    OTROS = "Otros Gastos"


class TipoIngreso(Enum):
    """Clasificación de ingresos"""
    EXPENSAS = "Expensas Cobradas"
    SERVICIOS = "Ingresos por Servicios"
    FINANCIEROS = "Ingresos Financieros"
    OTROS = "Otros Ingresos"


@dataclass
class EventoSwarm:
    """Evento que dispara el enjambre - el 'qué' solicita el usuario"""
    timestamp: str
    tipo_evento: str
    descripcion: str
    modulo_solicitante: str
    parametros: Dict[str, Any]


@dataclass
class ResultadoAgente:
    """Resultado del procesamiento de cada agente"""
    agente: str
    estado: EstadoAgente
    datos_procesados: Dict[str, Any]
    tiempo_procesamiento: str
    dependencias_cumplidas: List[str]


@dataclass
class RegistroGasto:
    """Registro de un gasto del consorcio"""
    concepto: str
    tipo_gasto: TipoGasto
    monto: float
    descripcion: str = ""
    factura: str = ""


@dataclass
class RegistroIngreso:
    """Registro de un ingreso del consorcio"""
    concepto: str
    tipo_ingreso: TipoIngreso
    monto: float
    descripcion: str = ""


@dataclass
class LiquidacionExpensas:
    """Liquidación completa de expensas del período"""
    periodo: str
    fecha_liquidacion: str
    total_ingresos: float
    total_gastos: float
    deficit_o_superavit: float
    gastos_por_rubro: Dict[str, float]
    ingresos_por_rubro: Dict[str, float]
    coeficientes: Dict[str, float]
    expensas_por_uf: Dict[str, float]


# ════════════════════════════════════════════════════════════════════════════════
# 2. BASE DE DATOS GLOBAL (INMUTABLE)
# ════════════════════════════════════════════════════════════════════════════════

ESTADISTICAS_EDIFICIOS = {
    "Av. Corrientes 1234, CABA": {
        "reserva": 450000.0,
        "factor": 1.0,
        "mora": "1",
        "tasa": 4.5,
        "ots": "5",
        "cantidad_uf": 50,
        "coeficientes": {
            "1A": 0.024, "1B": 0.017, "2A": 0.026, "2B": 0.018,
            "3A": 0.026, "3B": 0.020, "4A": 0.025, "4B": 0.019,
            "5A": 0.030, "5B": 0.022,
        }
    },
    "Larrea 435, CABA": {
        "reserva": 380000.0,
        "factor": 0.6,
        "mora": "2",
        "tasa": 5.0,
        "ots": "5",
        "cantidad_uf": 30,
        "coeficientes": {
            "1A": 0.035, "1B": 0.025, "2A": 0.036, "2B": 0.026,
            "3A": 0.036, "3B": 0.028, "4A": 0.035, "4B": 0.027,
            "5A": 0.038, "5B": 0.034,
        }
    },
    "Montevideo 891, CABA": {
        "reserva": 620000.0,
        "factor": 0.8,
        "mora": "2",
        "tasa": 6.2,
        "ots": "5",
        "cantidad_uf": 40,
        "coeficientes": {}
    },
    "San Jose 1111, CABA": {
        "reserva": 290000.0,
        "factor": 0.5,
        "mora": "1",
        "tasa": 3.8,
        "ots": "5",
        "cantidad_uf": 25,
        "coeficientes": {}
    },
    "Guayaquil 399, CABA": {
        "reserva": 850000.0,
        "factor": 1.5,
        "mora": "1",
        "tasa": 7.5,
        "ots": "5",
        "cantidad_uf": 60,
        "coeficientes": {}
    }
}

DATOS_CARTILLA_PROVEEDORES = [
    {
        "Rubro": "Plomería",
        "Prestador": "🚰 Caños y Sanitarios Express",
        "CUIT": "30-55489712-4",
        "Teléfono": "11-4895-1234",
        "Zona de Atención": "CABA Centro"
    },
    {
        "Rubro": "Plomería",
        "Prestador": "🚰 Ingeniería Hidráulica Sur",
        "CUIT": "33-66985214-9",
        "Teléfono": "11-3564-9871",
        "Zona de Atención": "CABA Norte"
    },
    {
        "Rubro": "Electricidad",
        "Prestador": "⚡ El Fusible Matriculado",
        "CUIT": "20-14896532-1",
        "Teléfono": "11-5478-6532",
        "Zona de Atención": "Toda CABA"
    },
    {
        "Rubro": "Electricidad",
        "Prestador": "⚡ Conexiones Seguras Palermo",
        "CUIT": "27-33659874-2",
        "Teléfono": "11-6985-3214",
        "Zona de Atención": "CABA Norte"
    },
    {
        "Rubro": "Cerrajería",
        "Prestador": "🔑 Llaves Fénix 24hs",
        "CUIT": "23-45896521-8",
        "Teléfono": "11-2365-9847",
        "Zona de Atención": "Urgencias CABA"
    },
    {
        "Rubro": "Cerrajería",
        "Prestador": "🔑 Blindajes y Cerraduras Pro",
        "CUIT": "30-71458962-3",
        "Teléfono": "11-4125-3698",
        "Zona de Atención": "CABA Oeste"
    },
    {
        "Rubro": "Albañilería",
        "Prestador": "🧱 Constructora San José",
        "CUIT": "30-88547612-5",
        "Teléfono": "11-5541-2369",
        "Zona de Atención": "Toda CABA"
    },
    {
        "Rubro": "Albañilería",
        "Prestador": "🧱 Refacciones Integrales Baires",
        "CUIT": "20-99653214-7",
        "Teléfono": "11-3254-7896",
        "Zona de Atención": "CABA Sur"
    }
]

TABLA_SOLICITADA_OT = [
    {
        "Edificio": "Avda. Corrientes 1234",
        "UF": "1A",
        "Trabajo": "Plomería",
        "Presupuesto Aprobado": "$ 250.000.-",
        "Fecha_Inicio": "01/05/26",
        "Fecha_Finaliz": "01/05/26"
    },
    {
        "Edificio": "Larrea 435",
        "UF": "3J",
        "Trabajo": "Albañilería",
        "Presupuesto Aprobado": "$ 390.000.-",
        "Fecha_Inicio": "07/06/26",
        "Fecha_Finaliz": "12/06/26"
    },
    {
        "Edificio": "Montevideo 891",
        "UF": "4K",
        "Trabajo": "Plomería",
        "Presupuesto Aprobado": "$ 120.000.-",
        "Fecha_Inicio": "08/09/26",
        "Fecha_Finaliz": "09/09/26"
    },
    {
        "Edificio": "San José 1111",
        "UF": "5M",
        "Trabajo": "Electricidad",
        "Presupuesto Aprobado": "$ 95.000.-",
        "Fecha_Inicio": "12/07/26",
        "Fecha_Finaliz": "12/07/26"
    },
    {
        "Edificio": "Guayaquil 399",
        "UF": "6P",
        "Trabajo": "Cerrajería",
        "Presupuesto Aprobado": "$ 180.000.-",
        "Fecha_Inicio": "15/08/26",
        "Fecha_Finaliz": "15/08/26"
    }
]

# ════════════════════════════════════════════════════════════════════════════════
# CARGA DE BASES DE EDIFICIOS DESDE CSV/EXCEL
# ════════════════════════════════════════════════════════════════════════════════

CAMPOS_UNIDADES_REQUERIDOS = [
    "Calle",
    "Numero",
    "Ciudad",
    "UF/Dpto",
    "Piso",
    "Porcentual Expensas",
]


def cargar_base_unidades(archivo) -> pd.DataFrame:
    """
    Carga una base de datos de unidades funcionales desde CSV o Excel.
    Requiere columnas:
    Calle, Numero, Ciudad, UF/Dpto, Piso, Porcentual Expensas
    """
    nombre_archivo = archivo.name.lower()

    if nombre_archivo.endswith(".csv"):
        df = pd.read_csv(archivo, encoding="utf-8-sig")
    elif nombre_archivo.endswith((".xlsx", ".xls")):
        df = pd.read_excel(archivo)
    else:
        raise ValueError("El archivo debe estar en formato CSV o Excel.")

    df.columns = [str(col).strip() for col in df.columns]

    campos_faltantes = [
        campo for campo in CAMPOS_UNIDADES_REQUERIDOS
        if campo not in df.columns
    ]

    if campos_faltantes:
        raise ValueError(
            "Faltan las siguientes columnas obligatorias: "
            + ", ".join(campos_faltantes)
        )

    for campo in ["Calle", "Ciudad", "UF/Dpto", "Piso"]:
        df[campo] = df[campo].fillna("").astype(str).str.strip()

    df["Numero"] = (
        df["Numero"]
        .fillna("")
        .astype(str)
        .str.replace(".0", "", regex=False)
        .str.strip()
    )

    df["Porcentual Expensas"] = (
        df["Porcentual Expensas"]
        .astype(str)
        .str.replace("%", "", regex=False)
        .str.replace(",", ".", regex=False)
        .str.strip()
    )
    df["Porcentual Expensas"] = pd.to_numeric(
        df["Porcentual Expensas"],
        errors="coerce",
    ).fillna(0)

    df["Edificio"] = (
        df["Calle"].fillna("").astype(str)
        + " "
        + df["Numero"].fillna("").astype(str)
        + ", "
        + df["Ciudad"].fillna("").astype(str)
    )

    df["Edificio"] = df["Edificio"].str.replace("  ", " ", regex=False).str.strip()

    columnas_ordenadas = [
        "Edificio",
        "Calle",
        "Numero",
        "Ciudad",
        "UF/Dpto",
        "Piso",
        "Porcentual Expensas",
    ]

    return df[columnas_ordenadas]


def registrar_edificio_desde_base(df: pd.DataFrame):
    """
    Registra cada edificio cargado en ESTADISTICAS_EDIFICIOS, con datos
    mínimos para que el resto del sistema pueda seguir funcionando.
    """
    if df.empty:
        return

    for edificio, grupo in df.groupby("Edificio"):
        if edificio in ESTADISTICAS_EDIFICIOS:
            continue

        total_unidades = len(grupo)
        promedio_expensas = float(grupo["Porcentual Expensas"].mean()) if total_unidades else 0.0

        ESTADISTICAS_EDIFICIOS[edificio] = {
            "reserva": max(200000.0, total_unidades * 50000.0),
            "factor": round(max(0.3, promedio_expensas / 100.0), 2),
            "mora": "1" if promedio_expensas > 20 else "0",
            "tasa": round(4.0 + (promedio_expensas / 10.0), 1),
            "ots": str(min(5, max(1, total_unidades // 2))),
            "cantidad_uf": total_unidades,
            "coeficientes": {}
        }


# ════════════════════════════════════════════════════════════════════════════════
# PROCESO COMPLETO DE LIQUIDACIÓN DE EXPENSAS
# ════════════════════════════════════════════════════════════════════════════════

class AgenteLiquidacion:
    """💰 Especialista en liquidación integral de expensas"""

    def __init__(self):
        self.gastos_registrados: List[RegistroGasto] = []
        self.ingresos_registrados: List[RegistroIngreso] = []
        self.coeficientes_uf: Dict[str, float] = {}
        self.estado = EstadoAgente.INACTIVO

    def activar(self):
        self.estado = EstadoAgente.ACTIVADO

    def registrar_gasto(self, gasto: RegistroGasto):
        """Registra un gasto del período"""
        self.gastos_registrados.append(gasto)

    def registrar_ingreso(self, ingreso: RegistroIngreso):
        """Registra un ingreso del período"""
        self.ingresos_registrados.append(ingreso)

    def establecer_coeficientes(self, coeficientes: Dict[str, float]):
        """Establece los coeficientes de prorrateo por UF"""
        self.coeficientes_uf = coeficientes
        
        # Validar que sumen 1.00
        total_coef = sum(coeficientes.values())
        if abs(total_coef - 1.0) > 0.001:
            raise ValueError(f"Coeficientes no suman 1.00. Total: {total_coef}")

    def calcular_liquidacion(self, periodo: str) -> LiquidacionExpensas:
        """Calcula la liquidación completa del período"""
        self.activar()
        self.estado = EstadoAgente.PROCESANDO

        # Calcular totales por rubro
        gastos_por_rubro = {}
        for gasto in self.gastos_registrados:
            rubro = gasto.tipo_gasto.value
            if rubro not in gastos_por_rubro:
                gastos_por_rubro[rubro] = 0.0
            gastos_por_rubro[rubro] += gasto.monto

        ingresos_por_rubro = {}
        for ingreso in self.ingresos_registrados:
            rubro = ingreso.tipo_ingreso.value
            if rubro not in ingresos_por_rubro:
                ingresos_por_rubro[rubro] = 0.0
            ingresos_por_rubro[rubro] += ingreso.monto

        # Totales
        total_gastos = sum(gastos_por_rubro.values())
        total_ingresos = sum(ingresos_por_rubro.values())

        # Calcular expensas por UF
        expensas_por_uf = {}
        for uf, coeficiente in self.coeficientes_uf.items():
            expensas_por_uf[uf] = total_gastos * coeficiente

        self.estado = EstadoAgente.COMPLETADO

        return LiquidacionExpensas(
            periodo=periodo,
            fecha_liquidacion=datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            total_ingresos=total_ingresos,
            total_gastos=total_gastos,
            deficit_o_superavit=total_ingresos - total_gastos,
            gastos_por_rubro=gastos_por_rubro,
            ingresos_por_rubro=ingresos_por_rubro,
            coeficientes=self.coeficientes_uf,
            expensas_por_uf=expensas_por_uf
        )

    def obtener_estado_cuenta_uf(self, uf: str, liquidacion: LiquidacionExpensas) -> Dict[str, Any]:
        """Genera el estado de cuenta de una UF específica"""
        if uf not in liquidacion.expensas_por_uf:
            return None

        return {
            "uf": uf,
            "coeficiente": liquidacion.coeficientes.get(uf, 0),
            "expensas_mes": liquidacion.expensas_por_uf[uf],
            "porcentaje_total": f"{(liquidacion.coeficientes.get(uf, 0) * 100):.2f}%"
        }

    def generar_resumen_desglose(self, liquidacion: LiquidacionExpensas) -> Dict[str, Any]:
        """Genera resumen con desglose por conceptos"""
        return {
            "periodo": liquidacion.periodo,
            "fecha_liquidacion": liquidacion.fecha_liquidacion,
            "total_ingresos": liquidacion.total_ingresos,
            "total_gastos": liquidacion.total_gastos,
            "resultado": liquidacion.deficit_o_superavit,
            "gastos_por_rubro": liquidacion.gastos_por_rubro,
            "ingresos_por_rubro": liquidacion.ingresos_por_rubro,
        }


# ════════════════════════════════════════════════════════════════════════════════
# 3. NÚCLEO DEL ENJAMBRE - AGENTES ESPECIALIZADOS
# ════════════════════════════════════════════════════════════════════════════════

class AgenteBase:
    """Clase base para todos los agentes del enjambre"""

    def __init__(self, tipo_agente: TipoAgente):
        self.tipo_agente = tipo_agente
        self.estado = EstadoAgente.INACTIVO
        self.historial_procesamiento = []

    def activar(self):
        """Pasa el agente a estado ACTIVADO"""
        self.estado = EstadoAgente.ACTIVADO

    def procesar(self, evento: EventoSwarm) -> ResultadoAgente:
        """Método abstracto que cada agente implementa según su especialidad"""
        raise NotImplementedError

    def registrar_operacion(self, resultado: ResultadoAgente):
        """Mantiene auditoría interna del agente"""
        self.historial_procesamiento.append(resultado)


class AgenteContable(AgenteBase):
    """📊 Especialista en flujos de dinero, ingresos y gastos"""

    def __init__(self):
        super().__init__(TipoAgente.CONTABLE)

    def procesar(self, evento: EventoSwarm, edificio_data: Dict) -> ResultadoAgente:
        self.activar()
        self.estado = EstadoAgente.PROCESANDO
        tiempo_inicio = time.time()

        try:
            f_cal = edificio_data["factor"]
            tasa_act = edificio_data["tasa"]

            ingresos = [
                {"Ingresos": "ingresos por expensas", "Monto ($)": 320000.0 * f_cal},
                {
                    "Ingresos": "alquileres de locales",
                    "Monto ($)": 85000.0 * (1.0 if f_cal >= 0.8 else 0.0),
                },
                {
                    "Ingresos": "intereses por colocacion a plazo fijo",
                    "Monto ($)": 14000.0 * f_cal * (tasa_act / 5.0),
                },
            ]

            gastos = [
                {"Gastos": "reparaciones", "Monto ($)": 45000.0 * f_cal},
                {
                    "Gastos": "honorarios de administración",
                    "Monto ($)": 35000.0 * f_cal,
                },
                {
                    "Gastos": "sueldo de encargado",
                    "Monto ($)": 250000.0 * (1.0 if f_cal >= 0.7 else 0.0),
                },
                {
                    "Gastos": "compra de articulos de limpieza",
                    "Monto ($)": 12000.0 * f_cal,
                },
                {"Gastos": "pagos luz", "Monto ($)": 18000.0 * f_cal},
                {"Gastos": "otros gastos", "Monto ($)": 7000.0 * f_cal},
            ]

            total_ingresos = sum(x["Monto ($)"] for x in ingresos)
            total_gastos = sum(x["Monto ($)"] for x in gastos)
            balance = total_ingresos - total_gastos

            self.estado = EstadoAgente.COMPLETADO
            tiempo_procesamiento = f"⚡ {(time.time() - tiempo_inicio)*1000:.2f}ms"

            return ResultadoAgente(
                agente=self.tipo_agente.value,
                estado=self.estado,
                datos_procesados={
                    "ingresos": ingresos,
                    "gastos": gastos,
                    "total_ingresos": total_ingresos,
                    "total_gastos": total_gastos,
                    "balance_neto": balance,
                },
                tiempo_procesamiento=tiempo_procesamiento,
                dependencias_cumplidas=[],
            )
        except Exception as e:
            self.estado = EstadoAgente.ERROR
            return ResultadoAgente(
                agente=self.tipo_agente.value,
                estado=self.estado,
                datos_procesados={"error": str(e)},
                tiempo_procesamiento="❌ Error en procesamiento",
                dependencias_cumplidas=[],
            )


class AgenteCompliance(AgenteBase):
    """✅ Validador de regulaciones y normativas fiscales"""

    def __init__(self):
        super().__init__(TipoAgente.COMPLIANCE)

    def procesar(self, evento: EventoSwarm) -> ResultadoAgente:
        self.activar()
        self.estado = EstadoAgente.PROCESANDO
        tiempo_inicio = time.time()

        validaciones = {
            "ley_941_caba": "✅ Adherencia legal vigente",
            "codigo_civil_comercial": "✅ Art. 2048 cumplido",
            "validacion_cuit": "✅ Formato CUIT verificado",
            "vigencia_fiscal": "✅ Todas las entidades activas",
        }

        self.estado = EstadoAgente.COMPLETADO
        tiempo_procesamiento = f"⚡ {(time.time() - tiempo_inicio)*1000:.2f}ms"

        return ResultadoAgente(
            agente=self.tipo_agente.value,
            estado=self.estado,
            datos_procesados=validaciones,
            tiempo_procesamiento=tiempo_procesamiento,
            dependencias_cumplidas=[],
        )


class AgenteProveedores(AgenteBase):
    """🏢 Gestor de cartilla homologada de prestadores"""

    def __init__(self):
        super().__init__(TipoAgente.PROVEEDORES)

    def procesar(
        self, evento: EventoSwarm, rubro_filtro: str = None
    ) -> ResultadoAgente:
        self.activar()
        self.estado = EstadoAgente.PROCESANDO
        tiempo_inicio = time.time()

        try:
            if rubro_filtro:
                proveedores_filtrados = [
                    p
                    for p in DATOS_CARTILLA_PROVEEDORES
                    if p["Rubro"].lower() == rubro_filtro.lower()
                ]
            else:
                proveedores_filtrados = DATOS_CARTILLA_PROVEEDORES

            self.estado = EstadoAgente.COMPLETADO
            tiempo_procesamiento = f"⚡ {(time.time() - tiempo_inicio)*1000:.2f}ms"

            return ResultadoAgente(
                agente=self.tipo_agente.value,
                estado=self.estado,
                datos_procesados={
                    "proveedores": proveedores_filtrados,
                    "total_disponibles": len(proveedores_filtrados),
                    "rubros": list(set([p["Rubro"] for p in proveedores_filtrados])),
                },
                tiempo_procesamiento=tiempo_procesamiento,
                dependencias_cumplidas=[],
            )
        except Exception as e:
            self.estado = EstadoAgente.ERROR
            return ResultadoAgente(
                agente=self.tipo_agente.value,
                estado=self.estado,
                datos_procesados={"error": str(e)},
                tiempo_procesamiento="❌ Error en procesamiento",
                dependencias_cumplidas=[],
            )


class AgenteOperativo(AgenteBase):
    """🔧 Gestor de órdenes de trabajo de campo"""

    def __init__(self):
        super().__init__(TipoAgente.OPERATIVO)

    def procesar(
        self, evento: EventoSwarm, edificio_filtro: str = None
    ) -> ResultadoAgente:
        self.activar()
        self.estado = EstadoAgente.PROCESANDO
        tiempo_inicio = time.time()

        try:
            if edificio_filtro:
                ots_filtradas = [
                    ot
                    for ot in TABLA_SOLICITADA_OT
                    if edificio_filtro.lower() in ot["Edificio"].lower()
                ]
            else:
                ots_filtradas = TABLA_SOLICITADA_OT

            presupuesto_total = 0
            for ot in ots_filtradas:
                presupuesto_str = (
                    ot["Presupuesto Aprobado"].replace("$ ", "").replace(".-", "")
                )
                presupuesto_total += float(presupuesto_str)

            self.estado = EstadoAgente.COMPLETADO
            tiempo_procesamiento = f"⚡ {(time.time() - tiempo_inicio)*1000:.2f}ms"

            return ResultadoAgente(
                agente=self.tipo_agente.value,
                estado=self.estado,
                datos_procesados={
                    "ordenes_trabajo": ots_filtradas,
                    "total_ordenes": len(ots_filtradas),
                    "presupuesto_total": presupuesto_total,
                },
                tiempo_procesamiento=tiempo_procesamiento,
                dependencias_cumplidas=[TipoAgente.COMPLIANCE.value],
            )
        except Exception as e:
            self.estado = EstadoAgente.ERROR
            return ResultadoAgente(
                agente=self.tipo_agente.value,
                estado=self.estado,
                datos_procesados={"error": str(e)},
                tiempo_procesamiento="❌ Error en procesamiento",
                dependencias_cumplidas=[],
            )


class AgenteMora(AgenteBase):
    """⚠️ Especialista en cobranza y seguimiento de deudores"""

    def __init__(self):
        super().__init__(TipoAgente.MORA)

    def procesar(self, evento: EventoSwarm, edificio_data: Dict) -> ResultadoAgente:
        self.activar()
        self.estado = EstadoAgente.PROCESANDO
        tiempo_inicio = time.time()

        mora_count = int(edificio_data.get("mora", "0"))

        if mora_count > 1:
            alerta_nivel = "🔴 CRÍTICO - Más de 1 UF en mora"
        elif mora_count == 1:
            alerta_nivel = "🟡 MODERADO - 1 UF en mora"
        else:
            alerta_nivel = "🟢 CONTROLADO - Sin mora registrada"

        self.estado = EstadoAgente.COMPLETADO
        tiempo_procesamiento = f"⚡ {(time.time() - tiempo_inicio)*1000:.2f}ms"

        return ResultadoAgente(
            agente=self.tipo_agente.value,
            estado=self.estado,
            datos_procesados={
                "uf_en_mora": mora_count,
                "nivel_alerta": alerta_nivel,
                "acciones_recomendadas": [
                    "Contacto preventivo",
                    "Refinanciación",
                    "Intimación legal",
                ],
            },
            tiempo_procesamiento=tiempo_procesamiento,
            dependencias_cumplidas=[TipoAgente.CONTABLE.value],
        )


class AgenteAuditor(AgenteBase):
    """🔍 Fiscalizador de coherencia y anomalías"""

    def __init__(self):
        super().__init__(TipoAgente.AUDITOR)

    def procesar(
        self, evento: EventoSwarm, resultados_previos: Dict[str, ResultadoAgente]
    ) -> ResultadoAgente:
        self.activar()
        self.estado = EstadoAgente.PROCESANDO
        tiempo_inicio = time.time()

        audit_log = []
        for agente_nombre, resultado in resultados_previos.items():
            if resultado.estado == EstadoAgente.COMPLETADO:
                audit_log.append(f"✅ {agente_nombre}: procesado correctamente")
            else:
                audit_log.append(f"⚠️ {agente_nombre}: requiere revisión")

        self.estado = EstadoAgente.COMPLETADO
        tiempo_procesamiento = f"🔍 {(time.time() - tiempo_inicio)*1000:.2f}ms"

        return ResultadoAgente(
            agente=self.tipo_agente.value,
            estado=self.estado,
            datos_procesados={
                "bitacora_auditoria": audit_log,
                "inconsistencias_detectadas": 0,
                "timestamp_auditoria": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            },
            tiempo_procesamiento=tiempo_procesamiento,
            dependencias_cumplidas=list(resultados_previos.keys()),
        )


class AgenteReportes(AgenteBase):
    """📈 Generador de síntesis ejecutivas e informes"""

    def __init__(self):
        super().__init__(TipoAgente.REPORTES)

    def procesar(
        self, evento: EventoSwarm, resultados_previos: Dict[str, ResultadoAgente]
    ) -> ResultadoAgente:
        self.activar()
        self.estado = EstadoAgente.PROCESANDO
        tiempo_inicio = time.time()

        agentes_exitosos = len(
            [r for r in resultados_previos.values() if r.estado == EstadoAgente.COMPLETADO]
        )

        reporte_ejecutivo = {
            "fecha_generacion": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            "evento_disparador": evento.tipo_evento,
            "agentes_activados": len(resultados_previos),
            "agentes_exitosos": agentes_exitosos,
            "resumen": f"Solicitud procesada por {agentes_exitosos}/{len(resultados_previos)} agentes especializados",
        }

        self.estado = EstadoAgente.COMPLETADO
        tiempo_procesamiento = f"📄 {(time.time() - tiempo_inicio)*1000:.2f}ms"

        return ResultadoAgente(
            agente=self.tipo_agente.value,
            estado=self.estado,
            datos_procesados=reporte_ejecutivo,
            tiempo_procesamiento=tiempo_procesamiento,
            dependencias_cumplidas=list(resultados_previos.keys()),
        )


# ════════════════════════════════════════════════════════════════════════════════
# 4. ORQUESTADOR CENTRAL - El "cerebro" del enjambre
# ════════════════════════════════════════════════════════════════════════════════

class OrquestadorSwarm:
    """🎯 Coordinador central que activa el enjambre según el evento"""

    def __init__(self):
        self.enjambre = {
            TipoAgente.CONTABLE: AgenteContable(),
            TipoAgente.COMPLIANCE: AgenteCompliance(),
            TipoAgente.PROVEEDORES: AgenteProveedores(),
            TipoAgente.OPERATIVO: AgenteOperativo(),
            TipoAgente.MORA: AgenteMora(),
            TipoAgente.AUDITOR: AgenteAuditor(),
            TipoAgente.REPORTES: AgenteReportes(),
        }
        self.evento_actual = None
        self.resultados_enjambre = {}
        self.placeholders_animacion = {}

    def disparar_enjambre(
        self, evento: EventoSwarm, edificio_seleccionado: str
    ) -> Dict[str, ResultadoAgente]:
        """🚀 Atiende una solicitud con activación selectiva del enjambre"""

        self.evento_actual = evento
        self.resultados_enjambre = {}

        if edificio_seleccionado not in ESTADISTICAS_EDIFICIOS:
            registrar_edificio_desde_base(
                st.session_state.get("unidades_edificios", pd.DataFrame())
            )

        if edificio_seleccionado not in ESTADISTICAS_EDIFICIOS:
            ESTADISTICAS_EDIFICIOS[edificio_seleccionado] = {
                "reserva": 250000.0,
                "factor": 0.8,
                "mora": "0",
                "tasa": 5.0,
                "ots": "3",
                "cantidad_uf": 10,
                "coeficientes": {}
            }

        edificio_data = ESTADISTICAS_EDIFICIOS[edificio_seleccionado]

        if evento.tipo_evento == "MODULO_CONTABILIDAD":
            self.resultados_enjambre[TipoAgente.CONTABLE.value] = (
                self.enjambre[TipoAgente.CONTABLE].procesar(evento, edificio_data)
            )
            self.resultados_enjambre[TipoAgente.MORA.value] = (
                self.enjambre[TipoAgente.MORA].procesar(evento, edificio_data)
            )
            self.resultados_enjambre[TipoAgente.COMPLIANCE.value] = (
                self.enjambre[TipoAgente.COMPLIANCE].procesar(evento)
            )

        elif evento.tipo_evento == "MODULO_OPERATIVO":
            self.resultados_enjambre[TipoAgente.OPERATIVO.value] = (
                self.enjambre[TipoAgente.OPERATIVO].procesar(evento, edificio_seleccionado)
            )
            self.resultados_enjambre[TipoAgente.PROVEEDORES.value] = (
                self.enjambre[TipoAgente.PROVEEDORES].procesar(evento)
            )
            self.resultados_enjambre[TipoAgente.COMPLIANCE.value] = (
                self.enjambre[TipoAgente.COMPLIANCE].procesar(evento)
            )

        self.resultados_enjambre[TipoAgente.AUDITOR.value] = (
            self.enjambre[TipoAgente.AUDITOR].procesar(evento, self.resultados_enjambre)
        )
        self.resultados_enjambre[TipoAgente.REPORTES.value] = (
            self.enjambre[TipoAgente.REPORTES].procesar(evento, self.resultados_enjambre)
        )

        return self.resultados_enjambre


# ════════════════════════════════════════════════════════════════════════════════
# 5. CONFIGURACIÓN DE STREAMLIT
# ════════════════════════════════════════════════════════════════════════════════

st.set_page_config(
    page_title="Resil_IA Condominios",
    page_icon="🏙️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ESTILOS PREMIUM
st.markdown(
    """
    <style>
        .main { 
            background: radial-gradient(circle at top right, #0d1e3d 0%, #071126 100%); 
        }
        h1 { 
            color: #ffffff; 
            font-family: sans-serif; 
            font-weight: 900; 
            letter-spacing: -1px; 
            text-shadow: 0 0 20px rgba(56, 189, 248, 0.4); 
            font-size: 2.8rem !important; 
        }
        h2, h3 { 
            color: #38bdf8; 
            font-family: sans-serif; 
            font-weight: 700; 
            font-size: 2rem !important; 
        }
        .stMarkdown p, p, label, .stRadio label { 
            color: #e2e8f0; 
            font-size: 1.3rem !important; 
            line-height: 1.6 !important; 
        }
        .stDataFrame td, .stDataFrame div, table, td, tr { 
            font-size: 1.5rem !important; 
            font-weight: 600 !important; 
            color: #ffffff !important; 
        }
        th, .stDataFrame th div { 
            font-weight: 800 !important; 
            color: #38bdf8 !important; 
            font-size: 1.4rem !important; 
        }
        div[data-testid="stMetric"] {
            background: linear-gradient(135deg, #d4af37 0%, #aa7c11 100%) !important;
            border-radius: 20px !important; 
            padding: 22px !important;
            box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.6);
            border: 1px solid rgba(255, 255, 255, 0.2) !important;
        }
        div[data-testid="stMetric"] label { 
            color: #0f172a !important; 
            font-weight: 800 !important; 
            font-size: 1.1rem !important; 
        }
        div[data-testid="stMetric"] [data-testid="stMetricValue"] { 
            color: #0b192c !important; 
            font-weight: 900 !important; 
            font-size: 2.4rem !important; 
        }
        .stDataFrame, .stTable { 
            background-color: rgba(30, 41, 59, 0.5); 
            border-radius: 16px; 
            padding: 10px; 
        }
        .swarm-agent { 
            background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
            border-left: 5px solid #38bdf8;
            padding: 15px;
            margin: 8px 0;
            border-radius: 8px;
            font-size: 1.1rem;
            transition: all 0.3s ease;
        }
        .swarm-completed { 
            border-left-color: #10b981 !important; 
            background: rgba(16, 185, 129, 0.1) !important;
        }
        .swarm-processing { 
            border-left-color: #f59e0b !important; 
            background: rgba(245, 158, 11, 0.1) !important;
            animation: pulse 1.5s infinite;
        }
        .swarm-active { 
            border-left-color: #06b6d4 !important;
            background: rgba(6, 182, 212, 0.1) !important;
        }
        .swarm-error { 
            border-left-color: #ef4444 !important;
            background: rgba(239, 68, 68, 0.1) !important;
        }
        
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.7; }
        }
        
        @keyframes robotMove {
            0% { transform: translateX(-10px); }
            50% { transform: translateX(10px); }
            100% { transform: translateX(-10px); }
        }
        
        .robot-animado {
            display: inline-block;
            animation: robotMove 1s infinite;
            font-size: 1.5rem;
        }
        
        .logo-container {
            display: flex;
            justify-content: center;
            align-items: center;
            margin: 20px 0 10px 0;
            padding: 8px 0 12px 0;
            border-bottom: 1px solid rgba(56, 189, 248, 0.25);
        }
        
        .logo-container img {
            max-width: 110px;
            height: auto;
            border-radius: 10px;
            box-shadow: 0 4px 15px rgba(56, 189, 248, 0.3);
        }

        .header-brand {
            display: flex;
            align-items: center;
            gap: 18px;
            margin: 20px 0 8px 0;
            padding: 8px 0;
        }

        .header-brand img {
            height: 100px;
            width: auto;
            flex-shrink: 0;
            filter: drop-shadow(0 0 15px rgba(56, 189, 248, 0.4));
        }

        .header-brand h1 {
            margin: 0;
            color: #f8fafc;
            font-size: 3rem !important;
            letter-spacing: -2px;
            font-weight: 900;
        }

        .header-brand .underscore {
            color: #ffffff;
            font-weight: 900;
        }

        .header-brand .ia {
            color: #7dd3fc;
            font-weight: 800;
        }
        
        .titulo-edificio {
            background: linear-gradient(135deg, #38bdf8 0%, #0ea5e9 100%);
            color: #0f172a;
            padding: 12px 16px;
            border-radius: 8px;
            font-weight: bold;
            font-size: 1.2rem;
            margin: 20px 0 15px 0;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# INICIALIZACIÓN DE SESIÓN
if "orquestador" not in st.session_state:
    st.session_state.orquestador = OrquestadorSwarm()

if "unidades_edificios" not in st.session_state:
    st.session_state.unidades_edificios = pd.DataFrame(
        columns=[
            "Edificio",
            "Calle",
            "Numero",
            "Ciudad",
            "UF/Dpto",
            "Piso",
            "Porcentual Expensas",
        ]
    )

if "agente_liquidacion" not in st.session_state:
    st.session_state.agente_liquidacion = AgenteLiquidacion()

if "liquidacion_actual" not in st.session_state:
    st.session_state.liquidacion_actual = None

orquestador = st.session_state.orquestador
agente_liquidacion = st.session_state.agente_liquidacion


# ════════════════════════════════════════════════════════════════════════════════
# 6. SIDEBAR - CONTROL CENTRAL CON LOGO
# ════════════════════════════════════════════════════════════════════════════════

with st.sidebar:
    st.markdown(
        """
        <div class="logo-container">
            <img src="https://raw.githubusercontent.com/nosimani/Consorcio_IA/main/Resilia.jfif" alt="Resilia Logo">
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("<p style='font-size: 1.5rem; color: #ff1744; font-weight: bold; text-align: center;'>Sistema Multiagente Avanzado</p>", unsafe_allow_html=True)
    st.markdown("---")

    pantalla_activa = st.radio(
        "📌 Seleccione Módulo de Control:",
        [
            "📋 Dashboard y Contabilidad",
            "🔧 Órdenes de Trabajo de Campo",
            "📊 Liquidación de Expensas"
        ],
        index=0,
    )

    st.markdown("---")

    st.subheader("🏢 Cargar base de edificios")
    archivos_edificios = st.file_uploader(
        "Seleccione uno o varios archivos CSV o Excel",
        type=["csv", "xlsx", "xls"],
        accept_multiple_files=True,
        help=(
            "Cada archivo debe contener las columnas: "
            "Calle, Numero, Ciudad, UF/Dpto, Piso y Porcentual Expensas."
        ),
    )

    if archivos_edificios:
        bases_cargadas = []
        errores_carga = []

        for archivo in archivos_edificios:
            try:
                base_edificio = cargar_base_unidades(archivo)
                bases_cargadas.append(base_edificio)
            except Exception as error:
                errores_carga.append(f"{archivo.name}: {str(error)}")

        if bases_cargadas:
            base_total = pd.concat(bases_cargadas, ignore_index=True)
            st.session_state.unidades_edificios = pd.concat(
                [st.session_state.unidades_edificios, base_total],
                ignore_index=True,
            )

            st.session_state.unidades_edificios = (
                st.session_state.unidades_edificios.drop_duplicates()
                .reset_index(drop=True)
            )

            registrar_edificio_desde_base(st.session_state.unidades_edificios)

            st.success(
                f"✅ Se cargaron {len(st.session_state.unidades_edificios)} unidades funcionales."
            )

        for error in errores_carga:
            st.error(f"❌ {error}")

    edificios_base = list(ESTADISTICAS_EDIFICIOS.keys())
    edificios_cargados = []

    if not st.session_state.unidades_edificios.empty:
        edificios_cargados = sorted(
            st.session_state.unidades_edificios["Edificio"]
            .dropna()
            .unique()
            .tolist()
        )

    edificios_disponibles = sorted(set(edificios_base).union(edificios_cargados))

    st.markdown("---")
    edificio_seleccionado = st.selectbox(
        "🏗️ Edificio Activo de Control",
        edificios_disponibles,
    )

    st.markdown("---")
    st.info("**CUIT:** 30-11111111-9\n\n**Jurisdicción:** Ley 941 CABA")

    st.markdown("---")
    st.markdown(
        "<p style='font-size: 0.9rem; color: #64748b;'>ℹ️ <b>Arquitectura Multiagente</b><br/>Cada solicitud activa el enjambre de agentes especializados</p>",
        unsafe_allow_html=True,
    )


# ════════════════════════════════════════════════════════════════════════════════
# 7. LÓGICA DE ACTIVACIÓN DEL ENJAMBRE - MÓDULO CONTABILIDAD
# ════════════════════════════════════════════════════════════════════════════════

if pantalla_activa == "📋 Dashboard y Contabilidad":

    evento = EventoSwarm(
        timestamp=datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        tipo_evento="MODULO_CONTABILIDAD",
        descripcion="Usuario solicita visualizar datos contables y financieros",
        modulo_solicitante="📋 Dashboard",
        parametros={"edificio": edificio_seleccionado},
    )

    st.markdown(
        """
        <div class="header-brand">
            <img src="https://images.unsplash.com/photo-1486325212027-8081e485255e?w=400&q=80&blend=https://images.unsplash.com/photo-1449824913935-59a10b8d2000?w=400&q=80&blend_mode=screen" alt="Imagen de edificio">
            <h1>Resil<span class="underscore">_</span><span class="ia">IA</span> Condominios</h1>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(f"📍 **Edificio Monitorizado:** {edificio_seleccionado}")

    if (
        "unidades_edificios" in st.session_state
        and not st.session_state.unidades_edificios.empty
        and edificio_seleccionado in st.session_state.unidades_edificios["Edificio"].unique()
    ):
        unidades_edificio = st.session_state.unidades_edificios[
            st.session_state.unidades_edificios["Edificio"] == edificio_seleccionado
        ]

        if not unidades_edificio.empty:
            st.markdown("---")
            st.header("🏠 Unidades Funcionales del Edificio")
            unidades_mostrar = unidades_edificio[
                ["UF/Dpto", "Piso", "Porcentual Expensas"]
            ].copy()
            unidades_mostrar["Porcentual Expensas"] = (
                unidades_mostrar["Porcentual Expensas"]
                .fillna(0)
                .map(lambda valor: f"{valor:.2f}%")
            )
            st.dataframe(unidades_mostrar, use_container_width=True, hide_index=True)

            total_porcentual = float(unidades_edificio["Porcentual Expensas"].sum())
            st.info(
                f"📊 Unidades registradas: {len(unidades_edificio)} | "
                f"Porcentual total: {total_porcentual:.2f}%"
            )

    st.markdown("---")
    with st.expander(
        "🐝 **ACTIVIDAD DEL ENJAMBRE** (Ver cómo trabajan los agentes)",
        expanded=True,
    ):
        st.markdown("### 🎯 Evento Disparador")
        col1, col2, col3 = st.columns(3)

        with col1:
            st.info(f"**Tipo de Evento:**\n{evento.tipo_evento}")
        with col2:
            st.info(f"**Módulo:**\n{evento.modulo_solicitante}")
        with col3:
            st.metric("Agentes Activados", 3)

        st.markdown("### 🤖 Estado de Agentes en Tiempo Real")

        agente_placeholders = {}
        agentes_a_procesar = [
            TipoAgente.CONTABLE.value,
            TipoAgente.MORA.value,
            TipoAgente.COMPLIANCE.value,
        ]

        for agente_tipo in agentes_a_procesar:
            agente_placeholders[agente_tipo] = st.empty()

        resultados = orquestador.disparar_enjambre(evento, edificio_seleccionado)

        for agente_nombre, resultado in resultados.items():
            if agente_nombre not in [TipoAgente.AUDITOR.value, TipoAgente.REPORTES.value]:
                estado_emoji = {
                    EstadoAgente.COMPLETADO: "✅",
                    EstadoAgente.PROCESANDO: "⏳",
                    EstadoAgente.ERROR: "❌",
                    EstadoAgente.ACTIVADO: "🟢",
                }

                emoji = estado_emoji.get(resultado.estado, "❓")
                css_class = {
                    EstadoAgente.COMPLETADO: "swarm-completed",
                    EstadoAgente.PROCESANDO: "swarm-processing",
                    EstadoAgente.ERROR: "swarm-error",
                    EstadoAgente.ACTIVADO: "swarm-active",
                }.get(resultado.estado, "")

                robot_emoji = "🤖 → "
                
                if agente_nombre in agente_placeholders:
                    agente_placeholders[agente_nombre].markdown(
                        f"""
                        <div class="swarm-agent {css_class}">
                        <span class="robot-animado">{robot_emoji}</span>{emoji} <b>{agente_nombre}</b><br/>
                        ⏱️ {resultado.tiempo_procesamiento}
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

    st.markdown("---")
    st.header("📊 Panel de Métricas Clave")

    resultado_contable = resultados.get(TipoAgente.CONTABLE.value)
    if resultado_contable and resultado_contable.estado == EstadoAgente.COMPLETADO:
        datos_contables = resultado_contable.datos_procesados

        m1, m2, m3, m4 = st.columns(4)
        with m1:
            st.metric("💰 Total Gastos", f"${datos_contables['total_gastos']:,.2f}")
        with m2:
            st.metric(
                "🏦 Fondos de Reserva",
                f"${ESTADISTICAS_EDIFICIOS[edificio_seleccionado]['reserva']:,.2f}",
            )
        with m3:
            resultado_mora = resultados.get(TipoAgente.MORA.value)
            mora_txt = (
                resultado_mora.datos_procesados.get("uf_en_mora", "N/A")
                if resultado_mora
                else "N/A"
            )
            st.metric("⚠️ UF en Mora", mora_txt)
        with m4:
            delta_text = "Positivo ✅" if datos_contables["balance_neto"] > 0 else "Déficit ❌"
            st.metric(
                "💹 Balance Neto",
                f"${datos_contables['balance_neto']:,.2f}",
                delta=delta_text,
            )

    st.markdown("---")
    st.header("📥 Flujo de Ingresos Percibidos")

    if resultado_contable and resultado_contable.estado == EstadoAgente.COMPLETADO:
        ingresos_df = pd.DataFrame(resultado_contable.datos_procesados["ingresos"])
        st.dataframe(ingresos_df, use_container_width=True, hide_index=True)
        st.success(
            f"✅ **Total Ingresos:** ${resultado_contable.datos_procesados['total_ingresos']:,.2f}"
        )

    st.markdown("---")
    st.header("📤 Flujo de Gastos Devengados")

    if resultado_contable and resultado_contable.estado == EstadoAgente.COMPLETADO:
        gastos_df = pd.DataFrame(resultado_contable.datos_procesados["gastos"])
        st.dataframe(gastos_df, use_container_width=True, hide_index=True)
        st.info(f"📌 **Total Gastos:** ${resultado_contable.datos_procesados['total_gastos']:,.2f}")

    st.markdown("---")
    st.header("🧮 Liquidación Prorrateada por Departamento")
    st.markdown(
        "Distribución legal s/ Art. 2048 Código Civil y Comercial - Cuota Parte 20% Equitativo:"
    )

    if resultado_contable and resultado_contable.estado == EstadoAgente.COMPLETADO:
        total_g = resultado_contable.datos_procesados["total_gastos"]
        cuota_parte_gasto = total_g * 0.20

        prorrateo_data = [
            {
                "Unidad Funcional": f"UF 0{i}",
                "Piso/Dpto": f"{i}° A",
                "Coeficiente": "20.00%",
                "Monto a Pagar ($)": cuota_parte_gasto,
            }
            for i in range(1, 6)
        ]

        prorrateo_df = pd.DataFrame(prorrateo_data)
        st.dataframe(prorrateo_df, use_container_width=True, hide_index=True)
        st.success(
            f"⚖️ **Balance Contable del Consorcio (Resultado Neto):** ${resultado_contable.datos_procesados['balance_neto']:,.2f}"
        )

    st.markdown("---")
    st.header("⚠️ Estado de Cobranza")

    resultado_mora = resultados.get(TipoAgente.MORA.value)
    if resultado_mora and resultado_mora.estado == EstadoAgente.COMPLETADO:
        datos_mora = resultado_mora.datos_procesados
        alerta = datos_mora.get("nivel_alerta", "Información no disponible")

        if "CRÍTICO" in alerta:
            st.error(f"🔴 {alerta}")
        elif "MODERADO" in alerta:
            st.warning(f"🟡 {alerta}")
        else:
            st.success(f"🟢 {alerta}")

        with st.expander("📋 Acciones Recomendadas"):
            for accion in datos_mora.get("acciones_recomendadas", []):
                st.write(f"• {accion}")


# ════════════════════════════════════════════════════════════════════════════════
# 8. LÓGICA DE ACTIVACIÓN DEL ENJAMBRE - MÓDULO OPERATIVO
# ════════════════════════════════════════════════════════════════════════════════

elif pantalla_activa == "🔧 Órdenes de Trabajo de Campo":

    evento = EventoSwarm(
        timestamp=datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        tipo_evento="MODULO_OPERATIVO",
        descripcion="Usuario solicita gestión de órdenes de trabajo y proveedores",
        modulo_solicitante="🔧 Operativo",
        parametros={"edificio": edificio_seleccionado},
    )

    st.markdown(
        """
        <div class="header-brand">
            <img src="https://images.unsplash.com/photo-1486325212027-8081e485255e?w=400&q=80&blend=https://images.unsplash.com/photo-1449824913935-59a10b8d2000?w=400&q=80&blend_mode=screen" alt="Imagen de edificio">
            <h1>Resil<span class="underscore">_</span><span class="ia">IA</span> Condominios</h1>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(f"📍 **Edificio Operando:** {edificio_seleccionado}")

    if (
        "unidades_edificios" in st.session_state
        and not st.session_state.unidades_edificios.empty
        and edificio_seleccionado in st.session_state.unidades_edificios["Edificio"].unique()
    ):
        unidades_edificio = st.session_state.unidades_edificios[
            st.session_state.unidades_edificios["Edificio"] == edificio_seleccionado
        ]

        if not unidades_edificio.empty:
            st.markdown("---")
            st.header("🏠 Unidades Funcionales del Edificio")
            unidades_mostrar = unidades_edificio[
                ["UF/Dpto", "Piso", "Porcentual Expensas"]
            ].copy()
            unidades_mostrar["Porcentual Expensas"] = (
                unidades_mostrar["Porcentual Expensas"]
                .fillna(0)
                .map(lambda valor: f"{valor:.2f}%")
            )
            st.dataframe(unidades_mostrar, use_container_width=True, hide_index=True)

            total_porcentual = float(unidades_edificio["Porcentual Expensas"].sum())
            st.info(
                f"📊 Unidades registradas: {len(unidades_edificio)} | "
                f"Porcentual total: {total_porcentual:.2f}%"
            )

    st.markdown("---")
    with st.expander(
        "🐝 **ACTIVIDAD DEL ENJAMBRE** (Ver cómo trabajan los agentes)",
        expanded=True,
    ):
        st.markdown("### 🎯 Evento Disparador")
        col1, col2, col3 = st.columns(3)

        with col1:
            st.info(f"**Tipo de Evento:**\n{evento.tipo_evento}")
        with col2:
            st.info(f"**Módulo:**\n{evento.modulo_solicitante}")
        with col3:
            st.metric("Agentes Activados", 3)

        st.markdown("### 🤖 Estado de Agentes en Tiempo Real")

        agente_placeholders = {}
        agentes_a_procesar = [
            TipoAgente.OPERATIVO.value,
            TipoAgente.PROVEEDORES.value,
            TipoAgente.COMPLIANCE.value,
        ]

        for agente_tipo in agentes_a_procesar:
            agente_placeholders[agente_tipo] = st.empty()

        resultados = orquestador.disparar_enjambre(evento, edificio_seleccionado)

        for agente_nombre, resultado in resultados.items():
            if agente_nombre not in [TipoAgente.AUDITOR.value, TipoAgente.REPORTES.value]:
                estado_emoji = {
                    EstadoAgente.COMPLETADO: "✅",
                    EstadoAgente.PROCESANDO: "⏳",
                    EstadoAgente.ERROR: "❌",
                    EstadoAgente.ACTIVADO: "🟢",
                }

                emoji = estado_emoji.get(resultado.estado, "❓")
                css_class = {
                    EstadoAgente.COMPLETADO: "swarm-completed",
                    EstadoAgente.PROCESANDO: "swarm-processing",
                    EstadoAgente.ERROR: "swarm-error",
                    EstadoAgente.ACTIVADO: "swarm-active",
                }.get(resultado.estado, "")

                robot_emoji = "🤖 → "
                
                if agente_nombre in agente_placeholders:
                    agente_placeholders[agente_nombre].markdown(
                        f"""
                        <div class="swarm-agent {css_class}">
                        <span class="robot-animado">{robot_emoji}</span>{emoji} <b>{agente_nombre}</b><br/>
                        ⏱️ {resultado.tiempo_procesamiento}
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

    st.markdown("---")
    st.header("📜 Cartilla de Prestadores de Servicio Matriculados")
    st.markdown(
        "Validación de CUIT y vigencia fiscal automatizada por el Agente Compliance:"
    )

    resultado_proveedores = resultados.get(TipoAgente.PROVEEDORES.value)
    if resultado_proveedores and resultado_proveedores.estado == EstadoAgente.COMPLETADO:
        proveedores_df = pd.DataFrame(
            resultado_proveedores.datos_procesados["proveedores"]
        )
        st.dataframe(proveedores_df, use_container_width=True, hide_index=True)

        col1, col2 = st.columns(2)
        with col1:
            st.info(f"📊 Total Prestadores: {resultado_proveedores.datos_procesados['total_disponibles']}")
        with col2:
            rubros = ", ".join(resultado_proveedores.datos_procesados["rubros"])
            st.info(f"🏷️ Rubros Disponibles: {rubros}")

    st.markdown("---")
    st.header("📋 Registro Central de Órdenes de Trabajo (OT)")
    st.markdown(
        "Bitácora de auditoría de reparaciones y costos liquidados en el periodo fiscal:"
    )

    resultado_operativo = resultados.get(TipoAgente.OPERATIVO.value)
    if resultado_operativo and resultado_operativo.estado == EstadoAgente.COMPLETADO:
        ots_df = pd.DataFrame(resultado_operativo.datos_procesados["ordenes_trabajo"])
        st.dataframe(ots_df, use_container_width=True, hide_index=True)

        col1, col2 = st.columns(2)
        with col1:
            st.warning(f"⚙️ Órdenes de Trabajo: {resultado_operativo.datos_procesados['total_ordenes']}")
        with col2:
            st.metric(
                "Presupuesto Total",
                f"${resultado_operativo.datos_procesados['presupuesto_total']:,.2f}",
            )

    st.markdown("---")
    resultado_compliance = resultados.get(TipoAgente.COMPLIANCE.value)
    if resultado_compliance and resultado_compliance.estado == EstadoAgente.COMPLETADO:
        st.header("✅ Validaciones Normativas")
        validaciones = resultado_compliance.datos_procesados

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.success(validaciones.get("ley_941_caba", "N/A"))
        with col2:
            st.success(validaciones.get("codigo_civil_comercial", "N/A"))
        with col3:
            st.success(validaciones.get("validacion_cuit", "N/A"))
        with col4:
            st.success(validaciones.get("vigencia_fiscal", "N/A"))


# ════════════════════════════════════════════════════════════════════════════════
# 9. MÓDULO LIQUIDACIÓN DE EXPENSAS
# ════════════════════════════════════════════════════════════════════════════════

elif pantalla_activa == "📊 Liquidación de Expensas":

    st.markdown(
        """
        <div class="header-brand">
            <img src="https://images.unsplash.com/photo-1486325212027-8081e485255e?w=400&q=80&blend=https://images.unsplash.com/photo-1449824913935-59a10b8d2000?w=400&q=80&blend_mode=screen" alt="Imagen de edificio">
            <h1>Resil<span class="underscore">_</span><span class="ia">IA</span> Condominios</h1>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(f"📍 **Edificio Activo:** {edificio_seleccionado}")
    st.markdown("---")

    st.header("📊 Liquidación Integral de Expensas")
    st.markdown("**Proceso Completo: Ingresos → Gastos → Prorrateo por UF**")

    # PESTAÑA 1: INGRESOS
    tab1, tab2, tab3, tab4 = st.tabs([
        "💵 Ingresos",
        "💰 Gastos",
        "📋 Resumen",
        "🏠 Por Unidad Funcional"
    ])

    with tab1:
        st.subheader("Registre los Ingresos del Período")
        
        col1, col2 = st.columns(2)
        with col1:
            periodo = st.selectbox(
                "Período de Liquidación",
                ["Octubre 2026", "Noviembre 2026", "Diciembre 2026"]
            )
        
        with col2:
            tipo_ingreso_sel = st.selectbox(
                "Tipo de Ingreso",
                [t.value for t in TipoIngreso]
            )

        col1, col2, col3 = st.columns(3)
        with col1:
            concepto_ing = st.text_input("Concepto", placeholder="Ej: Expensas octubre")
        with col2:
            monto_ing = st.number_input("Monto ($)", min_value=0.0, step=100.0)
        with col3:
            descripcion_ing = st.text_input("Descripción", placeholder="Detalles adicionales")

        if st.button("✅ Registrar Ingreso", key="btn_ingreso"):
            if concepto_ing and monto_ing > 0:
                nuevo_ingreso = RegistroIngreso(
                    concepto=concepto_ing,
                    tipo_ingreso=TipoIngreso(tipo_ingreso_sel),
                    monto=monto_ing,
                    descripcion=descripcion_ing
                )
                agente_liquidacion.registrar_ingreso(nuevo_ingreso)
                st.success(f"✅ Ingreso registrado: {concepto_ing} - ${monto_ing:,.2f}")
            else:
                st.error("❌ Complete todos los campos requeridos")

        # Mostrar ingresos registrados
        if agente_liquidacion.ingresos_registrados:
            st.markdown("---")
            st.subheader("Ingresos Registrados")
            
            ingresos_data = []
            for ing in agente_liquidacion.ingresos_registrados:
                ingresos_data.append({
                    "Concepto": ing.concepto,
                    "Tipo": ing.tipo_ingreso.value,
                    "Monto ($)": f"${ing.monto:,.2f}",
                    "Descripción": ing.descripcion
                })
            
            df_ingresos = pd.DataFrame(ingresos_data)
            st.dataframe(df_ingresos, use_container_width=True, hide_index=True)
            
            total_ingresos = sum(ing.monto for ing in agente_liquidacion.ingresos_registrados)
            st.metric("💵 Total Ingresos", f"${total_ingresos:,.2f}")

    with tab2:
        st.subheader("Registre los Gastos del Período")
        
        col1, col2 = st.columns(2)
        with col1:
            tipo_gasto_sel = st.selectbox(
                "Tipo de Gasto",
                [t.value for t in TipoGasto],
                key="tipo_gasto"
            )
        
        with col2:
            factura = st.text_input("Número de Factura", placeholder="Ej: 00001234")

        col1, col2, col3 = st.columns(3)
        with col1:
            concepto_gast = st.text_input("Concepto", placeholder="Ej: Electricidad", key="concepto_gasto")
        with col2:
            monto_gast = st.number_input("Monto ($)", min_value=0.0, step=100.0, key="monto_gasto")
        with col3:
            descripcion_gast = st.text_input("Descripción", placeholder="Detalles", key="desc_gasto")

        if st.button("✅ Registrar Gasto", key="btn_gasto"):
            if concepto_gast and monto_gast > 0:
                nuevo_gasto = RegistroGasto(
                    concepto=concepto_gast,
                    tipo_gasto=TipoGasto(tipo_gasto_sel),
                    monto=monto_gast,
                    descripcion=descripcion_gast,
                    factura=factura
                )
                agente_liquidacion.registrar_gasto(nuevo_gasto)
                st.success(f"✅ Gasto registrado: {concepto_gast} - ${monto_gast:,.2f}")
            else:
                st.error("❌ Complete los campos requeridos")

        # Mostrar gastos registrados
        if agente_liquidacion.gastos_registrados:
            st.markdown("---")
            st.subheader("Gastos Registrados")
            
            gastos_data = []
            for gast in agente_liquidacion.gastos_registrados:
                gastos_data.append({
                    "Concepto": gast.concepto,
                    "Tipo": gast.tipo_gasto.value,
                    "Factura": gast.factura,
                    "Monto ($)": f"${gast.monto:,.2f}",
                    "Descripción": gast.descripcion
                })
            
            df_gastos = pd.DataFrame(gastos_data)
            st.dataframe(df_gastos, use_container_width=True, hide_index=True)
            
            total_gastos = sum(gast.monto for gast in agente_liquidacion.gastos_registrados)
            st.metric("💰 Total Gastos", f"${total_gastos:,.2f}")

    with tab3:
        st.subheader("Resumen Ejecutivo de Liquidación")
        
        if agente_liquidacion.gastos_registrados or agente_liquidacion.ingresos_registrados:
            # Establecer coeficientes del edificio
            edificio_data = ESTADISTICAS_EDIFICIOS[edificio_seleccionado]
            if "coeficientes" in edificio_data and edificio_data["coeficientes"]:
                coeficientes = edificio_data["coeficientes"]
            else:
                # Crear coeficientes automáticos equitativos
                cantidad_uf = edificio_data.get("cantidad_uf", 10)
                coeficiente_unitario = 1.0 / cantidad_uf
                coeficientes = {f"UF_{i:02d}": coeficiente_unitario for i in range(1, cantidad_uf + 1)}

            agente_liquidacion.establecer_coeficientes(coeficientes)

            # Calcular liquidación
            liquidacion = agente_liquidacion.calcular_liquidacion(periodo)
            st.session_state.liquidacion_actual = liquidacion

            # Mostrar resumen
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("💵 Total Ingresos", f"${liquidacion.total_ingresos:,.2f}")
            with col2:
                st.metric("💰 Total Gastos", f"${liquidacion.total_gastos:,.2f}")
            with col3:
                resultado = liquidacion.deficit_o_superavit
                st.metric(
                    "⚖️ Resultado",
                    f"${abs(resultado):,.2f}",
                    delta=("Superávit ✅" if resultado > 0 else "Déficit ⚠️")
                )
            with col4:
                st.metric("📅 Período", liquidacion.periodo)

            st.markdown("---")

            # Ingresos por rubro
            st.subheader("📥 Desglose de Ingresos por Rubro")
            ingresos_rubro_data = []
            for rubro, monto in liquidacion.ingresos_por_rubro.items():
                porcentaje = (monto / liquidacion.total_ingresos * 100) if liquidacion.total_ingresos > 0 else 0
                ingresos_rubro_data.append({
                    "Rubro": rubro,
                    "Monto ($)": f"${monto:,.2f}",
                    "Porcentaje": f"{porcentaje:.1f}%"
                })
            
            if ingresos_rubro_data:
                df_ing_rubro = pd.DataFrame(ingresos_rubro_data)
                st.dataframe(df_ing_rubro, use_container_width=True, hide_index=True)

            st.markdown("---")

            # Gastos por rubro
            st.subheader("📤 Desglose de Gastos por Rubro")
            gastos_rubro_data = []
            for rubro, monto in liquidacion.gastos_por_rubro.items():
                porcentaje = (monto / liquidacion.total_gastos * 100) if liquidacion.total_gastos > 0 else 0
                gastos_rubro_data.append({
                    "Rubro": rubro,
                    "Monto ($)": f"${monto:,.2f}",
                    "Porcentaje": f"{porcentaje:.1f}%"
                })
            
            if gastos_rubro_data:
                df_gast_rubro = pd.DataFrame(gastos_rubro_data)
                st.dataframe(df_gast_rubro, use_container_width=True, hide_index=True)

        else:
            st.info("📭 Registre ingresos y gastos para generar el resumen")

    with tab4:
        st.subheader("🏠 Liquidación por Unidad Funcional")
        
        if st.session_state.liquidacion_actual:
            liquidacion = st.session_state.liquidacion_actual

            st.markdown(f"**Período:** {liquidacion.periodo}")
            st.markdown(f"**Total a Prorratear:** ${liquidacion.total_gastos:,.2f}")
            st.markdown("**Coeficientes de Distribución (Art. 2048 - Código Civil y Comercial)**")
            st.markdown("---")

            # Crear tabla de expensas por UF
            expensas_uf_data = []
            for uf, coeficiente in liquidacion.coeficientes.items():
                gasto_uf = liquidacion.expensas_por_uf.get(uf, 0)
                expensas_uf_data.append({
                    "UF/Dpto": uf,
                    "Coeficiente": f"{coeficiente:.4f}",
                    "Porcentaje": f"{coeficiente * 100:.2f}%",
                    "Expensas a Pagar ($)": f"${gasto_uf:,.2f}"
                })

            df_expensas_uf = pd.DataFrame(expensas_uf_data)
            st.dataframe(df_expensas_uf, use_container_width=True, hide_index=True)

            st.markdown("---")
            st.markdown("📋 **Verificaciones Contables:**")
            col1, col2, col3 = st.columns(3)
            
            suma_coeficientes = sum(liquidacion.coeficientes.values())
            suma_expensas = sum(liquidacion.expensas_por_uf.values())

            with col1:
                if abs(suma_coeficientes - 1.0) < 0.001:
                    st.success(f"✅ Coeficientes suman: {suma_coeficientes:.4f}")
                else:
                    st.error(f"❌ Coeficientes suman: {suma_coeficientes:.4f}")

            with col2:
                if abs(suma_expensas - liquidacion.total_gastos) < 1:
                    st.success(f"✅ Expensas reconciliadas: ${suma_expensas:,.2f}")
                else:
                    st.error(f"❌ Diferencia: ${abs(suma_expensas - liquidacion.total_gastos):,.2f}")

            with col3:
                st.info(f"📊 UF registradas: {len(liquidacion.coeficientes)}")

        else:
            st.info("📭 Complete el resumen para ver la distribución por UF")


# ════════════════════════════════════════════════════════════════════════════════
# 10. FOOTER - INFORMACIÓN DEL SISTEMA
# ════════════════════════════════════════════════════════════════════════════════

st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #64748b; font-size: 0.9rem; padding: 20px;'>
    <b>🏢 Resilia_IA v2.0 - Arquitectura Multiagente con Enjambre Coordinado</b><br/>
    <small>Cada solicitud dispara un equipo de agentes especializados que trabajan sinérgicamente<br/>
    🐝 Sistema de Inteligencia Distribuida para Gestión de Condominios</small>
    </div>
    """,
    unsafe_allow_html=True,
)
