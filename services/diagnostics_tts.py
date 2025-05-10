# diagnostic_tts.py
import os
import logging
import torch
import torch.serialization
from TTS.api import TTS

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_tts_models():
    """Test if TTS models can be loaded correctly"""
    # Print CUDA info
    print(f"CUDA available: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        print(f"CUDA version: {torch.version.cuda}")
        print(f"Number of GPUs: {torch.cuda.device_count()}")
        print(f"Current GPU: {torch.cuda.get_device_name()}")
    
    # Print PyTorch version
    print(f"PyTorch version: {torch.__version__}")
    
    # Print TTS version
    try:
        import importlib.metadata
        tts_version = importlib.metadata.version('TTS')
        print(f"TTS library version: {tts_version}")
    except:
        print("Could not determine TTS library version")
    
    # Force GPU if available
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Using device: {device}")
    
    # Add the class to the safe globals to fix the loading issue
    try:
        from TTS.tts.configs.xtts_config import XttsConfig
        torch.serialization.add_safe_globals([XttsConfig])
        print("Successfully added XttsConfig to safe globals")
    except Exception as e:
        print(f"Error adding XttsConfig to safe globals: {e}")
    
    # Try the correct path for XTTS v2
    try:
        print("\nTesting XTTS v2 model")
        model = TTS("tts_models/multilingual/multi-dataset/xtts_v2").to(device)
        print("✅ Successfully loaded XTTS v2 model")
        print(f"Model info: {model.model_name}")
    except Exception as e:
        print(f"❌ Failed to load XTTS v2 model: {e}")
    
    # Try the fallback VITS model
    try:
        print("\nTesting fallback VITS model")
        model = TTS("tts_models/en/vctk/vits").to(device)
        print("✅ Successfully loaded VITS model")
        print(f"Model info: {model.model_name}")
    except Exception as e:
        print(f"❌ Failed to load VITS model: {e}")

if __name__ == "__main__":
    test_tts_models()