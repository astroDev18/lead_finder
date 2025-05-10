# services/tts_service.py
import os
import torch
import logging
import uuid
from TTS.api import TTS
from pathlib import Path

logger = logging.getLogger(__name__)
os.environ["PHONEMIZER_ESPEAK_LIBRARY"] = "C:\\Program Files\\eSpeak NG\\espeak-ng.exe"

# This fixes the XTTS loading issue
try:
    from TTS.tts.configs.xtts_config import XttsConfig
    from TTS.tts.models.xtts import XttsAudioConfig
    torch.serialization.add_safe_globals([XttsConfig])
    # Add them all to safe globals
    torch.serialization.add_safe_globals([
        XttsConfig,
        XttsAudioConfig
    ])
    logger.info("Successfully added XTTS configs to safe globals")
except Exception as e:
    logger.error(f"Error adding to safe globals: {e}")

class TTSService:
    def __init__(self):
        # Check TTS and PyTorch versions
        try:
            import importlib.metadata
            tts_version = importlib.metadata.version('TTS')
            logger.info(f"Using TTS library version: {tts_version}")
            logger.info(f"Using PyTorch version: {torch.__version__}")
        except:
            logger.warning("Could not determine library versions")
            
        # Check if CUDA is available
        self.cuda_available = torch.cuda.is_available()
        if self.cuda_available:
            self.device = "cuda" 
            logger.info(f"CUDA is available. GPU: {torch.cuda.get_device_name()}")
        else:
            self.device = "cpu"
            logger.info("CUDA is not available, using CPU")
        
        # Audio cache directory
        self.cache_dir = os.path.join(os.getcwd(), "temp_audio")
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # Initialize TTS
        self._initialize_tts()
    
    def _initialize_tts(self):
        """Initialize TTS model with GPU acceleration if available"""
        try:
            # First, try to load the XTTS v2 model
            logger.info(f"Attempting to load XTTS v2 model on {self.device}")
            
            # Modify this to use weights_only=False for XTTS
            self.tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2").to(self.device)
            logger.info(f"XTTS v2 model loaded successfully on {self.device}")
            self.model_type = "xtts_v2"
        except Exception as e:
            logger.warning(f"Could not load XTTS v2 model: {e}, trying fallback model")
            try:
                # Fall back to VITS model
                logger.info(f"Attempting to load VITS model on {self.device}")
                self.tts = TTS("tts_models/en/vctk/vits").to(self.device)
                logger.info(f"VITS model loaded successfully on {self.device}")
                self.model_type = "vits"
            except Exception as e2:
                logger.error(f"Error loading fallback TTS model: {e2}")
                raise
    
    def generate_audio(self, text, speaker="p236", save_to_file=True):
        """Generate audio from text"""
        try:
            # Generate a unique filename
            filename = f"{uuid.uuid4()}.wav"
            file_path = os.path.join(self.cache_dir, filename)
            
            # Clean text
            cleaned_text = self._process_text(text)
            
            # Generate speech with proper parameters based on model type
            if self.model_type == "xtts_v2":
                # For XTTS v2
                self.tts.tts_to_file(
                    text=cleaned_text,
                    file_path=file_path,
                    speaker_name=speaker  # XTTS v2 uses speaker_name
                )
            else:
                # For VITS model
                self.tts.tts_to_file(
                    text=cleaned_text,
                    file_path=file_path,
                    speaker=speaker  # VITS uses speaker
                )
            
            if save_to_file:
                return filename
            else:
                # Read file and return bytes
                with open(file_path, 'rb') as f:
                    audio_data = f.read()
                    
                # Delete the file
                os.remove(file_path)
                return audio_data
                
        except Exception as e:
            logger.error(f"Error generating audio: {e}", exc_info=True)
            return None
        
    def _process_text(self, text):
        """Process text with SSML tags and clean it for TTS"""
        if not text:
            return "Hello."
        
        # Ensure text ends with punctuation
        if text and not text[-1] in ['.', '!', '?', ',', ';', ':']:
            text += '.'
        
        # Process SSML tags if present
        # This is a simplified implementation
        # Handle breaks
        text = text.replace('<break time="300ms"/>', ', ')
        text = text.replace('<break time="500ms"/>', '. ')
        text = text.replace('<break time="1s"/>', '... ')
        
        # Handle emphasis
        text = text.replace('<emphasis level="moderate">', '')
        text = text.replace('</emphasis>', '')
        
        return text
    
    def get_audio_path(self, filename):
        """Get full path to an audio file"""
        return os.path.join(self.cache_dir, filename)
    
    def clear_old_files(self, max_age_hours=6):
        """Clear audio files older than given hours"""
        try:
            import time
            current_time = time.time()
            max_age_seconds = max_age_hours * 3600
            
            count = 0
            for file in Path(self.cache_dir).glob("*.wav"):
                file_age = current_time - os.path.getmtime(file)
                if file_age > max_age_seconds:
                    os.remove(file)
                    count += 1
            
            if count > 0:
                logger.info(f"Cleared {count} old audio files")
        except Exception as e:
            logger.error(f"Error clearing old files: {e}")

    def download_voice_models(self):
        """Download voice models if needed"""
        try:
            # This will trigger model downloads if they don't exist locally
            logger.info("Checking/downloading voice models")
            
            # Try different model paths for XTTS v2
            try:
                # First try with full path
                TTS(model_name="tts_models/multilingual/multi-dataset/xtts_v2", progress_bar=True)
                logger.info("XTTS v2 model verified/downloaded successfully")
            except Exception as e:
                logger.warning(f"Could not download XTTS v2 with primary path: {e}, trying alternative")
                try:
                    # Try with short name
                    TTS(model_name="xtts_v2", progress_bar=True)
                    logger.info("XTTS v2 model verified/downloaded successfully with short name")
                except Exception as e2:
                    # Just log the error but continue to download the fallback
                    logger.error(f"Error downloading XTTS v2 model: {e2}")
            
            # Download the fallback VITS model
            TTS(model_name="tts_models/en/vctk/vits", progress_bar=True)
            logger.info("VITS model verified/downloaded successfully")
            
        except Exception as e:
            logger.error(f"Error downloading voice models: {e}")

# Singleton instance
_tts_service = None

def get_tts_service():
    """Get the TTS service singleton"""
    global _tts_service
    if _tts_service is None:
        _tts_service = TTSService()
    return _tts_service