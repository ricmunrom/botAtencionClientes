from flask import Flask, request, jsonify
import requests
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

app = Flask(__name__)

# Configuración de WhatsApp Business API
VERIFY_TOKEN = os.getenv('VERIFY_TOKEN', 'kavak_bot_2024')  # Cambia esto por un token único
PAGE_ACCESS_TOKEN = os.getenv('PAGE_ACCESS_TOKEN')  # Token de tu página/WhatsApp Business
PHONE_NUMBER_ID = os.getenv('PHONE_NUMBER_ID')  # ID del número de WhatsApp Business

@app.route('/')
def home():
    return "Kavak Bot está funcionando! 🚗", 200

@app.route('/webhook', methods=['GET'])
def webhook_verify():
    """Verificación del webhook para Facebook"""
    # Obtener parámetros de la verificación
    mode = request.args.get('hub.mode')
    token = request.args.get('hub.verify_token')
    challenge = request.args.get('hub.challenge')
    
    # Verificar que el token coincida
    if mode == 'subscribe' and token == VERIFY_TOKEN:
        print("Webhook verificado exitosamente!")
        return challenge, 200
    else:
        print("Verificación falló. Token incorrecto.")
        return "Forbidden", 403

@app.route('/webhook', methods=['POST'])
def webhook_receive():
    """Recibir mensajes de WhatsApp Business"""
    try:
        data = request.get_json()
        print(f"Webhook recibido: {data}")  # Debug: ver qué llega
        
        # WhatsApp Business API estructura
        if data.get('object') == 'whatsapp_business_account':
            for entry in data.get('entry', []):
                for change in entry.get('changes', []):
                    if change.get('field') == 'messages':
                        value = change.get('value', {})
                        
                        # Verificar que hay mensajes
                        if 'messages' in value:
                            for message in value['messages']:
                                # Obtener datos del mensaje
                                sender_phone = message.get('from')
                                message_id = message.get('id')
                                message_type = message.get('type', '')
                                
                                # Obtener texto del mensaje
                                message_text = ""
                                if message_type == 'text':
                                    message_text = message.get('text', {}).get('body', '')
                                
                                print(f"WhatsApp mensaje de {sender_phone}: {message_text} (tipo: {message_type})")
                                
                                # Responder solo a mensajes de texto
                                if message_text:
                                    send_whatsapp_message(sender_phone, f"¡Hola! Recibí tu mensaje: '{message_text}'. Soy el bot de Kavak y estoy funcionando! 🚗")
        
        return "OK", 200
    
    except Exception as e:
        print(f"Error procesando webhook: {e}")
        return "Error", 500

def send_whatsapp_message(recipient_phone, message_text):
    """Enviar mensaje a través de WhatsApp Business API"""
    if not PAGE_ACCESS_TOKEN:
        print("Error: PAGE_ACCESS_TOKEN no configurado")
        return False
    
    # Obtener el Phone Number ID (necesario para WhatsApp)
    # Este valor lo obtienes de Facebook Developers > WhatsApp > Getting Started
    PHONE_NUMBER_ID = os.getenv('PHONE_NUMBER_ID', 'tu_phone_number_id_aqui')
    
    url = f"https://graph.facebook.com/v18.0/{PHONE_NUMBER_ID}/messages"
    
    payload = {
        "messaging_product": "whatsapp",
        "to": recipient_phone,
        "type": "text",
        "text": {
            "body": message_text
        }
    }
    
    headers = {
        "Authorization": f"Bearer {PAGE_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code == 200:
            print(f"WhatsApp mensaje enviado exitosamente a {recipient_phone}")
            return True
        else:
            print(f"Error enviando WhatsApp mensaje: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"Excepción enviando WhatsApp mensaje: {e}")
        return False

def send_message(recipient_id, message_text):
    """Enviar mensaje a través de Facebook Messenger (legacy)"""
    if not PAGE_ACCESS_TOKEN:
        print("Error: PAGE_ACCESS_TOKEN no configurado")
        return False
    
    url = f"https://graph.facebook.com/v18.0/me/messages?access_token={PAGE_ACCESS_TOKEN}"
    
    payload = {
        "recipient": {"id": recipient_id},
        "message": {"text": message_text}
    }
    
    headers = {"Content-Type": "application/json"}
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code == 200:
            print(f"Mensaje enviado exitosamente a {recipient_id}")
            return True
        else:
            print(f"Error enviando mensaje: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"Excepción enviando mensaje: {e}")
        return False

@app.route('/health')
def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "kavak-bot"}, 200

if __name__ == '__main__':
    # Para desarrollo local
    app.run(debug=True, host='0.0.0.0', port=5000)