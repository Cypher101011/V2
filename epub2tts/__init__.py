"""
EPUB2TTS - A tool to convert ebooks to audiobooks
"""

__version__ = "2.0.0"

# Import core modules to make them available at the package level
from .core.config import Config
from .core.exceptions import EPUB2TTSError, FileError, TTSEngineError, WhisperError
from .core.logger import setup_logger, get_logger

# Setup default logger
logger = setup_logger()

# Version info
__all__ = [
    'Config',
    'EPUB2TTSError', 'FileError', 'TTSEngineError', 'WhisperError',
    'setup_logger', 'get_logger',
    '__version__',
]

