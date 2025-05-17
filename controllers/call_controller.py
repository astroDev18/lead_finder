# Update your controllers/call_controller.py with these new endpoints

from flask import Blueprint, request, jsonify
import logging
import os
from services.call_bridge_service import get_call_bridge_service
from services.tts_service import get_tts_service
from services.conversation_manager import ConversationManager
from services.storage_service import get_call_state
from templates.script_templates import get_script
from config.settings import SERVER_BASE_URL

# Set up logging
logger = logging.getLogger(__name__)

# Create or use existing call blueprint
call_bp = Blueprint('call', __name__)

# SIP Integration service URL
SIP_SERVICE_URL = os.environ.get('SIP_SERVICE_URL', 'http://localhost:5001')

@call_bp.route('/make-sip-call', methods=['POST'])
def make_sip_call():
    """Endpoint to initiate a call through the SIP Integration service"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
            
        logger.info(f"Make SIP call endpoint called with data: {data}")
        
        phone_number = data.get('phone_number')
        campaign_id = data.get('campaign_id')
        
        if not phone_number or not campaign_id:
            return jsonify({'error': 'Phone number and campaign ID required'}), 400
        
        # Initialize call bridge service
        call_bridge_service = get_call_bridge_service()
        
        # Generate callback URL
        server_base_url = SERVER_BASE_URL
        callback_url = f"{server_base_url}/call-webhook"
        
        # Initiate call through bridge service
        call_info = call_bridge_service.initiate_call(
            phone_number=phone_number,
            campaign_id=campaign_id,
            callback_url=callback_url
        )
        
        if not call_info:
            return jsonify({'error': 'Failed to initiate call through SIP Integration'}), 500
        
        return jsonify({
            'success': True, 
            'call_id': call_info.get('call_control_id'),
            'message': f"Call to {phone_number} initiated successfully"
        }), 200
    
    except Exception as e:
        logger.error(f"Error initiating SIP call: {e}")
        return jsonify({'error': f'Failed to initiate call: {str(e)}'}), 500

@call_bp.route('/call-webhook', methods=['POST'])
def call_webhook():
    """Webhook endpoint for SIP Integration service to send call events"""
    try:
        data = request.get_json()
        logger.info(f"Received webhook from SIP Integration: {data}")
        
        # Extract event information
        event_type = data.get('event_type')
        call_control_id = data.get('call_control_id')
        campaign_id = data.get('campaign_id')
        
        if not event_type or not call_control_id:
            return jsonify({'error': 'Missing required webhook data'}), 400
        
        # Get call bridge service
        call_bridge_service = get_call_bridge_service()
        
        # Process based on event type
        if event_type == 'call.answered':
            # Call was answered, we'll let the webhook handler in SIP integration handle greeting
            return jsonify({
                'success': True,
                'message': 'Call answered event received'
            }), 200
            
        elif event_type == 'user_input':
            # User provided input, process with conversation manager
            user_input = data.get('input')
            
            if not user_input:
                return jsonify({'error': 'No user input provided'}), 400
                
            # Process the user input
            conversation_manager = ConversationManager()
            
            # Get campaign script
            script = get_script(campaign_id)
            
            # Process the response
            result = conversation_manager.process_response(call_control_id, script, user_input)
            
            # Generate audio for response
            tts_service = get_tts_service()
            audio_url = None
            if tts_service and result.get('message'):
                response_filename = tts_service.generate_audio(result['message'], speaker="p273")
                if response_filename:
                    # We need a full URL that the SIP service can access
                    server_base_url = SERVER_BASE_URL
                    audio_url = f"{server_base_url}/audio/{response_filename}"
            
            # Return response for SIP service to speak
            return jsonify({
                'success': True,
                'message': result.get('message'),
                'audio_url': audio_url,
                'current_stage': result.get('current_stage'),
                'end_call': result.get('end_call', False)
            }), 200
            
        elif event_type == 'call.hangup':
            # Call ended, update our records
            duration = data.get('duration', 0)
            logger.info(f"Call {call_control_id} ended, duration: {duration}s")
            
            # You can add code here to update your database or analytics
            
            return jsonify({
                'success': True,
                'message': 'Call hangup event received'
            }), 200
        
        else:
            # Unknown event type
            logger.warning(f"Unknown event type received: {event_type}")
            return jsonify({
                'success': True,
                'message': f'Unhandled event type: {event_type}'
            }), 200
            
    except Exception as e:
        logger.error(f"Error handling webhook: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@call_bp.route('/api/get-greeting', methods=['POST'])
def get_greeting():
    """API endpoint for SIP Integration to get a greeting for a call"""
    try:
        data = request.get_json()
        
        call_control_id = data.get('call_control_id')
        campaign_id = data.get('campaign_id')
        
        if not call_control_id or not campaign_id:
            return jsonify({'error': 'Missing required data'}), 400
        
        # Get campaign script
        script = get_script(campaign_id)
        
        # Get greeting from script
        greeting = None
        if 'conversation_flow' in script:
            # New format: structured conversation flow
            greeting = script['conversation_flow'].get('greeting', {}).get('message', 
                      "Hello, this is an automated call. Would you be interested in our services?")
        else:
            # Legacy format: simple script
            greeting = script.get('greeting', "Hello, this is an automated call. Would you be interested in our services?")
        
        # Generate audio with TTS
        tts_service = get_tts_service()
        audio_url = None
        if tts_service:
            greeting_filename = tts_service.generate_audio(greeting, speaker="p273")
            if greeting_filename:
                server_base_url = SERVER_BASE_URL
                audio_url = f"{server_base_url}/audio/{greeting_filename}"
        
        # Return greeting with audio URL
        return jsonify({
            'success': True,
            'message': greeting,
            'audio_url': audio_url
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting greeting: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500