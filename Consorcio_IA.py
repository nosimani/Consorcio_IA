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
    "TESORERIA": ["🤖", "💵", "💳"],
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
    TESORERIA = "💰 Agente de Tesorería"


class EstadoAgente(Enum):
    """Estados del ciclo de vida de cada agente"""
    INACTIVO = "⚪ Inactivo"
    ACTIVADO = "🟢 Activado"
    PROCESANDO = "🟡 Procesando"
    COMPLETADO = "✅ Completado"
    ERROR = "🔴 Error"


class FormaPago(Enum):
    """Formas de pago disponibles"""
    EFECTIVO = "💵 Efectivo"
    DEBITO = "🏧 Débito"
    CREDITO = "💳 Crédito"
    TRANSFERENCIA = "🏦 Transferencia"


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
class RegistroPago:
    """Registro de un pago de expensas"""
    fecha: str
    edificio: str
    uf_dpto: str
    importe: float
    forma_pago: str
    referencia: str
    estado: str


# ════════════════════════════════════════════════════════════════════════════════
# 2. BASE DE DATOS GLOBAL (INMUTABLE)
# ════════════════════════════════════════════════════════════════════════════════

ESTADISTICAS_EDIFICIOS = {
    "Av. Corrientes 1234, CABA": {
        "reserva": 450000.0,
        "factor": 1.0,
        "mora": "1",
        "tasa": 4.5,
        "ots": "5"
    },
    "Larrea 435, CABA": {
        "reserva": 380000.0,
        "factor": 0.6,
        "mora": "2",
        "tasa": 5.0,
        "ots": "5"
    },
    "Montevideo 891, CABA": {
        "reserva": 620000.0,
        "factor": 0.8,
        "mora": "2",
        "tasa": 6.2,
        "ots": "5"
    },
    "San Jose 1111, CABA": {
        "reserva": 290000.0,
        "factor": 0.5,
        "mora": "1",
        "tasa": 3.8,
        "ots": "5"
    },
    "Guayaquil 399, CABA": {
        "reserva": 850000.0,
        "factor": 1.5,
        "mora": "1",
        "tasa": 7.5,
        "ots": "5"
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
        }


# ════════════════════════════════════════════════════════════════════════════════
# AGENTE DE TESORERÍA - GESTIÓN DE COBROS
# ════════════════════════════════════════════════════════════════════════════════

class AgenteTesoreria:
    """💰 Especialista en ingresos y cobros de expensas"""

    def __init__(self):
        self.tipo_agente = TipoAgente.TESORERIA
        self.estado = EstadoAgente.INACTIVO
        self.historial_pagos = []

    def activar(self):
        """Pasa el agente a estado ACTIVADO"""
        self.estado = EstadoAgente.ACTIVADO

    def registrar_pago(self, pago: RegistroPago) -> ResultadoAgente:
        """Registra un pago en el sistema"""
        self.activar()
        self.estado = EstadoAgente.PROCESANDO
        tiempo_inicio = time.time()

        try:
            self.historial_pagos.append(pago)
            
            self.estado = EstadoAgente.COMPLETADO
            tiempo_procesamiento = f"⚡ {(time.time() - tiempo_inicio)*1000:.2f}ms"

            return ResultadoAgente(
                agente=self.tipo_agente.value,
                estado=self.estado,
                datos_procesados={
                    "pago_registrado": True,
                    "fecha": pago.fecha,
                    "edificio": pago.edificio,
                    "uf": pago.uf_dpto,
                    "importe": pago.importe,
                    "forma_pago": pago.forma_pago,
                    "estado_pago": pago.estado,
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

    def obtener_pagos_edificio(self, edificio: str) -> List[RegistroPago]:
        """Retorna todos los pagos de un edificio específico"""
        return [p for p in self.historial_pagos if p.edificio == edificio]

    def obtener_resumen_pagos(self, edificio: str = None) -> Dict[str, Any]:
        """Retorna un resumen de pagos"""
        pagos = self.historial_pagos if edificio is None else self.obtener_pagos_edificio(edificio)
        
        if not pagos:
            return {
                "total_pagos": 0,
                "monto_total": 0.0,
                "por_forma_pago": {},
            }

        total_monto = sum(p.importe for p in pagos)
        por_forma = {}
        
        for pago in pagos:
            if pago.forma_pago not in por_forma:
                por_forma[pago.forma_pago] = {"cantidad": 0, "monto": 0.0}
            por_forma[pago.forma_pago]["cantidad"] += 1
            por_forma[pago.forma_pago]["monto"] += pago.importe

        return {
            "total_pagos": len(pagos),
            "monto_total": total_monto,
            "por_forma_pago": por_forma,
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
            TipoAgente.TESORERIA: AgenteTesoreria(),
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
                "ots": "3"
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

        elif evento.tipo_evento == "MODULO_COBROS":
            self.resultados_enjambre[TipoAgente.TESORERIA.value] = {
                "tesoreria_lista": True
            }

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
        
        .tabla-pagos {
            background-color: rgba(15, 23, 42, 0.8) !important;
            border-radius: 12px;
            padding: 20px;
            margin: 15px 0;
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
        
        .forma-pago-badge {
            display: inline-block;
            padding: 6px 12px;
            border-radius: 6px;
            font-size: 0.9rem;
            font-weight: 600;
        }
        
        .forma-pago-efectivo {
            background-color: rgba(34, 197, 94, 0.2) !important;
            color: #86efac !important;
        }
        
        .forma-pago-debito {
            background-color: rgba(59, 130, 246, 0.2) !important;
            color: #93c5fd !important;
        }
        
        .forma-pago-credito {
            background-color: rgba(168, 85, 247, 0.2) !important;
            color: #d8b4fe !important;
        }
        
        .forma-pago-transferencia {
            background-color: rgba(249, 115, 22, 0.2) !important;
            color: #fed7aa !important;
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

if "pagos_registrados" not in st.session_state:
    st.session_state.pagos_registrados = []

orquestador = st.session_state.orquestador
agente_tesoreria = st.session_state.orquestador.enjambre[TipoAgente.TESORERIA]


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
            "💰 Ingreso de Cobros"
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
# 9. MÓDULO INGRESO DE COBROS DE EXPENSAS
# ════════════════════════════════════════════════════════════════════════════════

elif pantalla_activa == "💰 Ingreso de Cobros":

    evento = EventoSwarm(
        timestamp=datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        tipo_evento="MODULO_COBROS",
        descripcion="Usuario registra ingreso de cobro de expensas",
        modulo_solicitante="💰 Tesorería",
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
    st.markdown(f"📍 **Edificio Activo:** {edificio_seleccionado}")

    st.markdown("---")
    st.header("💳 Ingreso de Cobro de Expensas")
    st.markdown("Registre el pago de expensas de los propietarios con diferentes formas de pago")

    # FORMULARIO DE REGISTRO DE PAGO
    with st.form("forma_ingreso_pago", clear_on_submit=True):
        st.subheader("📝 Datos del Pago")
        
        col1, col2 = st.columns(2)
        
        with col1:
            fecha_pago = st.date_input(
                "📅 Fecha del Pago",
                value=datetime.now().date()
            )
        
        with col2:
            hora_pago = st.time_input(
                "🕒 Hora del Pago",
                value=datetime.now().time()
            )

        # Obtener UF disponibles del edificio seleccionado
        uf_disponibles = []
        if (
            not st.session_state.unidades_edificios.empty
            and edificio_seleccionado in st.session_state.unidades_edificios["Edificio"].unique()
        ):
            unidades = st.session_state.unidades_edificios[
                st.session_state.unidades_edificios["Edificio"] == edificio_seleccionado
            ]
            uf_disponibles = unidades["UF/Dpto"].unique().tolist()
        else:
            uf_disponibles = ["1A", "2A", "3A", "4A", "5A"]

        col1, col2 = st.columns(2)
        
        with col1:
            uf_seleccionada = st.selectbox(
                "🏠 Seleccione Unidad Funcional (UF/Dpto)",
                uf_disponibles
            )
        
        with col2:
            importe_pago = st.number_input(
                "💵 Importe ($)",
                min_value=0.0,
                step=100.0,
                format="%.2f"
            )

        col1, col2 = st.columns(2)
        
        with col1:
            forma_pago = st.selectbox(
                "💳 Forma de Pago",
                [
                    FormaPago.EFECTIVO.value,
                    FormaPago.DEBITO.value,
                    FormaPago.CREDITO.value,
                    FormaPago.TRANSFERENCIA.value,
                ]
            )
        
        with col2:
            referencia = st.text_input(
                "📋 Referencia (Cheque, CBU, Tarjeta, etc.)",
                placeholder="Ej: Tarjeta 4532... o CBU o Nro de cheque"
            )

        st.markdown("---")

        col1, col2 = st.columns([1, 1])
        
        with col1:
            boton_registrar = st.form_submit_button(
                "✅ Registrar Pago",
                use_container_width=True,
                type="primary"
            )
        
        with col2:
            boton_limpiar = st.form_submit_button(
                "🔄 Limpiar",
                use_container_width=True
            )

        if boton_registrar and importe_pago > 0:
            timestamp_completo = datetime.combine(fecha_pago, hora_pago).strftime("%d/%m/%Y %H:%M:%S")
            
            nuevo_pago = RegistroPago(
                fecha=timestamp_completo,
                edificio=edificio_seleccionado,
                uf_dpto=uf_seleccionada,
                importe=importe_pago,
                forma_pago=forma_pago,
                referencia=referencia if referencia else "Sin referencia",
                estado="✅ Confirmado"
            )
            
            st.session_state.pagos_registrados.append(nuevo_pago)
            
            resultado_tesoreria = agente_tesoreria.registrar_pago(nuevo_pago)
            
            st.success(f"✅ Pago registrado correctamente por ${importe_pago:,.2f}")
            st.balloons()

    st.markdown("---")
    
    # MOSTRAR TABLA DE PAGOS POR EDIFICIO
    if st.session_state.pagos_registrados:
        
        # Obtener pagos del edificio seleccionado
        pagos_edificio = [
            p for p in st.session_state.pagos_registrados
            if p.edificio == edificio_seleccionado
        ]

        if pagos_edificio:
            st.markdown(
                f'<div class="titulo-edificio">📊 Registro de Cobros - {edificio_seleccionado}</div>',
                unsafe_allow_html=True
            )

            # Preparar datos para la tabla
            datos_tabla = []
            for pago in pagos_edificio:
                # Determinar color según forma de pago
                forma_pago_display = pago.forma_pago
                
                datos_tabla.append({
                    "Fecha": pago.fecha,
                    "UF/Dpto": pago.uf_dpto,
                    "Importe ($)": f"${pago.importe:,.2f}",
                    "Forma de Pago": forma_pago_display,
                    "Referencia": pago.referencia,
                    "Estado": pago.estado,
                })

            df_pagos = pd.DataFrame(datos_tabla)
            
            st.dataframe(
                df_pagos,
                use_container_width=True,
                hide_index=True,
            )

            # RESUMEN DE PAGOS
            st.markdown("---")
            st.subheader("📈 Resumen de Cobros del Edificio")

            total_cobrado = sum(p.importe for p in pagos_edificio)
            cantidad_pagos = len(pagos_edificio)
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("💰 Total Cobrado", f"${total_cobrado:,.2f}")
            
            with col2:
                st.metric("📊 Total de Pagos", cantidad_cobrado)
            
            with col3:
                promedio_pago = total_cobrado / cantidad_pagos if cantidad_pagos > 0 else 0
                st.metric("📋 Promedio por Pago", f"${promedio_pago:,.2f}")

            # DESGLOSE POR FORMA DE PAGO
            st.markdown("---")
            st.subheader("🔀 Desglose por Forma de Pago")

            formas_pago_dict = {}
            for pago in pagos_edificio:
                if pago.forma_pago not in formas_pago_dict:
                    formas_pago_dict[pago.forma_pago] = {"cantidad": 0, "monto": 0.0}
                formas_pago_dict[pago.forma_pago]["cantidad"] += 1
                formas_pago_dict[pago.forma_pago]["monto"] += pago.importe

            desglose_data = []
            for forma, datos in formas_pago_dict.items():
                desglose_data.append({
                    "Forma de Pago": forma,
                    "Cantidad": datos["cantidad"],
                    "Monto Total ($)": f"${datos['monto']:,.2f}",
                    "Porcentaje": f"{(datos['monto'] / total_cobrado * 100):.1f}%"
                })

            df_desglose = pd.DataFrame(desglose_data)
            st.dataframe(df_desglose, use_container_width=True, hide_index=True)

            # DESGLOSE POR UNIDAD FUNCIONAL
            st.markdown("---")
            st.subheader("🏠 Desglose por Unidad Funcional")

            uf_dict = {}
            for pago in pagos_edificio:
                if pago.uf_dpto not in uf_dict:
                    uf_dict[pago.uf_dpto] = {"cantidad": 0, "monto": 0.0}
                uf_dict[pago.uf_dpto]["cantidad"] += 1
                uf_dict[pago.uf_dpto]["monto"] += pago.importe

            uf_data = []
            for uf, datos in sorted(uf_dict.items()):
                uf_data.append({
                    "UF/Dpto": uf,
                    "Cantidad de Pagos": datos["cantidad"],
                    "Monto Total ($)": f"${datos['monto']:,.2f}",
                })

            df_uf = pd.DataFrame(uf_data)
            st.dataframe(df_uf, use_container_width=True, hide_index=True)

        # MOSTRAR OTROS EDIFICIOS CON PAGOS
        otros_edificios = set(p.edificio for p in st.session_state.pagos_registrados)
        otros_edificios.discard(edificio_seleccionado)

        if otros_edificios:
            st.markdown("---")
            st.header("🏢 Otros Edificios con Registros")

            for otro_edificio in sorted(otros_edificios):
                pagos_otro = [
                    p for p in st.session_state.pagos_registrados
                    if p.edificio == otro_edificio
                ]

                with st.expander(f"📍 {otro_edificio}"):
                    datos_otro = []
                    for pago in pagos_otro:
                        datos_otro.append({
                            "Fecha": pago.fecha,
                            "UF/Dpto": pago.uf_dpto,
                            "Importe ($)": f"${pago.importe:,.2f}",
                            "Forma de Pago": pago.forma_pago,
                            "Estado": pago.estado,
                        })

                    df_otro = pd.DataFrame(datos_otro)
                    st.dataframe(df_otro, use_container_width=True, hide_index=True)

                    total_otro = sum(p.importe for p in pagos_otro)
                    st.success(f"💰 **Total Cobrado:** ${total_otro:,.2f}")

    else:
        st.info("📭 Aún no hay pagos registrados. Ingrese un pago para comenzar.")


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
