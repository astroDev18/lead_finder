from flask import Flask
from dotenv import load_dotenv
import logging
import threading


# Import controllers
from controllers.campaign_controller import campaign_bp
from controllers.call_controller import call_bp
from controllers.voice_controller import voice_bp

# Import services initialization
from services import init_services
from services.asterisk_service import AsteriskARIClient

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Create Asterisk ARI client
ari_client = AsteriskARIClient(
    host=os.environ.get('ASTERISK_HOST', 'asterisk'),
    port=int(os.environ.get('ASTERISK_PORT', 8088)),
    username=os.environ.get('ASTERISK_ARI_USER', 'ai-calling'),
    password=os.environ.get('ASTERISK_ARI_PASSWORD', 'secret'),
    app='ai-calling'
)

def initiate_call(phone_number, campaign_id):
    """
    Initiates a call through the SIP Integration Service
    """
    try:
        response = requests.post(
            "http://localhost:5001/make-call",  # Adjust URL if needed
            json={
                "phone_number": phone_number,
                "campaign_id": campaign_id,
                "callback_url": "http://your-main-app-url/call-webhook"  # For notifications back to your main app
            }
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"Error initiating call: {response.text}")
            return None
    except Exception as e:
        logger.error(f"Exception initiating call: {e}")
        return None

@app.route('/telnyx-webhook', methods=['POST'])
def telnyx_webhook():
    """Handle incoming webhooks from Telnyx"""
    try:
        data = request.json
        logger.info(f"Received webhook from Telnyx: {data}")
        
        # Get the event type
        event_type = data.get('data', {}).get('event_type')
        
        # Process different event types
        if event_type == 'call.initiated':
            # Outbound call has been initiated
            call_control_id = data.get('data', {}).get('payload', {}).get('call_control_id')
            logger.info(f"Call initiated: {call_control_id}")
            
        elif event_type == 'call.answered':
            # Call has been answered
            call_control_id = data.get('data', {}).get('payload', {}).get('call_control_id')
            logger.info(f"Call answered: {call_control_id}")
            # Start your AI conversation flow
            
        elif event_type == 'call.hangup':
            # Call has ended
            call_control_id = data.get('data', {}).get('payload', {}).get('call_control_id')
            logger.info(f"Call ended: {call_control_id}")
            # Clean up resources
        
        # Return 200 OK to acknowledge receipt
        return jsonify({'status': 'ok'}), 200
    
    except Exception as e:
        logger.error(f"Error processing webhook: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

def create_app():
    def init_tts():
        try:
            from services.tts_service import get_tts_service
            tts_service = get_tts_service()
            # Download models if needed
            tts_service.download_voice_models()
            logger.info("TTS service initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing TTS service: {e}")

    # Start in a separate thread to avoid blocking app startup
    tts_thread = threading.Thread(target=init_tts)
    tts_thread.daemon = True
    tts_thread.start()
    
    # Schedule maintenance to remove old audio files
    def run_maintenance():
        from time import sleep
        while True:
            try:
                from services.tts_service import get_tts_service
                tts_service = get_tts_service()
                tts_service.clear_old_files(max_age_hours=6)
            except Exception as e:
                logger.error(f"Maintenance error: {e}")
            sleep(3600)  # Run hourly
    
    maintenance_thread = threading.Thread(target=run_maintenance)
    maintenance_thread.daemon = True
    maintenance_thread.start()

    """Initialize and configure the Flask application"""
    app = Flask(__name__)
    
    # Initialize services
    init_services(app)
    
    # Register blueprints
    app.register_blueprint(campaign_bp)
    app.register_blueprint(call_bp)
    app.register_blueprint(voice_bp)
    
    return app

if __name__ == '__main__':
    app = create_app()
    port = 5001  # Hardcoded to avoid conflicts
    print(f"Starting server on port {port}...")
    app.run(host='0.0.0.0', port=port, debug=True)