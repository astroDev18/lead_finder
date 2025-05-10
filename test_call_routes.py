import logging
from flask import Flask, Response
from twilio.twiml.voice_response import VoiceResponse
from services.tts_service import get_tts_service

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)

@app.route('/test-voice', methods=['GET', 'POST'])
def test_voice():
    """Test endpoint to check voice generation"""
    try:
        logger.info("Test voice endpoint called")
        
        # Initialize TTS service
        tts_service = get_tts_service()
        logger.info(f"TTS Service initialized with model type: {tts_service.model_type}")
        
        # Generate a simple greeting
        greeting = "Hello, this is a test of the text to speech system."
        filename = tts_service.generate_audio(greeting, speaker="p273")
        audio_path = tts_service.get_audio_path(filename)
        
        logger.info(f"Generated audio file: {audio_path}")
        
        # Create TwiML response
        response = VoiceResponse()
        
        # Get server base URL
        server_base_url = "http://your-server-url"  # Replace with your actual URL
        audio_url = f"{server_base_url}/audio/{filename}"
        
        # Play the generated audio
        response.say("This is a test call with generated speech.")
        
        # Add debugging info
        logger.info(f"Generated TwiML: {response}")
        
        return Response(str(response), mimetype='text/xml')
    
    except Exception as e:
        logger.error(f"Error in test voice endpoint: {e}", exc_info=True)
        response = VoiceResponse()
        response.say("An error occurred in the test endpoint. Please check the logs.")
        return Response(str(response), mimetype='text/xml')

# Run this file directly to test
if __name__ == "__main__":
    app.run(debug=True, port=5002)