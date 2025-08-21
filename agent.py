import os
from typing import Dict, Any, List, Optional
from langchain.tools import BaseTool
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.schema import BaseMessage
from pydantic import BaseModel, Field
from estado_global import EstadoGlobal, GestorEstados
from conocimiento_kavak import buscar_informacion


class PropuestaValorTool(BaseTool):
    """
    Tool para responder información básica sobre la propuesta de valor.
    Proporciona información general sobre servicios, garantías, proceso de compra, etc.
    """
    
    name: str = "propuesta_valor"
    description: str = "Proporciona información básica sobre la propuesta de valor, servicios, garantías y beneficios de Kavak. Usa esta tool para preguntas sobre: sedes/ubicaciones, certificación de autos, proceso digital, financiamiento, garantías, app, o información general de la empresa"
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
        try:
            
            # Obtener el estado del usuario actual
            estado = self.gestor_estados.obtener_estado(self.telefono_actual)
            
            # Registrar la consulta en el estado global
            estado.actualizar('ultima_consulta', f"propuesta_valor: {query}")
            estado.actualizar('tipo_consulta', 'informacion_general')
            
            # Buscar información relevante usando la base de conocimiento
            respuesta = buscar_informacion(query)
            
            # Registrar que se proporcionó información
            estado.actualizar('ultima_respuesta_tipo', 'propuesta_valor')
            
            # Agregar contexto amigable a la respuesta
            respuesta_final = f"¡Hola! Te comparto la información sobre Kavak:\n\n{respuesta}\n\n¿Te gustaría saber algo más específico o necesitas ayuda con algo más?"
            
            return respuesta_final
            
        except ImportError:
            return "Lo siento, hay un problema técnico con la información. ¿Podrías ser más específico sobre qué te gustaría saber de Kavak?"
        
        except Exception as e:
            print(f"Error en PropuestaValorTool: {e}")
            return "Disculpa, ocurrió un error al buscar la información. ¿Podrías reformular tu pregunta sobre Kavak?"


class CatalogoTool(BaseTool):
    """
    Tool para brindar recomendaciones de autos disponibles en el catálogo
    según las preferencias del cliente.
    """
    
    name: str = "catalogo_autos"
    description: str = "Busca y recomienda autos del catálogo basado en preferencias como presupuesto, marca, modelo, año, tipo de vehículo, kilometraje, características (bluetooth, carplay). Usa esta tool cuando el usuario quiera ver autos disponibles, buscar un auto específico, o pida recomendaciones de vehículos."
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
        try:
            # Importar módulos necesarios
            from catalogo_autos import CatalogoAutos, formatear_lista_autos
            
            # Obtener el estado del usuario actual
            estado = self.gestor_estados.obtener_estado(self.telefono_actual)
            
            # Registrar consulta y preferencias en estado global
            estado.actualizar('ultima_consulta', f"catalogo: {preferencias}")
            estado.actualizar('cliente_preferencias', preferencias)
            estado.actualizar('tipo_consulta', 'busqueda_catalogo')
            
            print(f"🔍 DEBUG CatalogoTool: Buscando autos con preferencias: {preferencias}")
            
            # Inicializar catálogo
            catalogo = CatalogoAutos()
            
            # Buscar autos según preferencias
            autos_encontrados = catalogo.buscar_autos(preferencias)
            
            print(f"🔍 DEBUG CatalogoTool: Encontrados {len(autos_encontrados)} autos")
            
            # Guardar resultados en el estado
            estado.actualizar_autos_recomendados(autos_encontrados)
            
            # Si se encontraron autos, guardar filtros aplicados
            if autos_encontrados:
                # Extraer filtros para guardar en estado
                filtros_aplicados = catalogo._extraer_filtros(preferencias)
                estado.actualizar_filtros_busqueda(filtros_aplicados)
                
                print(f"🔍 DEBUG CatalogoTool: Filtros aplicados: {filtros_aplicados}")
            
            # Detectar si el usuario muestra interés específico en un auto
            if autos_encontrados:
                auto_especifico = self._detectar_auto_especifico(preferencias, autos_encontrados)
                
                if auto_especifico:
                    # Guardar el auto específico en el estado
                    estado.actualizar_auto_seleccionado(auto_especifico)
                    print(f"🔍 DEBUG CatalogoTool: Auto específico guardado: {auto_especifico.get('make')} {auto_especifico.get('model')} {auto_especifico.get('year')}")
            
            # Formatear respuesta
            respuesta_formateada = formatear_lista_autos(autos_encontrados)
            
            # Registrar que se proporcionaron recomendaciones
            estado.actualizar('ultima_respuesta_tipo', 'catalogo_autos')
            
            # Agregar contexto adicional
            if autos_encontrados:
                respuesta_final = f"{respuesta_formateada}\n\n💡 También puedo ayudarte con el financiamiento de cualquiera de estos autos si te interesa."
            else:
                # Sugerir alternativas si no se encontraron autos
                estadisticas = catalogo.obtener_estadisticas()
                marcas_disponibles = estadisticas.get('marcas_disponibles', [])[:5]  # Top 5 marcas
                
                respuesta_final = f"{respuesta_formateada}\n\n💡 Tenemos autos de estas marcas disponibles: {', '.join(marcas_disponibles)}\n\n¿Te gustaría ajustar tu búsqueda o ver opciones de alguna marca específica?"
            
            return respuesta_final
            
        except ImportError as e:
            print(f"❌ ERROR ImportError en CatalogoTool: {e}")
            return "Lo siento, hay un problema técnico con el catálogo. ¿Podrías intentar de nuevo en un momento?"
        
        except Exception as e:
            print(f"❌ ERROR en CatalogoTool: {e}")
            import traceback
            traceback.print_exc()
            return "Disculpa, ocurrió un error al buscar en el catálogo. ¿Podrías reformular tu búsqueda o ser más específico sobre qué tipo de auto buscas?"
    
    def _detectar_auto_especifico(self, preferencias: str, autos_encontrados: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """
        Detectar si el usuario está preguntando por un auto específico
        
        Args:
            preferencias: Texto de preferencias del usuario
            autos_encontrados: Lista de autos encontrados
            
        Returns:
            Auto específico si se detecta interés, None en caso contrario
        """
        if not autos_encontrados:
            return None
        
        preferencias_lower = preferencias.lower()
        
        # Detectar palabras que indican interés específico
        palabras_interes = [
            'quiero el', 'me interesa el', 'detalles del', 'información del',
            'dime sobre el', 'cuéntame del', 'ese auto', 'este auto',
            'quiero detalles', 'más información', 'me gusta el'
        ]
        
        # Si hay indicadores de interés específico
        for palabra in palabras_interes:
            if palabra in preferencias_lower:
                print(f"🔍 DEBUG: Detectada palabra de interés: {palabra}")
                
                # Si solo hay un auto encontrado, ese es el de interés
                if len(autos_encontrados) == 1:
                    print(f"🔍 DEBUG: Solo un auto encontrado, seleccionando automáticamente")
                    return autos_encontrados[0]
                
                # Si hay múltiples, buscar coincidencia específica en el texto
                for auto in autos_encontrados:
                    auto_descripcion = f"{auto.get('make', '')} {auto.get('model', '')}".lower()
                    if auto_descripcion in preferencias_lower:
                        print(f"🔍 DEBUG: Coincidencia específica encontrada: {auto_descripcion}")
                        return auto
                
                # Si no encuentra específico pero hay indicador de interés, tomar el primero
                print(f"🔍 DEBUG: Palabra de interés pero sin coincidencia específica, tomando el primero")
                return autos_encontrados[0]
        
        # Buscar modelo específico en las preferencias
        for auto in autos_encontrados:
            modelo = auto.get('model', '').lower()
            marca = auto.get('make', '').lower()
            año = str(auto.get('year', ''))
            
            # Verificar si menciona modelo específico
            if modelo in preferencias_lower and len(preferencias_lower.split()) <= 5:
                print(f"🔍 DEBUG: Modelo específico mencionado: {modelo}")
                return auto
            
            # Verificar si menciona marca + modelo
            if f"{marca} {modelo}" in preferencias_lower:
                print(f"🔍 DEBUG: Marca + modelo mencionados: {marca} {modelo}")
                return auto
            
            # Verificar si menciona modelo + año
            if modelo in preferencias_lower and año in preferencias_lower:
                print(f"🔍 DEBUG: Modelo + año mencionados: {modelo} {año}")
                return auto
        
        # Si la búsqueda es muy específica (pocas palabras) y hay pocos resultados
        if len(preferencias.split()) <= 3 and len(autos_encontrados) <= 2:
            print(f"🔍 DEBUG: Búsqueda específica con pocos resultados")
            return autos_encontrados[0]
        
        print(f"🔍 DEBUG: No se detectó interés específico")
        return None

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
        self.agent = create_openai_tools_agent(
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
        prompt = ChatPromptTemplate.from_messages([
            ("system", """
            Eres un asistente de atención al cliente especializado para Kavak México.
            
            INSTRUCCIONES IMPORTANTES:
            1. Cuando uses una herramienta, SIEMPRE utiliza su respuesta completa como base para tu respuesta final
            2. NO agregues respuestas genéricas como "¿Hay algo más en lo que pueda ayudarte?"
            3. Responde directamente con la información que te proporciona la herramienta
            
            Herramientas disponibles:
            - propuesta_valor: Para información sobre Kavak, beneficios, sedes, procesos, etc.
            - catalogo_autos: Para buscar vehículos específicos
            - planes_financiamiento: Para calcular opciones de pago
            
            Cuando el usuario haga una pregunta específica, usa la herramienta apropiada y responde con esa información.
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
        """
        try:
            # Configurar tools para el usuario actual
            self._configurar_tools_para_usuario(telefono_usuario)
            
            # Obtener estado del usuario
            estado_usuario = self.gestor_estados.obtener_estado(telefono_usuario)
            
            # Registrar el mensaje en el historial del usuario
            estado_usuario.actualizar('ultimo_mensaje', mensaje)
            
            print(f"🔍 DEBUG: Procesando mensaje: {mensaje}")
            print(f"🔍 DEBUG: Tools disponibles: {[tool.name for tool in self.tools]}")
            
            # Ejecutar agente
            respuesta = self.agent_executor.invoke({
                "input": mensaje
            })
            
            print(f"🔍 DEBUG: Respuesta completa del agente: {respuesta}")
            print(f"🔍 DEBUG: Pasos intermedios: {respuesta.get('intermediate_steps', [])}")
            
            # Extraer respuesta final
            respuesta_final = respuesta.get('output', 'Lo siento, no pude procesar tu mensaje.')
            
            # Registrar la respuesta en el estado del usuario
            estado_usuario.actualizar('ultima_respuesta', respuesta_final)
            
            return respuesta_final
            
        except Exception as e:
            print(f"❌ ERROR procesando mensaje para {telefono_usuario}: {e}")
            import traceback
            traceback.print_exc()
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