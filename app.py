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

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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