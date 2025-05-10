import os
import sys
import logging
from flask import Flask, jsonify

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

@app.route('/diagnostic', methods=['GET'])
def diagnostic():
    """Run diagnostic tests on the TTS system"""
    results = {
        "status": "running",
        "tests": [],
        "errors": []
    }
    
    # Test 1: Check CUDA
    try:
        import torch
        results["tests"].append({
            "name": "CUDA Check",
            "status": "success" if torch.cuda.is_available() else "warning",
            "message": f"CUDA Available: {torch.cuda.is_available()}, Device: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'None'}"
        })
    except Exception as e:
        results["errors"].append(f"CUDA check error: {str(e)}")
    
    # Test 2: Check TTS Service initialization
    try:
        from services.tts_service import get_tts_service
        tts_service = get_tts_service()
        results["tests"].append({
            "name": "TTS Service",
            "status": "success",
            "message": f"TTS service initialized with model: {tts_service.model_type}"
        })
    except Exception as e:
        results["errors"].append(f"TTS service error: {str(e)}")
    
    # Test 3: Generate a simple audio file
    try:
        tts_service = get_tts_service()
        test_text = "This is a test of the text to speech system."
        filename = tts_service.generate_audio(test_text, speaker="p273")
        file_path = tts_service.get_audio_path(filename)
        
        results["tests"].append({
            "name": "Audio Generation",
            "status": "success",
            "message": f"Generated audio file: {file_path}"
        })
    except Exception as e:
        results["errors"].append(f"Audio generation error: {str(e)}")
    
    # Determine overall status
    if len(results["errors"]) > 0:
        results["status"] = "error"
    elif any(test["status"] == "warning" for test in results["tests"]):
        results["status"] = "warning"
    else:
        results["status"] = "success"
    
    return jsonify(results)

if __name__ == "__main__":
    # Make sure the paths are set up correctly
    current_dir = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, current_dir)
    
    app.run(debug=True, port=5003)