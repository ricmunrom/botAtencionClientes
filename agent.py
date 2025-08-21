import os
from typing import Dict, Any, List, Optional
from langchain.tools import BaseTool
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.schema import BaseMessage
from pydantic import BaseModel, Field
from estado_global import EstadoGlobal, GestorEstados


class PropuestaValorTool(BaseTool):
    """
    Tool para responder información básica sobre la propuesta de valor.
    Proporciona información general sobre servicios, garantías, proceso de compra, etc.
    """
    
    name: str = "propuesta_valor"
    description: str = "Proporciona información básica sobre la propuesta de valor, servicios, garantías y beneficios disponibles"
    gestor_estados: GestorEstados = Field(exclude=True)
    telefono_actual: str = Field(exclude=True)
    
    def __init__(self, gestor_estados: GestorEstados, **kwargs):
        super().__init__(gestor_estados=gestor_estados, telefono_actual="", **kwargs)
    
    def _run(self, query: str) -> str:
        """
        Ejecutar tool de propuesta de valor
        
        Args:
            query: Consulta del usuario sobre información general
            
        Returns:
            Respuesta con información de propuesta de valor
        """
        # Obtener el estado del usuario actual
        estado = self.gestor_estados.obtener_estado(self.telefono_actual)
        
        # Registrar la consulta en el estado global
        estado.actualizar('ultima_consulta', f"propuesta_valor: {query}")
        
        # Por ahora solo pass - implementaremos lógica después
        pass
        
        return "Información de propuesta de valor - En construcción"


class CatalogoTool(BaseTool):
    """
    Tool para brindar recomendaciones de autos disponibles en el catálogo
    según las preferencias del cliente.
    """
    
    name: str = "catalogo_autos"
    description: str = "Busca y recomienda autos del catálogo basado en preferencias como presupuesto, marca, modelo, año, tipo de vehículo"
    gestor_estados: GestorEstados = Field(exclude=True)
    telefono_actual: str = Field(exclude=True)
    
    def __init__(self, gestor_estados: GestorEstados, **kwargs):
        super().__init__(gestor_estados=gestor_estados, telefono_actual="", **kwargs)
    
    def _run(self, preferencias: str) -> str:
        """
        Ejecutar búsqueda en catálogo
        
        Args:
            preferencias: Preferencias del cliente (presupuesto, marca, modelo, etc.)
            
        Returns:
            Recomendaciones de autos del catálogo
        """
        # Obtener el estado del usuario actual
        estado = self.gestor_estados.obtener_estado(self.telefono_actual)
        
        # Registrar consulta y preferencias en estado global
        estado.actualizar('ultima_consulta', f"catalogo: {preferencias}")
        estado.actualizar('cliente_preferencias', preferencias)
        
        # Por ahora solo pass - implementaremos lógica después
        pass
        
        return "Recomendaciones de catálogo - En construcción"


class FinanzasTool(BaseTool):
    """
    Tool para calcular y otorgar planes de financiamiento.
    Calcula pagos basado en enganche, precio del auto, tasa 10% y plazos 3-6 años.
    """
    
    name: str = "planes_financiamiento"
    description: str = "Calcula planes de financiamiento basado en enganche, precio del auto, tasa de interés del 10% y plazos de 3 a 6 años"
    gestor_estados: GestorEstados = Field(exclude=True)
    telefono_actual: str = Field(exclude=True)
    
    def __init__(self, gestor_estados: GestorEstados, **kwargs):
        super().__init__(gestor_estados=gestor_estados, telefono_actual="", **kwargs)
    
    def _run(self, parametros_financiamiento: str) -> str:
        """
        Calcular plan de financiamiento
        
        Args:
            parametros_financiamiento: Parámetros como precio, enganche, plazo
            
        Returns:
            Plan de financiamiento calculado
        """
        # Obtener el estado del usuario actual
        estado = self.gestor_estados.obtener_estado(self.telefono_actual)
        
        # Registrar consulta en estado global
        estado.actualizar('ultima_consulta', f"financiamiento: {parametros_financiamiento}")
        
        # Por ahora solo pass - implementaremos lógica después
        pass
        
        return "Plan de financiamiento - En construcción"


class AgentePrincipal:
    """
    Agente principal que coordina las tools y maneja la lógica de conversación.
    Utiliza OpenAI GPT-3.5-turbo como modelo base.
    Ahora gestiona estados separados por número de teléfono.
    """
    
    def __init__(self):
        """Inicializar el agente principal con gestor de estados multiusuario"""
        
        # Inicializar gestor de estados (uno por teléfono)
        self.gestor_estados = GestorEstados()
        
        # Inicializar modelo OpenAI
        self.llm = ChatOpenAI(
            model="gpt-3.5-turbo",
            temperature=0.3,
            openai_api_key=os.getenv('OPENAI_API_KEY')
        )
        
        # Inicializar tools con gestor de estados
        self.tools = [
            PropuestaValorTool(self.gestor_estados),
            CatalogoTool(self.gestor_estados),
            FinanzasTool(self.gestor_estados)
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
    
    def _configurar_tools_para_usuario(self, telefono_usuario: str) -> None:
        """
        Configurar las tools para que usen el estado del usuario específico
        
        Args:
            telefono_usuario: Número de teléfono del usuario actual
        """
        for tool in self.tools:
            tool.telefono_actual = telefono_usuario
    
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
            # Configurar tools para el usuario actual
            self._configurar_tools_para_usuario(telefono_usuario)
            
            # Obtener estado del usuario
            estado_usuario = self.gestor_estados.obtener_estado(telefono_usuario)
            
            # Registrar el mensaje en el historial del usuario
            estado_usuario.actualizar('ultimo_mensaje', mensaje)
            
            # Ejecutar agente
            respuesta = self.agent_executor.invoke({
                "input": mensaje
            })
            
            # Extraer respuesta final
            respuesta_final = respuesta.get('output', 'Lo siento, no pude procesar tu mensaje.')
            
            # Registrar la respuesta en el estado del usuario
            estado_usuario.actualizar('ultima_respuesta', respuesta_final)
            
            return respuesta_final
            
        except Exception as e:
            print(f"Error procesando mensaje para {telefono_usuario}: {e}")
            return "Lo siento, ocurrió un error procesando tu consulta. ¿Podrías intentar de nuevo?"
    
    def obtener_estado_actual(self, telefono_usuario: str) -> Dict[str, Any]:
        """
        Obtener el estado actual del agente para un usuario específico
        
        Args:
            telefono_usuario: Número de teléfono del usuario
            
        Returns:
            Resumen del estado del usuario
        """
        estado_usuario = self.gestor_estados.obtener_estado(telefono_usuario)
        return estado_usuario.obtener_resumen()
    
    def reiniciar_conversacion(self, telefono_usuario: str) -> None:
        """
        Reiniciar la conversación para un usuario específico
        
        Args:
            telefono_usuario: Número de teléfono del usuario
        """
        self.gestor_estados.reiniciar_estado(telefono_usuario)
        print(f"Conversación reiniciada para usuario: {telefono_usuario}")
    
    def obtener_historial(self, telefono_usuario: str) -> List[Dict[str, Any]]:
        """
        Obtener historial de acciones para un usuario específico
        
        Args:
            telefono_usuario: Número de teléfono del usuario
            
        Returns:
            Lista de acciones realizadas por el usuario
        """
        estado_usuario = self.gestor_estados.obtener_estado(telefono_usuario)
        return estado_usuario.obtener('historial_acciones') or []
    
    def obtener_resumen_general(self) -> Dict[str, Any]:
        """
        Obtener resumen de todos los usuarios activos
        
        Returns:
            Diccionario con información de todos los usuarios
        """
        return self.gestor_estados.obtener_resumen_general()
    
    def limpiar_usuarios_inactivos(self, horas: int = 24) -> int:
        """
        Limpiar usuarios inactivos por más de X horas
        
        Args:
            horas: Horas de inactividad para limpiar
            
        Returns:
            Número de usuarios eliminados
        """
        usuarios_eliminados = self.gestor_estados.limpiar_estados_antiguos(horas)
        print(f"Limpiados {usuarios_eliminados} usuarios inactivos por más de {horas} horas")
        return usuarios_eliminados
    
    def obtener_usuarios_activos(self) -> List[str]:
        """
        Obtener lista de usuarios con conversaciones activas
        
        Returns:
            Lista de números de teléfono activos
        """
        return self.gestor_estados.obtener_usuarios_activos()
    
    def eliminar_usuario(self, telefono_usuario: str) -> bool:
        """
        Eliminar un usuario específico del sistema
        
        Args:
            telefono_usuario: Número de teléfono del usuario
            
        Returns:
            True si se eliminó exitosamente
        """
        return self.gestor_estados.eliminar_estado(telefono_usuario)