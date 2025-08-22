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
            
            print(f"🔍 DEBUG FinanzasTool: Calculando financiamiento con: {parametros_financiamiento}")
            
            # Obtener precio del auto seleccionado
            auto_precio = estado.obtener('auto_precio')
            auto_info = estado.obtener_info_auto_completa()
            
            if not auto_precio:
                return self._respuesta_sin_auto_seleccionado()
            
            # Extraer enganche del texto
            enganche_especificado = self._extraer_enganche(parametros_financiamiento, auto_precio)
            
            print(f"🔍 DEBUG FinanzasTool: Precio auto: ${auto_precio:,.0f}, Enganche: {enganche_especificado}")
            
            # Generar planes de financiamiento
            if enganche_especificado:
                # Si especificó enganche, calcular para ese enganche específico
                respuesta = self._generar_plan_especifico(auto_info, auto_precio, enganche_especificado, parametros_financiamiento)
                
            else:
                # Si no especificó enganche, mostrar múltiples opciones
                respuesta = self._generar_opciones_multiples(auto_info, auto_precio)
            
            # Registrar que se proporcionó financiamiento
            estado.actualizar('ultima_respuesta_tipo', 'planes_financiamiento')
            
            return respuesta
            
        except Exception as e:
            print(f"❌ ERROR en FinanzasTool: {e}")
            import traceback
            traceback.print_exc()
            return "Disculpa, ocurrió un error al calcular el financiamiento. ¿Podrías proporcionar más detalles sobre el enganche que tienes disponible?"
    
    def _respuesta_sin_auto_seleccionado(self) -> str:
        """Respuesta cuando no hay auto seleccionado"""
        return """Para calcular tu financiamiento necesito que primero selecciones un auto.
        
🔍 Puedes buscar autos diciendo algo como:
• "Quiero un Toyota con presupuesto de 300000"
• "Muéstrame autos del 2020"
• "Busco un auto con bluetooth"

Una vez que selecciones un auto, podremos calcular las opciones de financiamiento perfectas para ti."""
    
    def _extraer_enganche(self, texto: str, precio_auto: float) -> Optional[float]:
        """
        Extraer enganche del texto del usuario
        
        Args:
            texto: Texto con parámetros de financiamiento
            precio_auto: Precio del auto para calcular porcentajes
            
        Returns:
            Monto del enganche o None si no se especifica
        """
        texto_lower = texto.lower()
        
        # Buscar monto específico
        import re
        patron_monto = r'(\d{1,3}(?:,?\d{3})*(?:\.\d{2})?)\s*(?:pesos|mx|mxn|de enganche|enganche)?'
        montos = re.findall(patron_monto, texto_lower.replace(',', ''))
        
        if montos:
            try:
                monto = float(montos[0].replace(',', ''))
                # Si es menor a 1000, probablemente son miles
                if monto < 1000:
                    monto *= 1000
                
                # Validar que el enganche no sea mayor al precio del auto
                if monto <= precio_auto:
                    return monto
            except:
                pass
        
        # Buscar porcentaje
        patron_porcentaje = r'(\d{1,2})\s*%'
        porcentajes = re.findall(patron_porcentaje, texto_lower)
        
        if porcentajes:
            try:
                porcentaje = float(porcentajes[0]) / 100
                if 0.05 <= porcentaje <= 0.80:  # Entre 5% y 80%
                    return precio_auto * porcentaje
            except:
                pass
        
        return None
    
    def _extraer_plazo(self, texto: str) -> Optional[int]:
        """
        Extraer plazo específico del texto
        
        Args:
            texto: Texto con parámetros de financiamiento
            
        Returns:
            Plazo en años o None
        """
        import re
        texto_lower = texto.lower()
        
        # Buscar patrones como "3 años", "a 4 años", "financiar a 5 años"
        patrones_plazo = [
            r'(\d)\s*años?',
            r'a\s*(\d)\s*años?',
            r'financiar\s*a\s*(\d)\s*años?',
            r'plazo\s*de\s*(\d)\s*años?'
        ]
        
        for patron in patrones_plazo:
            matches = re.findall(patron, texto_lower)
            if matches:
                try:
                    plazo = int(matches[0])
                    # Validar que esté en el rango permitido (3-6 años)
                    if 3 <= plazo <= 6:
                        print(f"🔍 DEBUG: Plazo específico detectado: {plazo} años")
                        return plazo
                except:
                    pass
        
        return None
    
    def _calcular_pago_mensual(self, monto_financiar: float, años: int) -> float:
        """
        Calcular pago mensual con fórmula de financiamiento
        
        Args:
            monto_financiar: Monto a financiar
            años: Años del plazo
            
        Returns:
            Pago mensual
        """
        if monto_financiar <= 0:
            return 0
        
        tasa_anual = 0.10  # 10% fijo
        tasa_mensual = tasa_anual / 12
        num_pagos = años * 12
        
        # Fórmula de financiamiento: PMT = [P × r × (1 + r)^n] / [(1 + r)^n - 1]
        if tasa_mensual == 0:
            return monto_financiar / num_pagos
        
        factor = (1 + tasa_mensual) ** num_pagos
        pago_mensual = (monto_financiar * tasa_mensual * factor) / (factor - 1)
        
        return pago_mensual
    
    def _generar_plan_especifico(self, auto_info: Dict, precio_auto: float, enganche: float, parametros_financiamiento: str) -> str:
        """Generar plan para enganche específico"""
        monto_financiar = precio_auto - enganche
        auto_descripcion = f"{auto_info.get('marca', 'N/A')} {auto_info.get('modelo', 'N/A')} {auto_info.get('año', 'N/A')}"
        
        # Verificar si se especificó un plazo específico
        plazo_especifico = self._extraer_plazo(parametros_financiamiento)
        
        if plazo_especifico:
            # Plan específico para un plazo
            pago_mensual = self._calcular_pago_mensual(monto_financiar, plazo_especifico)
            total_pagos = pago_mensual * plazo_especifico * 12
            total_intereses = total_pagos - monto_financiar
            
            respuesta = f"""💰 **Plan de financiamiento para {auto_descripcion}**

🚗 Precio del auto: ${precio_auto:,.0f} MXN
💵 Enganche: ${enganche:,.0f} MXN ({enganche/precio_auto*100:.1f}%)
🏦 Monto a financiar: ${monto_financiar:,.0f} MXN
📊 Tasa de interés: 10% anual

⏱️ **Financiamiento a {plazo_especifico} años ({plazo_especifico * 12} mensualidades)**
💳 Pago mensual: ${pago_mensual:,.0f} MXN
💰 Total a pagar: ${total_pagos:,.0f} MXN
📈 Total intereses: ${total_intereses:,.0f} MXN

¿Te interesa esta opción? ¡Puedo ayudarte con los siguientes pasos!"""
            
            # Guardar todos los valores en el estado
            estado = self.gestor_estados.obtener_estado(self.telefono_actual)
            estado.actualizar('enganche', enganche)
            estado.actualizar('monto_financiar', monto_financiar)
            estado.actualizar('plazo_años', plazo_especifico)
            estado.actualizar('pago_mensual', pago_mensual)
            
            print(f"🔍 DEBUG: Guardado en estado - Enganche: ${enganche:,.0f}, Plazo: {plazo_especifico} años, Pago mensual: ${pago_mensual:,.0f}")
            
        else:
            # Plan con múltiples opciones de plazo
            respuesta = f"""💰 **Plan de financiamiento para {auto_descripcion}**

🚗 Precio del auto: ${precio_auto:,.0f} MXN
💵 Enganche: ${enganche:,.0f} MXN ({enganche/precio_auto*100:.1f}%)
🏦 Monto a financiar: ${monto_financiar:,.0f} MXN
📊 Tasa de interés: 10% anual

**Opciones de pago mensual:**
"""
            
            for años in [3, 4, 5, 6]:
                pago_mensual = self._calcular_pago_mensual(monto_financiar, años)
                total_pagos = pago_mensual * años * 12
                total_intereses = total_pagos - monto_financiar
                
                respuesta += f"""
⏱️ **{años} años ({años * 12} mensualidades)**
   💳 Pago mensual: ${pago_mensual:,.0f} MXN
   💰 Total a pagar: ${total_pagos:,.0f} MXN
   📈 Total intereses: ${total_intereses:,.0f} MXN
"""
            
            respuesta += "\n¿Te interesa alguna de estas opciones? ¡Puedo ayudarte con los siguientes pasos!"
            
            # Solo guardar enganche cuando no hay plazo específico
            estado = self.gestor_estados.obtener_estado(self.telefono_actual)
            estado.actualizar('enganche', enganche)
            estado.actualizar('monto_financiar', monto_financiar)
        
        return respuesta
    
    def _generar_opciones_multiples(self, auto_info: Dict, precio_auto: float) -> str:
        """Generar múltiples opciones de enganche"""
        auto_descripcion = f"{auto_info.get('marca', 'N/A')} {auto_info.get('modelo', 'N/A')} {auto_info.get('año', 'N/A')}"
        
        respuesta = f"""💰 **Opciones de financiamiento para {auto_descripcion}**
🚗 Precio: ${precio_auto:,.0f} MXN | 📊 Tasa: 10% anual

"""
        
        # Opciones de enganche: 10%, 20%, 30%
        enganches = [0.10, 0.20, 0.30]
        
        for porcentaje_enganche in enganches:
            enganche = precio_auto * porcentaje_enganche
            monto_financiar = precio_auto - enganche
            
            respuesta += f"""**💵 Con {porcentaje_enganche*100:.0f}% de enganche (${enganche:,.0f} MXN):**
"""
            
            for años in [3, 4, 5, 6]:
                pago_mensual = self._calcular_pago_mensual(monto_financiar, años)
                respuesta += f"   • {años} años: ${pago_mensual:,.0f}/mes\n"
            
            respuesta += "\n"
        
        respuesta += "💡 ¿Qué enganche y plazo te conviene más? Puedo darte más detalles de cualquier opción."
        
        return respuesta

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