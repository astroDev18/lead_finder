# Modified voice_controller.py with Dialogflow dependencies removed
from flask import Blueprint, request, Response, jsonify, send_file
import logging
import os
import re
import random

# Remove Dialogflow imports
# from services.dialogflow_service import detect_intent

from services.storage_service import get_call_state, save_call_state
from services.db_helper import get_db_service
from datetime import datetime
from utils.helpers import parse_speech_intent, log_call_event
from config.settings import VOICE_NAME, VOICE_RATE, VOICE_PITCH, SPEECH_TIMEOUT, GATHER_TIMEOUT
from services.tts_service import get_tts_service
from services.conversation_manager import ConversationManager

# Set up logging
logger = logging.getLogger(__name__)

# Create a Blueprint for voice-related routes
voice_bp = Blueprint('voice', __name__)

# Simple helper function to replace detect_intent
def simple_intent_detection(speech_result, call_sid=None):
    """Simple function to replace Dialogflow's detect_intent"""
    if not speech_result:
        return {
            "query_text": "",
            "intent": "fallback",
            "intent_confidence": 0,
            "fulfillment_text": "I didn't hear anything. Can you please repeat?",
            "parameters": {}
        }
    
    speech_lower = speech_result.lower()
    
    # Simple keyword detection
    if any(word in speech_lower for word in ['yes', 'yeah', 'sure', 'okay', 'interested', 'tell me']):
        intent = "RealEstateInterest"
        confidence = 0.8
    elif any(word in speech_lower for word in ['no', 'not', 'don\'t', 'isn\'t', 'not interested']):
        intent = "RealEstateDecline"
        confidence = 0.8
    else:
        intent = "fallback"
        confidence = 0.5
    
    return {
        "query_text": speech_result,
        "intent": intent,
        "intent_confidence": confidence,
        "fulfillment_text": "Thank you for your response.",
        "parameters": {}
    }

@voice_bp.route('/test-speech', methods=['POST'])
def test_speech():
    """Simple endpoint to test speech recognition"""
    logger.info(f"Test speech endpoint called with form data: {request.form}")
    
    response = VoiceResponse()
    response.say("This is a speech recognition test. Please say something after the beep.", 
                 voice=VOICE_NAME, 
                 rate=VOICE_RATE)
    response.pause(length=1)
    response.play('https://cdn.freesound.org/previews/411/411642_5121236-lq.mp3')
    
    gather = Gather(
        input='speech',  # Speech only
        action='/speech-result',
        method='POST',
        timeout=10,
        speech_timeout=5,
        speech_model='phone_call',
        enhanced=True
    )
    
    response.append(gather)
    
    response.say("We didn't detect any speech. The test is now complete.", 
                 voice=VOICE_NAME, 
                 rate=VOICE_RATE)
    
    return Response(str(response), mimetype='text/xml')

@voice_bp.route('/speech-result', methods=['POST'])
def speech_result():
    """Endpoint to report speech recognition results"""
    speech_result = request.form.get('SpeechResult', '')
    
    logger.info(f"TEST - Received speech: {speech_result}")
    
    response = VoiceResponse()
    
    if speech_result:
        response.say(f"We detected your speech. You said: {speech_result}", 
                     voice=VOICE_NAME, 
                     rate=VOICE_RATE)
    else:
        response.say("We didn't detect any speech result even though the gather completed.", 
                     voice=VOICE_NAME, 
                     rate=VOICE_RATE)
    
    return Response(str(response), mimetype='text/xml')

# Additional routes follow similar pattern - replace any dialogflow references with simple_intent_detection

@voice_bp.route('/process-followup', methods=['POST'])
def process_followup():
    """Handle follow-up response"""
    try:
        logger.info(f"Process followup called with form data: {request.form}")
        
        speech_result = request.form.get('SpeechResult', '')
        digits = request.form.get('Digits', '')
        call_sid = request.form.get('CallSid')
        
        logger.info(f"Received speech: {speech_result}")
        logger.info(f"Received digits: {digits}")
        
        # Get call state
        call_state = get_call_state(call_sid)
        if not call_state:
            logger.error(f"Call state not found for {call_sid}")
            call_state = {
                'campaign_id': 'campaign_001',
                'stage': 'more_info',
                'responses': []
            }
        
        campaign_id = call_state['campaign_id']
        script = get_script(campaign_id)
        
        # Record response
        if speech_result:
            call_state['responses'].append(speech_result)
            logger.info(f"Caller said (followup): {speech_result}")
            # Log the speech event
            log_call_event(call_sid, 'followup_speech', {'speech': speech_result})
        
        response = VoiceResponse()
        
        # Simple logic for DTMF input
        if digits == '1':
            # Treat as a positive response
            response.say(script['closing'], 
                         voice=VOICE_NAME, 
                         rate=VOICE_RATE)
            response.hangup()
            call_state['stage'] = 'ended'
        elif digits == '2':
            # Treat as a negative response
            response.say(script['negative_response'], 
                         voice=VOICE_NAME, 
                         rate=VOICE_RATE)
            response.hangup()
            call_state['stage'] = 'ended'
        # Process with simple intent detection instead of Dialogflow
        elif speech_result:
            try:
                # Get response using our simplified intent detection
                intent_result = simple_intent_detection(speech_result, call_sid)
                intent = intent_result['intent']
                logger.info(f"Detected intent (followup): {intent}, Confidence: {intent_result['intent_confidence']}")
            except Exception as error:
                logger.error(f"Error in intent detection: {error}, using fallback")
                # Fallback to basic intent detection
                intent = "RealEstateFollowUp" if parse_speech_intent(speech_result) == 'positive' else "RealEstateDecline"
            
            if intent == "RealEstateFollowUp" or intent == "RealEstateInterest" or any(word in speech_result.lower() for word in ['yes', 'would', 'like', 'sure', 'send']):
                response.say(script['closing'], 
                             voice=VOICE_NAME, 
                             rate=VOICE_RATE)
                response.hangup()
                call_state['stage'] = 'ended'
            else:
                response.say(script['negative_response'], 
                             voice=VOICE_NAME, 
                             rate=VOICE_RATE)
                response.hangup()
                call_state['stage'] = 'ended'
        else:
            # No input detected
            response.say(script['fallback'], 
                         voice=VOICE_NAME, 
                         rate=VOICE_RATE)
            response.hangup()
            call_state['stage'] = 'ended'
        
        # Save updated state
        save_call_state(call_sid, call_state)
        
        return Response(str(response), mimetype='text/xml')
    
    except Exception as e:
        logger.error(f"Error processing followup: {e}")
        # Return a simple response to avoid breaking the call
        response = VoiceResponse()
        response.say("I apologize, but we're experiencing technical difficulties. Please try again later.", 
                     voice=VOICE_NAME, 
                     rate=VOICE_RATE)
        return Response(str(response), mimetype='text/xml')

@voice_bp.route('/audio/<filename>', methods=['GET'])
def serve_audio(filename):
    """Serve generated audio files"""
    try:
        tts_service = get_tts_service()
        file_path = tts_service.get_audio_path(filename)
        
        if os.path.exists(file_path):
            return send_file(file_path, mimetype='audio/wav')
        else:
            logger.error(f"Audio file not found: {filename}")
            return "File not found", 404
    except Exception as e:
        logger.error(f"Error serving audio file {filename}: {e}")
        return "Error serving file", 500

# Add other routes from voice_controller.py but make sure to replace any dialogflow.detect_intent calls
# with the simple_intent_detection function