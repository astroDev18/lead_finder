# services/__init__.py
# Check if these imports exist, and comment them out if needed
# from services.twilio_service import init_twilio_client
# from services.dialogflow_service import init_dialogflow_client
# from services.storage_service import init_storage
# from services.campaign_service import init_campaign_manager

def init_services(app):
    """Initialize all service dependencies"""
    # Initialize storage first
    try:
        from services.storage_service import init_storage
        storage = init_storage()
    except (ImportError, AttributeError):
        # If init_storage doesn't exist, create a simple version
        import logging
        logger = logging.getLogger(__name__)
        logger.warning("init_storage not found, using empty dict")
        storage = {}
    
    # Initialize other clients
    try:
        from services.campaign_service import init_campaign_manager
        campaign_manager = init_campaign_manager()
    except (ImportError, AttributeError):
        campaign_manager = None
    
    try:
        from services.twilio_service import init_twilio_client
        twilio_client = init_twilio_client()
    except (ImportError, AttributeError):
        twilio_client = None
    
    try:
        from services.dialogflow_service import init_dialogflow_client
        dialogflow_client = init_dialogflow_client()
    except (ImportError, AttributeError):
        dialogflow_client = None
    
    # Initialize database service
    try:
        from services.db_helper import get_db_service
        db_service = get_db_service()
    except (ImportError, AttributeError):
        db_service = None
    
    # Make services available to the application context
    if app:
        app.config['CAMPAIGN_MANAGER'] = campaign_manager
        app.config['TWILIO_CLIENT'] = twilio_client
        app.config['DIALOGFLOW_CLIENT'] = dialogflow_client
        app.config['STORAGE'] = storage
        app.config['DB_SERVICE'] = db_service
    
    return app