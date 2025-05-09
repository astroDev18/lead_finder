# test_conversation.py
import os
import sys
import uuid
import json
from services.storage_service import save_call_state, get_call_state
from services.tts_service import get_tts_service

def test_conversation():
    """Test the enhanced conversation flow with TTS"""
    # Set up paths for imports
    if os.path.basename(os.getcwd()) == 'lead_finder':
        sys.path.insert(0, os.getcwd())
    else:
        sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    
    # Import after path setup to avoid circular dependencies
    from services.conversation_manager import ConversationManager
    
    # Initialize services
    conversation_manager = ConversationManager()
    tts_service = get_tts_service()
    
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
                'message': 'Perfect! We\'ll have an agent call you to confirm. Thank you for your time!',
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
        'previous_stages': [],
        'campaign_id': 'test'
    }
    save_call_state(call_sid, call_state)
    
    # Override the get_script function to return our test script
    def mock_get_script(*args, **kwargs):
        return test_script
    
    # Monkey patch to use our test script
    import types
    import templates.script_templates
    templates.script_templates.get_script = mock_get_script
    
    # Get the initial greeting message
    greeting = test_script['conversation_flow']['greeting']['message']
    
    # Generate greeting audio
    speaker = "p273"  # Use your preferred voice
    greeting_file = tts_service.generate_audio(greeting, speaker=speaker)
    greeting_path = tts_service.get_audio_path(greeting_file)
    
    print(f"\n--- Starting conversation flow test ---")
    print(f"AI: {greeting}")
    print(f"Audio saved to: {greeting_path}")
    
    # Simulated conversation loop
    while True:
        # Get user input
        user_input = input("\nYou (type 'exit' to end): ")
        
        if user_input.lower() in ['exit', 'quit', 'bye']:
            break
        
        # Process response
        result = conversation_manager.process_response(call_sid, test_script, user_input)
        
        # Generate audio for response
        response_file = tts_service.generate_audio(result['message'], speaker=speaker)
        response_path = tts_service.get_audio_path(response_file)
        
        print(f"AI: {result['message']}")
        print(f"Audio saved to: {response_path}")
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