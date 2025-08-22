from flask import Flask, request, jsonify
import requests
import os
from typing import Dict, Optional, Any, List
from agent import AgentePrincipal
import logging

# Crear directorio logs si no existe
if not os.path.exists('logs'):
    os.makedirs('logs')

# Configuración básica
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/bot.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class AtencionClientesBot:
    """
    Bot de atención al cliente que integra WhatsApp Business API con agente LangChain
    """
    
    def __init__(self):
        """Inicializar el bot con configuraciones y agente"""
        
        # Configuración de WhatsApp Business API
        self.verify_token = os.getenv('VERIFY_TOKEN', 'bot_atencion_2024')
        self.page_access_token = os.getenv('PAGE_ACCESS_TOKEN')
        self.phone_number_id = os.getenv('PHONE_NUMBER_ID')
        
        # Inicializar agente principal
        self.agente = AgentePrincipal()
        
        # Validar configuración
        if not self.page_access_token:
            logger.warning("PAGE_ACCESS_TOKEN no configurado")
        if not self.phone_number_id:
            logger.warning("PHONE_NUMBER_ID no configurado")
        if not os.getenv('OPENAI_API_KEY'):
            logger.warning("OPENAI_API_KEY no configurado")
    
    def verificar_webhook(self, mode: str, token: str, challenge: str) -> tuple:
        """
        Verificar webhook de WhatsApp Business
        
        Args:
            mode: Modo de verificación
            token: Token de verificación
            challenge: Challenge code
            
        Returns:
            Tupla (respuesta, código_status)
        """
        if mode == 'subscribe' and token == self.verify_token:
            logger.info("Webhook verificado exitosamente!")
            return challenge, 200
        else:
            logger.warning("Verificación falló. Token incorrecto.")
            return "Forbidden", 403
    
    def procesar_webhook_whatsapp(self, data: Dict) -> tuple:
        """
        Procesar webhook recibido de WhatsApp Business
        
        Args:
            data: Datos del webhook
            
        Returns:
            Tupla (respuesta, código_status)
        """
        try:
            logger.info(f"Webhook recibido: {data}")
            if data.get('object') == 'whatsapp_business_account':
                for entry in data.get('entry', []):
                    for change in entry.get('changes', []):
                        if change.get('field') == 'messages':
                            self._procesar_mensajes(change.get('value', {}))
            return "OK", 200
        except Exception as e:
            logger.error(f"Error procesando webhook: {e}")
            return "Error", 500
    
    def _procesar_mensajes(self, value: Dict) -> None:
        """
        Procesar mensajes recibidos de WhatsApp
        
        Args:
            value: Datos de los mensajes
        """
        if 'messages' not in value:
            return
        
        for message in value['messages']:
            # Obtener datos del mensaje
            sender_phone = message.get('from')
            message_id = message.get('id')
            message_type = message.get('type', '')
            
            # Procesar solo mensajes de texto
            if message_type == 'text':
                message_text = message.get('text', {}).get('body', '')
                
                if message_text and sender_phone:
                    logger.info(f"Mensaje de {sender_phone}: {message_text}")
                    
                    # Procesar mensaje con el agente 
                    respuesta = self.agente.procesar_mensaje(message_text, sender_phone)
                    
                    # Enviar respuesta
                    self.enviar_mensaje_whatsapp(sender_phone, respuesta)
    
    def enviar_mensaje_whatsapp(self, recipient_phone: str, message_text: str) -> bool:
        """
        Enviar mensaje a través de WhatsApp Business API
        
        Args:
            recipient_phone: Teléfono del destinatario
            message_text: Texto del mensaje
            
        Returns:
            True si se envió exitosamente, False en caso contrario
        """
        if not self.page_access_token or not self.phone_number_id:
            logger.error("Error: Credenciales de WhatsApp no configuradas")
            return False
        
        url = f"https://graph.facebook.com/v18.0/{self.phone_number_id}/messages"
        
        payload = {
            "messaging_product": "whatsapp",
            "to": recipient_phone,
            "type": "text",
            "text": {
                "body": message_text
            }
        }
        
        headers = {
            "Authorization": f"Bearer {self.page_access_token}",
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.post(url, json=payload, headers=headers)
            if response.status_code == 200:
                logger.info(f"WhatsApp mensaje enviado exitosamente a {recipient_phone}")
                return True
            else:
                logger.error(f"Error enviando WhatsApp mensaje: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            logger.error(f"Excepción enviando WhatsApp mensaje: {e}")
            return False
    
    def obtener_estado_agente(self, telefono: str) -> Dict:
        """
        Obtener estado actual del agente para un usuario
        
        Args:
            telefono: Teléfono del usuario
            
        Returns:
            Diccionario con estado del agente
        """
        return self.agente.obtener_estado_actual(telefono)
    
    def reiniciar_conversacion(self, telefono: str) -> bool:
        """
        Reiniciar conversación para un usuario específico
        
        Args:
            telefono: Teléfono del usuario
            
        Returns:
            True si se reinició exitosamente
        """
        try:
            self.agente.reiniciar_conversacion(telefono)
            return True
        except Exception as e:
            logger.error(f"Error reiniciando conversación: {e}")
            return False

    def obtener_resumen_general(self) -> Dict[str, Any]:
        """
        Obtener resumen de todos los usuarios activos
        
        Returns:
            Diccionario con información de todos los usuarios
        """
        return self.agente.gestor_estados.obtener_resumen_general()
    
    def limpiar_usuarios_inactivos(self, horas: int = 24) -> int:
        """
        Limpiar usuarios inactivos por más de X horas
        
        Args:
            horas: Horas de inactividad para limpiar
            
        Returns:
            Número de usuarios eliminados
        """
        usuarios_eliminados = self.agente.gestor_estados.limpiar_estados_antiguos(horas)
        logger.info(f"Limpiados {usuarios_eliminados} usuarios inactivos por más de {horas} horas")
        return usuarios_eliminados
    
    def obtener_usuarios_activos(self) -> List[str]:
        """
        Obtener lista de usuarios con conversaciones activas
        
        Returns:
            Lista de números de teléfono activos
        """
        return self.agente.gestor_estados.obtener_usuarios_activos()
    
    def eliminar_usuario(self, telefono_usuario: str) -> bool:
        """
        Eliminar un usuario específico del sistema
        
        Args:
            telefono_usuario: Número de teléfono del usuario
            
        Returns:
            True si se eliminó exitosamente
        """
        return self.agente.gestor_estados.eliminar_estado(telefono_usuario)            


# Inicializar aplicación Flask
app = Flask(__name__)

# Inicializar bot
bot_atencion = AtencionClientesBot()

@app.route('/')
def home():
    """Endpoint de inicio"""
    return "Bot de Atención al Cliente está funcionando! 🤖", 200

@app.route('/webhook', methods=['GET'])
def webhook_verify():
    """Verificación del webhook para WhatsApp Business"""
    mode = request.args.get('hub.mode')
    token = request.args.get('hub.verify_token')
    challenge = request.args.get('hub.challenge')
    
    respuesta, status = bot_atencion.verificar_webhook(mode, token, challenge)
    return respuesta, status

@app.route('/webhook', methods=['POST'])
def webhook_receive():
    """Recibir mensajes de WhatsApp Business"""
    data = request.get_json()
    respuesta, status = bot_atencion.procesar_webhook_whatsapp(data)
    return respuesta, status

@app.route('/health')
def health_check():
    """Health check endpoint"""
    usuarios_activos = len(bot_atencion.obtener_usuarios_activos())
    return {
        "status": "healthy", 
        "service": "atencion-clientes-bot",
        "agent_status": "initialized",
        "usuarios_activos": usuarios_activos
    }, 200

@app.route('/estado/<telefono>')
def obtener_estado(telefono: str):
    """
    Obtener estado actual del agente para un usuario
    Endpoint para debugging/monitoreo
    """
    try:
        estado = bot_atencion.obtener_estado_agente(telefono)
        return jsonify(estado), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/reiniciar/<telefono>', methods=['POST'])
def reiniciar_conversacion(telefono: str):
    """
    Reiniciar conversación para un usuario
    Endpoint para debugging/administración
    """
    try:
        exito = bot_atencion.reiniciar_conversacion(telefono)
        if exito:
            return jsonify({"mensaje": "Conversación reiniciada exitosamente"}), 200
        else:
            return jsonify({"error": "No se pudo reiniciar la conversación"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/resumen-general')
def resumen_general():
    """
    Obtener resumen de todos los usuarios activos
    Endpoint para monitoreo del sistema
    """
    try:
        resumen = bot_atencion.obtener_resumen_general()
        return jsonify(resumen), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/limpiar-inactivos', methods=['POST'])
def limpiar_usuarios_inactivos():
    """
    Limpiar usuarios inactivos por más de 24 horas
    Endpoint para mantenimiento del sistema
    """
    try:
        horas = request.json.get('horas', 24) if request.is_json else 24
        usuarios_limpiados = bot_atencion.limpiar_usuarios_inactivos(horas)
        return jsonify({
            "mensaje": f"Limpieza completada",
            "usuarios_eliminados": usuarios_limpiados,
            "horas_inactividad": horas
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/usuarios-activos')
def obtener_usuarios_activos():
    """
    Obtener lista de usuarios activos
    Endpoint para monitoreo del sistema
    """
    try:
        usuarios = bot_atencion.obtener_usuarios_activos()
        return jsonify({
            "total_usuarios": len(usuarios),
            "usuarios_activos": usuarios
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/eliminar-usuario/<telefono>', methods=['DELETE'])
def eliminar_usuario(telefono: str):
    """
    Eliminar un usuario específico del sistema
    Endpoint para administración del sistema
    """
    try:
        eliminado = bot_atencion.eliminar_usuario(telefono)
        if eliminado:
            return jsonify({"mensaje": f"Usuario {telefono} eliminado exitosamente"}), 200
        else:
            return jsonify({"error": f"Usuario {telefono} no encontrado"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/historial/<telefono>')
def obtener_historial_usuario(telefono: str):
    """Ver historial completo de acciones"""
    try:
        estado_usuario = bot_atencion.agente.gestor_estados.obtener_estado(telefono)
        historial = estado_usuario.obtener('historial_acciones') or []
        
        return jsonify({
            "usuario": telefono,
            "total_acciones": len(historial),
            "historial_completo": historial
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/test-agente', methods=['POST'])
def test_agente():
    """Endpoint para probar el agente directamente"""
    try:
        data = request.get_json()
        mensaje = data.get('mensaje', 'Necesito información sobre los beneficios de Kavak')
        telefono = data.get('telefono', '5215519118275')
        
        #logger.debug(f"Probando agente con mensaje: {mensaje}")
        #logger.debug(f"Teléfono: {telefono}")
        # Probar agente directamente
        respuesta = bot_atencion.agente.procesar_mensaje(mensaje, telefono)
        #logger.debug(f"Respuesta del agente: {respuesta}")
        
        # Obtener estado después
        estado = bot_atencion.obtener_estado_agente(telefono)
        
        return jsonify({
            "mensaje_enviado": mensaje,
            "respuesta_agente": respuesta,
            "estado_usuario": estado,
            "tools_disponibles": [tool.name for tool in bot_atencion.agente.tools]
        }), 200
        
    except Exception as e:
        logger.error(f"ERROR en test-agente: {e}")
        logger.error("Traceback completo:", exc_info=True)
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
