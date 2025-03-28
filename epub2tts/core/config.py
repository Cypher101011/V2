"""
Configuration management for EPUB2TTS
"""

import os
import json
import logging
from pathlib import Path
from .exceptions import ConfigError

logger = logging.getLogger(__name__)

class Config:
    """Configuration manager for EPUB2TTS"""
    
    def __init__(self, config_file=None):
        """
        Initialize configuration
        
        Args:
            config_file (str, optional): Path to configuration file
        """
        self.config = {
            # TTS settings
            'tts_engine': 'edge',  # Default TTS engine
            'voice': 'en-US-ChristopherNeural',  # Default voice
            'language': 'en',  # Default language
            'speed': 150,  # Default speed (words per minute)
            'volume': 100,  # Default volume (0-100)
            'pitch': 0,  # Default pitch adjustment
            'pause_length': 500,  # Default pause length between sentences (ms)
            
            # Processing settings
            'chunk_size': 2000,  # Default chunk size for text processing
            'max_workers': 4,  # Default number of worker processes
            'temp_dir': None,  # Default temp directory (None = use system default)
            'keep_temp_files': False,  # Whether to keep temporary files
            
            # Output settings
            'output_format': 'mp3',  # Default output format
            'output_quality': 192,  # Default output quality (kbps)
            'output_sample_rate': 44100,  # Default output sample rate (Hz)
            
            # Whisper settings
            'whisper_model': 'base',  # Default Whisper model
            'whisper_language': None,  # Default Whisper language (None = auto-detect)
            
            # GUI settings
            'theme': 'system',  # Default theme (system, light, dark)
            'window_size': '800x600',  # Default window size
            'recent_files': [],  # Recently opened files
            'last_directory': None,  # Last used directory
        }
        
        # Set config file path
        if config_file:
            self.config_file = Path(config_file)
        else:
            # Use default config file in user's home directory
            self.config_file = Path.home() / ".epub2tts" / "config.json"
        
        # Create config directory if it doesn't exist
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Load configuration if file exists
        if self.config_file.exists():
            try:
                self.load()
            except Exception as e:
                logger.warning(f"Failed to load configuration: {str(e)}")
    
    def get(self, key, default=None):
        """
        Get configuration value
        
        Args:
            key (str): Configuration key
            default: Default value if key doesn't exist
            
        Returns:
            Configuration value
        """
        return self.config.get(key, default)
    
    def set(self, key, value):
        """
        Set configuration value
        
        Args:
            key (str): Configuration key
            value: Configuration value
        """
        self.config[key] = value
    
    def load(self):
        """
        Load configuration from file
        
        Raises:
            ConfigError: If configuration file cannot be loaded
        """
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                loaded_config = json.load(f)
                self.config.update(loaded_config)
            logger.debug(f"Configuration loaded from {self.config_file}")
        except Exception as e:
            raise ConfigError(f"Failed to load configuration: {str(e)}")
    
    def save(self):
        """
        Save configuration to file
        
        Raises:
            ConfigError: If configuration file cannot be saved
        """
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4)
            logger.debug(f"Configuration saved to {self.config_file}")
        except Exception as e:
            raise ConfigError(f"Failed to save configuration: {str(e)}")
    
    def reset(self):
        """Reset configuration to defaults"""
        self.__init__(self.config_file)
        logger.debug("Configuration reset to defaults")
    
    def __str__(self):
        """String representation of configuration"""
        return json.dumps(self.config, indent=4)

