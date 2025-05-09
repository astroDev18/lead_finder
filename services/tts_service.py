# services/tts_service.py
import os
import torch
import logging
import uuid
from TTS.api import TTS
from pathlib import Path

logger = logging.getLogger(__name__)
os.environ["PHONEMIZER_ESPEAK_LIBRARY"] = "C:\\Program Files\\eSpeak NG\\espeak-ng.exe"

class TTSService:
    def __init__(self):
        # Check if CUDA is available
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"TTS service initializing on device: {self.device}")
        
        # Audio cache directory
        self.cache_dir = os.path.join(os.getcwd(), "temp_audio")
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # Model directory
        self.model_dir = os.path.join(os.getcwd(), "models", "tts")
        os.makedirs(self.model_dir, exist_ok=True)
        
        # Initialize TTS
        self._initialize_tts()
    
    def _initialize_tts(self):
        """Initialize TTS model with GPU acceleration"""
        try:
            # First, attempt to load the XTTS v2 model (best quality)
            # This model supports voice cloning and is highly realistic
            self.tts = TTS("tts_models/en/xtts_v2/xtts_v2").to(self.device)
            logger.info("XTTS v2 model loaded successfully on %s", self.device)
            self.model_type = "xtts_v2"
        except Exception as e:
            logger.warning(f"Could not load XTTS v2 model: {e}, trying fallback model")
            try:
                # Fall back to VITS model (still very good quality)
                self.tts = TTS("tts_models/en/vctk/vits").to(self.device)
                logger.info("VITS model loaded successfully on %s", self.device)
                self.model_type = "vits"
            except Exception as e2:
                logger.error(f"Error loading fallback TTS model: {e2}")
                raise
    
    def generate_audio(self, text, speaker="p266", save_to_file=True):
        """
        Generate audio from text
        
        Args:
            text (str): Text to convert to speech
            speaker (str): Speaker ID for multi-speaker models (default: "p225")
            save_to_file (bool): Whether to save to file or return bytes
            
        Returns:
            str or bytes: Path to audio file if save_to_file=True, otherwise audio bytes
        """
        try:
            # Generate a unique filename
            filename = f"{uuid.uuid4()}.wav"
            file_path = os.path.join(self.cache_dir, filename)
            
            # Clean text
            cleaned_text = self._process_text(text)
            
            # Generate speech - INCLUDE SPEAKER PARAMETER
            self.tts.tts_to_file(
                text=cleaned_text,
                file_path=file_path,
                speaker=speaker  # This is required for multi-speaker models
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
            # Force model download 
            # This is useful on first run to ensure models are ready
            TTS().download_model("tts_models/en/xtts_v2/xtts_v2")
            logger.info("Voice models downloaded/verified successfully")
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
