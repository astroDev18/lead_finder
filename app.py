from flask import Flask, request, jsonify
from dotenv import load_dotenv
import logging
import threading
import os
import requests
import json

# Import controllers
from controllers.campaign_controller import campaign_bp
from controllers.call_controller import call_bp
from controllers.voice_controller import voice_bp
from flask import Flask, request, jsonify, send_file
# Import services initialization
from services import init_services

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
PUBLIC_BASE_URL = os.environ.get('PUBLIC_BASE_URL', 'http://localhost:5001')
logger.info(f"Using PUBLIC_BASE_URL: {PUBLIC_BASE_URL}")

# Dictionary to store active calls and their associated campaign IDs
active_calls = {}

def initiate_call(phone_number, campaign_id):
    """
    Initiates a call through the SIP Integration Service
    """
    try:
        # URL for the SIP integration service
        sip_service_url = os.environ.get('SIP_SERVICE_URL', 'http://localhost:5002')
        
        # Construct the callback URL that SIP service should use to notify this service
        callback_url = os.environ.get('CALLBACK_URL', 'http://localhost:5001/call-webhook')
        
        # Make the call through the SIP integration service
        response = requests.post(
            f"{sip_service_url}/make-call",
            json={
                "phone_number": phone_number,
                "campaign_id": campaign_id,
                "callback_url": callback_url
            }
        )
        
        if response.status_code == 200:
            response_data = response.json()
            call_control_id = response_data.get('call_control_id')
            
            # Store the call information for later reference
            if call_control_id:
                active_calls[call_control_id] = {
                    'phone_number': phone_number,
                    'campaign_id': campaign_id,
                    'status': 'initiated'
                }
                
            return response_data
        else:
            logger.error(f"Error initiating call: {response.text}")
            return None
    except Exception as e:
        logger.error(f"Exception initiating call: {e}")
        return None

def create_app():
    """Initialize and configure the Flask application"""
    app = Flask(__name__)
    
    # Initialize services
    init_services(app)
    
    @app.route('/api/get-greeting', methods=['POST'])
    def get_greeting():
        """
        API endpoint for SIP service to get initial greeting for a call
        """
        try:
            data = request.json
            call_control_id = data.get('call_control_id')
            campaign_id = data.get('campaign_id')
            
            if not call_control_id or not campaign_id:
                return jsonify({
                    'success': False,
                    'error': 'call_control_id and campaign_id are required'
                }), 400
                    
            logger.info(f"Getting greeting for call {call_control_id}, campaign {campaign_id}")
            
            # Get the campaign script
            try:
                # Import here to avoid circular imports
                from services.campaign_service import get_campaign_manager
                campaign_manager = get_campaign_manager()
                campaign = campaign_manager.get_campaign_by_id(campaign_id)
                
                if not campaign:
                    return jsonify({
                        'success': False,
                        'error': f"Campaign {campaign_id} not found"
                    }), 404
                    
                # Get the script - Fix: access the attribute directly, not using .get()
                script = campaign.script_template if campaign else None
                
                if not script:
                    # Fall back to template
                    from templates.script_templates import get_script
                    script = get_script(campaign_id)
                    
                # Get the greeting message
                if 'conversation_flow' in script:
                    # New format
                    greeting_stage = script.get('conversation_flow', {}).get('greeting', {})
                    greeting_message = greeting_stage.get('message', "Hello, thanks for taking our call.")
                else:
                    # Legacy format
                    greeting_message = script.get('greeting', "Hello, thanks for taking our call.")
                    
                # Generate audio for the greeting
                from services.tts_service import get_tts_service
                tts_service = get_tts_service()
                
                # Changed generate_speech to generate_audio
                audio_file = tts_service.generate_audio(
                    text=greeting_message,
                    speaker="p273"  # Changed voice_id to speaker
                )
                
                # Get public URL for the audio file
                audio_url = f"{PUBLIC_BASE_URL}/audio/{os.path.basename(audio_file)}"

                
                # Store the call in active calls if not already there
                if call_control_id not in active_calls:
                    active_calls[call_control_id] = {
                        'campaign_id': campaign_id,
                        'status': 'greeting',
                        'conversation_stage': 'greeting'
                    }
                else:
                    active_calls[call_control_id].update({
                        'campaign_id': campaign_id,
                        'status': 'greeting',
                        'conversation_stage': 'greeting'
                    })
                
                # Return the greeting
                return jsonify({
                    'success': True,
                    'message': greeting_message,
                    'audio_url': audio_url,
                    'current_stage': 'greeting'
                }), 200
                
            except Exception as e:
                logger.error(f"Error getting greeting: {e}", exc_info=True)
                return jsonify({
                    'success': False,
                    'error': str(e),
                    'message': "Hello, thanks for taking our call."  # Fallback message
                }), 200
                
        except Exception as e:
            logger.error(f"Error in get_greeting: {e}", exc_info=True)
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @app.route('/call-webhook', methods=['POST'])
    def call_webhook():
        """
        Handle incoming webhooks from SIP service
        """
        try:
            data = request.json
            logger.info(f"Received webhook from SIP service: {data}")
            
            event_type = data.get('event_type')
            call_control_id = data.get('call_control_id')
            campaign_id = data.get('campaign_id')
            
            if not call_control_id:
                return jsonify({'error': 'call_control_id is required'}), 400
                
            # Update our tracking of the call
            if call_control_id not in active_calls:
                active_calls[call_control_id] = {
                    'campaign_id': campaign_id,
                    'status': event_type
                }
            else:
                active_calls[call_control_id]['status'] = event_type
            
            # Process different event types
            if event_type == 'call.answered':
                # Call has been answered, but we don't need to do anything here
                # as the SIP service will request the greeting via /api/get-greeting
                pass
                
            elif event_type == 'user_input':
                # Process user input through the conversation manager
                user_input = data.get('input', '')
                
                if not user_input:
                    return jsonify({
                        'success': False,
                        'error': 'No user input provided',
                        'message': "I'm sorry, I didn't catch that. Could you please repeat?"
                    }), 200
                
                # Process the input through the conversation manager
                try:
                    # Import here to avoid circular imports
                    from services.conversation_manager import get_conversation_manager
                    conversation_manager = get_conversation_manager()
                    
                    # Process the response
                    result = conversation_manager.process_response(
                        call_sid=call_control_id,  # We use call_control_id as call_sid
                        script_or_campaign_id=campaign_id,
                        user_input=user_input
                    )
                    
                    # Get the response message
                    message = result.get('message', "I'm sorry, I didn't catch that.")
                    end_call = result.get('end_call', False)
                    current_stage = result.get('current_stage', 'unknown')
                    
                    # Update call state in our active calls
                    active_calls[call_control_id]['conversation_stage'] = current_stage
                    
                    # Generate audio for the response
                    from services.tts_service import get_tts_service
                    tts_service = get_tts_service()
                    
                    # Changed generate_speech to generate_audio
                    audio_file = tts_service.generate_audio(
                        text=message,
                        speaker="p273"  # Changed voice_id to speaker
                    )
                    
                    # Get public URL for the audio file
                    audio_url = f"http://localhost:5001/audio/{os.path.basename(audio_file)}"
                    
                    # Return the response
                    return jsonify({
                        'success': True,
                        'message': message,
                        'audio_url': audio_url,
                        'end_call': end_call,
                        'current_stage': current_stage
                    }), 200
                    
                except Exception as e:
                    logger.error(f"Error processing user input: {e}", exc_info=True)
                    return jsonify({
                        'success': False,
                        'error': str(e),
                        'message': "I'm sorry, we're experiencing technical difficulties."
                    }), 200
                
            elif event_type == 'call.hangup':
                # Call has ended
                duration = data.get('duration', 0)
                
                # Clean up resources
                if call_control_id in active_calls:
                    # Mark as ended
                    active_calls[call_control_id]['status'] = 'ended'
                    active_calls[call_control_id]['duration'] = duration
                    
                    # Schedule removal after a delay
                    def cleanup_call():
                        import time
                        time.sleep(30)  # Wait 30 seconds before cleanup
                        if call_control_id in active_calls:
                            del active_calls[call_control_id]
                    
                    cleanup_thread = threading.Thread(target=cleanup_call)
                    cleanup_thread.daemon = True
                    cleanup_thread.start()
            
            # Return 200 OK to acknowledge receipt
            return jsonify({'status': 'ok'}), 200
            
        except Exception as e:
            logger.error(f"Error processing call webhook: {e}", exc_info=True)
            return jsonify({'error': str(e)}), 500
    
    @app.route('/audio/<filename>')
    def serve_audio(filename):
        """
        Serve audio files generated by TTS
        """
        try:
            from services.tts_service import get_tts_service
            tts_service = get_tts_service()
            
            audio_path = os.path.join(tts_service.cache_dir, filename)
            
            if os.path.exists(audio_path):
                return send_file(audio_path, mimetype='audio/wav')
            else:
                logger.error(f"Audio file not found: {filename}")
                return "File not found", 404
        except Exception as e:
            logger.error(f"Error serving audio file: {e}")
            return "Error serving file", 500
    
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