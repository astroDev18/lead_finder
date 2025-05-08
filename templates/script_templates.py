"""
Script templates for voice calls.
Contains all the campaign scripts that can be used in calls.
Uses a template-based system that can be easily adapted for any industry.
"""
import json
import logging

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
        'name': 'Real Estate Lead Generation',
        'greeting': "Hi there! <break time='300ms'/> This is {agent_name} from {company_name}. I hope I caught you at a good time. <break time='500ms'/> We've been helping homeowners <emphasis level='moderate'>just like you</emphasis> in your neighborhood sell their properties for <emphasis level='moderate'>top dollar</emphasis>. {custom_opening_question}",
        
        'more_info': "I'm glad to hear that. What makes our approach different is {unique_value_prop}. We've helped clients in your area {key_benefit}. Would you like to receive more information about {offer_type}?",
        
        'closing': "Perfect! {follow_up_action}. Thanks for your time today, and we look forward to {next_steps}.",
        
        'no_answer': "We're sorry we missed you. {company_name} has been helping homeowners in your area sell their properties for top dollar. If you're interested in a free home valuation or would like information about the real estate market in your neighborhood, please call us back at our office number. Thank you and have a great day.",
        
        'negative_response': "No problem at all. Thank you for your time. Have a great day!",
        
        'unclear_response': "I'm sorry, I didn't understand your response. Could you please say 'yes' if you're interested or 'no' if you're not?",
        
        'no_speech': "I didn't hear your response. Could you please say 'yes' if you're interested or 'no' if you're not?",
        
        'fallback': "I didn't catch that. Thank you for your time today. Feel free to reach out if you have any questions in the future."
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
    }
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

def get_script(campaign_id, default_id='campaign_001'):
    """
    Get a rendered script by campaign ID with fallback to default
    
    Args:
        campaign_id (str): The campaign identifier
        default_id (str): Default campaign to use if requested one doesn't exist
        
    Returns:
        dict: The rendered script for the specified campaign
    """
    # Get the campaign config or default to campaign_001
    campaign_config = CAMPAIGN_SCRIPTS.get(campaign_id, CAMPAIGN_SCRIPTS[default_id])
    
    # Get the industry template
    industry = campaign_config['industry']
    industry_template = INDUSTRY_TEMPLATES.get(industry, INDUSTRY_TEMPLATES['real_estate'])
    
    # Get the template variables
    template_variables = campaign_config['template_variables']
    
    # Render each script component
    rendered_script = {
        'name': campaign_config['name'],
        'industry': industry
    }
    
    for component in SCRIPT_COMPONENTS:
        if component in industry_template:
            template = industry_template[component]
            rendered_script[component] = render_script(template, template_variables)
    
    return rendered_script

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
    return [
        {
            'id': campaign_id,
            'name': script['name'],
            'industry': script['industry']
        }
        for campaign_id, script in CAMPAIGN_SCRIPTS.items()
    ]

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