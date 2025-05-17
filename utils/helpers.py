# Modified utils/helpers.py to enhance parse_speech_intent function
import logging
import re

logger = logging.getLogger(__name__)

def sanitize_phone_number(phone_number):
    """
    Sanitize a phone number to E.164 format for Twilio
    
    Args:
        phone_number (str): Phone number in any format
        
    Returns:
        str: Phone number in E.164 format or None if invalid
    """
    # Remove all non-digit characters
    digits_only = re.sub(r'\D', '', phone_number)
    
    # Handle US numbers (add +1 if 10 digits)
    if len(digits_only) == 10:
        return f"+1{digits_only}"
    # If already has country code (11+ digits with leading 1 for US)
    elif len(digits_only) >= 11:
        # Assume it's a US number with country code if it starts with 1 and has 11 digits
        if digits_only.startswith('1') and len(digits_only) == 11:
            return f"+{digits_only}"
        # Otherwise just add + prefix
        else:
            return f"+{digits_only}"
    else:
        logger.error(f"Invalid phone number format: {phone_number}")
        return None

def parse_speech_intent(speech_result):
    """
    More comprehensive intent parsing based on keywords (replacement for Dialogflow)
    
    Args:
        speech_result (str): The transcribed speech from the caller
        
    Returns:
        str: The detected intent ('positive', 'negative', or 'unclear')
    """
    if not speech_result:
        return 'unclear'
    
    speech_lower = speech_result.lower()
    
    # Check for positive responses - comprehensive list
    positive_keywords = [
        'yes', 'yeah', 'sure', 'okay', 'ok', 'fine', 
        'interested', 'tell me more', 'send', 'please', 
        'would like', 'i want', 'i would', 'i do', 'i am', 
        'of course', 'certainly', 'absolutely', 'definitely',
        'sounds good', 'that works', 'go ahead'
    ]
    
    # Check for negative responses - comprehensive list
    negative_keywords = [
        'no', 'not', 'don\'t', 'isn\'t', 'wouldn\'t', 
        'not interested', 'stop', 'bye', 'later',
        'i don\'t want', 'i don\'t need', 'not now',
        'go away', 'leave me alone', 'not right now',
        'no thanks', 'nope', 'pass', 'decline'
    ]
    
    # Check for positive intent
    for keyword in positive_keywords:
        if keyword in speech_lower:
            return 'positive'
    
    # Check for negative intent
    for keyword in negative_keywords:
        if keyword in speech_lower:
            return 'negative'
    
    # Default to unclear if no clear intent detected
    return 'unclear'

def log_call_event(call_sid, event_type, details=None):
    """
    Log call events in a standardized format
    
    Args:
        call_sid (str): The call SID
        event_type (str): Type of event (e.g., 'initiated', 'speech_received')
        details (dict, optional): Additional details about the event
    """
    log_data = {
        'call_sid': call_sid,
        'event': event_type
    }
    
    if details:
        log_data.update(details)
    
    logger.info(f"CALL EVENT: {log_data}")
    
    return log_data