# Modified services/__init__.py without Twilio
from services.storage_service import init_storage
from services.campaign_service import init_campaign_manager

def init_services(app):
    """Initialize all service dependencies"""
    # Initialize clients
    campaign_manager = init_campaign_manager()
    storage = init_storage()
    
    # Initialize database service
    from services.db_helper import get_db_service
    db_service = get_db_service()
    
    # Make services available to the application context
    app.config['CAMPAIGN_MANAGER'] = campaign_manager
    app.config['STORAGE'] = storage
    app.config['DB_SERVICE'] = db_service
    
    return app