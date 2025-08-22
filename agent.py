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
from catalogo_autos import CatalogoAutos, formatear_lista_autos
import financiamiento
import traceback


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
        Ejecutar búsqueda en catálogo con lógica híbrida:
        - Si hay stock_id: buscar por ID específico
        - Si no hay stock_id: buscar por filtros
        
        Args:
            preferencias: Preferencias del cliente o consulta sobre auto actual
            
        Returns:
            Recomendaciones de autos del catálogo
        """
        try:    
            # Obtener el estado del usuario actual
            estado = self.gestor_estados.obtener_estado(self.telefono_actual)
            
            # Registrar consulta en estado global
            estado.actualizar('ultima_consulta', f"catalogo: {preferencias}")
            estado.actualizar('tipo_consulta', 'busqueda_catalogo')
            
            print(f"DEBUG CatalogoTool: Procesando: {preferencias}")
            
            # Inicializar catálogo
            catalogo = CatalogoAutos()
            
            # LÓGICA HÍBRIDA: Verificar si ya hay un auto seleccionado
            stock_id_actual = estado.obtener('auto_stock_id')
            
            if stock_id_actual and self._es_consulta_sobre_auto_actual(preferencias):
                # CASO 1: Ya hay auto seleccionado y pregunta sobre él
                print(f"DEBUG: Consultando auto actual con stock_id: {stock_id_actual}")
                return self._procesar_consulta_auto_actual(catalogo, estado, preferencias)
            
            elif self._es_nueva_busqueda(preferencias):
                # CASO 2: Nueva búsqueda - limpiar auto anterior y buscar por filtros
                print(f"DEBUG: Nueva búsqueda detectada, limpiando auto anterior")
                estado.limpiar_auto_completo()
                return self._procesar_nueva_busqueda(catalogo, estado, preferencias)
            
            else:
                # CASO 3: Búsqueda normal por filtros (primera vez o sin auto específico)
                print(f"DEBUG: Búsqueda por filtros")
                return self._procesar_nueva_busqueda(catalogo, estado, preferencias)
                
        except Exception as e:
            print(f"ERROR en CatalogoTool: {e}")
            traceback.print_exc()
            return "Disculpa, ocurrió un error al buscar en el catálogo. ¿Podrías reformular tu búsqueda?"

    def _es_consulta_sobre_auto_actual(self, preferencias: str) -> bool:
        """
        Detectar si la consulta es sobre el auto ya seleccionado
        
        Args:
            preferencias: Texto del usuario
            
        Returns:
            True si consulta sobre auto actual
        """
        preferencias_lower = preferencias.lower()
        
        # Palabras que indican consulta sobre auto actual
        palabras_consulta_actual = [
            'detalles', 'información', 'más info', 'dime más', 'cuéntame',
            'tiene bluetooth', 'tiene carplay', 'dimensiones', 'características',
            'este auto', 'ese auto', 'el auto', 'más sobre', 'especificaciones'
        ]
        
        return any(palabra in preferencias_lower for palabra in palabras_consulta_actual)

    def _es_nueva_busqueda(self, preferencias: str) -> bool:
        """
        Detectar si es una nueva búsqueda que requiere limpiar auto anterior
        
        Args:
            preferencias: Texto del usuario
            
        Returns:
            True si es nueva búsqueda
        """
        preferencias_lower = preferencias.lower()
        
        # Palabras que indican nueva búsqueda
        palabras_nueva_busqueda = [
            'quiero', 'busco', 'prefiero', 'mejor', 'otro', 'diferente',
            'muéstrame', 'opciones', 'alternativa', 'cambiar'
        ]
        
        return any(palabra in preferencias_lower for palabra in palabras_nueva_busqueda)

    def _procesar_consulta_auto_actual(self, catalogo: CatalogoAutos, estado: EstadoGlobal, preferencias: str) -> str:
        """
        Procesar consulta sobre auto ya seleccionado
        
        Args:
            catalogo: Instancia del catálogo
            estado: Estado del usuario
            preferencias: Consulta del usuario
            
        Returns:
            Información detallada del auto seleccionado
        """
        stock_id = estado.obtener('auto_stock_id')
        
        # Obtener auto completo por stock_id
        auto_completo = catalogo.obtener_auto_por_stock_id(stock_id)
        
        if not auto_completo:
            estado.limpiar_auto_completo()
            return "Lo siento, el auto que tenías seleccionado ya no está disponible. ¿Te gustaría buscar otro?"
        
        # Actualizar estado con datos más recientes
        estado.actualizar_auto_seleccionado(auto_completo)
        
        # Generar respuesta detallada
        respuesta = self._generar_respuesta_detallada(auto_completo, preferencias)
        
        estado.actualizar('ultima_respuesta_tipo', 'detalles_auto_actual')
        
        return respuesta

    def _procesar_nueva_busqueda(self, catalogo: CatalogoAutos, estado: EstadoGlobal, preferencias: str) -> str:
        """
        Procesar nueva búsqueda por filtros
        
        Args:
            catalogo: Instancia del catálogo
            estado: Estado del usuario
            preferencias: Preferencias de búsqueda
            
        Returns:
            Lista de autos encontrados
        """
        # Buscar autos según preferencias
        autos_encontrados = catalogo.buscar_autos(preferencias)
        
        print(f"DEBUG: Encontrados {len(autos_encontrados)} autos")
        
        # Guardar resultados en el estado
        estado.actualizar_autos_recomendados(autos_encontrados)
        
        # Si se encontraron autos, guardar filtros aplicados
        if autos_encontrados:
            filtros_aplicados = catalogo._extraer_filtros(preferencias)
            estado.actualizar_filtros_busqueda(filtros_aplicados)
            
            # Detectar si el usuario muestra interés específico en un auto
            auto_especifico = self._detectar_auto_especifico(preferencias, autos_encontrados)
            
            if auto_especifico:
                # Guardar el auto específico Y su stock_id
                estado.actualizar_auto_seleccionado(auto_especifico)
                print(f"DEBUG: Auto específico seleccionado - stock_id: {auto_especifico.get('stock_id')}")
        
        # Formatear respuesta
        respuesta_formateada = formatear_lista_autos(autos_encontrados)
        
        estado.actualizar('ultima_respuesta_tipo', 'busqueda_catalogo')
        
        # Agregar contexto adicional
        if autos_encontrados:
            respuesta_final = f"{respuesta_formateada}\n\nTambién puedo ayudarte con el financiamiento de cualquiera de estos autos si te interesa."
        else:
            # Sugerir alternativas si no se encontraron autos
            estadisticas = catalogo.obtener_estadisticas()
            marcas_disponibles = estadisticas.get('marcas_disponibles', [])[:5]
            
            respuesta_final = f"{respuesta_formateada}\n\nTenemos autos de estas marcas disponibles: {', '.join(marcas_disponibles)}\n\n¿Te gustaría ajustar tu búsqueda o ver opciones de alguna marca específica?"
        
        return respuesta_final

    def _generar_respuesta_detallada(self, auto: Dict[str, Any], consulta: str) -> str:
        """
        Generar respuesta detallada sobre auto específico
        
        Args:
            auto: Datos completos del auto
            consulta: Consulta específica del usuario
            
        Returns:
            Respuesta detallada
        """
        consulta_lower = consulta.lower()
        
        # Información básica siempre incluida
        precio_formateado = f"${auto.get('price', 0):,.0f} MXN"
        km_formateado = f"{auto.get('km', 0):,} km"
        
        respuesta = f"""Aquí tienes los detalles de tu {auto.get('make', 'N/A')} {auto.get('model', 'N/A')} {auto.get('year', 'N/A')}:

    Precio: {precio_formateado}
    Kilometraje: {km_formateado}
    Versión: {auto.get('version', 'N/A')}
    Bluetooth: {'Sí' if auto.get('bluetooth') == 'Sí' else 'No'}
    CarPlay: {'Sí' if auto.get('car_play') == 'Sí' else 'No'}"""
        
        # Agregar información específica según la consulta
        if 'bluetooth' in consulta_lower:
            bluetooth_status = 'Sí' if auto.get('bluetooth') == 'Sí' else 'No'
            respuesta += f"\n\nBluetooth: {bluetooth_status}"
        
        if 'carplay' in consulta_lower or 'car play' in consulta_lower:
            carplay_status = 'Sí' if auto.get('car_play') == 'Sí' else 'No'
            respuesta += f"\n\nCarPlay: {carplay_status}"
        
        if 'dimensiones' in consulta_lower:
            respuesta += f"\n\nDimensiones:"
            respuesta += f"\nLargo: {auto.get('largo', 'N/A')} mm"
            respuesta += f"\nAncho: {auto.get('ancho', 'N/A')} mm"
            respuesta += f"\nAltura: {auto.get('altura', 'N/A')} mm"
        
        respuesta += f"\n\nID del vehículo: {auto.get('stock_id', 'N/A')}"
        respuesta += "\n\n¿Te gustaría conocer las opciones de financiamiento para este auto?"
        
        return respuesta

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
    description: str = "Calcula planes de financiamiento para autos con tasa fija del 10% anual y plazos de 3, 4, 5 o 6 años. Usa esta tool cuando el usuario pregunte sobre financiamiento, pagos mensuales, enganches, o planes de pago para un auto."
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
        try:
            # Obtener el estado del usuario actual
            estado = self.gestor_estados.obtener_estado(self.telefono_actual)
            
            # Registrar consulta en estado global
            estado.actualizar('ultima_consulta', f"financiamiento: {parametros_financiamiento}")
            estado.actualizar('tipo_consulta', 'calculo_financiamiento')
            
            print(f"DEBUG FinanzasTool: Calculando financiamiento con: {parametros_financiamiento}")
            
            # Obtener información del auto seleccionado
            auto_precio = estado.obtener('auto_precio')
            auto_info = estado.obtener_info_auto_completa()
            
            # Validar que hay auto seleccionado
            if not financiamiento.validar_auto_seleccionado(auto_precio):
                return financiamiento.generar_mensaje_sin_auto()
            
            # Extraer parámetros del texto del usuario
            enganche_especificado = financiamiento.extraer_enganche(parametros_financiamiento, auto_precio)
            plazo_especifico = financiamiento.extraer_plazo(parametros_financiamiento)
            
            print(f"DEBUG FinanzasTool: Precio auto: ${auto_precio:,.0f}, Enganche: {enganche_especificado}, Plazo: {plazo_especifico}")
            
            # Generar respuesta según parámetros especificados
            if enganche_especificado:
                # Enganche específico proporcionado
                respuesta = financiamiento.generar_plan_especifico(auto_info, auto_precio, enganche_especificado, plazo_especifico)
                
                # Guardar parámetros en el estado
                estado.actualizar('enganche', enganche_especificado)
                estado.actualizar('monto_financiar', auto_precio - enganche_especificado)
                
                if plazo_especifico:
                    # Calcular y guardar pago mensual para plazo específico
                    pago_mensual = financiamiento.CalculadoraFinanciamiento.calcular_pago_mensual(
                        auto_precio - enganche_especificado, plazo_especifico
                    )
                    estado.actualizar('plazo_años', plazo_especifico)
                    estado.actualizar('pago_mensual', pago_mensual)
                    
                    print(f"DEBUG: Guardado en estado - Enganche: ${enganche_especificado:,.0f}, Plazo: {plazo_especifico} años, Pago mensual: ${pago_mensual:,.0f}")
                
            else:
                # Sin enganche específico, mostrar múltiples opciones
                respuesta = financiamiento.generar_opciones_multiples(auto_info, auto_precio)
            
            # Registrar que se proporcionó financiamiento
            estado.actualizar('ultima_respuesta_tipo', 'planes_financiamiento')
            
            return respuesta
            
        except Exception as e:
            print(f"ERROR en FinanzasTool: {e}")
            traceback.print_exc()
            return "Disculpa, ocurrió un error al calcular el financiamiento. ¿Podrías proporcionar más detalles sobre el enganche que tienes disponible?"

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
            Eres un asistente de atención al cliente para Kavak México.

            REGLAS IMPORTANTES:
            1. SIEMPRE usa las herramientas para responder preguntas específicas
            2. Incluye TODA la información que devuelve la herramienta en tu respuesta
            3. Puedes agregar contexto útil adicional después de la información de la herramienta

            HERRAMIENTAS DISPONIBLES:
            - propuesta_valor: Para información sobre Kavak (sedes, beneficios, procesos)
            - catalogo_autos: Para buscar vehículos disponibles
            - planes_financiamiento: Para calcular financiamiento

            EJEMPLOS DE USO:
            - "Quiero un auto Toyota" → usa catalogo_autos y muestra TODA la lista detallada
            - "¿Qué es Kavak?" → usa propuesta_valor y proporciona la información completa
            - "Financiamiento para Toyota 2020" → usa catalogo_autos primero, luego planes_financiamiento

            IMPORTANTE: Cuando uses una herramienta, incluye TODA su respuesta en tu mensaje final.
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
            
            # CORRECCIÓN: Usar la respuesta del agente que YA incluye la info de las tools
            respuesta_final = respuesta.get('output', 'Lo siento, no pude procesar tu mensaje.')
            
            # Registrar la respuesta en el estado del usuario
            estado_usuario.actualizar('ultima_respuesta', respuesta_final)
            
            return respuesta_final
            
        except Exception as e:
            print(f"❌ ERROR procesando mensaje para {telefono_usuario}: {e}")
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