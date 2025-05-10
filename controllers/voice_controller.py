from flask import Blueprint, request, Response
from twilio.twiml.voice_response import VoiceResponse, Gather
import logging
import os

from templates.script_templates import get_script
from services.dialogflow_service import detect_intent
from services.storage_service import get_call_state, save_call_state
from services.db_helper import get_db_service
from datetime import datetime
from utils.helpers import parse_speech_intent, log_call_event
from config.settings import VOICE_NAME, VOICE_RATE, VOICE_PITCH, SPEECH_TIMEOUT, GATHER_TIMEOUT
from services.tts_service import get_tts_service
from services.conversation_manager import ConversationManager
from flask import send_file

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

        # Add detailed step-by-step logging
        logger.info("STEP 1: Voice webhook starting")

        campaign_id = request.args.get('campaign_id')
        call_sid = request.form.get('CallSid')
        
        logger.info(f"STEP 2: Got campaign_id={campaign_id}, call_sid={call_sid}")

        # Get database service
        db_service, db = get_db_service()
        
        logger.info("STEP 3: Database service initialized")

        try:
            # Get the campaign script
            campaign = db_service.get_campaign_by_id(campaign_id)
            
            if not campaign:
                logger.error(f"Campaign not found: {campaign_id}")
                response = VoiceResponse()
                response.say("We encountered an issue with your call. Please contact support.")
                response.hangup()
                return Response(str(response), mimetype='text/xml')

            script = campaign.script_template
            
            # Initialize call state
            call_state = {
                'conversation_stage': 'greeting',
                'conversation_data': {},
                'phone_number': request.form.get('To'),
                'previous_stages': []
            }
            save_call_state(call_sid, call_state)
            
            # Create TwiML response
            response = VoiceResponse()
            
            # Configure Gather for speech recognition
            gather = Gather(
                input='speech dtmf',
                action=f'/process-response?campaign_id={campaign_id}',
                method='POST',
                timeout=int(os.environ.get('GATHER_TIMEOUT', 5)),
                speech_timeout=int(os.environ.get('SPEECH_TIMEOUT', 3)),
                speech_model='phone_call',
                hints='yes,no,interested,not interested',
                profanity_filter='false',
                enhanced='true'
            )
            
            # Get greeting from script
            if 'conversation_flow' in script:
                # New format: structured conversation flow
                greeting = script['conversation_flow'].get('greeting', {}).get('message', 
                          "Hello, this is an automated call. Would you be interested in our services?")
            else:
                # Legacy format: simple script
                greeting = script.get('greeting', "Hello, this is an automated call. Would you be interested in our services?")
            
            # Generate audio with local TTS
            tts_service = get_tts_service()
            greeting_filename = tts_service.generate_audio(greeting, speaker="p273")  # Use your preferred voice
            
            if greeting_filename:
                # Use the audio endpoint to serve the file
                server_base_url = os.environ.get('SERVER_BASE_URL', request.url_root.rstrip('/'))
                audio_url = f"{server_base_url}/audio/{greeting_filename}"
                gather.play(url=audio_url)
            else:
                # Fallback to Twilio's TTS if local TTS fails
                gather.say(greeting, voice='Polly.Matthew')
            
            response.append(gather)
            
            # Generate fallback audio
            fallback_message = "I didn't catch your response. Please call us back if you're interested."
            fallback_filename = tts_service.generate_audio(fallback_message, speaker="p273")
            
            if fallback_filename:
                audio_url = f"{server_base_url}/audio/{fallback_filename}"
                response.play(url=audio_url)
            else:
                response.say(fallback_message, voice='Polly.Matthew')
            
            logger.info(f"Sending TwiML greeting response for call {call_sid}")
            return Response(str(response), mimetype='text/xml')
        
        finally:
            if db:
                db.close()
    
    except Exception as e:
        logger.error(f"Error in voice webhook: {e}", exc_info=True)
        response = VoiceResponse()
        response.say("I apologize, but we're experiencing technical difficulties. Please try again later.")
        return Response(str(response), mimetype='text/xml')



@voice_bp.route('/process-response', methods=['POST'])
def process_response():
    """Process the caller's spoken response using the Conversation Manager"""
    try:
        logger.info(f"Process response called with form data: {request.form}")
        logger.info(f"Process response called with form data: {request.form}")
        logger.info(f"Process response query parameters: {request.args}")

        speech_result = request.form.get('SpeechResult', '')
        digits = request.form.get('Digits', '')
        call_sid = request.form.get('CallSid')
        campaign_id = request.args.get('campaign_id')
        
        # Use either speech or digits
        user_input = speech_result or digits
        
        logger.info(f"Received input from caller: '{user_input}'")
        
        # Get database service and TTS service
        db_service, db = get_db_service()
        tts_service = get_tts_service()
        
        try:
            # Get the campaign script
            campaign = db_service.get_campaign_by_id(campaign_id)
            if not campaign:
                logger.error(f"Campaign not found: {campaign_id}")
                response = VoiceResponse()
                response.say("We encountered an issue with your call.")
                response.hangup()
                return Response(str(response), mimetype='text/xml')
                
            script = campaign.script_template
            
            # Initialize the conversation manager
            conversation_manager = ConversationManager()
            
            # Process the response
            result = conversation_manager.process_response(call_sid, script, user_input)
            
            # Create TwiML response
            response = VoiceResponse()
            
            # If we have a response message, generate audio for it
            if result.get('message'):
                # Generate audio with TTS service
                message_filename = tts_service.generate_audio(result['message'], speaker="p273")  # Use preferred voice
                
                if message_filename:
                    # Get server URL
                    server_base_url = os.environ.get('SERVER_BASE_URL', request.url_root.rstrip('/'))
                    audio_url = f"{server_base_url}/audio/{message_filename}"
                    
                    if result.get('end_call'):
                        # If we're ending the call, just play the message
                        response.play(url=audio_url)
                        response.hangup()
                    else:
                        # Otherwise, gather the next response
                        gather = Gather(
                            input='speech dtmf',
                            action=f'/process-response?campaign_id={campaign_id}',
                            method='POST',
                            timeout=int(os.environ.get('GATHER_TIMEOUT', 5)),
                            speech_timeout=int(os.environ.get('SPEECH_TIMEOUT', 3)),
                            speech_model='phone_call',
                            hints='yes,no,interested,not interested',
                            profanity_filter='false',
                            enhanced='true'
                        )
                        gather.play(url=audio_url)
                        response.append(gather)
                        
                        # Add fallback for no response
                        fallback_message = "I didn't catch your response. If you're interested, please call us back."
                        fallback_filename = tts_service.generate_audio(fallback_message, speaker="p273")
                        if fallback_filename:
                            fallback_url = f"{server_base_url}/audio/{fallback_filename}"
                            response.play(url=fallback_url)
                        else:
                            response.say(fallback_message, voice='Polly.Matthew')
                else:
                    # Fallback to Twilio TTS if our TTS fails
                    response.say(result['message'], voice='Polly.Matthew')
                    if result.get('end_call'):
                        response.hangup()
            
            logger.info(f"Sending response for call {call_sid}, stage: {result.get('current_stage')}")
            return Response(str(response), mimetype='text/xml')
            
        finally:
            if db:
                db.close()
    
    except Exception as e:
        logger.error(f"Error processing response: {e}", exc_info=True)
        response = VoiceResponse()
        response.say("I apologize, but we're experiencing technical difficulties. Please try again later.")
        response.hangup()
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