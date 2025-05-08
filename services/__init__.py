from services.twilio_service import init_twilio_client
from services.dialogflow_service import init_dialogflow_client
from services.storage_service import init_storage
from services.campaign_service import init_campaign_manager

def init_services(app):
    """Initialize all service dependencies"""
    # Initialize clients
    campaign_manager = init_campaign_manager()
    twilio_client = init_twilio_client()
    dialogflow_client = init_dialogflow_client()
    storage = init_storage()
    
    # Make services available to the application context



    app.config['CAMPAIGN_MANAGER'] = campaign_manager
    app.config['TWILIO_CLIENT'] = twilio_client
    app.config['DIALOGFLOW_CLIENT'] = dialogflow_client
    app.config['STORAGE'] = storage
    
    return app