"""
TTS engines for EPUB2TTS
"""

import os
import logging
import tempfile
import importlib
from abc import ABC, abstractmethod
from .exceptions import TTSEngineError

logger = logging.getLogger(__name__)

class TTSEngine(ABC):
    """Abstract base class for TTS engines"""
    
    def __init__(self, config=None):
        """
        Initialize TTS engine
        
        Args:
            config (dict, optional): Configuration dictionary
        """
        self.config = config or {}
        self.language = self.config.get('language', 'en')
        self.voice = self.config.get('voice', 'default')
        self.speed = self.config.get('speed', 150)
        self.volume = self.config.get('volume', 100)
        self.pitch = self.config.get('pitch', 0)
        self.pause_length = self.config.get('pause_length', 500)
    
    @abstractmethod
    def say(self, text):
        """
        Speak text
        
        Args:
            text (str): Text to speak
        """
        pass
    
    @abstractmethod
    def save_to_file(self, text, output_file):
        """
        Save text to audio file
        
        Args:
            text (str): Text to speak
            output_file (str): Output file path
            
        Returns:
            bool: True if successful, False otherwise
        """
        pass
    
    @abstractmethod
    def is_available(self):
        """
        Check if TTS engine is available
        
        Returns:
            bool: True if available, False otherwise
        """
        pass
    
    @abstractmethod
    def get_available_voices(self):
        """
        Get available voices
        
        Returns:
            list: List of available voices
        """
        pass
    
    def stop(self):
        """Stop speaking"""
        pass
    
    def pause(self):
        """Pause speaking"""
        pass
    
    def resume(self):
        """Resume speaking"""
        pass
    
    def is_speaking(self):
        """
        Check if engine is currently speaking
        
        Returns:
            bool: True if speaking, False otherwise
        """
        return False


class EdgeTTSEngine(TTSEngine):
    """Microsoft Edge TTS engine"""
    
    def __init__(self, config=None):
        """
        Initialize Edge TTS engine
        
        Args:
            config (dict, optional): Configuration dictionary
        """
        super().__init__(config)
        
        try:
            import edge_tts
            self.edge_tts = edge_tts
            self.communicate = None
            self.is_speaking_flag = False
        except ImportError:
            logger.error("edge-tts not installed. Please install it with 'pip install edge-tts'.")
            raise TTSEngineError("edge-tts not installed. Please install it with 'pip install edge-tts'.")
    
    async def _say_async(self, text):
        """
        Speak text asynchronously
        
        Args:
            text (str): Text to speak
        """
        try:
            self.is_speaking_flag = True
            self.communicate = self.edge_tts.Communicate(
                text,
                self.voice,
                rate=f"{self.speed:+d}%",
                volume=f"{self.volume:d}%"
            )
            await self.communicate.play()
            self.is_speaking_flag = False
        except Exception as e:
            self.is_speaking_flag = False
            logger.error(f"Edge TTS error: {str(e)}")
            raise TTSEngineError(f"Edge TTS error: {str(e)}")
    
    def say(self, text):
        """
        Speak text
        
        Args:
            text (str): Text to speak
        """
        import asyncio
        
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        try:
            loop.run_until_complete(self._say_async(text))
        except Exception as e:
            logger.error(f"Edge TTS error: {str(e)}")
            raise TTSEngineError(f"Edge TTS error: {str(e)}")
    
    async def _save_to_file_async(self, text, output_file):
        """
        Save text to audio file asynchronously
        
        Args:
            text (str): Text to speak
            output_file (str): Output file path
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            self.communicate = self.edge_tts.Communicate(
                text,
                self.voice,
                rate=f"{self.speed:+d}%",
                volume=f"{self.volume:d}%"
            )
            await self.communicate.save(output_file)
            return True
        except Exception as e:
            logger.error(f"Edge TTS error: {str(e)}")
            raise TTSEngineError(f"Edge TTS error: {str(e)}")
    
    def save_to_file(self, text, output_file):
        """
        Save text to audio file
        
        Args:
            text (str): Text to speak
            output_file (str): Output file path
            
        Returns:
            bool: True if successful, False otherwise
        """
        import asyncio
        
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        try:
            return loop.run_until_complete(self._save_to_file_async(text, output_file))
        except Exception as e:
            logger.error(f"Edge TTS error: {str(e)}")
            raise TTSEngineError(f"Edge TTS error: {str(e)}")
    
    def is_available(self):
        """
        Check if Edge TTS engine is available
        
        Returns:
            bool: True if available, False otherwise
        """
        try:
            import edge_tts
            return True
        except ImportError:
            return False
    
    async def _get_voices_async(self):
        """
        Get available voices asynchronously
        
        Returns:
            list: List of available voices
        """
        try:
            voices = await self.edge_tts.VoicesManager.create()
            return [voice["ShortName"] for voice in voices.voices]
        except Exception as e:
            logger.error(f"Edge TTS error: {str(e)}")
            raise TTSEngineError(f"Edge TTS error: {str(e)}")
    
    def get_available_voices(self):
        """
        Get available voices
        
        Returns:
            list: List of available voices
        """
        import asyncio
        
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        try:
            return loop.run_until_complete(self._get_voices_async())
        except Exception as e:
            logger.error(f"Edge TTS error: {str(e)}")
            return []
    
    def stop(self):
        """Stop speaking"""
        if self.communicate:
            self.communicate.stop()
            self.is_speaking_flag = False
    
    def is_speaking(self):
        """
        Check if engine is currently speaking
        
        Returns:
            bool: True if speaking, False otherwise
        """
        return self.is_speaking_flag


class GoogleTTSEngine(TTSEngine):
    """Google Text-to-Speech engine"""
    
    def __init__(self, config=None):
        """
        Initialize Google TTS engine
        
        Args:
            config (dict, optional): Configuration dictionary
        """
        super().__init__(config)
        
        try:
            from gtts import gTTS
            import pygame
            self.gTTS = gTTS
            self.pygame = pygame
            self.pygame.mixer.init()
            self.is_speaking_flag = False
            self.is_paused = False
        except ImportError:
            logger.error("gtts or pygame not installed. Please install them with 'pip install gtts pygame'.")
            raise TTSEngineError("gtts or pygame not installed. Please install them with 'pip install gtts pygame'.")
    
    def say(self, text):
        """
        Speak text
        
        Args:
            text (str): Text to speak
        """
        try:
            # Create temporary file
            with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as f:
                temp_file = f.name
            
            # Generate speech
            tts = self.gTTS(text=text, lang=self.language, slow=False)
            tts.save(temp_file)
            
            # Play speech
            self.is_speaking_flag = True
            self.pygame.mixer.music.load(temp_file)
            self.pygame.mixer.music.play()
            
            # Wait for playback to finish
            while self.pygame.mixer.music.get_busy():
                self.pygame.time.Clock().tick(10)
            
            # Clean up
            self.is_speaking_flag = False
            os.unlink(temp_file)
        
        except Exception as e:
            self.is_speaking_flag = False
            logger.error(f"Google TTS error: {str(e)}")
            raise TTSEngineError(f"Google TTS error: {str(e)}")
    
    def save_to_file(self, text, output_file):
        """
        Save text to audio file
        
        Args:
            text (str): Text to speak
            output_file (str): Output file path
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Create output directory if it doesn't exist
            output_dir = os.path.dirname(os.path.abspath(output_file))
            os.makedirs(output_dir, exist_ok=True)
            
            # Generate speech
            tts = self.gTTS(text=text, lang=self.language, slow=False)
            tts.save(output_file)
            
            return True
        
        except Exception as e:
            logger.error(f"Google TTS error: {str(e)}")
            raise TTSEngineError(f"Google TTS error: {str(e)}")
    
    def is_available(self):
        """
        Check if Google TTS engine is available
        
        Returns:
            bool: True if available, False otherwise
        """
        try:
            from gtts import gTTS
            import pygame
            return True
        except ImportError:
            return False
    
    def get_available_voices(self):
        """
        Get available voices
        
        Returns:
            list: List of available voices
        """
        # Google TTS doesn't have voice selection, just languages
        return ["default"]
    
    def stop(self):
        """Stop speaking"""
        if self.is_speaking_flag:
            self.pygame.mixer.music.stop()
            self.is_speaking_flag = False
            self.is_paused = False
    
    def pause(self):
        """Pause speaking"""
        if self.is_speaking_flag and not self.is_paused:
            self.pygame.mixer.music.pause()
            self.is_paused = True
    
    def resume(self):
        """Resume speaking"""
        if self.is_speaking_flag and self.is_paused:
            self.pygame.mixer.music.unpause()
            self.is_paused = False
    
    def is_speaking(self):
        """
        Check if engine is currently speaking
        
        Returns:
            bool: True if speaking, False otherwise
        """
        return self.is_speaking_flag


class XTTSEngine(TTSEngine):
    """XTTS (Coqui TTS) engine"""
    
    def __init__(self, config=None):
        """
        Initialize XTTS engine
        
        Args:
            config (dict, optional): Configuration dictionary
        """
        super().__init__(config)
        
        try:
            import torch
            from TTS.api import TTS
            self.torch = torch
            self.TTS = TTS
            self.model = None
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
            self.is_speaking_flag = False
            self.voice_sample = self.config.get('voice_sample', None)
            self._load_model()
        except ImportError:
            logger.error("TTS not installed. Please install it with 'pip install TTS'.")
            raise TTSEngineError("TTS not installed. Please install it with 'pip install TTS'.")
    
    def _load_model(self):
        """Load XTTS model"""
        try:
            self.model = self.TTS("tts_models/multilingual/multi-dataset/xtts_v2").to(self.device)
            logger.info(f"XTTS model loaded on {self.device}")
        except Exception as e:
            logger.error(f"XTTS error: {str(e)}")
            raise TTSEngineError(f"XTTS error: {str(e)}")
    
    def say(self, text):
        """
        Speak text
        
        Args:
            text (str): Text to speak
        """
        try:
            # Create temporary file
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
                temp_file = f.name
            
            # Generate speech
            self.is_speaking_flag = True
            self.model.tts_to_file(
                text=text,
                file_path=temp_file,
                speaker_wav=self.voice_sample,
                language=self.language
            )
            
            # Play speech
            import pygame
            pygame.mixer.init()
            pygame.mixer.music.load(temp_file)
            pygame.mixer.music.play()
            
            # Wait for playback to finish
            while pygame.mixer.music.get_busy():
                pygame.time.Clock().tick(10)
            
            # Clean up
            self.is_speaking_flag = False
            os.unlink(temp_file)
        
        except Exception as e:
            self.is_speaking_flag = False
            logger.error(f"XTTS error: {str(e)}")
            raise TTSEngineError(f"XTTS error: {str(e)}")
    
    def save_to_file(self, text, output_file):
        """
        Save text to audio file
        
        Args:
            text (str): Text to speak
            output_file (str): Output file path
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Create output directory if it doesn't exist
            output_dir = os.path.dirname(os.path.abspath(output_file))
            os.makedirs(output_dir, exist_ok=True)
            
            # Generate speech
            self.model.tts_to_file(
                text=text,
                file_path=output_file,
                speaker_wav=self.voice_sample,
                language=self.language
            )
            
            return True
        
        except Exception as e:
            logger.error(f"XTTS error: {str(e)}")
            raise TTSEngineError(f"XTTS error: {str(e)}")
    
    def is_available(self):
        """
        Check if XTTS engine is available
        
        Returns:
            bool: True if available, False otherwise
        """
        try:
            import torch
            from TTS.api import TTS
            return True
        except ImportError:
            return False
    
    def get_available_voices(self):
        """
        Get available voices
        
        Returns:
            list: List of available voices
        """
        # XTTS uses voice samples, not predefined voices
        return ["default"]
    
    def stop(self):
        """Stop speaking"""
        if self.is_speaking_flag:
            import pygame
            pygame.mixer.music.stop()
            self.is_speaking_flag = False
    
    def is_speaking(self):
        """
        Check if engine is currently speaking
        
        Returns:
            bool: True if speaking, False otherwise
        """
        return self.is_speaking_flag


def get_tts_engine(engine_name="edge", config=None):
    """
    Get TTS engine by name
    
    Args:
        engine_name (str): TTS engine name
        config (dict, optional): Configuration dictionary
        
    Returns:
        TTSEngine: TTS engine instance
        
    Raises:
        TTSEngineError: If TTS engine is not available
    """
    engines = {
        "edge": EdgeTTSEngine,
        "google": GoogleTTSEngine,
        "xtts": XTTSEngine,
    }
    
    if engine_name not in engines:
        logger.error(f"Unknown TTS engine: {engine_name}")
        raise TTSEngineError(f"Unknown TTS engine: {engine_name}")
    
    engine_class = engines[engine_name]
    
    try:
        engine = engine_class(config)
        if not engine.is_available():
            logger.error(f"TTS engine {engine_name} is not available")
            raise TTSEngineError(f"TTS engine {engine_name} is not available")
        return engine
    except Exception as e:
        logger.error(f"Error initializing TTS engine {engine_name}: {str(e)}")
        raise TTSEngineError(f"Error initializing TTS engine {engine_name}: {str(e)}")

def list_engines():
    """
    List available TTS engines
    
    Returns:
        list: List of available TTS engines
    """
    engines = []
    
    # Check Edge TTS
    try:
        import edge_tts
        engines.append("edge")
    except ImportError:
        pass
    
    # Check Google TTS
    try:
        from gtts import gTTS
        engines.append("google")
    except ImportError:
        pass
    
    # Check XTTS
    try:
        import torch
        from TTS.api import TTS
        engines.append("xtts")
    except ImportError:
        pass
    
    return engines

def list_voices(engine_name="edge"):
    """
    List available voices for TTS engine
    
    Args:
        engine_name (str): TTS engine name
        
    Returns:
        list: List of available voices
    """
    try:
        engine = get_tts_engine(engine_name)
        return engine.get_available_voices()
    except Exception as e:
        logger.error(f"Error listing voices for TTS engine {engine_name}: {str(e)}")
        return []

