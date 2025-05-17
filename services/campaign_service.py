"""
Campaign management service for handling campaign operations.
"""
import logging
import json
from datetime import datetime

from templates.script_templates import (
    get_script, create_campaign, get_all_campaigns,
    get_industries, get_industry_template
)

# Set up logging
logger = logging.getLogger(__name__)

# Campaign manager instance (initialized lazily)
_campaign_manager = None

class CampaignManager:
    """Manager for campaign operations and storage"""
    
    def __init__(self):
        self.campaigns = {}
        self.campaign_stats = {}
        logger.info("Campaign manager initialized")
    
    def get_script(self, campaign_id, default_id='campaign_001'):
        """Get a rendered script for a campaign"""
        return get_script(campaign_id, default_id)
    
    def create_campaign(self, campaign_id, name, industry, template_variables):
        """Create a new campaign"""
        success = create_campaign(campaign_id, name, industry, template_variables)
        
        if success:
            # Initialize campaign statistics
            self.campaign_stats[campaign_id] = {
                'created_at': datetime.now().isoformat(),
                'call_count': 0,
                'success_count': 0,
                'failure_count': 0,
                'average_duration': 0,
                'reached_stages': {
                    'greeting': 0,
                    'more_info': 0,
                    'closing': 0,
                    'ended': 0
                }
            }
        
        return success
    
    def get_all_campaigns(self):
        """Get all available campaigns"""
        return get_all_campaigns()
    
    def get_campaign_stats(self, campaign_id):
        """Get statistics for a specific campaign"""
        return self.campaign_stats.get(campaign_id, None)
    
    def get_all_campaign_stats(self):
        """Get statistics for all campaigns"""
        return self.campaign_stats
    
    def update_campaign_stats(self, campaign_id, call_data):
        """Update campaign statistics based on call data"""
        if campaign_id not in self.campaign_stats:
            logger.warning(f"Attempted to update stats for unknown campaign: {campaign_id}")
            return False
        
        stats = self.campaign_stats[campaign_id]
        
        # Update call count
        stats['call_count'] += 1
        
        # Update success/failure counts
        if call_data.get('status') == 'completed':
            stats['success_count'] += 1
        elif call_data.get('status') in ['failed', 'busy', 'no-answer']:
            stats['failure_count'] += 1
        
        # Update stage counts
        final_stage = call_data.get('final_stage', 'greeting')
        if final_stage in stats['reached_stages']:
            stats['reached_stages'][final_stage] += 1
        
        # Update average duration
        call_duration = float(call_data.get('duration', 0))
        old_avg = stats['average_duration']
        old_count = stats['success_count'] + stats['failure_count'] - 1
        
        if old_count > 0:
            stats['average_duration'] = (old_avg * old_count + call_duration) / (old_count + 1)
        else:
            stats['average_duration'] = call_duration
        
        logger.info(f"Updated stats for campaign {campaign_id}")
        return True
    
    def get_industries(self):
        """Get all available industry templates"""
        return get_industries()
    
    def get_industry_template(self, industry_id):
        """Get the template for a specific industry"""
        return get_industry_template(industry_id)
    
    def get_campaign_by_id(self, campaign_id):
        """
        Get a campaign by ID
        
        Args:
            campaign_id (str): ID of the campaign to retrieve
            
        Returns:
            Campaign: Campaign object with script_template attribute
        """
        try:
            # Get the script for this campaign
            script = self.get_script(campaign_id)
            
            # Create a simple class to mimic your database model
            class Campaign:
                def __init__(self, id, script):
                    self.campaign_id = id
                    self.name = f"Campaign {id}"
                    self.script_template = script
            
            # Return a campaign object with the script template
            return Campaign(campaign_id, script)
        except Exception as e:
            logger.error(f"Error getting campaign by ID {campaign_id}: {e}")
            return None

def init_campaign_manager():
    """
    Initialize the campaign manager
    
    Returns:
        CampaignManager: Initialized campaign manager
    """
    global _campaign_manager
    
    try:
        logger.info("Initializing campaign manager")
        _campaign_manager = CampaignManager()
        logger.info("Campaign manager initialized successfully")
        return _campaign_manager
    except Exception as e:
        logger.error(f"Error initializing campaign manager: {e}")
        raise

def get_campaign_manager():
    """
    Get the campaign manager instance, initializing it if necessary
    
    Returns:
        CampaignManager: Campaign manager instance
    """
    global _campaign_manager
    
    if _campaign_manager is None:
        _campaign_manager = init_campaign_manager()
    
    return _campaign_manager