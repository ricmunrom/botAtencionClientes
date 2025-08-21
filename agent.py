import os
from typing import Dict, Any, List, Optional
from langchain.tools import tool
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.schema import BaseMessage
from pydantic import BaseModel, Field
from estado_global import EstadoGlobal

# Variable global para estado (será inicializada por AgentePrincipal)
_estado_global = None

@tool
def propuesta_valor(query: str) -> str:
    """Proporciona información básica sobre la propuesta de valor, servicios, garantías y beneficios disponibles"""
    global _estado_global
    if _estado_global:
        _estado_global.actualizar('ultima_consulta', f"propuesta_valor: {query}")
    
    # Por ahora solo pass - implementaremos lógica después
    pass
    
    return "Información de propuesta de valor - En construcción"

@tool
def catalogo_autos(preferencias: str) -> str:
    """Busca y recomienda autos del catálogo basado en preferencias como presupuesto, marca, modelo, año, tipo de vehículo"""
    global _estado_global
    if _estado_global:
        _estado_global.actualizar('ultima_consulta', f"catalogo: {preferencias}")
        _estado_global.actualizar('cliente_preferencias', preferencias)
    
    # Por ahora solo pass - implementaremos lógica después
    pass
    
    return "Recomendaciones de catálogo - En construcción"

@tool
def planes_financiamiento(parametros_financiamiento: str) -> str:
    """Calcula planes de financiamiento basado en enganche, precio del auto, tasa de interés del 10% y plazos de 3 a 6 años"""
    global _estado_global
    if _estado_global:
        _estado_global.actualizar('ultima_consulta', f"financiamiento: {parametros_financiamiento}")
    
    # Por ahora solo pass - implementaremos lógica después
    pass
    
    return "Plan de financiamiento - En construcción"


class AgentePrincipal:
    """
    Agente principal que coordina las tools y maneja la lógica de conversación.
    Utiliza OpenAI GPT-3.5-turbo como modelo base.
    """
    
    def __init__(self):
        """Inicializar el agente principal con las tools y estado global"""
        
        # Inicializar estado global
        self.estado_global = EstadoGlobal()
        
        # Configurar variable global para las tools
        global _estado_global
        _estado_global = self.estado_global
        
        # Inicializar modelo OpenAI
        self.llm = ChatOpenAI(
            model="gpt-3.5-turbo",
            temperature=0.3,
            openai_api_key=os.getenv('OPENAI_API_KEY')
        )
        
        # Inicializar tools (ahora son funciones decoradas)
        self.tools = [
            propuesta_valor,
            catalogo_autos,
            planes_financiamiento
        ]
        
        # Crear prompt del sistema
        self.system_prompt = self._crear_prompt_sistema()
        
        # Crear agente
        self.agent = create_openai_functions_agent(
            self.llm, 
            self.tools, 
            self.system_prompt
        )
        
        # Crear executor
        self.agent_executor = AgentExecutor(
            agent=self.agent,
            tools=self.tools,
            verbose=True,
            return_intermediate_steps=True
        )
    
    def _crear_prompt_sistema(self) -> ChatPromptTemplate:
        """
        Crear el prompt del sistema para el agente
        
        Returns:
            Template de prompt configurado
        """
        prompt = ChatPromptTemplate.from_messages([
            ("system", """
            Eres un asistente de atención al cliente especializado en venta de autos usados.
            
            Tu objetivo es ayudar a los clientes con:
            1. Información sobre la propuesta de valor y servicios
            2. Recomendaciones de autos del catálogo según sus preferencias
            3. Cálculo de planes de financiamiento
            
            IMPORTANTE:
            - Sé amable, profesional y útil
            - Haz preguntas para entender mejor las necesidades del cliente
            - Usa las herramientas disponibles cuando sea necesario
            - Mantén el contexto de la conversación
            - Los planes de financiamiento tienen tasa fija del 10% anual y plazos de 3-6 años
            
            Herramientas disponibles:
            - propuesta_valor: Para información general sobre servicios y beneficios
            - catalogo_autos: Para buscar y recomendar vehículos
            - planes_financiamiento: Para calcular opciones de pago
            """),
            ("user", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])
        
        return prompt
    
    def procesar_mensaje(self, mensaje: str, telefono_usuario: str) -> str:
        """
        Procesar mensaje del usuario y generar respuesta
        
        Args:
            mensaje: Mensaje del usuario
            telefono_usuario: Número de teléfono del usuario
            
        Returns:
            Respuesta del agente
        """
        try:
            # Actualizar información del usuario en estado global
            self.estado_global.actualizar('cliente_telefono', telefono_usuario)
            
            # Ejecutar agente
            respuesta = self.agent_executor.invoke({
                "input": mensaje
            })
            
            # Extraer respuesta final
            respuesta_final = respuesta.get('output', 'Lo siento, no pude procesar tu mensaje.')
            
            return respuesta_final
            
        except Exception as e:
            print(f"Error procesando mensaje: {e}")
            return "Lo siento, ocurrió un error procesando tu consulta. ¿Podrías intentar de nuevo?"
    
    def obtener_estado_actual(self) -> Dict[str, Any]:
        """
        Obtener el estado actual del agente
        
        Returns:
            Resumen del estado global actual
        """
        return self.estado_global.obtener_resumen()
    
    def reiniciar_conversacion(self, telefono_usuario: str) -> None:
        """
        Reiniciar la conversación manteniendo info básica del usuario
        
        Args:
            telefono_usuario: Número de teléfono del usuario
        """
        self.estado_global.reiniciar()
        self.estado_global.actualizar('cliente_telefono', telefono_usuario)
    
    def obtener_historial(self) -> List[Dict[str, Any]]:
        """
        Obtener historial de acciones del estado global
        
        Returns:
            Lista de acciones realizadas
        """
        return self.estado_global.obtener('historial_acciones') or []