"""
Dialogflow integration service for intent detection.
"""
import os
import logging
import uuid
from google.cloud import dialogflow

from config.settings import DIALOGFLOW_PROJECT_ID

# Set up logging
logger = logging.getLogger(__name__)

# Dialogflow client instance (initialized lazily)
_dialogflow_client = None

def init_dialogflow_client():
    """
    Initialize the Dialogflow client
    
    Returns:
        SessionsClient: Initialized Dialogflow client
    """
    global _dialogflow_client
    
    try:
        logger.info("Initializing Dialogflow client")
        _dialogflow_client = dialogflow.SessionsClient()
        logger.info("Dialogflow client initialized successfully")
        return _dialogflow_client
    except Exception as e:
        logger.error(f"Error initializing Dialogflow client: {e}")
        raise

def get_dialogflow_client():
    """
    Get the Dialogflow client instance, initializing it if necessary
    
    Returns:
        SessionsClient: Dialogflow client instance
    """
    global _dialogflow_client
    
    if _dialogflow_client is None:
        _dialogflow_client = init_dialogflow_client()
    
    return _dialogflow_client

def detect_intent(text, session_id=None, language_code="en-US"):
    """
    Detect the intent of a text using Dialogflow
    
    Args:
        text (str): Text input from the caller
        session_id (str, optional): Unique session ID (defaults to random UUID)
        language_code (str, optional): Language code (defaults to en-US)
    
    Returns:
        dict: The response from Dialogflow including fulfillment text
    """
    try:
        client = get_dialogflow_client()
        
        # Use provided session ID or generate a random one
        if not session_id:
            session_id = str(uuid.uuid4())
        
        session = client.session_path(DIALOGFLOW_PROJECT_ID, session_id)
        
        text_input = dialogflow.TextInput(text=text, language_code=language_code)
        query_input = dialogflow.QueryInput(text=text_input)
        
        logger.info(f"Sending to Dialogflow: '{text}' (session: {session_id})")
        
        response = client.detect_intent(
            request={"session": session, "query_input": query_input}
        )
        
        result = {
            "query_text": response.query_result.query_text,
            "intent": response.query_result.intent.display_name,
            "intent_confidence": response.query_result.intent_detection_confidence,
            "fulfillment_text": response.query_result.fulfillment_text,
            "parameters": dict(response.query_result.parameters)
        }
        
        logger.info(f"Dialogflow response: Intent={result['intent']}, Confidence={result['intent_confidence']}")
        
        return result
    
    except Exception as e:
        logger.error(f"Error with Dialogflow: {e}")
        # Return fallback intent as failsafe
        return {
            "query_text": text,
            "intent": "fallback",
            "intent_confidence": 0,
            "fulfillment_text": "I'm sorry, I didn't quite understand that. Would you like to hear more about our services?",
            "parameters": {}
        }