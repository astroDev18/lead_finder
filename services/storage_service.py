# Add these functions to your existing storage_service.py
import os
import json
from datetime import datetime
import logging
logger = logging.getLogger(__name__)

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

def save_call_state_to_disk(call_sid, state):
    """Save call state to disk for persistence"""
    storage_dir = os.path.join(os.getcwd(), "conversation_states")
    os.makedirs(storage_dir, exist_ok=True)
    
    file_path = os.path.join(storage_dir, f"{call_sid}.json")
    with open(file_path, 'w') as f:
        json.dump(state, f, indent=2)
    
    logger.debug(f"Saved state to disk for call {call_sid}")
    return state

def load_call_state_from_disk(call_sid):
    """Load call state from disk if exists"""
    storage_dir = os.path.join(os.getcwd(), "conversation_states")
    file_path = os.path.join(storage_dir, f"{call_sid}.json")
    
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            state = json.load(f)
            logger.debug(f"Loaded state from disk for call {call_sid}")
            return state
    
    return None

# Update your existing save_call_state function
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
    
    # Store state in memory
    _call_states[call_sid] = state
    
    # Also save to disk for persistence
    storage_dir = os.path.join(os.getcwd(), "conversation_states")
    os.makedirs(storage_dir, exist_ok=True)
    
    file_path = os.path.join(storage_dir, f"{call_sid}.json")
    with open(file_path, 'w') as f:
        json.dump(state, f, indent=2)
    
    logger.debug(f"Saved state for call {call_sid}")
    
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
    
    # Try memory first
    state = _call_states.get(call_sid)
    
    # If not in memory, try disk
    if not state:
        storage_dir = os.path.join(os.getcwd(), "conversation_states")
        file_path = os.path.join(storage_dir, f"{call_sid}.json")
        
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                state = json.load(f)
                _call_states[call_sid] = state
    
    if state:
        logger.debug(f"Retrieved state for call {call_sid}")
    else:
        logger.warning(f"Call state not found for {call_sid}")
        # Create a new state if not found
        state = {
            'conversation_stage': 'greeting',
            'conversation_data': {},
            'previous_stages': []
        }
    
    return state