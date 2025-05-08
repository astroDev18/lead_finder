from flask import Flask
from dotenv import load_dotenv
import logging


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
    app.run(host='0.0.0.0', port=port, debug=True)