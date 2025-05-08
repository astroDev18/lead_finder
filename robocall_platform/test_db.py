# test_db.py
from database import SessionLocal, engine, Base
from services.db_service import DatabaseService
import models

def create_test_data():
    """Create some test data to verify database setup"""
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    # Create a database session
    db = SessionLocal()
    db_service = DatabaseService(db)
    
    try:
        # Create a test campaign
        campaign_data = {
            'name': 'Test Real Estate Campaign',
            'industry': 'real_estate',
            'script_template': {
                'greeting': 'Hello, this is {agent_name} from {company_name}. I wanted to discuss your property at {address}.',
                'more_info': 'We have a great opportunity for you to sell your property at a premium price.',
                'closing': 'Thank you for your time. We look forward to working with you.'
            },
            'sms_templates': {
                'follow_up': 'Hi {first_name}, thank you for speaking with us about your property. Would you like more information?',
                'appointment_reminder': 'Reminder: Your appointment with {agent_name} is tomorrow at {time}.'
            }
        }
        
        campaign = db_service.create_campaign(campaign_data)
        print(f"Created campaign: ID={campaign.campaign_id}, Name={campaign.name}")
        
        # Create a test contact
        contact_data = {
            'phone_number': '+18162039617',
            'email': 'test@example.com',
            'first_name': 'John',
            'last_name': 'Doe',
            'source_campaign': campaign.campaign_id,
            'lead_score': 75,
            'lead_status': 'qualified',
            'custom_fields': {
                'property_type': 'Single Family Home',
                'bedrooms': '4',
                'bathrooms': '2.5',
                'square_feet': '2500',
                'interested_in': 'selling'
            }
        }
        
        contact = db_service.create_contact(contact_data)
        print(f"Created contact: ID={contact.contact_id}, Name={contact.first_name} {contact.last_name}")
        
        # Create a test call
        call_data = {
            'contact_id': contact.contact_id,
            'campaign_id': campaign.campaign_id,
            'call_sid': 'CA12345678',
            'status': 'completed',
            'duration': 240,  # 4 minutes
            'transcript': 'Agent: Hello, this is John from Real Estate Company.\nCustomer: Hi, I am interested in selling my house.'
        }
        
        call = db_service.create_call(call_data)
        print(f"Created call: ID={call.call_id}, Status={call.status}")
        
        # Create a test SMS
        sms_data = {
            'contact_id': contact.contact_id,
            'campaign_id': campaign.campaign_id,
            'message_sid': 'SM12345678',
            'message_body': 'Hi John, thank you for your interest in our services. When would be a good time to call?',
            'direction': 'outbound',
            'status': 'delivered'
        }
        
        sms = db_service.create_sms(sms_data)
        print(f"Created SMS: ID={sms.message_id}, Status={sms.status}")
        
        # Verify we can retrieve the data
        retrieved_contact = db_service.get_contact_by_id(contact.contact_id)
        print(f"Retrieved contact: {retrieved_contact.first_name} {retrieved_contact.last_name}")
        print("Custom fields:")
        for field in retrieved_contact.custom_data:
            print(f"  {field.field_name}: {field.field_value}")
        
        print("\nDatabase test completed successfully!")
    
    finally:
        db.close()

if __name__ == "__main__":
    create_test_data()
