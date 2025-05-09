# services/db_helper.py
import logging
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

# This will be our placeholder until we implement the actual database service
class SimpleDatabaseService:
    def __init__(self):
        logger.info("Initializing simple database service")
        self.calls = {}
        self.contacts = {}
    
    def save_call(self, call_sid, call_data):
        """Simple method to save call data"""
        self.calls[call_sid] = call_data
        logger.info(f"Saved call data for {call_sid}")
        return call_data
    
    def get_call(self, call_sid):
        """Get call data by SID"""
        return self.calls.get(call_sid)
    
    def save_contact(self, phone_number, contact_data):
        """Save contact information"""
        self.contacts[phone_number] = contact_data
        logger.info(f"Saved contact data for {phone_number}")
        return contact_data
    
    def get_contact_by_phone(self, phone_number):
        """Get contact by phone number"""
        return self.contacts.get(phone_number)

# Singleton instance
_db_service = None

def get_db_service():
    """Get database service instance"""
    global _db_service
    if _db_service is None:
        _db_service = SimpleDatabaseService()
    return _db_service
