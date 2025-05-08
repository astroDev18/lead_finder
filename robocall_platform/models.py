# models.py
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base
import uuid
from datetime import datetime

class Contact(Base):
    __tablename__ = "contacts"
    
    contact_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    phone_number = Column(String(20), nullable=False, index=True)
    email = Column(String(255), nullable=True, index=True)
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    source_campaign = Column(String(36), ForeignKey("campaigns.campaign_id"), nullable=True)
    lead_score = Column(Integer, default=0)
    lead_status = Column(String(50), default="new")
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    calls = relationship("Call", back_populates="contact")
    messages = relationship("SMSMessage", back_populates="contact")
    custom_data = relationship("LeadData", back_populates="contact")

class Call(Base):
    __tablename__ = "calls"
    
    call_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    contact_id = Column(String(36), ForeignKey("contacts.contact_id"), nullable=False, index=True)
    campaign_id = Column(String(36), ForeignKey("campaigns.campaign_id"), nullable=True, index=True)
    call_sid = Column(String(100), nullable=True)
    duration = Column(Integer, default=0)  # in seconds
    status = Column(String(50), default="pending")
    recording_url = Column(String(255), nullable=True)
    transcript = Column(Text, nullable=True)
    call_date = Column(DateTime, default=func.now())
    agent_notes = Column(Text, nullable=True)
    
    # Relationships
    contact = relationship("Contact", back_populates="calls")
    campaign = relationship("Campaign", back_populates="calls")

class SMSMessage(Base):
    __tablename__ = "sms_messages"
    
    message_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    contact_id = Column(String(36), ForeignKey("contacts.contact_id"), nullable=False, index=True)
    campaign_id = Column(String(36), ForeignKey("campaigns.campaign_id"), nullable=True, index=True)
    message_sid = Column(String(100), nullable=True)
    message_body = Column(Text, nullable=False)
    direction = Column(String(10), nullable=False)  # "inbound" or "outbound"
    status = Column(String(50), default="pending")
    sent_at = Column(DateTime, default=func.now())
    template_id = Column(String(100), nullable=True)
    
    # Relationships
    contact = relationship("Contact", back_populates="messages")
    campaign = relationship("Campaign", back_populates="messages")

class Campaign(Base):
    __tablename__ = "campaigns"
    
    campaign_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    industry = Column(String(100), nullable=False, index=True)
    script_template = Column(JSON, nullable=True)
    sms_templates = Column(JSON, nullable=True)
    active_status = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    calls = relationship("Call", back_populates="campaign")
    messages = relationship("SMSMessage", back_populates="campaign")

class LeadData(Base):
    __tablename__ = "lead_data"
    
    lead_data_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    contact_id = Column(String(36), ForeignKey("contacts.contact_id"), nullable=False, index=True)
    field_name = Column(String(100), nullable=False)
    field_value = Column(Text, nullable=True)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    contact = relationship("Contact", back_populates="custom_data")
    
    # Composite index for efficient lookups by field name and value
    __table_args__ = (
        {'sqlite_autoincrement': True},
    )
