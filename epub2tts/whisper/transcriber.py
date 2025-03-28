"""
Whisper transcriber for EPUB2TTS
"""

import os
import logging
from pathlib import Path
from ..core.exceptions import WhisperError

logger = logging.getLogger(__name__)

class WhisperTranscriber:
    """Transcriber using OpenAI Whisper"""
    
    def __init__(self, model_name="base", language=None, config=None):
        """
        Initialize Whisper transcriber
        
        Args:
            model_name (str): Whisper model name
            language (str, optional): Language code
            config (dict, optional): Configuration dictionary
            
        Raises:
            WhisperError: If Whisper is not available
        """
        self.model_name = model_name
        self.language = language
        self.config = config or {}
        self.model = None
        
        try:
            import whisper
            self.whisper = whisper
            self._load_model()
        except ImportError:
            logger.error("whisper not installed. Please install it with 'pip install openai-whisper'.")
            raise WhisperError("whisper not installed. Please install it with 'pip install openai-whisper'.")
    
    def _load_model(self):
        """Load Whisper model"""
        try:
            self.model = self.whisper.load_model(self.model_name)
            logger.info(f"Loaded Whisper model: {self.model_name}")
        except Exception as e:
            logger.error(f"Error loading Whisper model: {str(e)}")
            raise WhisperError(f"Error loading Whisper model: {str(e)}")
    
    def transcribe(self, audio_file, output_file=None):
        """
        Transcribe audio file
        
        Args:
            audio_file (str): Audio file path
            output_file (str, optional): Output file path
            
        Returns:
            str: Transcription text
            
        Raises:
            WhisperError: If audio file cannot be transcribed
        """
        try:
            # Check if audio file exists
            if not os.path.exists(audio_file):
                logger.error(f"Audio file not found: {audio_file}")
                raise WhisperError(f"Audio file not found: {audio_file}")
            
            # Transcribe audio
            options = {}
            if self.language:
                options['language'] = self.language
            
            result = self.model.transcribe(audio_file, **options)
            
            # Get transcription text
            text = result['text']
            
            # Save to file if output_file is specified
            if output_file:
                # Create output directory if it doesn't exist
                output_dir = os.path.dirname(os.path.abspath(output_file))
                os.makedirs(output_dir, exist_ok=True)
                
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(text)
                
                logger.info(f"Transcription saved to {output_file}")
            
            return text
        
        except Exception as e:
            logger.error(f"Error transcribing audio: {str(e)}")
            raise WhisperError(f"Error transcribing audio: {str(e)}")
    
    def record_and_transcribe(self, duration=5, output_audio=None, output_text=None):
        """
        Record audio and transcribe
        
        Args:
            duration (int): Recording duration in seconds
            output_audio (str, optional): Output audio file path
            output_text (str, optional): Output text file path
            
        Returns:
            str: Transcription text
            
        Raises:
            WhisperError: If audio cannot be recorded or transcribed
        """
        try:
            from ..core.audio_utils import record_audio
            
            # Create temporary audio file if output_audio is not specified
            if not output_audio:
                import tempfile
                with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
                    output_audio = f.name
            
            # Record audio
            record_audio(output_audio, duration)
            
            # Transcribe audio
            text = self.transcribe(output_audio, output_text)
            
            return text
        
        except Exception as e:
            logger.error(f"Error recording and transcribing: {str(e)}")
            raise WhisperError(f"Error recording and transcribing: {str(e)}")
    
    def list_models(self):
        """
        List available Whisper models
        
        Returns:
            list: List of available models
        """
        return [
            "tiny", "base", "small", "medium", "large",
            "tiny.en", "base.en", "small.en", "medium.en"
        ]

