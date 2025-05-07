# app.py
from flask import Flask, request, Response
from twilio.twiml.voice_response import VoiceResponse, Gather
from twilio.rest import Client
import os
from dotenv import load_dotenv
import json
import logging
from google.cloud import dialogflow
import uuid

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)

# Initialize Twilio client
client = Client(
    os.environ.get('TWILIO_ACCOUNT_SID'),
    os.environ.get('TWILIO_AUTH_TOKEN')
)

# Initialize Dialogflow client
project_id = os.environ.get('DIALOGFLOW_PROJECT_ID')
session_client = dialogflow.SessionsClient()

# Campaign scripts database (replace with actual database in production)
campaign_scripts = {
    'campaign_001': {
        'greeting': "Hi there! This is Sarah from TechBoost Solutions. We've got an exciting new offer for small businesses like yours. Would you like to hear more?",
        'more_info': "Great! Our new software helps businesses increase online visibility by 40% on average. It's designed specifically for your industry and comes with a 14-day free trial. Would you like me to send you more information?",
        'closing': "Perfect! I'll send the details to your email. You'll also receive a text with a special discount code. Thank you for your time and have a great day!"
    }
}

# Conversation state tracker
call_states = {}

def detect_intent(text, session_id, language_code="en-US"):
    """
    Detect the intent of a text using Dialogflow
    
    Args:
        text: Text input from the caller
        session_id: Unique session ID
        language_code: Language code (defaults to en-US)
    
    Returns:
        The response from Dialogflow including fulfillment text
    """
    try:
        session = session_client.session_path(project_id, session_id)
        
        text_input = dialogflow.TextInput(text=text, language_code=language_code)
        query_input = dialogflow.QueryInput(text=text_input)
        
        response = session_client.detect_intent(
            request={"session": session, "query_input": query_input}
        )
        
        return {
            "query_text": response.query_result.query_text,
            "intent": response.query_result.intent.display_name,
            "intent_confidence": response.query_result.intent_detection_confidence,
            "fulfillment_text": response.query_result.fulfillment_text,
            "parameters": dict(response.query_result.parameters)
        }
    except Exception as e:
        logger.error(f"Error with Dialogflow: {e}")
        return {
            "query_text": text,
            "intent": "fallback",
            "intent_confidence": 0,
            "fulfillment_text": "I'm sorry, I didn't quite understand that. Would you like to hear more about our offer?",
            "parameters": {}
        }

@app.route('/make-call', methods=['POST'])
def make_call():
    """Endpoint to initiate calls"""
    try:
        data = request.get_json()
        phone_number = data.get('phone_number')
        campaign_id = data.get('campaign_id')
        
        if not phone_number or not campaign_id:
            return {'error': 'Phone number and campaign ID required'}, 400
        
        # Check if campaign exists
        if campaign_id not in campaign_scripts:
            return {'error': 'Campaign not found'}, 404
        
        # Initiate call via Twilio
        call = client.calls.create(
            url=f"{os.environ.get('SERVER_BASE_URL')}/voice-webhook?campaign_id={campaign_id}",
            to=phone_number,
            from_=os.environ.get('TWILIO_PHONE_NUMBER'),
            status_callback=f"{os.environ.get('SERVER_BASE_URL')}/call-status",
            status_callback_event=['initiated', 'ringing', 'answered', 'completed'],
            status_callback_method='POST'
        )
        
        # Initialize call state
        call_states[call.sid] = {
            'campaign_id': campaign_id,
            'stage': 'greeting',
            'responses': []
        }
        
        return {'success': True, 'call_sid': call.sid}, 200
    
    except Exception as e:
        logger.error(f"Error initiating call: {e}")
        return {'error': f'Failed to initiate call: {str(e)}'}, 500

@app.route('/voice-webhook', methods=['POST'])
def voice_webhook():
    """Voice webhook that Twilio calls when the call is answered"""
    campaign_id = request.args.get('campaign_id')
    # Default to campaign_001 if campaign not found
    script = campaign_scripts.get(campaign_id, campaign_scripts['campaign_001'])
    call_sid = request.form.get('CallSid')
    
    # Initialize call state if not exists
    if call_sid not in call_states:
        call_states[call_sid] = {
            'campaign_id': campaign_id,
            'stage': 'greeting',
            'responses': []
        }
    
    response = VoiceResponse()
    
    # Use AI-generated audio or Twilio's built-in TTS
    response.say(
        script['greeting'],
        voice='Polly.Joanna',
        # Slight adjustments for more natural sound
        rate='95%',
        pitch='0%'
    )
    
    # Gather customer's response
    gather = Gather(
        input='speech',
        action='/process-response',
        method='POST',
        speech_timeout='auto',
        speech_model='phone_call',
        enhanced=True,  # Better speech recognition
        action_on_empty_result=True
    )
    
    response.append(gather)
    
    return Response(str(response), mimetype='text/xml')

@app.route('/process-response', methods=['POST'])
def process_response():
    """Process the customer's spoken response using Dialogflow"""
    speech_result = request.form.get('SpeechResult', '')
    call_sid = request.form.get('CallSid')
    
    # Get call state
    state = call_states.get(call_sid, {
        'campaign_id': 'campaign_001',
        'stage': 'greeting',
        'responses': []
    })
    
    campaign_id = state['campaign_id']
    script = campaign_scripts.get(campaign_id, campaign_scripts['campaign_001'])
    
    # Record response
    if speech_result:
        state['responses'].append(speech_result)
        logger.info(f"Caller said: {speech_result}")
    
    response = VoiceResponse()
    
    # Process with Dialogflow if speech detected
    if speech_result:
        # Get AI response from Dialogflow
        dialogflow_response = detect_intent(speech_result, call_sid)
        intent = dialogflow_response['intent']
        ai_response = dialogflow_response['fulfillment_text']
        logger.info(f"Detected intent: {intent}, Confidence: {dialogflow_response['intent_confidence']}")
        
        # If Dialogflow returned an empty response, use defaults based on intent
        if not ai_response:
            if 'positive' in intent.lower() or intent.lower() == 'yes':
                ai_response = script['more_info']
                state['stage'] = 'more_info'
            elif 'negative' in intent.lower() or intent.lower() == 'no':
                ai_response = "No problem at all. Thank you for your time and have a great day!"
                state['stage'] = 'ended'
            else:
                ai_response = "I'm sorry, I didn't quite understand. Would you like to hear more about our offer?"
        
        # Process the response based on intent
        if 'negative' in intent.lower() or intent.lower() == 'no':
            # Negative response - end call
            response.say(
                ai_response,
                voice='Polly.Joanna'
            )
            response.hangup()
            state['stage'] = 'ended'
        elif 'positive' in intent.lower() or intent.lower() == 'yes':
            # Positive response - proceed with more info
            if state['stage'] == 'greeting':
                state['stage'] = 'more_info'
                response.say(
                    ai_response,
                    voice='Polly.Joanna',
                    rate='95%',
                    pitch='0%'
                )
                # Gather follow-up response
                gather = Gather(
                    input='speech',
                    action='/process-followup',
                    method='POST',
                    speech_timeout='auto',
                    speech_model='phone_call',
                    enhanced=True
                )
                response.append(gather)
            else:
                # Second positive response - proceed to closing
                response.say(
                    script['closing'],
                    voice='Polly.Joanna'
                )
                response.hangup()
                state['stage'] = 'ended'
        else:
            # Unclear intent - ask for clarification
            response.say(
                ai_response,
                voice='Polly.Joanna'
            )
            # Gather next response
            gather = Gather(
                input='speech',
                action='/process-response',
                method='POST',
                speech_timeout='auto',
                speech_model='phone_call',
                enhanced=True
            )
            response.append(gather)
    else:
        # No speech detected
        response.say(
            "I didn't hear your response. Would you like to hear more about our offer?",
            voice='Polly.Joanna'
        )
        
        gather = Gather(
            input='speech',
            action='/process-response',
            method='POST',
            speech_timeout='auto',
            speech_model='phone_call',
            enhanced=True
        )
        response.append(gather)
    
    # Save updated state
    call_states[call_sid] = state
    
    return Response(str(response), mimetype='text/xml')

@app.route('/process-followup', methods=['POST'])
def process_followup():
    """Handle follow-up response with Dialogflow"""
    speech_result = request.form.get('SpeechResult', '')
    call_sid = request.form.get('CallSid')
    
    # Get call state
    state = call_states.get(call_sid, {
        'campaign_id': 'campaign_001',
        'stage': 'more_info',
        'responses': []
    })
    
    campaign_id = state['campaign_id']
    script = campaign_scripts.get(campaign_id, campaign_scripts['campaign_001'])
    
    # Record response
    if speech_result:
        state['responses'].append(speech_result)
        logger.info(f"Caller said (followup): {speech_result}")
    
    response = VoiceResponse()
    
    # Process with Dialogflow if speech detected
    if speech_result:
        # Get AI response from Dialogflow
        dialogflow_response = detect_intent(speech_result, call_sid)
        intent = dialogflow_response['intent']
        ai_response = dialogflow_response['fulfillment_text']
        logger.info(f"Detected intent (followup): {intent}, Confidence: {dialogflow_response['intent_confidence']}")
        
        # If positive intent, close with success
        if 'positive' in intent.lower() or intent.lower() == 'yes':
            response.say(
                script['closing'],
                voice='Polly.Joanna'
            )
        else:
            # For any other response, thank and end call
            response.say(
                "No problem. Thank you for your time. Feel free to visit our website for more information. Have a great day!",
                voice='Polly.Joanna'
            )
    else:
        # No speech detected
        response.say(
            "I didn't catch that. Thank you for your time today. Feel free to reach out if you have any questions in the future.",
            voice='Polly.Joanna'
        )
    
    # End call
    response.hangup()
    state['stage'] = 'ended'
    
    # Save updated state
    call_states[call_sid] = state
    
    return Response(str(response), mimetype='text/xml')

@app.route('/call-status', methods=['POST'])
def call_status():
    """Track call status and save call data"""
    call_status = request.form.get('CallStatus')
    call_sid = request.form.get('CallSid')
    call_duration = request.form.get('CallDuration')
    
    logger.info(f"Call {call_sid} status: {call_status}, duration: {call_duration}s")
    
    # If call is completed or failed, store the call data
    if call_status in ['completed', 'failed', 'busy', 'no-answer']:
        state = call_states.get(call_sid, {})
        
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
        
        # Remove from memory
        if call_sid in call_states:
            del call_states[call_sid]
    
    return '', 200

@app.route('/analyze-calls', methods=['GET'])
def analyze_calls():
    """Endpoint to analyze call data and refine pitches"""
    # In production, this would:
    # 1. Fetch call data from database
    # 2. Analyze responses using NLP
    # 3. Identify patterns in successful/failed calls
    # 4. Generate recommendations for script improvements
    
    # Placeholder for demo
    return {
        'success': True,
        'analysis': {
            'success_rate': '45%',
            'avg_call_duration': '38s',
            'common_positive_responses': ['yes', 'tell me more', 'sounds interesting'],
            'common_objections': ['too expensive', 'not now', 'send me email'],
            'recommended_improvements': [
                'Address pricing earlier in the call',
                'Offer email option proactively',
                'Shorten initial greeting by 10%'
            ]
        }
    }, 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    print(f"Starting server on port {port}...")
    app.run(host='0.0.0.0', port=port, debug=True)