import os
import json
import asyncio
from datetime import datetime
from typing import List, Dict, Any

# =====================================================================
# SIMULADORES DE LLAMADOS A LLM / HERRAMIENTAS EXTERNAS
# =====================================================================
class LLMEngine:
    """Simula la ejecución y el razonamiento de un Modelo de Lenguaje de IA."""
    @staticmethod
    async def chat(prompt: str, system_instruction: str) -> str:
        await asyncio.sleep(0.1) # Simulación de latencia de red / inferencia
        
        # Enrutamiento de respuestas simuladas de IA altamente contextualizadas
        if "liquidacion" in prompt.lower() or "contable" in prompt.lower():
            return json.dumps({
                "estado": "PROCESADO",
                "total_gastos": 850000.00,
                "fondo_reserva_detraido": 50000.00,
                "observacion_legal": "Aplicación estricta Art. 2048 CCyCN. Expensas ordinarias devengadas de forma equitativa."
            })
        elif "reclamo" in prompt.lower() or "propietario" in prompt.lower():
            return json.dumps({
                "categoria": "Plomería",
                "urgencia": "ALTA",
                "requiere_proveedor": True,
                "respuesta_propietario": "Estimado Propietario de la UF 4B: Hemos recibido su reclamo por filtración. Se ha derivado de manera urgente al servicio de Plomería homologado. Lo mantendremos informado."
            })
        elif "cotizacion" in prompt.lower() or "proveedor" in prompt.lower():
            return json.dumps({
                "proveedor_seleccionado": "Plomería Swift S.R.L.",
                "presupuesto_ars": 45000.00,
                "fecha_visita": "2026-09-28",
                "aprobado_automatico": True
            })
        elif "legal" in prompt.lower() or "afip" in prompt.lower():
            return json.dumps({
                "cumplimiento_estatutario": "OK",
                "alerta": "Verificar presentación del Libro de Órdenes digital s/ Ley 941 CABA.",
                "retenciones_suterh": "Aplicadas s/ CCT 589/10."
            })
        return '{"status": "OK", "message": "Procesado correctamente."}'

# =====================================================================
# MENSAJERÍA ENTRE AGENTES (SWARM EVENT BROKER)
# =====================================================================
class SwarmMessage:
    def __init__(self, sender: str, receiver: str, content: Dict[str, Any], topic: str):
        self.sender = sender
        self.receiver = receiver
        self.content = content
        self.topic = topic
        self.timestamp = datetime.now().isoformat()

class SwarmBroker:
    def __init__(self):
        self.history: List[SwarmMessage] = []

    def dispatch(self, message: SwarmMessage):
        self.history.append(message)
        print(f"📡 [BROKER] {message.sender} ➔ {message.receiver} | Evento: {message.topic}")

# =====================================================================
# DEFINICIÓN DE LOS AGENTES ESPECIALIZADOS
# =====================================================================
class BaseAgent:
    def __init__(self, name: str, role: str, broker: SwarmBroker):
        self.name = name
        self.role = role
        self.broker = broker
        self.system_instruction = f"Actúa como el agente {name}, experto senior en {role}."

    async def execute_task(self, prompt: str) -> Dict[str, Any]:
        response_raw = await LLMEngine.chat(prompt, self.system_instruction)
        try:
            return json.loads(response_raw)
        except json.JSONDecodeError:
            return {"raw_reply": response_raw}

# 1. Agente de Atención al Propietario (Atención y Clasificación)
class OwnerRelationAgent(BaseAgent):
    def __init__(self, broker: SwarmBroker):
        super().__init__("Agente_Atencion_Propietarios", "Atención al cliente, recepción de incidentes y derivación s/ Código Civil y Comercial", broker)

    async def procesar_mensaje_propietario(self, uf: str, edificio: str, mensaje: str):
        print(f"\n📥 [PROCESANDO MENSAJE] UF {uf} de Edificio {edificio}: '{mensaje}'")
        prompt = f"Analizar reclamo de UF {uf} Edificio {edificio}. Mensaje: {mensaje}."
        analisis = await self.execute_task(prompt)
        
        if analisis.get("requiere_proveedor"):
            msg = SwarmMessage(
                sender=self.name,
                receiver="Agente_Operaciones_Proveedores",
                content={"edificio": edificio, "uf": uf, "categoria": analisis["categoria"], "urgencia": analisis["urgencia"]},
                topic="SOLICITUD_PROVEEDOR_URGENTE"
            )
            self.broker.dispatch(msg)
        return analisis["respuesta_propietario"]

# 2. Agente de Operaciones y Licitación Automática de Proveedores
class OperationsSupplierAgent(BaseAgent):
    def __init__(self, broker: SwarmBroker):
        super().__init__("Agente_Operaciones_Proveedores", "Búsqueda, cotización y contratación de prestadores de servicios matriculados", broker)

    async def gestionar_incidente(self, datos_incidente: Dict[str, Any]):
        print(f"🛠️  [CONTRATACIÓN] Buscando prestadores para el rubro: {datos_incidente['categoria']}...")
        prompt = f"Cotizar y seleccionar el mejor proveedor para rubro {datos_incidente['categoria']} en {datos_incidente['edificio']}. Urgencia: {datos_incidente['urgencia']}."
        seleccion = await self.execute_task(prompt)
        
        msg = SwarmMessage(
            sender=self.name,
            receiver="Agente_Contable_Liquidaciones",
            content={"proveedor": seleccion["proveedor_seleccionado"], "monto": seleccion["presupuesto_ars"], "edificio": datos_incidente["edificio"]},
            topic="GASTO_DEVENGADO"
        )
        self.broker.dispatch(msg)
        return seleccion

# 3. Agente Contable y Liquidación de Expensas
class AccountingLiquidationsAgent(BaseAgent):
    def __init__(self, broker: SwarmBroker):
        super().__init__("Agente_Contable_Liquidaciones", "Liquidación de expensas mensuales, devengamientos, fondos de reserva y prorrateo s/ CCyCN", broker)

    async def liquidar_periodo(self, edificio: str, gastos_adicionales: List[Dict[str, Any]]):
        print(f"🧮 [LIQUIDACIÓN] Procesando expensas del edificio {edificio}...")
        prompt = f"Calcular liquidación total para {edificio} incorporando gastos: {json.dumps(gastos_adicionales)}."
        resultado = await self.execute_task(prompt)
        
        msg = SwarmMessage(
            sender=self.name,
            receiver="Agente_Legal_Normativo",
            content=resultado,
            topic="VALIDACION_LIQUIDACION"
        )
        self.broker.dispatch(msg)
        return resultado

# 4. Agente Legal y de Cumplimiento Normativo
class LegalComplianceAgent(BaseAgent):
    def __init__(self, broker: SwarmBroker):
        super().__init__("Agente_Legal_Normativo", "Derecho de Propiedad Horizontal, Paritarias SUTERH, Ley 941 CABA y AFIP", broker)

    async def auditar_transaccion(self, datos_auditoria: Dict[str, Any]):
        print(f"⚖️  [LEGAL & FISCAL] Auditando cumplimiento impositivo y normativo...")
        prompt = f"Validar legalidad del siguiente balance o acción: {json.dumps(datos_auditoria)}."
        dictamen = await self.execute_task(prompt)
        return dictamen

# =====================================================================
# COORDINADOR CENTRAL DE ENJAMBRE (ORQUESTADOR PRINCIPAL)
# =====================================================================
class ConsorcioSwarmOrchestrator:
    def __init__(self):
        self.broker = SwarmBroker()
        self.atencion = OwnerRelationAgent(self.broker)
        self.operaciones = OperationsSupplierAgent(self.broker)
        self.contable = AccountingLiquidationsAgent(self.broker)
        self.legal = LegalComplianceAgent(self.broker)

    async def simular_ciclo_consorcio(self):
        print("="*60)
        print("🚀 INICIANDO ENJAMBRE DE INTELIGENCIA ARTIFICIAL PARA CONSORCIOS")
        print("="*60)
        
        # Paso 1: Recepción de mensaje crítico de un propietario
        respuesta_usuario = await self.atencion.procesar_mensaje_propietario(
            uf="4B", 
            edificio="Av. Santa Fe 2300, CABA", 
            mensaje="Hola, me está cayendo agua del techo del baño a baldes, por favor manden a alguien urgente."
        )
        print(f"💬 [Respuesta Automática a Propietario]:\n  -> '{respuesta_usuario}'")
        
        # Paso 2: El Broker detecta la orden de plomería y el Agente Operativo gestiona la orden
        ultimo_mensaje = self.broker.history[-1]
        if ultimo_mensaje.topic == "SOLICITUD_PROVEEDOR_URGENTE":
            proveedor_elegido = await self.operaciones.gestionar_incidente(ultimo_mensaje.content)
            print(f"✅ [Proveedor Contratado]: {proveedor_elegido['proveedor_seleccionado']} | Costo: ${proveedor_elegido['presupuesto_ars']} ARS")
        
        # Paso 3: Al cierre de periodo, el Agente Contable compila los gastos del broker y realiza la liquidación
        gastos_mes = [{"concepto": m.content["proveedor"], "monto": m.content["monto"]} for m in self.broker.history if m.topic == "GASTO_DEVENGADO"]
        liquidacion = await self.contable.liquidar_periodo("Av. Santa Fe 2300, CABA", gastos_mes)
        print(f"📊 [Resumen Liquidación Expensas]: Total de Gastos Liquidados: ${liquidacion['total_gastos']} ARS")
        
        # Paso 4: El Agente Legal fiscaliza de manera cruzada el proceso
        ultimo_mensaje_liquidacion = self.broker.history[-1]
        if ultimo_mensaje_liquidacion.topic == "VALIDACION_LIQUIDACION":
            dictamen_final = await self.legal.auditar_transaccion(ultimo_mensaje_liquidacion.content)
            print(f"📝 [Dictamen Final de Auditoría]: {dictamen_final['alerta']} | {dictamen_final['retenciones_suterh']}")
            
