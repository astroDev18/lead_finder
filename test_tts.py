# test_tts.py
import os
import sys
from flask import Flask
from services.tts_service import get_tts_service
import time

# Create a minimal Flask app to maintain compatibility
app = Flask(__name__)

def test_speakers():
    """Test different speaker voices for real estate application"""
    print("Testing different speaker voices for real estate...")
    tts_service = get_tts_service()
    
    real_estate_script = """Hello, this is Matthew from Premier Real Estate. 
    I'm calling because we've seen increased interest in properties in your neighborhood recently. 
    Based on recent sales, similar homes are selling at competitive prices. 
    Would you be interested in a no-obligation valuation of your property?"""
    
    test_speakers = ["p226", "p229", "p273", "p250", "p236", "p233", "p243", "p275", "p266", "p294"]
    
    for speaker in test_speakers:
        print(f"Generating sample with speaker {speaker}...")
        filename = tts_service.generate_audio(real_estate_script, speaker=speaker)
        print(f"Created {filename}")
    
    print("\nAll speaker samples completed. You can find the audio files in the temp_audio directory.")
    print(f"Audio files should be in: {os.path.join(os.getcwd(), 'temp_audio')}")

def test_tts():
    """Test the TTS service"""
    print("Initializing TTS service...")
    tts_service = get_tts_service()
    
    # Print available speakers AFTER initializing the service
    print("\nAvailable speakers:")
    print(tts_service.tts.speakers)
    
    # Test 1: Basic TTS
    print("\nTest 1: Basic TTS generation")
    start_time = time.time()
    filename = tts_service.generate_audio("Hello, this is a test of the speech generation system.", speaker="p225")  # Added speaker
    duration = time.time() - start_time
    print(f"Generated audio file: {filename} in {duration:.2f} seconds")
    
    # Test 2: TTS with SSML
    print("\nTest 2: TTS with SSML tags")
    start_time = time.time()
    ssml_text = "Hi there! <break time='300ms'/> This is a test with pauses. <break time='500ms'/> And <emphasis level='moderate'>emphasized</emphasis> words."
    filename = tts_service.generate_audio(ssml_text, speaker="p225")  # Added speaker
    duration = time.time() - start_time
    print(f"Generated SSML audio file: {filename} in {duration:.2f} seconds")
    
    # Test 3: Longer text
    print("\nTest 3: Longer text generation")
    long_text = """
    Thank you for taking the time to speak with me today. I'm calling regarding your property 
    and would like to discuss the current real estate market in your area. Based on recent sales, 
    properties similar to yours have been selling for competitive prices. Would you be interested 
    in a free valuation to see what your home might be worth in today's market?
    """
    start_time = time.time()
    filename = tts_service.generate_audio(long_text, speaker="p225")  # Added speaker
    duration = time.time() - start_time
    print(f"Generated long text audio file: {filename} in {duration:.2f} seconds")
    
    print("\nAll tests completed. You can find the audio files in the temp_audio directory.")
    print(f"Audio files should be in: {os.path.join(os.getcwd(), 'temp_audio')}")

if __name__ == "__main__":
    # Set up Python path for imports
    if os.path.basename(os.getcwd()) == 'lead_finder':
         sys.path.insert(0, os.getcwd())
    else:
         sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

    with app.app_context():
        # Comment out the function you don't want to run
        # test_tts()  # Basic TTS testing
        test_speakers()  # Test different speaker voices