from flask import Blueprint, request, Response
from twilio.twiml.voice_response import VoiceResponse, Gather
import logging
import os

from templates.script_templates import get_script
from services.dialogflow_service import detect_intent
from services.storage_service import get_call_state, save_call_state
from utils.helpers import parse_speech_intent, log_call_event
from config.settings import VOICE_NAME, VOICE_RATE, VOICE_PITCH, SPEECH_TIMEOUT, GATHER_TIMEOUT

# Set up logging
logger = logging.getLogger(__name__)

# Create a Blueprint for voice-related routes
voice_bp = Blueprint('voice', __name__)

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

@voice_bp.route('/voice-webhook', methods=['POST'])
def voice_webhook():
    """Voice webhook that Twilio calls when the call is answered"""
    try:
        logger.info(f"Voice webhook called with args: {request.args}")
        logger.info(f"Voice webhook form data: {request.form}")
        
        campaign_id = request.args.get('campaign_id')
        call_sid = request.form.get('CallSid')
        
        # Get the campaign script
        script = get_script(campaign_id)
        
        # Initialize or retrieve call state
        call_state = get_call_state(call_sid)
        if not call_state:
            call_state = {
                'campaign_id': campaign_id,
                'stage': 'greeting',
                'responses': []
            }
            save_call_state(call_sid, call_state)
        
        response = VoiceResponse()
        
        # Configure Gather for speech recognition with natural voice
        gather = Gather(
            input='speech dtmf',
            action='/process-response',
            method='POST',
            timeout=GATHER_TIMEOUT,
            speech_timeout=SPEECH_TIMEOUT,
            speech_model='phone_call',
            hints='yes,no,interested,not interested',
            profanity_filter='false',
            enhanced='true'
        )
        
        # Use the natural voice with pauses
        gather.say(script['greeting'], 
                   voice=VOICE_NAME, 
                   rate=VOICE_RATE, 
                   pitch=VOICE_PITCH)
        response.append(gather)
        
        # Fallback message if no response received
        response.say("I didn't catch your response. If you're interested in our services, please call us back.", 
                     voice=VOICE_NAME, 
                     rate=VOICE_RATE, 
                     pitch=VOICE_PITCH)
        
        logger.info(f"Sending TwiML greeting response: {response}")
        return Response(str(response), mimetype='text/xml')
    
    except Exception as e:
        logger.error(f"Error in voice webhook: {e}")
        # Return a simple response to avoid breaking the call
        response = VoiceResponse()
        response.say("I apologize, but we're experiencing technical difficulties. Please try again later.", 
                     voice=VOICE_NAME, 
                     rate=VOICE_RATE)
        return Response(str(response), mimetype='text/xml')

@voice_bp.route('/process-response', methods=['POST'])
def process_response():
    """Process the customer's spoken response using Dialogflow"""
    try:
        logger.info(f"Process response called with form data: {request.form}")
        
        speech_result = request.form.get('SpeechResult', '')
        call_sid = request.form.get('CallSid')
        
        logger.info(f"Received speech: {speech_result}")
        
        # Get call state
        call_state = get_call_state(call_sid)
        if not call_state:
            logger.error(f"Call state not found for {call_sid}")
            call_state = {
                'campaign_id': 'campaign_001',
                'stage': 'greeting',
                'responses': []
            }
        
        campaign_id = call_state['campaign_id']
        script = get_script(campaign_id)
        
        # Record response
        if speech_result:
            call_state['responses'].append(speech_result)
            logger.info(f"Caller said: {speech_result}")
            # Log the speech event
            log_call_event(call_sid, 'speech_received', {'speech': speech_result})
        
        response = VoiceResponse()
        
        # Process with Dialogflow if speech detected
        if speech_result:
            try:
                # Get AI response from Dialogflow
                dialogflow_response = detect_intent(speech_result, call_sid)
                intent = dialogflow_response['intent']
                logger.info(f"Detected intent: {intent}, Confidence: {dialogflow_response['intent_confidence']}")
            except Exception as df_error:
                logger.error(f"Dialogflow error: {df_error}, using fallback intent detection")
                # Fallback to basic intent detection
                intent = "RealEstateInterest" if parse_speech_intent(speech_result) == 'positive' else "RealEstateDecline"
            
            # Map Dialogflow intents to responses
            if intent == "RealEstateInterest" or any(word in speech_result.lower() for word in ['yes', 'have', 'interested', 'sure']):
                # Positive response - proceed with more info
                call_state['stage'] = 'more_info'
                response.say(script['more_info'], 
                             voice=VOICE_NAME, 
                             rate=VOICE_RATE)
                
                # Set up another gather for the follow-up
                gather = Gather(
                    input='speech',
                    action='/process-followup',
                    method='POST',
                    timeout=GATHER_TIMEOUT,
                    speech_timeout=SPEECH_TIMEOUT,
                    speech_model='phone_call',
                    hints='yes,no,interested,not interested'
                )
                response.append(gather)
            elif intent == "RealEstateDecline" or any(word in speech_result.lower() for word in ['no', 'not', 'don\'t']):
                # Negative response - end call
                response.say(script['negative_response'], 
                             voice=VOICE_NAME, 
                             rate=VOICE_RATE)
                response.hangup()
                call_state['stage'] = 'ended'
            else:
                # Unclear intent - ask for clarification
                response.say(script['unclear_response'], 
                             voice=VOICE_NAME, 
                             rate=VOICE_RATE)
                
                gather = Gather(
                    input='speech',
                    action='/process-response',
                    method='POST',
                    timeout=GATHER_TIMEOUT,
                    speech_timeout=SPEECH_TIMEOUT,
                    speech_model='phone_call',
                    hints='yes,no'
                )
                response.append(gather)
        else:
            # No speech detected
            response.say(script['no_speech'], 
                         voice=VOICE_NAME, 
                         rate=VOICE_RATE)
            
            gather = Gather(
                input='speech',
                action='/process-response',
                method='POST',
                timeout=GATHER_TIMEOUT,
                speech_timeout=SPEECH_TIMEOUT,
                speech_model='phone_call',
                hints='yes,no'
            )
            response.append(gather)
        
        # Save updated state
        save_call_state(call_sid, call_state)
        
        return Response(str(response), mimetype='text/xml')
    
    except Exception as e:
        logger.error(f"Error processing response: {e}")
        # Return a simple response to avoid breaking the call
        response = VoiceResponse()
        response.say("I apologize, but we're experiencing technical difficulties. Please try again later.", 
                     voice=VOICE_NAME, 
                     rate=VOICE_RATE)
        return Response(str(response), mimetype='text/xml')

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
        # Process with Dialogflow if speech detected
        elif speech_result:
            try:
                # Get AI response from Dialogflow
                dialogflow_response = detect_intent(speech_result, call_sid)
                intent = dialogflow_response['intent']
                logger.info(f"Detected intent (followup): {intent}, Confidence: {dialogflow_response['intent_confidence']}")
            except Exception as df_error:
                logger.error(f"Dialogflow error: {df_error}, using fallback intent detection")
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