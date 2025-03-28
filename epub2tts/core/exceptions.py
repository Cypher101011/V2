"""
Exception classes for EPUB2TTS
"""

class EPUB2TTSError(Exception):
    """Base exception for EPUB2TTS errors"""
    pass

class FileError(EPUB2TTSError):
    """File-related errors"""
    pass

class TTSEngineError(EPUB2TTSError):
    """TTS engine errors"""
    pass

class WhisperError(EPUB2TTSError):
    """Whisper-related errors"""
    pass

class ResourceError(EPUB2TTSError):
    """Resource-related errors (memory, disk space, etc.)"""
    pass

class ConfigError(EPUB2TTSError):
    """Configuration errors"""
    pass

class GUIError(EPUB2TTSError):
    """GUI-related errors"""
    pass

class ProcessingError(EPUB2TTSError):
    """Processing-related errors"""
    pass

class ConversionError(EPUB2TTSError):
    """Conversion-related errors"""
    pass

