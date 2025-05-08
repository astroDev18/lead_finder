"""
Controller for campaign management endpoints.
"""
from flask import Blueprint, request, jsonify
import logging
import uuid

from services.campaign_service import get_campaign_manager

# Set up logging
logger = logging.getLogger(__name__)

# Create a Blueprint for campaign-related routes
campaign_bp = Blueprint('campaign', __name__)

@campaign_bp.route('/campaigns', methods=['GET'])
def get_campaigns():
    """Get all available campaigns"""
    try:
        campaign_manager = get_campaign_manager()
        campaigns = campaign_manager.get_all_campaigns()
        
        return jsonify({
            'success': True,
            'campaigns': campaigns
        }), 200
    
    except Exception as e:
        logger.error(f"Error retrieving campaigns: {e}")
        return jsonify({'error': str(e)}), 500

@campaign_bp.route('/campaigns/<campaign_id>', methods=['GET'])
def get_campaign(campaign_id):
    """Get details for a specific campaign"""
    try:
        campaign_manager = get_campaign_manager()
        script = campaign_manager.get_script(campaign_id)
        
        if not script:
            return jsonify({'error': 'Campaign not found'}), 404
        
        # Get campaign statistics
        stats = campaign_manager.get_campaign_stats(campaign_id)
        
        return jsonify({
            'success': True,
            'campaign': {
                'id': campaign_id,
                'name': script['name'],
                'industry': script.get('industry', 'unknown'),
                'script': script,
                'stats': stats
            }
        }), 200
    
    except Exception as e:
        logger.error(f"Error retrieving campaign {campaign_id}: {e}")
        return jsonify({'error': str(e)}), 500

@campaign_bp.route('/campaigns', methods=['POST'])
def create_campaign():
    """Create a new campaign"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        # Extract data
        name = data.get('name')
        industry = data.get('industry')
        template_variables = data.get('template_variables', {})
        
        # Validate data
        if not name or not industry:
            return jsonify({'error': 'Name and industry are required'}), 400
        
        # Generate a campaign ID if not provided
        campaign_id = data.get('campaign_id', f"campaign_{str(uuid.uuid4())[:8]}")
        
        # Create the campaign
        campaign_manager = get_campaign_manager()
        success = campaign_manager.create_campaign(
            campaign_id=campaign_id,
            name=name,
            industry=industry,
            template_variables=template_variables
        )
        
        if not success:
            return jsonify({'error': 'Failed to create campaign'}), 400
        
        # Get the created campaign
        script = campaign_manager.get_script(campaign_id)
        
        return jsonify({
            'success': True,
            'campaign': {
                'id': campaign_id,
                'name': name,
                'industry': industry,
                'script': script
            }
        }), 201
    
    except Exception as e:
        logger.error(f"Error creating campaign: {e}")
        return jsonify({'error': str(e)}), 500

@campaign_bp.route('/campaigns/<campaign_id>', methods=['PUT'])
def update_campaign(campaign_id):
    """Update an existing campaign"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        # Extract data
        name = data.get('name')
        industry = data.get('industry')
        template_variables = data.get('template_variables', {})
        
        # Validate data
        if not name or not industry:
            return jsonify({'error': 'Name and industry are required'}), 400
        
        # Update the campaign (for now, just recreate it)
        campaign_manager = get_campaign_manager()
        success = campaign_manager.create_campaign(
            campaign_id=campaign_id,
            name=name,
            industry=industry,
            template_variables=template_variables
        )
        
        if not success:
            return jsonify({'error': 'Failed to update campaign'}), 400
        
        # Get the updated campaign
        script = campaign_manager.get_script(campaign_id)
        
        return jsonify({
            'success': True,
            'campaign': {
                'id': campaign_id,
                'name': name,
                'industry': industry,
                'script': script
            }
        }), 200
    
    except Exception as e:
        logger.error(f"Error updating campaign {campaign_id}: {e}")
        return jsonify({'error': str(e)}), 500

@campaign_bp.route('/industries', methods=['GET'])
def get_industries():
    """Get all available industry templates"""
    try:
        campaign_manager = get_campaign_manager()
        industries = campaign_manager.get_industries()
        
        return jsonify({
            'success': True,
            'industries': industries
        }), 200
    
    except Exception as e:
        logger.error(f"Error retrieving industries: {e}")
        return jsonify({'error': str(e)}), 500

@campaign_bp.route('/industries/<industry_id>', methods=['GET'])
def get_industry(industry_id):
    """Get details for a specific industry template"""
    try:
        campaign_manager = get_campaign_manager()
        template = campaign_manager.get_industry_template(industry_id)
        
        if not template:
            return jsonify({'error': 'Industry not found'}), 404
        
        return jsonify({
            'success': True,
            'industry': {
                'id': industry_id,
                'name': template['name'],
                'template': template
            }
        }), 200
    
    except Exception as e:
        logger.error(f"Error retrieving industry {industry_id}: {e}")
        return jsonify({'error': str(e)}), 500

@campaign_bp.route('/campaigns/<campaign_id>/preview', methods=['POST'])
def preview_campaign(campaign_id):
    """Preview a campaign script with custom variables"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        # Extract data
        template_variables = data.get('template_variables', {})
        
        # Get the campaign manager
        campaign_manager = get_campaign_manager()
        
        # Get the current campaign
        script = campaign_manager.get_script(campaign_id)
        
        if not script:
            return jsonify({'error': 'Campaign not found'}), 404
        
        # Create a temporary campaign with the custom variables
        temp_id = f"temp_{str(uuid.uuid4())[:8]}"
        success = campaign_manager.create_campaign(
            campaign_id=temp_id,
            name=f"Preview of {script['name']}",
            industry=script.get('industry', 'real_estate'),
            template_variables=template_variables
        )
        
        if not success:
            return jsonify({'error': 'Failed to create preview'}), 400
        
        # Get the preview script
        preview_script = campaign_manager.get_script(temp_id)
        
        return jsonify({
            'success': True,
            'preview': preview_script
        }), 200
    
    except Exception as e:
        logger.error(f"Error previewing campaign {campaign_id}: {e}")
        return jsonify({'error': str(e)}), 500