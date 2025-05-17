# services/call_bridge_service.py
import os
import logging
import requests
import json
from urllib.parse import urljoin
import time

logger = logging.getLogger(__name__)

class CallBridgeService:
    """
    Service to bridge Lead Finder conversation flows with SIP Integration calling
    """
    
    def __init__(self, 
                 sip_service_url=None,
                 tts_service=None,
                 conversation_manager=None,
                 storage_service=None):
        """
        Initialize the call bridge service
        
        Args:
            sip_service_url (str): URL of the SIP integration service
            tts_service: TTS service instance
            conversation_manager: Conversation manager instance
            storage_service: Storage service for call state
        """
        self.sip_service_url = "http://localhost:5002"
        self.tts_service = tts_service
        self.conversation_manager = conversation_manager
        self.storage_service = storage_service
        
        logger.info(f"Call Bridge Service initialized with SIP service URL: {self.sip_service_url}")
    
    def initiate_call(self, phone_number, campaign_id, callback_url=None):
        """
        Initiate a call through the SIP integration service
        
        Args:
            phone_number (str): Destination phone number
            campaign_id (str): Campaign ID to use for the call
            callback_url (str, optional): URL for callbacks
            
        Returns:
            dict: Call information including call_control_id
        """
        try:
            # Prepare the call request
            call_request = {
                "phone_number": phone_number,
                "campaign_id": campaign_id
            }
        
            if callback_url:
                call_request["callback_url"] = callback_url
            
            # Log the request details
            logger.info(f"Making call with SIP URL: {self.sip_service_url}")
            logger.info(f"Call request: {call_request}")
            
            # Make the API call to SIP integration service
            endpoint = urljoin(self.sip_service_url, "/make-call")
            logger.info(f"Calling endpoint: {endpoint}")
            
            response = requests.post(
                endpoint,
                json=call_request,
                timeout=10
            )
            
            logger.info(f"Response status: {response.status_code}")
            logger.info(f"Response content: {response.text[:200]}")  # Log first 200 chars
            
            response.raise_for_status()
            call_data = response.json()
            
            if call_data.get('success'):
                logger.info(f"Successfully initiated call to {phone_number} with call_id: {call_data.get('call_control_id')}")
                
                # Initialize call state
                call_info = {
                    'call_control_id': call_data.get('call_control_id'),
                    'campaign_id': campaign_id,
                    'phone_number': phone_number,
                    'status': 'initiated',
                    'start_time': time.time()
                }
                
                # Store the call state if we have storage service
                if self.storage_service:
                    self.storage_service.save_call_state(call_data.get('call_control_id'), {
                        'conversation_stage': 'greeting',
                        'conversation_data': {},
                        'previous_stages': [],
                        'campaign_id': campaign_id,
                        'phone_number': phone_number,
                        'start_time': time.time(),
                        'status': 'initiated'
                    })
                
                return call_info
            else:
                logger.error(f"Error initiating call: {call_data.get('error')}")
                return None
                
        except requests.RequestException as e:
            logger.error(f"Error making call through SIP integration: {e}")
            return None
    
    def handle_call_event(self, event_data):
        """
        Handle events from the SIP integration service
        
        Args:
            event_data (dict): Event data from webhook
            
        Returns:
            dict: Response with instructions or next steps
        """
        try:
            # Extract relevant information
            event_type = event_data.get('data', {}).get('event_type')
            call_control_id = event_data.get('data', {}).get('payload', {}).get('call_control_id')
            
            logger.info(f"Handling call event: {event_type} for call {call_control_id}")
            
            # Get call state
            call_state = None
            if self.storage_service:
                call_state = self.storage_service.get_call_state(call_control_id)
            
            if not call_state:
                logger.warning(f"No state found for call {call_control_id}")
                return {"success": False, "error": "Call state not found"}
            
            # Process based on event type
            if event_type == 'call.initiated':
                # Call has been initiated, update state
                call_state['status'] = 'initiated'
                if self.storage_service:
                    self.storage_service.save_call_state(call_control_id, call_state)
                
                return {"success": True}
                
            elif event_type == 'call.answered':
                # Call has been answered, start conversation
                call_state['status'] = 'in_progress'
                
                # Get campaign script
                from templates.script_templates import get_script
                campaign_id = call_state.get('campaign_id', 'campaign_001')
                script = get_script(campaign_id)
                
                # Start with greeting
                greeting = None
                if 'conversation_flow' in script:
                    # New format: structured conversation flow
                    greeting = script['conversation_flow'].get('greeting', {}).get('message')
                else:
                    # Legacy format: simple script
                    greeting = script.get('greeting')
                
                if not greeting:
                    greeting = "Hello, this is an automated call. Thank you for answering."
                
                # Generate TTS for greeting if we have TTS service
                audio_url = None
                if self.tts_service:
                    # Generate greeting audio
                    greeting_filename = self.tts_service.generate_audio(greeting, speaker="p273")
                    if greeting_filename:
                        # We'd need the full URL to the audio file
                        # In a real environment, this should be a publicly accessible URL
                        # For now we'll use a placeholder that the SIP service would understand
                        audio_url = f"/audio/{greeting_filename}"
                
                # Save updated state
                if self.storage_service:
                    self.storage_service.save_call_state(call_control_id, call_state)
                
                # Send a speak command to the SIP service if we have audio
                if audio_url:
                    self._send_speak_command(call_control_id, greeting, audio_url)
                else:
                    # Fallback to plain text if no audio URL
                    self._send_speak_command(call_control_id, greeting)
                
                return {
                    "success": True,
                    "message": greeting,
                    "audio_url": audio_url
                }
                
            elif event_type == 'call.speak.ended':
                # Speaking has ended, if we're in greeting stage advance the conversation
                current_stage = call_state.get('conversation_stage', 'greeting')
                
                if current_stage == 'greeting':
                    # User hasn't responded yet, wait for input
                    # No need to do anything here as we'll wait for user input
                    pass
                
                return {"success": True}
                
            elif event_type == 'call.hangup':
                # Call has ended
                call_state['status'] = 'completed'
                call_state['end_time'] = time.time()
                call_state['duration'] = call_state['end_time'] - call_state.get('start_time', call_state['end_time'])
                
                if self.storage_service:
                    self.storage_service.save_call_state(call_control_id, call_state)
                
                logger.info(f"Call {call_control_id} has ended, duration: {call_state.get('duration', 0):.2f} seconds")
                
                return {"success": True}
                
            elif event_type == 'call.gather.ended':
                # User has provided input
                user_input = event_data.get('data', {}).get('payload', {}).get('speech', {}).get('text')
                
                if not user_input:
                    # No input detected
                    fallback_message = "I'm sorry, I didn't catch that. Could you please repeat?"
                    self._send_speak_command(call_control_id, fallback_message)
                    return {"success": True, "message": fallback_message}
                
                # Process the user input with conversation manager
                if self.conversation_manager:
                    from templates.script_templates import get_script
                    campaign_id = call_state.get('campaign_id', 'campaign_001')
                    script = get_script(campaign_id)
                    
                    # Process response
                    result = self.conversation_manager.process_response(call_control_id, script, user_input)
                    
                    # Generate audio for response
                    audio_url = None
                    if self.tts_service and result.get('message'):
                        response_filename = self.tts_service.generate_audio(result['message'], speaker="p273")
                        if response_filename:
                            audio_url = f"/audio/{response_filename}"
                    
                    # Speak the response
                    if result.get('message'):
                        self._send_speak_command(call_control_id, result['message'], audio_url)
                    
                    # If this is the end of the call, hang up
                    if result.get('end_call'):
                        # Wait a bit to ensure message is spoken
                        # In a real system, we'd wait for speak.ended event
                        time.sleep(1)
                        self._send_hangup_command(call_control_id)
                    
                    return {
                        "success": True,
                        "message": result.get('message'),
                        "audio_url": audio_url,
                        "end_call": result.get('end_call', False)
                    }
                else:
                    # No conversation manager, use simple response
                    response = "Thank you for your input. Our team will follow up with you soon."
                    self._send_speak_command(call_control_id, response)
                    
                    # End the call after response
                    time.sleep(1)
                    self._send_hangup_command(call_control_id)
                    
                    return {
                        "success": True,
                        "message": response,
                        "end_call": True
                    }
            
            # Default response for unhandled event types
            return {"success": True, "event_handled": False}
                
        except Exception as e:
            logger.error(f"Error handling call event: {e}", exc_info=True)
            return {"success": False, "error": str(e)}
    
    def _send_speak_command(self, call_control_id, text, audio_url=None):
        """
        Send a speak command to the SIP integration service
        
        Args:
            call_control_id (str): The call control ID
            text (str): Text to speak
            audio_url (str, optional): URL to audio file
            
        Returns:
            bool: Success or failure
        """
        try:
            speak_data = {
                "call_control_id": call_control_id,
                "text": text
            }
            
            if audio_url:
                speak_data["audio_url"] = audio_url
            
            response = requests.post(
                urljoin(self.sip_service_url, "/speak"),
                json=speak_data,
                timeout=10
            )
            
            response.raise_for_status()
            result = response.json()
            
            if result.get('success'):
                logger.info(f"Successfully sent speak command for call {call_control_id}")
                return True
            else:
                logger.error(f"Error sending speak command: {result.get('error')}")
                return False
                
        except requests.RequestException as e:
            logger.error(f"Error sending speak command: {e}")
            return False
    
    def _send_hangup_command(self, call_control_id):
        """
        Send a hangup command to the SIP integration service
        
        Args:
            call_control_id (str): The call control ID
            
        Returns:
            bool: Success or failure
        """
        try:
            response = requests.post(
                urljoin(self.sip_service_url, "/hangup"),
                json={"call_control_id": call_control_id},
                timeout=10
            )
            
            response.raise_for_status()
            result = response.json()
            
            if result.get('success'):
                logger.info(f"Successfully sent hangup command for call {call_control_id}")
                return True
            else:
                logger.error(f"Error sending hangup command: {result.get('error')}")
                return False
                
        except requests.RequestException as e:
            logger.error(f"Error sending hangup command: {e}")
            return False

# Helper function to get call bridge service (singleton pattern)
_call_bridge_service = None

def get_call_bridge_service():
    """Get the call bridge service singleton"""
    global _call_bridge_service
    if _call_bridge_service is None:
        # Import here to avoid circular imports
        from services.tts_service import get_tts_service
        from services.conversation_manager import ConversationManager
        from services.storage_service import init_storage
        
        _call_bridge_service = CallBridgeService(
            tts_service=get_tts_service(),
            conversation_manager=ConversationManager(),
            storage_service=init_storage()
        )
    return _call_bridge_service