from flask import Flask, request, jsonify
import requests
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

app = Flask(__name__)

# Configuración de Facebook Messenger
VERIFY_TOKEN = os.getenv('VERIFY_TOKEN', 'kavak_bot_2024')  # Cambia esto por un token único
PAGE_ACCESS_TOKEN = os.getenv('PAGE_ACCESS_TOKEN')  # Token de tu página de Facebook

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
    """Recibir mensajes de Facebook Messenger"""
    try:
        data = request.get_json()
        
        # Verificar que sea un mensaje
        if data.get('object') == 'page':
            for entry in data.get('entry', []):
                for messaging_event in entry.get('messaging', []):
                    
                    # Verificar que es un mensaje recibido
                    if messaging_event.get('message'):
                        sender_id = messaging_event['sender']['id']
                        message_text = messaging_event['message'].get('text', '')
                        
                        print(f"Mensaje recibido de {sender_id}: {message_text}")
                        
                        # Respuesta simple por ahora
                        send_message(sender_id, f"¡Hola! Recibí tu mensaje: '{message_text}'. Soy el bot de Kavak y estoy en desarrollo. 🚗")
        
        return "OK", 200
    
    except Exception as e:
        print(f"Error procesando webhook: {e}")
        return "Error", 500

def send_message(recipient_id, message_text):
    """Enviar mensaje a través de Facebook Messenger"""
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