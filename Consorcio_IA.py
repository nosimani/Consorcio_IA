# -*- coding: utf-8 -*-
"""
Sistema Multiagente de Administración de Consorcios (PH-AI Swarm)
Cumple con el Código Civil y Comercial de la Nación (Ley 26.994) y Ley 941.
"""

import json
import random
from datetime import datetime

class LLMEngine:
    """Simula la lógica de clasificación por IA (NLP) para procesar los mensajes del enjambre."""
    @staticmethod
    def procesar(rol: str, prompt: str) -> dict:
        if "RECLAMO" in prompt.upper() or "FILTRACIÓN" in prompt.upper() or "AGUA" in prompt.upper():
            return {
                "categoria": "mantenimiento",
                "rubro": "plomería" if any(x in prompt.lower() for x in ["agua", "caño", "techo", "baño"]) else "electricidad",
                "gravedad": "alta" if "urgente" in prompt.lower() or "terrible" in prompt.lower() else "media",
                "descripcion": "Incidente crítico reportado por el propietario."
            }
        return {"categoria": "general", "accion": "atencion_humana"}

class AgenteBase:
    def __init__(self, nombre: str, especialidad: str):
        self.nombre = nombre
        self.especialidad = especialidad

    def registrar_log(self, mensaje: str):
        print(f"[{self.nombre} - {self.especialidad}]: {mensaje}")

class AgenteLegalContable(AgenteBase):
    """Audita las liquidaciones según el Art. 2067 del CCyC (Obligaciones del Administrador)."""
    def __init__(self):
        super().__init__("Agente_LegalContable", "Derecho de Propiedad Horizontal y Contabilidad Federal")

    def verificar_cumplimiento_normativo(self, liquidacion: dict) -> bool:
        self.registrar_log("Verificando consistencia de Fondos de Reserva y aportes de seguridad social...")
        if liquidacion.get("fondo_reserva", 0) <= 0:
            self.registrar_log("Alerta Legal: Se omitió el Fondo de Reserva obligatorio por asamblea.")
        if not liquidacion.get("cargas_sociales_pagas", True):
            self.registrar_log("Falta Grave: Retención indebida de aportes previsionales del encargado.")
            return False
        return True

    def liquidar_expensas(self, consorcio: dict, gastos: list) -> dict:
        self.registrar_log(f"Calculando expensas para: {consorcio['nombre']}.")
        total_gastos = sum(g['monto'] for g in gastos)
        fondo_reserva = total_gastos * 0.10  # Previsión estándar de contingencia
        
        liquidacion_final = {
            "periodo": "09-2026",
            "total_gastos_A": total_gastos,
            "fondo_reserva": fondo_reserva,
            "total_a_recaudar": total_gastos + fondo_reserva,
            "cargas_sociales_pagas": True,
            "distribucion_unidades": {}
        }

        for uf, data in consorcio["unidades"].items():
            cuota_parte = liquidacion_final["total_a_recaudar"] * data["porcentual"]
            liquidacion_final["distribucion_unidades"][uf] = round(cuota_parte, 2)
            
        return liquidacion_final

class AgenteAtencionPropietario(AgenteBase):
    """Gestiona los canales de comunicación y notifica saldos/estados de reclamos."""
    def __init__(self):
        super().__init__("Agente_AtencionPropietario", "Atención al Copropietario e Ingesta de Datos")

    def recibir_mensaje(self, propietario: str, uf: str, mensaje: str) -> dict:
        self.registrar_log(f"Mensaje de {propietario} (UF: {uf}): '{mensaje}'")
        analisis = LLMEngine.procesar("Atencion", mensaje)
        return {"propietario": propietario, "uf": uf, "analisis": analisis}

    def enviar_notificacion(self, destinatario: str, mensaje: str):
        print(f"   >>> [SMS/WhatsApp Enviado a {destinatario}]: {mensaje}")

class AgenteProveedoresMantenimiento(AgenteBase):
    """Interactúa automátizadamente con el ecosistema de gremios matriculados."""
    def __init__(self):
        super().__init__("Agente_Proveedores", "Bolsa de Trabajo y Compulsa de Precios")
        self.proveedores = {
            "plomería": [
                {"nombre": "Plomería San Martín S.R.L.", "matricula": "M-12345", "mail": "contacto@sanmartin.com"},
                {"nombre": "Destapaciones Delta", "matricula": "M-9876", "mail": "delta@gmail.com"}
            ]
        }

    def solicitar_cotizaciones(self, rubro: str, detalle: str) -> list:
        self.registrar_log(f"Abriendo licitación automática para el rubro: {rubro}")
        cotizaciones = []
        for p in self.proveedores.get(rubro, []):
            precio_estimado = round(random.uniform(15000, 35000), 2)
            cotizaciones.append({"proveedor": p["nombre"], "matricula": p["matricula"], "precio": precio_estimado})
        return cotizaciones

class OrchestratorConsorcio:
    """Core Engine: Vincula y hace interactuar los agentes entre sí en tiempo real (Swarm Paradigm)."""
    def __init__(self):
        self.legal = AgenteLegalContable()
        self.atencion = AgenteAtencionPropietario()
        self.proveedores = AgenteProveedoresMantenimiento()
        self.consorcio_db = {
            "nombre": "Consorcio Av. Corrientes 1500, CABA",
            "unidades": {
                "1A": {"propietario": "Carlos Gómez", "porcentual": 0.40},
                "1B": {"propietario": "Ana Milone", "porcentual": 0.60}
            }
        }
        self.gastos_mes = [
            {"concepto": "Abono Ascensores S.A.", "monto": 90000},
            {"concepto": "Sueldo Encargado SUTERH", "monto": 420000}
        ]

    def procesar_incidente(self, propietario: str, uf: str, mensaje: str):
        ticket = self.atencion.recibir_mensaje(propietario, uf, mensaje)
        analisis = ticket["analisis"]
        
        if analisis.get("categoria") == "mantenimiento":
            rubro = analisis.get("rubro")
            cotizaciones = self.proveedores.solicitar_cotizaciones(rubro, mensaje)
            
            if cotizaciones:
                ganador = min(cotizaciones, key=lambda x: x["precio"])
                print(f"--> [Orquestador]: Adjudicación automática a {ganador['proveedor']} por ${ganador['precio']}.")
                
                self.atencion.enviar_notificacion(
                    propietario, 
                    f"Tu reclamo de {rubro} fue aprobado. El especialista {ganador['proveedor']} (Mat: {ganador['matricula']}) coordinará la visita técnica."
                )
                self.gastos_mes.append({"concepto": f"Reparación {rubro} - UF {uf}", "monto": ganador["precio"]})

    def emitir_periodo(self):
        liquidacion = self.legal.liquidar_expensas(self.consorcio_db, self.gastos_mes)
        if self.legal.verificar_cumplimiento_normativo(liquidacion):
            print("\n================== EXPENSAS EMITIDAS ==================")
            for uf, monto in liquidacion["distribucion_unidades"].items():
                prop = self.consorcio_db["unidades"][uf]["propietario"]
                self.atencion.enviar_notificacion(prop, f"Expensas listas Periodo 09-2026. Importe: ${monto}")

if __name__ == "__main__":
    sistema = OrchestratorConsorcio()
    # Simulación de reclamo entrante por canal digital
    sistema.procesar_incidente("Carlos Gómez", "1A", "Urgente, se rompió un caño en el baño y tengo una filtración terrible!")
    # Simulación de cierre contable automatizado
    sistema.emitir_periodo()
