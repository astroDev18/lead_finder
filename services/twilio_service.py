"""
Twilio integration service for handling Twilio client operations.
"""
import os
import logging
from twilio.rest import Client

from config.settings import TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN

# Set up logging
logger = logging.getLogger(__name__)

# Twilio client instance (initialized lazily)
_twilio_client = None

def init_twilio_client():
    """
    Initialize the Twilio client with credentials
    
    Returns:
        Client: Initialized Twilio client
    """
    global _twilio_client
    
    try:
        logger.info("Initializing Twilio client")
        _twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        logger.info("Twilio client initialized successfully")
        return _twilio_client
    except Exception as e:
        logger.error(f"Error initializing Twilio client: {e}")
        raise

def get_twilio_client():
    """
    Get the Twilio client instance, initializing it if necessary
    
    Returns:
        Client: Twilio client instance
    """
    global _twilio_client
    
    if _twilio_client is None:
        _twilio_client = init_twilio_client()
    
    return _twilio_client

def make_call(to_number, from_number, webhook_url, status_callback_url=None):
    """
    Initiate a call using Twilio
    
    Args:
        to_number (str): Destination phone number
        from_number (str): Source phone number
        webhook_url (str): URL for Twilio to request TwiML when call connects
        status_callback_url (str, optional): URL for call status callbacks
    
    Returns:
        Call: Twilio Call instance
    """
    client = get_twilio_client()
    
    call_params = {
        'url': webhook_url,
        'to': to_number,
        'from_': from_number,
    }
    
    if status_callback_url:
        call_params.update({
            'status_callback': status_callback_url,
            'status_callback_event': ['initiated', 'ringing', 'answered', 'completed'],
            'status_callback_method': 'POST'
        })
    
    logger.info(f"Making call to {to_number} from {from_number}")
    call = client.calls.create(**call_params)
    logger.info(f"Call initiated with SID: {call.sid}")
    
    return call

def get_call_status(call_sid):
    """
    Get the status of a call
    
    Args:
        call_sid (str): Call SID
    
    Returns:
        str: Call status
    """
    client = get_twilio_client()
    
    try:
        call = client.calls(call_sid).fetch()
        return call.status
    except Exception as e:
        logger.error(f"Error fetching call status for {call_sid}: {e}")
        raise