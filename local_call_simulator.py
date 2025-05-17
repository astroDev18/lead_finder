import os
import sys
import logging
from flask import Flask, render_template, request, jsonify
import json
import uuid
import time 
from config.settings import SERVER_BASE_URL

# Set up logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Make sure we can find our modules
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# Import our services
from services.tts_service import get_tts_service
from services.conversation_manager import ConversationManager
from templates.script_templates import get_script

app = Flask(__name__)

# Create a dictionary to store active calls
active_calls = {}

@app.route('/')
def index():
    """Render the testing interface"""
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Local Call Simulator</title>
        <style>
            body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
            .call-container { border: 1px solid #ccc; padding: 15px; margin-bottom: 20px; border-radius: 5px; }
            .message { margin: 10px 0; padding: 10px; border-radius: 5px; }
            .ai { background-color: #e6f7ff; margin-left: 40px; }
            .user { background-color: #f0f0f0; margin-right: 40px; }
            button { padding: 10px; background-color: #4CAF50; color: white; border: none; cursor: pointer; }
            input[type=text] { padding: 10px; width: 70%; margin-right: 10px; }
            h1, h2 { color: #333; }
            #call-history { margin-top: 30px; }
            .controls { margin: 20px 0; }
            .audio-player { margin: 10px 0; }
        </style>
    </head>
    <body>
        <h1>Local Call Simulator</h1>
        
        <div class="controls">
            <h2>Start a New Call</h2>
            <select id="campaign-select">
                <option value="advanced_real_estate">Advanced Real Estate</option>
                <option value="advanced_mortgage">First Choice Mortgage</option>
            </select>
            <button onclick="startCall()">Start Call</button>
        </div>
        
        <div id="active-call" class="call-container" style="display: none;">
            <h2>Active Call - <span id="call-id"></span></h2>
            <div id="conversation"></div>
            <div id="audio-container" class="audio-player"></div>
            <div class="response-input">
                <input type="text" id="user-response" placeholder="Type your response...">
                <button onclick="sendResponse()">Send</button>
            </div>
            <button onclick="hangupCall()" style="background-color: #f44336;">Hang Up</button>
        </div>
        
        <div id="call-history">
            <h2>Call History</h2>
            <div id="history-list"></div>
        </div>
        
        <script>
            let activeCallId = null;
            
            async function startCall() {
                const campaignId = document.getElementById('campaign-select').value;
                
                try {
                    const response = await fetch('/api/start-call', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ campaign_id: campaignId })
                    });
                    
                    const data = await response.json();
                    if (data.success) {
                        activeCallId = data.call_id;
                        document.getElementById('call-id').textContent = activeCallId;
                        document.getElementById('active-call').style.display = 'block';
                        document.getElementById('conversation').innerHTML = '';
                        
                        // Add the initial greeting
                        addMessage('ai', data.greeting);
                        
                        // Play audio if available
                        if (data.audio_url) {
                            const audioPlayer = document.createElement('audio');
                            audioPlayer.controls = true;
                            audioPlayer.src = data.audio_url;
                            audioPlayer.autoplay = true;
                            document.getElementById('audio-container').innerHTML = '';
                            document.getElementById('audio-container').appendChild(audioPlayer);
                        }
                    } else {
                        alert('Error: ' + data.error);
                    }
                } catch (error) {
                    console.error('Error starting call:', error);
                    alert('Error starting call. See console for details.');
                }
            }
            
            async function sendResponse() {
                if (!activeCallId) {
                    alert('No active call!');
                    return;
                }
                
                const userInput = document.getElementById('user-response').value;
                if (!userInput.trim()) return;
                
                addMessage('user', userInput);
                document.getElementById('user-response').value = '';
                
                try {
                    const response = await fetch('/api/process-response', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            call_id: activeCallId,
                            user_input: userInput
                        })
                    });
                    
                    const data = await response.json();
                    if (data.success) {
                        addMessage('ai', data.message);
                        
                        // Play audio if available
                        if (data.audio_url) {
                            const audioPlayer = document.createElement('audio');
                            audioPlayer.controls = true;
                            audioPlayer.src = data.audio_url;
                            audioPlayer.autoplay = true;
                            document.getElementById('audio-container').innerHTML = '';
                            document.getElementById('audio-container').appendChild(audioPlayer);
                        }
                        
                        // End call if needed
                        if (data.end_call) {
                            alert('Call has ended.');
                            hangupCall();
                        }
                    } else {
                        alert('Error: ' + data.error);
                    }
                } catch (error) {
                    console.error('Error sending response:', error);
                    alert('Error sending response. See console for details.');
                }
            }
            
            function addMessage(type, text) {
                const conversation = document.getElementById('conversation');
                const messageDiv = document.createElement('div');
                messageDiv.className = `message ${type}`;
                messageDiv.textContent = text;
                conversation.appendChild(messageDiv);
                conversation.scrollTop = conversation.scrollHeight;
            }
            
            async function hangupCall() {
                if (!activeCallId) return;
                
                try {
                    await fetch('/api/hangup-call', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ call_id: activeCallId })
                    });
                    
                    document.getElementById('active-call').style.display = 'none';
                    updateCallHistory();
                    activeCallId = null;
                } catch (error) {
                    console.error('Error hanging up call:', error);
                }
            }
            
            async function updateCallHistory() {
                try {
                    const response = await fetch('/api/call-history');
                    const data = await response.json();
                    
                    const historyList = document.getElementById('history-list');
                    historyList.innerHTML = '';
                    
                    data.calls.forEach(call => {
                        const callDiv = document.createElement('div');
                        callDiv.className = 'call-container';
                        callDiv.innerHTML = `
                            <h3>Call ID: ${call.call_id}</h3>
                            <p>Campaign: ${call.campaign_id}</p>
                            <p>Duration: ${call.duration} seconds</p>
                            <p>Status: ${call.status}</p>
                            <p>Last Stage: ${call.last_stage}</p>
                        `;
                        historyList.appendChild(callDiv);
                    });
                } catch (error) {
                    console.error('Error updating call history:', error);
                }
            }
            
            // Initialize the page
            updateCallHistory();
            
            // Add event listener for Enter key
            document.getElementById('user-response').addEventListener('keypress', function(e) {
                if (e.key === 'Enter') {
                    sendResponse();
                }
            });
        </script>
    </body>
    </html>
    """
    return html

# Modified version of the start_call function for local_call_simulator.py:

@app.route('/api/start-call', methods=['POST'])
def start_call():
    """Start a simulated call with an advanced campaign script"""
    try:
        data = request.json
        campaign_id = data.get('campaign_id', 'advanced_real_estate')
        
        logger.info(f"Starting call with campaign {campaign_id}")
        
        # Create a unique call ID
        call_id = f"local_{uuid.uuid4().hex[:8]}"
        
        # Get the script
        script = get_script(campaign_id)
        
        # Initialize call state
        call_state = {
            'conversation_stage': 'greeting',
            'conversation_data': {},
            'previous_stages': [],
            'campaign_id': campaign_id,
            'start_time': time.time(),
            'status': 'active'
        }
        
        # Save call state
        from services.storage_service import save_call_state
        save_call_state(call_id, call_state)
        
        # Store in our active calls
        active_calls[call_id] = call_state
        
        # Get initial greeting
        greeting = script['conversation_flow']['greeting']['message']
        
        # Generate audio for greeting
        tts_service = get_tts_service()
        greeting_filename = tts_service.generate_audio(greeting, speaker="p273")
        
        # Get server base URL
        server_base_url = request.url_root.rstrip('/')
        audio_url = f"{server_base_url}/audio/{greeting_filename}"
        
        return jsonify({
            'success': True,
            'call_id': call_id,
            'greeting': greeting,
            'audio_url': audio_url
        })
    
    except Exception as e:
        logger.error(f"Error starting call: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/process-response', methods=['POST'])
def process_response():
    """Process a user response during a call"""
    try:
        data = request.json
        call_id = data.get('call_id')
        user_input = data.get('user_input')
        
        # Verify call exists
        if call_id not in active_calls:
            return jsonify({
                'success': False,
                'error': 'Call not found'
            })
        
        # Get call state
        from services.storage_service import get_call_state
        call_state = get_call_state(call_id)
        campaign_id = call_state.get('campaign_id', 'campaign_001')
        
        # Process the response
        conversation_manager = ConversationManager()
        script = get_script(campaign_id)
        
        # Add detailed logging for debugging
        logger.info(f"Processing response for call {call_id}")
        logger.info(f"User input: {user_input}")
        logger.info(f"Current stage: {call_state.get('conversation_stage')}")
        
        result = conversation_manager.process_response(call_id, script, user_input)
        
        # Generate audio for response
        tts_service = get_tts_service()
        response_file = tts_service.generate_audio(result['message'], speaker="p273")
        
        # Get server base URL
        server_base_url = request.url_root.rstrip('/')
        audio_url = f"{server_base_url}/audio/{response_file}"
        
        # Log the result
        logger.info(f"Response message: {result['message']}")
        logger.info(f"Next stage: {result['current_stage']}")
        logger.info(f"End call: {result.get('end_call', False)}")
        
        return jsonify({
            'success': True,
            'message': result['message'],
            'audio_url': audio_url,
            'current_stage': result['current_stage'],
            'end_call': result.get('end_call', False)
        })
    
    except Exception as e:
        logger.error(f"Error processing response: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/hangup-call', methods=['POST'])
def hangup_call():
    """End a call"""
    try:
        data = request.json
        call_id = data.get('call_id')
        
        if call_id in active_calls:
            # Update call state
            active_calls[call_id]['status'] = 'completed'
            active_calls[call_id]['end_time'] = time.time()
            active_calls[call_id]['duration'] = active_calls[call_id]['end_time'] - active_calls[call_id]['start_time']
            
            # Save final state
            from services.storage_service import save_call_state
            save_call_state(call_id, active_calls[call_id])
            
            logger.info(f"Call {call_id} hung up")
        
        return jsonify({'success': True})
    
    except Exception as e:
        logger.error(f"Error hanging up call: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/call-history')
def get_call_history():
    """Get call history"""
    try:
        # Convert active_calls to a list for the frontend
        calls = []
        for call_id, call_data in active_calls.items():
            duration = 0
            if 'end_time' in call_data and 'start_time' in call_data:
                duration = call_data['end_time'] - call_data['start_time']
            
            calls.append({
                'call_id': call_id,
                'campaign_id': call_data.get('campaign_id', 'unknown'),
                'status': call_data.get('status', 'unknown'),
                'duration': round(duration),
                'last_stage': call_data.get('conversation_stage', 'unknown')
            })
        
        return jsonify({'calls': calls})
    
    except Exception as e:
        logger.error(f"Error getting call history: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/audio/<filename>')
def serve_audio(filename):
    """Serve TTS audio files"""
    try:
        from services.tts_service import get_tts_service
        tts_service = get_tts_service()
        file_path = tts_service.get_audio_path(filename)
        
        if os.path.exists(file_path):
            return send_file(file_path, mimetype='audio/wav')
        else:
            logger.error(f"Audio file not found: {filename}")
            return "File not found", 404
    except Exception as e:
        logger.error(f"Error serving audio file {filename}: {e}")
        return "Error serving file", 500

if __name__ == '__main__':
    import time
    from flask import send_file
    
    # Additional imports needed
    try:
        from services.storage_service import init_storage
        init_storage()
    except:
        pass
    
    app.run(debug=True, port=5003)