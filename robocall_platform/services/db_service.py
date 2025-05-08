# services/db_service.py
from sqlalchemy.orm import Session
from typing import Dict, List, Optional, Any
import models
import uuid
from datetime import datetime

class DatabaseService:
    def __init__(self, db_session: Session):
        self.db = db_session
    
    # Contact methods
    def create_contact(self, contact_data: Dict[str, Any]) -> models.Contact:
        """Create a new contact"""
        contact = models.Contact(
            contact_id=str(uuid.uuid4()),
            phone_number=contact_data.get('phone_number'),
            email=contact_data.get('email'),
            first_name=contact_data.get('first_name'),
            last_name=contact_data.get('last_name'),
            source_campaign=contact_data.get('source_campaign'),
            lead_score=contact_data.get('lead_score', 0),
            lead_status=contact_data.get('lead_status', 'new')
        )
        
        self.db.add(contact)
        self.db.commit()
        self.db.refresh(contact)
        
        # Add any custom fields to lead_data
        custom_fields = contact_data.get('custom_fields', {})
        for field_name, field_value in custom_fields.items():
            lead_data = models.LeadData(
                lead_data_id=str(uuid.uuid4()),
                contact_id=contact.contact_id,
                field_name=field_name,
                field_value=str(field_value)
            )
            self.db.add(lead_data)
        
        self.db.commit()
        return contact
    
    def get_contact_by_id(self, contact_id: str) -> Optional[models.Contact]:
        """Get a contact by ID"""
        return self.db.query(models.Contact).filter(models.Contact.contact_id == contact_id).first()
    
    def get_contact_by_phone(self, phone_number: str) -> Optional[models.Contact]:
        """Get a contact by phone number"""
        return self.db.query(models.Contact).filter(models.Contact.phone_number == phone_number).first()
    
    def update_contact(self, contact_id: str, contact_data: Dict[str, Any]) -> Optional[models.Contact]:
        """Update a contact's information"""
        contact = self.get_contact_by_id(contact_id)
        if not contact:
            return None
        
        # Update basic fields
        for key, value in contact_data.items():
            if key != 'custom_fields' and hasattr(contact, key):
                setattr(contact, key, value)
        
        # Update custom fields
        custom_fields = contact_data.get('custom_fields', {})
        for field_name, field_value in custom_fields.items():
            # Check if field already exists
            lead_data = self.db.query(models.LeadData).filter(
                models.LeadData.contact_id == contact_id,
                models.LeadData.field_name == field_name
            ).first()
            
            if lead_data:
                # Update existing field
                lead_data.field_value = str(field_value)
                lead_data.updated_at = datetime.now()
            else:
                # Create new field
                lead_data = models.LeadData(
                    lead_data_id=str(uuid.uuid4()),
                    contact_id=contact_id,
                    field_name=field_name,
                    field_value=str(field_value)
                )
                self.db.add(lead_data)
        
        self.db.commit()
        self.db.refresh(contact)
        return contact
    
    # Campaign methods
    def create_campaign(self, campaign_data: Dict[str, Any]) -> models.Campaign:
        """Create a new campaign"""
        campaign = models.Campaign(
            campaign_id=str(uuid.uuid4()),
            name=campaign_data.get('name'),
            industry=campaign_data.get('industry'),
            script_template=campaign_data.get('script_template'),
            sms_templates=campaign_data.get('sms_templates'),
            active_status=campaign_data.get('active_status', True)
        )
        
        self.db.add(campaign)
        self.db.commit()
        self.db.refresh(campaign)
        return campaign
    
    def get_campaign_by_id(self, campaign_id: str) -> Optional[models.Campaign]:
        """Get a campaign by ID"""
        return self.db.query(models.Campaign).filter(models.Campaign.campaign_id == campaign_id).first()
    
    def get_active_campaigns(self) -> List[models.Campaign]:
        """Get all active campaigns"""
        return self.db.query(models.Campaign).filter(models.Campaign.active_status == True).all()
    
    # Call methods
    def create_call(self, call_data: Dict[str, Any]) -> models.Call:
        """Create a new call record"""
        call = models.Call(
            call_id=str(uuid.uuid4()),
            contact_id=call_data.get('contact_id'),
            campaign_id=call_data.get('campaign_id'),
            call_sid=call_data.get('call_sid'),
            status=call_data.get('status', 'pending'),
            call_date=datetime.now()
        )
        
        self.db.add(call)
        self.db.commit()
        self.db.refresh(call)
        return call
    
    def update_call(self, call_id: str, call_data: Dict[str, Any]) -> Optional[models.Call]:
        """Update a call record"""
        call = self.db.query(models.Call).filter(models.Call.call_id == call_id).first()
        if not call:
            return None
        
        for key, value in call_data.items():
            if hasattr(call, key):
                setattr(call, key, value)
        
        self.db.commit()
        self.db.refresh(call)
        return call
    
    # SMS methods
    def create_sms(self, sms_data: Dict[str, Any]) -> models.SMSMessage:
        """Create a new SMS message record"""
        sms = models.SMSMessage(
            message_id=str(uuid.uuid4()),
            contact_id=sms_data.get('contact_id'),
            campaign_id=sms_data.get('campaign_id'),
            message_sid=sms_data.get('message_sid'),
            message_body=sms_data.get('message_body'),
            direction=sms_data.get('direction'),
            status=sms_data.get('status', 'pending'),
            template_id=sms_data.get('template_id')
        )
        
        self.db.add(sms)
        self.db.commit()
        self.db.refresh(sms)
        return sms
    
    def get_contact_sms_history(self, contact_id: str) -> List[models.SMSMessage]:
        """Get SMS history for a contact"""
        return self.db.query(models.SMSMessage).filter(
            models.SMSMessage.contact_id == contact_id
        ).order_by(models.SMSMessage.sent_at).all()
