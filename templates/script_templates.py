"""
Script templates for voice calls.
Contains all the campaign scripts that can be used in calls.
Uses a template-based system that can be easily adapted for any industry.
"""
import json
import logging
import copy

logger = logging.getLogger(__name__)

# Base template for different script components
SCRIPT_COMPONENTS = [
    'greeting', 
    'more_info', 
    'closing', 
    'no_answer', 
    'negative_response', 
    'unclear_response', 
    'no_speech', 
    'fallback'
]

# Industry templates with variable placeholders
INDUSTRY_TEMPLATES = {
    'real_estate': {
        'name': 'Real Estate Services',
        'greeting': "Hello! This is {agent_name} from {company_name}. I hope I caught you at a good time. We've been helping homeowners in your area {key_benefit}. {custom_opening_question}",
        
        'more_info': "Great! Many homeowners are taking advantage of the current market conditions. We offer {unique_value_prop}. Would you like to learn more about {offer_type} and how it might benefit you?",
        
        'closing': "Excellent! {follow_up_action}. Thank you for your time, and we look forward to {next_steps}!",
        
        'no_answer': "We're sorry we missed you. {company_name} has been helping homeowners in your area with their real estate needs. Please call us back at our office to learn more about the opportunities in today's market.",
        
        'negative_response': "I understand. Thank you for your time. If your situation changes or if you'd like to explore your options in the future, please don't hesitate to contact us. Have a great day!",
        
        'unclear_response': "I'm sorry, I didn't catch that clearly. If you're interested in learning about your real estate options, please say 'yes', or say 'no' if you're not interested at this time.",
        
        'no_speech': "I didn't hear your response. If you're interested in your real estate options, please say 'yes', or 'no' if you're not interested at this time.",
        
        'fallback': "I apologize for the confusion. Thank you for your time today. If you'd like to learn more about your real estate options, please call our office directly. Have a great day!"
    },
    
    'mortgage': {
        'name': 'Mortgage Service',
        'greeting': "Hello, this is {agent_name} from {company_name}. <break time='300ms'/> With interest rates at {interest_rate_descriptor}, many homeowners in your area are saving {savings_amount} each month by refinancing. <break time='500ms'/> Based on current rates, you might qualify for significant savings on your mortgage. {custom_opening_question}",
        
        'more_info': "Great! We're currently offering {promotion_details}. Many of our clients are {client_benefit}. We can provide {service_offered}. Would you like to hear more about the specific options that might work best for you?",
        
        'closing': "Excellent! {follow_up_action}. Thank you for your time, and we look forward to {next_steps}!",
        
        'no_answer': "We're sorry we missed you. {company_name} has been helping homeowners save money through refinancing. With today's rates, you could potentially save hundreds each month. Please call us back at our office to learn more about your options.",
        
        'negative_response': "I understand. Thank you for your time. If your situation changes or if you'd like to explore your options in the future, please don't hesitate to contact us. Have a great day!",
        
        'unclear_response': "I'm sorry, I didn't catch that clearly. If you're interested in learning about our options, please say 'yes', or say 'no' if you're not interested at this time.",
        
        'no_speech': "I didn't hear your response. If you're interested in potentially saving on your mortgage, please say 'yes', or 'no' if you're not interested at this time.",
        
        'fallback': "I apologize for the confusion. Thank you for your time today. If you'd like to learn more about our options, please call our office directly. Have a great day!"
    },
    
    'landscaping': {
        'name': 'Landscaping Services',
        'greeting': "Hello! This is {agent_name} from {company_name}. With {season} approaching, we're offering {promotion_details} in your neighborhood. {custom_opening_question}",
        
        'more_info': "Great to hear! Our team specializes in {service_types} and we're offering {offer_details}. {social_proof}. Would you like to {call_to_action}?",
        
        'closing': "Excellent! {follow_up_action}. Is there a particular day that works best for you to {next_steps}?",
        
        'no_answer': "We're sorry we missed you. {company_name} has been helping homeowners enhance their outdoor spaces with professional landscaping services. If you'd like to learn more about our seasonal offers, please call our office. Thank you and have a great day!",
        
        'negative_response': "No problem at all. Thank you for your time. If you change your mind about enhancing your outdoor space, don't hesitate to reach out. Have a great day!",
        
        'unclear_response': "I'm sorry, I didn't catch that clearly. If you're interested in our landscaping services, please say 'yes', or 'no' if you're not interested right now.",
        
        'no_speech': "I didn't hear your response. If you're interested in learning about our landscaping services, please say 'yes', or 'no' if you're not interested at this time.",
        
        'fallback': "I apologize for the confusion. Thank you for your time today. If you'd like to learn more about our landscaping services, please contact our office directly. Have a great day!"
    },
    
    'insurance': {
        'name': 'Insurance Services',
        'greeting': "Hello! This is {agent_name} from {company_name}. Did you know that many people in your area are paying too much for their insurance? We've been helping customers save an average of {savings_amount} on their {insurance_type} policies. {custom_opening_question}",
        
        'more_info': "I'm glad you're interested! Our company specializes in finding {insurance_type} policies that provide excellent coverage at competitive rates. {unique_value_prop}. Would you like to hear about how we might be able to save you money while improving your coverage?",
        
        'closing': "Great! {follow_up_action}. Thank you for your time today, and we look forward to {next_steps}!",
        
        'no_answer': "We're sorry we missed you. {company_name} has been helping people save money on their {insurance_type} insurance. Many of our customers have found better coverage at lower rates. Please call us back at our office to learn more about your options.",
        
        'negative_response': "I understand completely. Thank you for your time. If you ever decide to review your insurance options in the future, please keep us in mind. Have a wonderful day!",
        
        'unclear_response': "I'm sorry, I didn't catch that clearly. If you're interested in learning about potentially saving on your insurance, please say 'yes', or 'no' if you're not interested at this time.",
        
        'no_speech': "I didn't hear your response. If you're interested in learning about our insurance options, please say 'yes', or 'no' if you're not interested at this time.",
        
        'fallback': "I apologize for the confusion. Thank you for your time today. If you'd like to learn more about our insurance services, please call our office directly. Have a great day!"
    },
    
    'solar': {
        'name': 'Solar Energy Services',
        'greeting': "Hello! This is {agent_name} from {company_name}. With energy costs on the rise, many homeowners in your area are switching to solar and saving {savings_amount} on their monthly energy bills. {custom_opening_question}",
        
        'more_info': "That's great to hear! Our solar solutions {unique_value_prop}. We're currently offering {promotion_details}, and many homeowners are qualifying for significant tax incentives and rebates. Would you like to learn more about how solar might benefit your home specifically?",
        
        'closing': "Excellent! {follow_up_action}. Thank you for your time, and we look forward to {next_steps}!",
        
        'no_answer': "We're sorry we missed you. {company_name} has been helping homeowners reduce their energy costs with solar solutions. With current incentives and rebates, now is a great time to consider going solar. Please call us back to learn more about your options.",
        
        'negative_response': "I understand. Thank you for your time. If your situation changes or if you'd like to explore solar options in the future, please don't hesitate to contact us. Have a great day!",
        
        'unclear_response': "I'm sorry, I didn't catch that clearly. If you're interested in learning about our solar options, please say 'yes', or 'no' if you're not interested at this time.",
        
        'no_speech': "I didn't hear your response. If you're interested in learning about solar energy solutions, please say 'yes', or 'no' if you're not interested at this time.",
        
        'fallback': "I apologize for the confusion. Thank you for your time today. If you'd like to learn more about our solar energy solutions, please call our office directly. Have a great day!"
    }
}

# Advanced conversation flow script for real estate
REAL_ESTATE_SCRIPT_ADVANCED = {
    'name': 'Advanced Real Estate Lead Generation',
    'industry': 'real_estate',
    'conversation_flow': {
        'greeting': {
            'message': "Hi there! This is {agent_name} from {company_name}. I hope I caught you at a good time. We've been helping homeowners just like you in your neighborhood sell their properties for top dollar. Have you thought about selling your home in the near future?",
            'responses': {
                'positive': {
                    'patterns': ['yes', 'yeah', 'sure', 'thinking about it', 'considering', 'possibly', 'maybe', 'in the future', 'tell me more'],
                    'next_stage': 'timeframe'
                },
                'negative': {
                    'patterns': ['no', 'not interested', 'no thanks', 'not selling', 'not now', 'wrong number'],
                    'next_stage': 'objection_handling'
                },
                'question': {
                    'patterns': ['who are you', 'what company', 'why are you calling', 'how did you get my number'],
                    'next_stage': 'answer_question'
                },
                'fallback': {
                    'next_stage': 'clarify'
                }
            }
        },
        'timeframe': {
            'message': "That's great to hear! Do you have a specific timeframe in mind for selling your property?",
            'responses': {
                'immediate': {
                    'patterns': ['now', 'immediately', 'right away', 'asap', 'this month', 'ready now', '1 month', '2 months', 'soon', 'couple of months', 'few months'],
                    'next_stage': 'property_details'
                },
                'medium_term': {
                    'patterns': ['later this year', 'next few months', '3 months', '6 months', 'this summer', 'this fall', 'this winter', 'this spring', 'not right now'],
                    'next_stage': 'property_details'
                },
                'long_term': {
                    'patterns': ['next year', 'in a year', 'year or two', 'long term', 'just exploring', 'not sure', 'someday', 'eventually'],
                    'next_stage': 'property_details'
                },
                'negative': {
                    'patterns': ['not selling', 'changed my mind', 'just looking', 'not interested anymore'],
                    'next_stage': 'objection_handling'
                },
                'fallback': {
                    'next_stage': 'property_details'
                }
            }
        },
        'property_details': {
            'message': "Thank you for sharing that. To help us provide an accurate valuation, could you tell me a little about your property? How many bedrooms and bathrooms does it have?",
            'responses': {
                'has_details': {
                    'patterns': ['bedroom', 'bathroom', 'bed', 'bath', 'square feet', 'sqft', 'sq ft'],
                    'extract_info': {
                        'bedrooms': '\\b(\\d+)\\s*(bed|bedroom|br|bdrm)s?\\b',
                        'bathrooms': '\\b(\\d+(?:\\.\\d+)?)\\s*(bath|bathroom|ba|bthrm)s?\\b',
                        'square_footage': '\\b(\\d+)\\s*(sq|square)\\s*(feet|foot|ft)\\b'
                    },
                    'next_stage': 'property_followup'
                },
                'no_details': {
                    'patterns': ['not sure', 'don\'t know', 'i don\'t remember', 'let me check'],
                    'next_stage': 'alternative_valuation'
                },
                'fallback': {
                    'next_stage': 'property_followup'
                }
            }
        },
        'property_followup': {
            'message': "Great! Based on recent sales in your neighborhood for similar properties, your home might be worth between $300,000 and $350,000. Would you be interested in a free, no-obligation professional valuation to get a more precise figure?",
            'responses': {
                'positive': {
                    'patterns': ['yes', 'yeah', 'sure', 'interested', 'tell me more', 'sounds good'],
                    'next_stage': 'schedule_valuation'
                },
                'negative': {
                    'patterns': ['no', 'not interested', 'no thanks'],
                    'next_stage': 'soft_close'
                },
                'question': {
                    'patterns': ['how does it work', 'what\'s involved', 'do i need to', 'what do you need', 'what is the process'],
                    'next_stage': 'explain_valuation'
                },
                'fallback': {
                    'next_stage': 'soft_close'
                }
            }
        },
        'alternative_valuation': {
            'message': "No problem! Even without specific details, we can still provide a general estimate for your area. Based on market trends, homes in your neighborhood have been selling for an average of $325,000. Would you like a free, professional valuation for a more accurate figure?",
            'responses': {
                'positive': {
                    'patterns': ['yes', 'yeah', 'sure', 'interested', 'sounds good'],
                    'next_stage': 'schedule_valuation'
                },
                'negative': {
                    'patterns': ['no', 'not interested', 'no thanks'],
                    'next_stage': 'soft_close'
                },
                'fallback': {
                    'next_stage': 'soft_close'
                }
            }
        },
        'schedule_valuation': {
            'message': "Excellent! One of our senior agents who specializes in your neighborhood will call you to arrange the valuation. What would be a good time for them to reach out to you?",
            'responses': {
                'time_given': {
                    'patterns': ['morning', 'afternoon', 'evening', 'tomorrow', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday', 'weekend', 'weekday'],
                    'extract_info': {
                        'appointment_time': '(morning|afternoon|evening|monday|tuesday|wednesday|thursday|friday|saturday|sunday)'
                    },
                    'next_stage': 'closing_with_appointment'
                },
                'anytime': {
                    'patterns': ['anytime', 'whenever', 'any time', 'flexible', 'you choose'],
                    'next_stage': 'closing_with_appointment'
                },
                'fallback': {
                    'next_stage': 'closing_with_appointment'
                }
            }
        },
        'objection_handling': {
            'message': "I completely understand. Many homeowners are curious about their property\'s value even if they\'re not ready to sell right away. Our market analysis can be a valuable resource for future planning. Would you at least like to know what your home might be worth in today\'s market?",
            'responses': {
                'positive': {
                    'patterns': ['yes', 'okay', 'i guess', 'sure', 'why not', 'that\'s fine'],
                    'next_stage': 'property_details'
                },
                'still_negative': {
                    'patterns': ['no', 'not interested', 'no thanks', 'stop calling'],
                    'next_stage': 'polite_end'
                },
                'fallback': {
                    'next_stage': 'soft_close'
                }
            }
        },
        'closing_with_appointment': {
            'message': "Perfect! I've noted that you're available {appointment_time}. Our agent {agent_name} will call you to confirm and answer any questions you might have. They'll also email you some recent sales data for your neighborhood. Is there anything else you'd like to know before we wrap up?",
            'responses': {
                'question': {
                    'patterns': ['yes', 'actually', 'question', 'want to know', 'tell me', 'explain'],
                    'next_stage': 'answer_final_question'
                },
                'no_question': {
                    'patterns': ['no', 'that\'s all', 'nothing', 'we\'re good', 'sounds good', 'thanks'],
                    'next_stage': 'final_goodbye'
                },
                'fallback': {
                    'next_stage': 'final_goodbye'
                }
            }
        },
        'explain_valuation': {
            'message': "Our professional valuation is completely free and no-obligation. One of our experienced agents will visit your property for about 30 minutes to assess its features and condition. They'll then prepare a detailed report with a recommended listing price based on recent comparable sales in your area. Would you like to schedule this free valuation?",
            'responses': {
                'positive': {
                    'patterns': ['yes', 'okay', 'sure', 'sounds good', 'interested'],
                    'next_stage': 'schedule_valuation'
                },
                'negative': {
                    'patterns': ['no', 'not interested', 'no thanks'],
                    'next_stage': 'soft_close'
                },
                'fallback': {
                    'next_stage': 'soft_close'
                }
            }
        },
        'answer_final_question': {
            'message': "I'd be happy to help with any questions. Our agent will be able to provide more specific details when they call you. They'll have access to the latest market data and can explain our selling process in detail. Is there anything specific you'd like me to note for them to address?",
            'responses': {
                'yes': {
                    'patterns': ['yes', 'there is', 'actually', 'question', 'want to know'],
                    'next_stage': 'note_question'
                },
                'no': {
                    'patterns': ['no', 'that\'s all', 'nothing', 'that\'s fine', 'thanks'],
                    'next_stage': 'final_goodbye'
                },
                'fallback': {
                    'next_stage': 'final_goodbye'
                }
            }
        },
        'note_question': {
            'message': "I've made a note of your question. Our agent will be sure to address this when they call. Thank you for your time today, and we look forward to helping you with your real estate needs.",
            'end_call': True
        },
        'soft_close': {
            'message': "I understand. Real estate decisions are important and personal. If you ever change your mind or have questions about the market in your area, please don't hesitate to contact our office at {office_phone}. Would it be okay if we send you some information about recent sales in your neighborhood for your reference?",
            'responses': {
                'positive': {
                    'patterns': ['yes', 'sure', 'okay', 'that\'s fine', 'send it'],
                    'next_stage': 'info_send_confirmation'
                },
                'negative': {
                    'patterns': ['no', 'don\'t send', 'no thanks', 'not necessary'],
                    'next_stage': 'final_goodbye'
                },
                'fallback': {
                    'next_stage': 'final_goodbye'
                }
            }
        },
        'info_send_confirmation': {
            'message': "Perfect! We'll email that information to you shortly. Thank you for your time today, and please don't hesitate to reach out if you have any questions in the future.",
            'end_call': True
        },
        'polite_end': {
            'message': "I understand completely. Thank you for your time today. Have a wonderful day!",
            'end_call': True
        },
        'final_goodbye': {
            'message': "Thank you for your time today. It was a pleasure speaking with you. If you have any questions in the future, our office number is {office_phone}. Have a great day!",
            'end_call': True
        },
        'clarify': {
            'message': "I'm sorry if I wasn't clear. I was calling because we've been helping homeowners in your area sell their properties, and I wanted to know if you've thought about selling your home in the near future?",
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
                    'next_stage': 'objection_handling'
                }
            }
        },
        'answer_question': {
            'message': "I'm {agent_name} calling from {company_name}. We're a real estate agency that specializes in your neighborhood. We've been helping homeowners get great prices for their properties, and I was wondering if you've thought about selling your home?",
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
                    'next_stage': 'objection_handling'
                }
            }
        }
    },
    'context_variables': {
        'agent_name': 'Matthew Wilson',
        'company_name': 'Premier Real Estate',
        'office_phone': '(555) 123-4567',
        'estimated_min_value': '$300,000',
        'estimated_max_value': '$350,000',
        'appointment_time': 'tomorrow afternoon'
    },
    'fallback_responses': [
        "I'm sorry, I didn't quite catch that. Could you please repeat?",
        "Would you mind rephrasing that? I want to make sure I understand correctly.",
        "I apologize, but I'm having trouble understanding. Could you say that again more clearly?"
    ]
}

# Advanced conversation flow script for mortgage
MORTGAGE_SCRIPT_ADVANCED = {
    'name': 'Advanced Mortgage Refinance Lead Generation',
    'industry': 'mortgage',
    'conversation_flow': {
        'greeting': {
            'message': "Hello, this is {agent_name} from {company_name}. With interest rates at {interest_rate_descriptor}, many homeowners in your area are saving {savings_amount} each month by refinancing. Based on current rates, you might qualify for significant savings on your mortgage. Would you be interested in learning what options are available to you?",
            'responses': {
                'positive': {
                    'patterns': ['yes', 'yeah', 'sure', 'interested', 'tell me more', 'possibly', 'maybe', 'what options'],
                    'next_stage': 'current_mortgage'
                },
                'negative': {
                    'patterns': ['no', 'not interested', 'no thanks', 'don\'t need', 'not now', 'wrong number'],
                    'next_stage': 'objection_handling'
                },
                'question': {
                    'patterns': ['who are you', 'what company', 'why are you calling', 'how did you get my number'],
                    'next_stage': 'answer_question'
                },
                'fallback': {
                    'next_stage': 'clarify'
                }
            }
        },
        'current_mortgage': {
            'message': "Great! To help us find the best options for you, could you tell me a little about your current mortgage? What's your approximate interest rate?",
            'responses': {
                'has_details': {
                    'patterns': ['percent', '%', 'rate', 'interest', 'apr'],
                    'extract_info': {
                        'interest_rate': '\\b(\\d+(?:\\.\\d+)?)\\s*(?:percent|%)\\b'
                    },
                    'next_stage': 'mortgage_followup'
                },
                'no_details': {
                    'patterns': ['not sure', 'don\'t know', 'i don\'t remember', 'let me check', 'would have to look'],
                    'next_stage': 'alternative_approach'
                },
                'fallback': {
                    'next_stage': 'mortgage_followup'
                }
            }
        },
        'mortgage_followup': {
            'message': "Thank you for sharing that information. Based on current rates, you might be able to refinance at {new_rate}%, which could save you approximately {monthly_savings} per month. Would you like to speak with one of our mortgage advisors to get a personalized quote?",
            'responses': {
                'positive': {
                    'patterns': ['yes', 'sure', 'interested', 'tell me more', 'sounds good'],
                    'next_stage': 'schedule_call'
                },
                'negative': {
                    'patterns': ['no', 'not interested', 'no thanks'],
                    'next_stage': 'soft_close'
                },
                'question': {
                    'patterns': ['how does it work', 'what\'s involved', 'do i need to', 'what do you need', 'what is the process', 'how long does it take'],
                    'next_stage': 'explain_process'
                },
                'fallback': {
                    'next_stage': 'soft_close'
                }
            }
        },
        'alternative_approach': {
            'message': "No problem! Many homeowners aren't sure about their exact rate. Our mortgage advisors can look up current rates and compare them to what you might qualify for. Would you like one of our advisors to give you a call to discuss potential savings?",
            'responses': {
                'positive': {
                    'patterns': ['yes', 'sure', 'okay', 'interested', 'sounds good'],
                    'next_stage': 'schedule_call'
                },
                'negative': {
                    'patterns': ['no', 'not interested', 'no thanks'],
                    'next_stage': 'soft_close'
                },
                'fallback': {
                    'next_stage': 'soft_close'
                }
            }
        },
        'objection_handling': {
            'message': "I understand. Many homeowners initially think refinancing might not be worth it, but with today's rates, even a small reduction can save thousands over the life of your loan. Would you at least like to know what rate you might qualify for, with no obligation?",
            'responses': {
                'positive': {
                    'patterns': ['yes', 'okay', 'i guess', 'sure', 'why not', 'that\'s fine'],
                    'next_stage': 'current_mortgage'
                },
                'still_negative': {
                    'patterns': ['no', 'not interested', 'no thanks', 'stop calling'],
                    'next_stage': 'polite_end'
                },
                'fallback': {
                    'next_stage': 'soft_close'
                }
            }
        },
        'schedule_call': {
            'message': "Great! What would be a good time for one of our mortgage specialists to give you a call with more information?",
            'responses': {
                'time_given': {
                    'patterns': ['morning', 'afternoon', 'evening', 'tomorrow', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday', 'weekend', 'weekday'],
                    'extract_info': {
                        'appointment_time': '(morning|afternoon|evening|monday|tuesday|wednesday|thursday|friday|saturday|sunday)'
                    },
                    'next_stage': 'closing_with_appointment'
                },
                'anytime': {
                    'patterns': ['anytime', 'whenever', 'any time', 'flexible', 'you choose'],
                    'next_stage': 'closing_with_appointment'
                },
                'fallback': {
                    'next_stage': 'closing_with_appointment'
                }
            }
        },
        'closing_with_appointment': {
            'message': "Perfect! I've noted that you're available {appointment_time}. Our mortgage specialist will call you then to provide you with personalized refinance options and answer any questions you might have. Is there anything specific you'd like them to prepare for the call?",
            'responses': {
                'yes': {
                    'patterns': ['yes', 'actually', 'question', 'want to know', 'tell me', 'explain'],
                    'next_stage': 'note_question'
                },
                'no': {
                    'patterns': ['no', 'that\'s all', 'nothing', 'that\'s fine', 'thanks'],
                    'next_stage': 'final_goodbye'
                },
                'fallback': {
                    'next_stage': 'final_goodbye'
                }
            }
        },
        'explain_process': {
            'message': "The refinance process is quite straightforward. Our mortgage advisors will review your current loan details, check current rates you qualify for, and provide options that could save you money. There's no obligation, and the initial consultation is completely free. Would you like to speak with one of our specialists?",
            'responses': {
                'positive': {
                    'patterns': ['yes', 'okay', 'sure', 'sounds good', 'interested'],
                    'next_stage': 'schedule_call'
                },
                'negative': {
                    'patterns': ['no', 'not interested', 'no thanks'],
                    'next_stage': 'soft_close'
                },
                'fallback': {
                    'next_stage': 'soft_close'
                }
            }
        },
        'soft_close': {
            'message': "I understand. Mortgage decisions are important and personal. If you change your mind or have questions about refinancing in the future, please don't hesitate to contact our office at {office_phone}. Would it be okay if we send you some information about current rates and refinancing options for your reference?",
            'responses': {
                'positive': {
                    'patterns': ['yes', 'sure', 'okay', 'that\'s fine', 'send it'],
                    'next_stage': 'info_send_confirmation'
                },
                'negative': {
                    'patterns': ['no', 'don\'t send', 'no thanks', 'not necessary'],
                    'next_stage': 'final_goodbye'
                },
                'fallback': {
                    'next_stage': 'final_goodbye'
                }
            }
        },
        'info_send_confirmation': {
            'message': "Perfect! We'll email that information to you shortly. Thank you for your time today, and please don't hesitate to reach out if you have any questions in the future.",
            'end_call': True
        },
        'polite_end': {
            'message': "I understand completely. Thank you for your time today. Have a wonderful day!",
            'end_call': True
        },
        'final_goodbye': {
            'message': "Thank you for your time today. It was a pleasure speaking with you. If you have any questions in the future, our office number is {office_phone}. Have a great day!",
            'end_call': True
        },
        'note_question': {
            'message': "I've made a note of your question. Our mortgage specialist will be sure to address this when they call. Thank you for your time today, and we look forward to helping you explore your refinancing options.",
            'end_call': True
        },
        'clarify': {
            'message': "I'm sorry if I wasn't clear. I was calling about potentially saving you money on your mortgage through refinancing. With current rates, many homeowners are saving significantly. Would you be interested in learning more?",
            'responses': {
                'positive': {
                    'patterns': ['yes', 'yeah', 'sure', 'tell me more', 'interested'],
                    'next_stage': 'current_mortgage'
                },
                'negative': {
                    'patterns': ['no', 'not interested', 'no thanks'],
                    'next_stage': 'objection_handling'
                },
                'fallback': {
                    'next_stage': 'objection_handling'
                }
            }
        },
        'answer_question': {
            'message': "I'm {agent_name} calling from {company_name}. We're a mortgage company that specializes in helping homeowners save money through refinancing. With today's rates, many people are able to lower their monthly payments significantly. I was wondering if you'd be interested in learning about your options?",
            'responses': {
                'positive': {
                    'patterns': ['yes', 'yeah', 'sure', 'tell me more', 'interested'],
                    'next_stage': 'current_mortgage'
                },
                'negative': {
                    'patterns': ['no', 'not interested', 'no thanks'],
                    'next_stage': 'objection_handling'
                },
                'fallback': {
                    'next_stage': 'objection_handling'
                }
            }
        }
    },
    'context_variables': {
        'agent_name': 'Sarah Johnson',
        'company_name': 'First Choice Mortgage',
        'interest_rate_descriptor': 'historic lows',
        'savings_amount': 'hundreds',
        'new_rate': '3.2',
        'monthly_savings': '$200 to $400',
        'office_phone': '(555) 456-7890',
        'appointment_time': 'tomorrow afternoon'
    },
    'fallback_responses': [
        "I'm sorry, I didn't quite catch that. Could you please repeat?",
        "Would you mind rephrasing that? I want to make sure I understand correctly.",
        "I apologize, but I'm having trouble understanding. Could you say that again more clearly?"
    ]
}

# Dictionary of all advanced campaigns
ADVANCED_CAMPAIGNS = {
    'advanced_real_estate': REAL_ESTATE_SCRIPT_ADVANCED,
    'advanced_mortgage': MORTGAGE_SCRIPT_ADVANCED
}

# Actual campaign configurations with template variables populated
CAMPAIGN_SCRIPTS = {
    'campaign_001': {
        'name': 'Premier Real Estate Lead Generation',
        'industry': 'real_estate',
        'template_variables': {
            'agent_name': 'Matthew from Premier Real Estate',
            'company_name': 'Premier Real Estate',
            'custom_opening_question': 'I was wondering - have you thought about selling your home in the near future?',
            'unique_value_prop': 'our team of local market experts who\'ve helped sellers in your area get an average of 5% above market value',
            'key_benefit': 'get an average of 5% above market value',
            'offer_type': 'recent sales in your neighborhood',
            'follow_up_action': 'I\'ll have our team send over our market report with recent sales in your area',
            'next_steps': 'helping you make an informed decision about your home'
        }
    },
    'campaign_002': {
        'name': 'First Choice Mortgage Refinance',
        'industry': 'mortgage',
        'template_variables': {
            'agent_name': 'Sarah',
            'company_name': 'First Choice Mortgage',
            'interest_rate_descriptor': 'historic lows',
            'savings_amount': 'hundreds',
            'custom_opening_question': 'Would you be interested in learning what options are available to you?',
            'promotion_details': 'no-cost refinance options with rates starting at just 3.2% APR',
            'client_benefit': 'reducing their monthly payments by $200 to $400',
            'service_offered': 'a quick estimate based on your current mortgage details',
            'follow_up_action': 'I\'ll have one of our mortgage advisors give you a call within the next 24 hours to discuss your specific situation and provide personalized options',
            'next_steps': 'helping you save on your mortgage'
        }
    },
    'campaign_003': {
        'name': 'Green Gardens Spring Services',
        'industry': 'landscaping',
        'template_variables': {
            'agent_name': 'Michael',
            'company_name': 'Green Gardens Landscaping',
            'season': 'spring',
            'promotion_details': 'special deals on landscaping services',
            'custom_opening_question': 'Have you been thinking about upgrading your outdoor space this season?',
            'service_types': 'lawn renovation, garden design, and outdoor living spaces',
            'offer_details': 'a 15% discount for first-time customers',
            'social_proof': 'Many of your neighbors have been amazed by the transformation we\'ve created',
            'call_to_action': 'schedule a free consultation',
            'follow_up_action': 'We\'ll send you some design ideas and have one of our specialists contact you to schedule your free consultation',
            'next_steps': 'discuss your landscaping vision'
        }
    }
}

def render_script(template, variables):
    """
    Render a script template with the given variables
    
    Args:
        template (str): The template string
        variables (dict): Dictionary of variables to insert into the template
        
    Returns:
        str: The rendered script
    """
    try:
        return template.format(**variables)
    except KeyError as e:
        logger.error(f"Missing template variable: {e}")
        # Return template with missing variables marked
        return template.format(**{**variables, **{str(e).strip("'"): f"[MISSING: {e}]"}})
    except Exception as e:
        logger.error(f"Error rendering template: {e}")
        return template

def get_script(campaign_id, default_id='advanced_real_estate'):
    """
    Get a script by campaign ID
    
    Args:
        campaign_id: The campaign identifier
        default_id: Default campaign to use if requested one doesn't exist
        
    Returns:
        dict: The script for the specified campaign
    """
    # Check if we have this campaign in our advanced campaigns
    if campaign_id in ADVANCED_CAMPAIGNS:
        # Create a deep copy of the script to avoid modifying the original
        script = copy.deepcopy(ADVANCED_CAMPAIGNS[campaign_id])
        
        # Process the template variables in all messages
        variables = script['context_variables']
        for stage_key, stage_data in script['conversation_flow'].items():
            if 'message' in stage_data:
                # Apply template variables to each message
                message = stage_data['message']
                for var_name, var_value in variables.items():
                    placeholder = f"{{{var_name}}}"
                    if placeholder in message:
                        message = message.replace(placeholder, str(var_value))
                stage_data['message'] = message
        
        return script
    
    # Fall back to default advanced campaign if requested one doesn't exist
    return get_script(default_id) if campaign_id != default_id else ADVANCED_CAMPAIGNS[default_id]

def create_campaign(campaign_id, name, industry, template_variables):
    """
    Create a new campaign with the specified parameters
    
    Args:
        campaign_id (str): Unique campaign identifier
        name (str): Campaign name
        industry (str): Industry template to use
        template_variables (dict): Variables to populate the template
        
    Returns:
        bool: True if campaign was created successfully
    """
    if industry not in INDUSTRY_TEMPLATES:
        logger.error(f"Unknown industry: {industry}")
        return False
    
    # Create the campaign configuration
    CAMPAIGN_SCRIPTS[campaign_id] = {
        'name': name,
        'industry': industry,
        'template_variables': template_variables
    }
    
    logger.info(f"Created campaign {campaign_id}: {name}")
    return True

def get_all_campaigns():
    """
    Get a list of all available campaigns
    
    Returns:
        list: List of campaign details
    """
    campaigns = []
    
    # Add all advanced campaigns
    for campaign_id, script in ADVANCED_CAMPAIGNS.items():
        campaigns.append({
            'id': campaign_id,
            'name': script['name'],
            'industry': script['industry']
        })
    
    # Add all regular campaigns 
    for campaign_id, config in CAMPAIGN_SCRIPTS.items():
        campaigns.append({
            'id': campaign_id,
            'name': config['name'],
            'industry': config['industry']
        })
    
    return campaigns

def get_industries():
    """
    Get a list of all available industry templates
    
    Returns:
        list: List of industry identifiers and names
    """
    return [
        {
            'id': industry_id,
            'name': template['name']
        }
        for industry_id, template in INDUSTRY_TEMPLATES.items()
    ]

def get_industry_template(industry_id):
    """
    Get the template for a specific industry
    
    Args:
        industry_id (str): Industry identifier
        
    Returns:
        dict: Industry template or None if not found
    """
    return INDUSTRY_TEMPLATES.get(industry_id)