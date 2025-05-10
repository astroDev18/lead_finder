from flask import Blueprint, request, jsonify
import logging
import os

from services.twilio_service import get_twilio_client
from templates.script_templates import get_script
from utils.helpers import sanitize_phone_number, log_call_event
from services.storage_service import save_call_state, get_call_state

# Set up logging
logger = logging.getLogger(__name__)

# Create a Blueprint for call-related routes
call_bp = Blueprint('call', __name__)

# Call state memory storage (to be replaced with a database in production)
call_states = {}

@call_bp.route('/make-call', methods=['POST'])
def make_call():
    """Endpoint to initiate calls"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
            
        logger.info(f"Make call endpoint called with data: {data}")
        
        phone_number = data.get('phone_number')
        campaign_id = data.get('campaign_id')
        
        if not phone_number or not campaign_id:
            return jsonify({'error': 'Phone number and campaign ID required'}), 400
        
        # Sanitize phone number
        formatted_number = sanitize_phone_number(phone_number)
        if not formatted_number:
            return jsonify({'error': 'Invalid phone number format'}), 400
        
        # Check if campaign script exists
        script = get_script(campaign_id)
        if not script:
            return jsonify({'error': 'Campaign not found'}), 404
        
        # Get Twilio client
        client = get_twilio_client()
        
        # Base URL for the voice webhooks
        server_base_url = os.environ.get('SERVER_BASE_URL')
        if not server_base_url:
            return jsonify({'error': 'SERVER_BASE_URL environment variable not set'}), 500
        
        # Initiate call via Twilio
        call = client.calls.create(
            url=f"{server_base_url}/voice-webhook?campaign_id={campaign_id}",
            to=formatted_number,
            from_=os.environ.get('TWILIO_PHONE_NUMBER'),
            status_callback=f"{server_base_url}/call-status",
            status_callback_event=['initiated', 'ringing', 'answered', 'completed'],
            status_callback_method='POST'
        )
        
        # Initialize call state
        call_state = {
            'campaign_id': campaign_id,
            'stage': 'greeting',
            'responses': [],
            'phone_number': formatted_number
        }
        
        # Save call state
        save_call_state(call.sid, call_state)
        
        # Log call initiation
        log_call_event(call.sid, 'initiated', {
            'campaign_id': campaign_id,
            'phone_number': formatted_number
        })
        
        return jsonify({
            'success': True, 
            'call_sid': call.sid,
            'message': f"Call to {formatted_number} initiated successfully"
        }), 200
    
    except Exception as e:
        logger.error(f"Error initiating call: {e}")
        return jsonify({'error': f'Failed to initiate call: {str(e)}'}), 500

@call_bp.route('/call-status', methods=['POST'])
def call_status():
    """Track call status and save call data"""
    try:
        call_status = request.form.get('CallStatus')
        call_sid = request.form.get('CallSid')
        call_duration = request.form.get('CallDuration')
        
        logger.info(f"Call {call_sid} status update: {call_status}, duration: {call_duration}s")
        
        # Log the call status event
        log_data = {
            'status': call_status,
            'duration': call_duration
        }
        log_call_event(call_sid, 'status_update', log_data)
        
        # If call is completed or failed, store the call data and clean up
        if call_status in ['completed', 'failed', 'busy', 'no-answer']:
            # Get current call state
            state = get_call_state(call_sid)
            
            if state:
                # In production, save to database
                # call_data = {
                #     'call_sid': call_sid,
                #     'status': call_status,
                #     'duration': call_duration,
                #     'campaign_id': state.get('campaign_id'),
                #     'responses': state.get('responses', []),
                #     'final_stage': state.get('stage')
                # }
                # database.save_call_data(call_data)
                
                # Remove from memory storage
                delete_call_state(call_sid)
        
        return '', 200
    
    except Exception as e:
        logger.error(f"Error processing call status: {e}")
        return jsonify({'error': str(e)}), 500