# test_conversation_simple.py
import os
import sys
import json
import uuid
import logging
from services.storage_service import save_call_state, get_call_state
import re
import random
from datetime import datetime

# In-memory storage for testing
_conversation_states = {}

logger = logging.getLogger(__name__)

def save_call_state(call_sid, state):
    """Save conversation state for a call"""
    # Add timestamp
    state['last_updated'] = datetime.now().isoformat()
    
    # Save to memory
    _conversation_states[call_sid] = state
    
    # Save to disk for persistence
    storage_dir = os.path.join(os.getcwd(), "conversation_states")
    os.makedirs(storage_dir, exist_ok=True)
    
    file_path = os.path.join(storage_dir, f"{call_sid}.json")
    with open(file_path, 'w') as f:
        json.dump(state, f, indent=2)
    
    return state

def get_call_state(call_sid):
    """Get conversation state for a call"""
    # Try memory first
    if call_sid in _conversation_states:
        return _conversation_states[call_sid]
    
    # Try disk
    storage_dir = os.path.join(os.getcwd(), "conversation_states")
    file_path = os.path.join(storage_dir, f"{call_sid}.json")
    
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            state = json.load(f)
            _conversation_states[call_sid] = state
            return state
    
    # Create new state if not found
    state = {
        'conversation_stage': 'greeting',
        'conversation_data': {},
        'previous_stages': []
    }
    return state

class ConversationManager:
    """Manager for multi-turn conversations"""
    
    def __init__(self, db_service=None):
        self.db_service = db_service
    
    def process_response(self, call_sid, script_or_campaign_id, user_input):
        """
        Process user response and determine next conversation step
        
        Args:
            call_sid (str): The call's unique identifier
            script_or_campaign_id: Either a script dictionary or campaign ID string
            user_input (str): The user's spoken or DTMF input
            
        Returns:
            Dict containing next response and actions
        """
        # Get call state
        call_state = get_call_state(call_sid)
        if not call_state:
            logger.warning(f"No state found for call {call_sid}, initializing")
            call_state = {
                'conversation_stage': 'greeting',
                'conversation_data': {},
                'previous_stages': []
            }
            
            # Set campaign_id if provided
            if isinstance(script_or_campaign_id, str):
                call_state['campaign_id'] = script_or_campaign_id
        
        # Get script
        try:
            # Check if we received a script dictionary or a campaign_id string
            if isinstance(script_or_campaign_id, str):
                # It's a campaign_id, get the script
                campaign_id = script_or_campaign_id
                
                # First try from database if db_service available
                if self.db_service:
                    campaign = self.db_service.get_campaign_by_id(campaign_id)
                    script = campaign.script_template if campaign and campaign.script_template else None
                else:
                    script = None
                    
                # Fall back to template if needed
                if not script:
                    from templates.script_templates import get_script
                    script = get_script(campaign_id)
            else:
                # We received the script directly
                script = script_or_campaign_id
                
        except Exception as e:
            logger.error(f"Error getting script: {e}")
            return {
                'message': "I apologize, but we're experiencing technical difficulties. Please try again later.",
                'end_call': True
            }
        
        # Get current stage
        current_stage = call_state.get('conversation_stage', 'greeting')
        conversation_data = call_state.get('conversation_data', {})
        
        logger.info(f"Processing response for stage: {current_stage}")
        
        # Get current stage definition
        if 'conversation_flow' in script:
            # New format: multi-turn conversation flow
            flow = script.get('conversation_flow', {})
            current_stage_data = flow.get(current_stage, {})
            
            # Check if this is an end stage
            if current_stage_data.get('end_call', False):
                return {
                    'message': current_stage_data.get('message', "Thank you for your time."),
                    'end_call': True,
                    'current_stage': current_stage
                }
            
            # Normalize input
            user_input_lower = user_input.lower().strip() if user_input else ""
            logger.info(f"User input: '{user_input_lower}'")
            
            # Try to match input to patterns
            next_stage = None
            matched_response = None
            
            responses = current_stage_data.get('responses', {})
            for response_type, response_data in responses.items():
                patterns = response_data.get('patterns', [])
                
                for pattern in patterns:
                    if pattern.lower() in user_input_lower:
                        next_stage = response_data.get('next_stage')
                        matched_response = response_type
                        logger.info(f"Matched pattern '{pattern}' for response type '{response_type}'")
                        break
                        
                if next_stage:
                    break
            
            # Extract information if configured
            if matched_response and 'extract_info' in responses.get(matched_response, {}):
                extraction_patterns = responses[matched_response]['extract_info']
                for field, pattern in extraction_patterns.items():
                    matches = re.search(pattern, user_input, re.IGNORECASE)
                    if matches:
                        conversation_data[field] = matches.group(1)
                        logger.info(f"Extracted {field}: {matches.group(1)}")
                        call_state['conversation_data'] = conversation_data
            
            # Use fallback if no match found
            if not next_stage and 'fallback' in responses:
                next_stage = responses['fallback'].get('next_stage')
                matched_response = 'fallback'
                logger.info("Using fallback response")
            
            # If still no next stage, stay on current stage
            if not next_stage:
                fallbacks = script.get('fallback_responses', 
                                    ["I'm sorry, I didn't understand that. Could you please repeat?"])
                return {
                    'message': random.choice(fallbacks),
                    'end_call': False,
                    'current_stage': current_stage,
                    'matched_response': 'fallback'
                }
            
            # Get the next stage data
            next_stage_data = flow.get(next_stage, {})
            
            # Get the response message and check if call should end
            response_message = next_stage_data.get('message', '')
            end_call = next_stage_data.get('end_call', False)
            
            # Process variables in the message
            for key, value in conversation_data.items():
                placeholder = f"{{{key}}}"
                if placeholder in response_message:
                    response_message = response_message.replace(placeholder, str(value))
            
            # Update call state
            call_state['conversation_stage'] = next_stage
            call_state['previous_stages'] = call_state.get('previous_stages', []) + [current_stage]
            call_state['matched_response'] = matched_response
            save_call_state(call_sid, call_state)
            
            logger.info(f"Moving to stage: {next_stage}, End call: {end_call}")
            
            return {
                'message': response_message,
                'end_call': end_call,
                'current_stage': next_stage,
                'matched_response': matched_response
            }
            
        else:
            # Legacy format: simple linear script
            # Simple fallback for older script format
            if current_stage == 'greeting':
                message = script.get('more_info', "Great! Let me tell you more about our services.")
                call_state['conversation_stage'] = 'more_info'
                save_call_state(call_sid, call_state)
                return {
                    'message': message,
                    'end_call': False,
                    'current_stage': 'more_info'
                }
            elif current_stage == 'more_info':
                message = script.get('closing', "Thank you for your time. We look forward to serving you!")
                call_state['conversation_stage'] = 'closing'
                save_call_state(call_sid, call_state)
                return {
                    'message': message,
                    'end_call': True,
                    'current_stage': 'closing'
                }
            else:
                message = script.get('fallback', "Thank you for your time.")
                return {
                    'message': message,
                    'end_call': True,
                    'current_stage': 'end'
                }

def test_conversation():
    """Test the enhanced conversation flow"""
    # Create test script with structured flow
    test_script = {
        'name': 'Test Conversation Flow',
        'conversation_flow': {
            'greeting': {
                'message': 'Hello! This is a test call. I\'m calling about real estate in your area. Have you thought about selling your home?',
                'responses': {
                    'positive': {
                        'patterns': ['yes', 'yeah', 'sure', 'thinking about it', 'considering', 'possibly', 'maybe'],
                        'next_stage': 'timeframe'
                    },
                    'negative': {
                        'patterns': ['no', 'not interested', 'no thanks', 'not selling', 'not now'],
                        'next_stage': 'objection_handling'
                    },
                    'fallback': {
                        'next_stage': 'clarify'
                    }
                }
            },
            'timeframe': {
                'message': 'Great! Do you have a specific timeframe in mind for selling?',
                'responses': {
                    'soon': {
                        'patterns': ['now', 'soon', 'right away', 'this month', 'next month', 'couple months'],
                        'next_stage': 'property_details'
                    },
                    'later': {
                        'patterns': ['later', 'not sure', 'next year', 'future', 'thinking about it'],
                        'next_stage': 'property_details'
                    },
                    'fallback': {
                        'next_stage': 'property_details'
                    }
                }
            },
            'property_details': {
                'message': 'Can you tell me a bit about your property? How many bedrooms and bathrooms?',
                'responses': {
                    'property_info': {
                        'patterns': ['bedroom', 'bathroom', 'bed', 'bath'],
                        'extract_info': {
                            'bedrooms': '\\b(\\d+)\\s*(bed|bedroom|br)s?\\b',
                            'bathrooms': '\\b(\\d+(?:\\.\\d+)?)\\s*(bath|bathroom|ba)s?\\b'
                        },
                        'next_stage': 'estimate'
                    },
                    'fallback': {
                        'next_stage': 'estimate'
                    }
                }
            },
            'estimate': {
                'message': 'Based on properties in your area, your home might be worth between $300,000 and $350,000. Would you like to schedule a professional valuation?',
                'responses': {
                    'yes': {
                        'patterns': ['yes', 'sure', 'okay', 'interested'],
                        'next_stage': 'schedule'
                    },
                    'no': {
                        'patterns': ['no', 'not now', 'later', 'think about it'],
                        'next_stage': 'close'
                    },
                    'fallback': {
                        'next_stage': 'close'
                    }
                }
            },
            'schedule': {
                'message': 'Great! When would be a good time for our agent to call you?',
                'responses': {
                    'time': {
                        'patterns': ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'weekend', 'morning', 'afternoon', 'evening'],
                        'extract_info': {
                            'appointment_time': '(morning|afternoon|evening|monday|tuesday|wednesday|thursday|friday|saturday|sunday)'
                        },
                        'next_stage': 'confirm'
                    },
                    'fallback': {
                        'next_stage': 'confirm'
                    }
                }
            },
            'confirm': {
                'message': 'Perfect! We\'ll have an agent call you to confirm the {appointment_time} appointment. Thank you for your time!',
                'end_call': True
            },
            'objection_handling': {
                'message': 'I understand. Many homeowners are curious about their property\'s value even if they\'re not ready to sell. Would you like to know what your home is worth anyway?',
                'responses': {
                    'yes': {
                        'patterns': ['yes', 'okay', 'sure', 'curious'],
                        'next_stage': 'property_details'
                    },
                    'no': {
                        'patterns': ['no', 'not interested', 'no thanks'],
                        'next_stage': 'close'
                    },
                    'fallback': {
                        'next_stage': 'close'
                    }
                }
            },
            'clarify': {
                'message': 'I\'m sorry if I wasn\'t clear. I was asking if you\'ve thought about selling your home in the near future?',
                'responses': {
                    'yes': {
                        'patterns': ['yes', 'yeah', 'sure', 'thinking about it'],
                        'next_stage': 'timeframe'
                    },
                    'no': {
                        'patterns': ['no', 'not interested', 'no thanks'],
                        'next_stage': 'objection_handling'
                    },
                    'fallback': {
                        'next_stage': 'objection_handling'
                    }
                }
            },
            'close': {
                'message': 'Thank you for your time. Have a great day!',
                'end_call': True
            }
        },
        'fallback_responses': [
            'I\'m sorry, I didn\'t quite catch that. Could you please repeat?',
            'I didn\'t understand. Could you say that again?',
            'Would you mind rephrasing that?'
        ]
    }
    
    # Create a test call ID
    call_sid = f"test_call_{uuid.uuid4().hex[:8]}"
    
    # Initialize call state
    call_state = {
        'conversation_stage': 'greeting',
        'conversation_data': {},
        'previous_stages': []
    }
    save_call_state(call_sid, call_state)
    
    # Initialize conversation manager
    conversation_manager = ConversationManager()
    
    # Get the initial greeting message
    greeting = test_script['conversation_flow']['greeting']['message']
    
    print(f"\n--- Starting conversation flow test ---")
    print(f"AI: {greeting}")
    
    # Simulated conversation loop
    while True:
        # Get user input
        user_input = input("\nYou (type 'exit' to end): ")
        
        if user_input.lower() in ['exit', 'quit', 'bye']:
            break
        
        # Process response
        result = conversation_manager.process_response(call_sid, test_script, user_input)
        
        print(f"AI: {result['message']}")
        print(f"Stage: {result['current_stage']}")
        
        # End if needed
        if result.get('end_call'):
            print("Call would end now")
            break
    
    # Show final state
    final_state = get_call_state(call_sid)
    print(f"\n--- Final conversation state ---")
    print(json.dumps(final_state, indent=2))

if __name__ == "__main__":
    test_conversation()