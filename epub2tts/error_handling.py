"""
Error handling utilities for EPUB2TTS
"""

import os
import sys
import logging
import traceback
import platform
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Define error types
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

# Error handler
def handle_error(error, gui_mode=False):
    """
    Handle errors gracefully
    
    Args:
        error: Exception object
        gui_mode (bool): Whether in GUI mode
        
    Returns:
        str: Error message
    """
    error_type = type(error).__name__
    error_message = str(error)
    error_traceback = traceback.format_exc()
    
    # Log error
    logger.error(f"{error_type}: {error_message}")
    logger.debug(error_traceback)
    
    # Create user-friendly message
    if isinstance(error, FileNotFoundError):
        user_message = f"File not found: {error_message}"
    elif isinstance(error, PermissionError):
        user_message = f"Permission denied: {error_message}"
    elif isinstance(error, TTSEngineError):
        user_message = f"TTS engine error: {error_message}"
    elif isinstance(error, WhisperError):
        user_message = f"Whisper error: {error_message}"
    elif isinstance(error, ResourceError):
        user_message = f"Resource error: {error_message}"
    elif isinstance(error, ConfigError):
        user_message = f"Configuration error: {error_message}"
    elif "No module named" in error_message:
        missing_module = error_message.split("'")[1]
        user_message = f"Missing module: {missing_module}. Please install it with 'pip install {missing_module}'."
    elif "_tkinter" in error_message:
        user_message = "Tkinter error: GUI may not be properly installed on your system."
        if platform.system() == "Linux":
            user_message += " Try installing python3-tk package."
    else:
        user_message = f"Error: {error_message}"
    
    # Return user-friendly message
    return user_message

def check_system_resources():
    """
    Check system resources
    
    Returns:
        dict: Resource information
    """
    import psutil
    
    try:
        # Get memory info
        memory = psutil.virtual_memory()
        memory_available_mb = memory.available / (1024 * 1024)
        memory_total_mb = memory.total / (1024 * 1024)
        memory_percent = memory.percent
        
        # Get disk info
        disk = psutil.disk_usage('/')
        disk_free_gb = disk.free / (1024 * 1024 * 1024)
        disk_total_gb = disk.total / (1024 * 1024 * 1024)
        disk_percent = disk.percent
        
        # Get CPU info
        cpu_percent = psutil.cpu_percent(interval=0.1)
        cpu_count = psutil.cpu_count(logical=True)
        
        # Check if resources are sufficient
        resources_ok = (
            memory_available_mb > 500 and  # At least 500 MB free memory
            disk_free_gb > 1.0 and  # At least 1 GB free disk space
            memory_percent < 90 and  # Less than 90% memory used
            disk_percent < 95  # Less than 95% disk used
        )
        
        # Create resource info
        resource_info = {
            'memory_available_mb': memory_available_mb,
            'memory_total_mb': memory_total_mb,
            'memory_percent': memory_percent,
            'disk_free_gb': disk_free_gb,
            'disk_total_gb': disk_total_gb,
            'disk_percent': disk_percent,
            'cpu_percent': cpu_percent,
            'cpu_count': cpu_count,
            'resources_ok': resources_ok
        }
        
        return resource_info
    
    except Exception as e:
        logger.warning(f"Failed to check system resources: {str(e)}")
        return {
            'resources_ok': True,  # Assume resources are OK if check fails
            'error': str(e)
        }

def check_ffmpeg():
    """
    Check if FFmpeg is installed
    
    Returns:
        bool: True if FFmpeg is installed
    """
    import subprocess
    
    try:
        subprocess.run(
            ["ffmpeg", "-version"], 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            check=True
        )
        return True
    except (subprocess.SubprocessError, FileNotFoundError):
        return False

def create_error_report(error, system_info=True):
    """
    Create detailed error report
    
    Args:
        error: Exception object
        system_info (bool): Whether to include system info
        
    Returns:
        str: Error report
    """
    error_type = type(error).__name__
    error_message = str(error)
    error_traceback = traceback.format_exc()
    
    report = [
        "=== EPUB2TTS Error Report ===",
        f"Error Type: {error_type}",
        f"Error Message: {error_message}",
        "",
        "Traceback:",
        error_traceback,
        ""
    ]
    
    if system_info:
        report.extend([
            "System Information:",
            f"Python Version: {sys.version}",
            f"Platform: {platform.platform()}",
            f"System: {platform.system()}",
            f"Machine: {platform.machine()}",
            f"Processor: {platform.processor()}",
            ""
        ])
        
        # Add resource info if psutil is available
        try:
            import psutil
            resources = check_system_resources()
            
            report.extend([
                "Resource Information:",
                f"Memory Available: {resources['memory_available_mb']:.2f} MB",
                f"Memory Total: {resources['memory_total_mb']:.2f} MB",
                f"Memory Usage: {resources['memory_percent']}%",
                f"Disk Free: {resources['disk_free_gb']:.2f} GB",
                f"Disk Total: {resources['disk_total_gb']:.2f} GB",
                f"Disk Usage: {resources['disk_percent']}%",
                f"CPU Usage: {resources['cpu_percent']}%",
                f"CPU Count: {resources['cpu_count']}",
                ""
            ])
        except ImportError:
            report.append("Resource Information: psutil not available")
            report.append("")
    
    # Add installed packages
    try:
        import pkg_resources
        installed_packages = sorted([f"{pkg.key}=={pkg.version}" for pkg in pkg_resources.working_set])
        
        report.extend([
            "Installed Packages:",
            *installed_packages,
            ""
        ])
    except ImportError:
        report.append("Installed Packages: pkg_resources not available")
        report.append("")
    
    # Check FFmpeg
    ffmpeg_installed = check_ffmpeg()
    report.append(f"FFmpeg Installed: {ffmpeg_installed}")
    report.append("")
    
    return "\n".join(report)

def save_error_report(error, output_path=None):
    """
    Save error report to file
    
    Args:
        error: Exception object
        output_path (str, optional): Path to save report
        
    Returns:
        str: Path to error report
    """
    report = create_error_report(error)
    
    if output_path is None:
        # Use user's home directory
        home_dir = str(Path.home())
        output_dir = os.path.join(home_dir, ".epub2tts", "logs")
        
        # Create directory if it doesn't exist
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # Create filename with timestamp
        import datetime
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = os.path.join(output_dir, f"error_report_{timestamp}.txt")
    
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report)
        
        logger.info(f"Error report saved to {output_path}")
        return output_path
    
    except Exception as e:
        logger.error(f"Failed to save error report: {str(e)}")
        return None

