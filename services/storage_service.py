"""
Storage service for managing call state and data.
This is currently an in-memory implementation, but could be replaced with
a database implementation in production.
"""
import logging
import json
from datetime import datetime

# Set up logging
logger = logging.getLogger(__name__)

# In-memory storage for call states (replace with database in production)
_call_states = {}

def init_storage():
    """
    Initialize the storage service
    
    Returns:
        dict: The storage object (for now, just an empty dict)
    """
    global _call_states
    
    logger.info("Initializing storage service")
    _call_states = {}
    
    return _call_states

def save_call_state(call_sid, state):
    """
    Save or update call state
    
    Args:
        call_sid (str): Twilio call SID
        state (dict): Call state to save
    
    Returns:
        dict: Updated call state
    """
    global _call_states
    
    # Add timestamp to state
    state['last_updated'] = datetime.now().isoformat()
    
    # Store state
    _call_states[call_sid] = state
    
    logger.debug(f"Saved state for call {call_sid}: {state}")
    
    return state

def get_call_state(call_sid):
    """
    Get call state
    
    Args:
        call_sid (str): Twilio call SID
    
    Returns:
        dict: Call state or None if not found
    """
    global _call_states
    
    state = _call_states.get(call_sid)
    
    if state:
        logger.debug(f"Retrieved state for call {call_sid}")
    else:
        logger.warning(f"Call state not found for {call_sid}")
    
    return state

def delete_call_state(call_sid):
    """
    Delete call state
    
    Args:
        call_sid (str): Twilio call SID
    
    Returns:
        bool: True if state was deleted, False otherwise
    """
    global _call_states
    
    if call_sid in _call_states:
        del _call_states[call_sid]
        logger.debug(f"Deleted state for call {call_sid}")
        return True
    else:
        logger.warning(f"Attempted to delete non-existent call state for {call_sid}")
        return False

def get_all_call_states():
    """
    Get all call states
    
    Returns:
        dict: All call states
    """
    global _call_states
    
    return _call_states

def save_call_data(call_data):
    """
    Save call data for analytics/history (placeholder for database implementation)
    
    Args:
        call_data (dict): Call data to save
    
    Returns:
        dict: Saved call data
    """
    # In a real implementation, this would save to a database
    # For now, just log it
    logger.info(f"Call data saved (placeholder): {call_data}")
    
    # Add timestamp
    call_data['saved_at'] = datetime.now().isoformat()
    
    return call_data