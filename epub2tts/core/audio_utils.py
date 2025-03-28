"""
Audio processing utilities for EPUB2TTS
"""

import os
import subprocess
import logging
import tempfile
from pathlib import Path
from .exceptions import ProcessingError

logger = logging.getLogger(__name__)

def check_ffmpeg():
    """
    Check if FFmpeg is installed
    
    Returns:
        bool: True if FFmpeg is installed, False otherwise
    """
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

def combine_audio_files(audio_files, output_file, format="mp3", bitrate="192k"):
    """
    Combine multiple audio files into one
    
    Args:
        audio_files (list): List of audio file paths
        output_file (str): Output file path
        format (str): Output format (mp3, wav, etc.)
        bitrate (str): Output bitrate (e.g., "192k")
        
    Returns:
        bool: True if successful, False otherwise
        
    Raises:
        ProcessingError: If audio files cannot be combined
    """
    if not audio_files:
        logger.warning("No audio files to combine")
        return False
    
    # Check if FFmpeg is installed
    if not check_ffmpeg():
        raise ProcessingError("FFmpeg is not installed. Please install FFmpeg to combine audio files.")
    
    try:
        # Create temporary file list
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            file_list = f.name
            for audio_file in audio_files:
                f.write(f"file '{os.path.abspath(audio_file)}'\n")
        
        # Create output directory if it doesn't exist
        output_dir = os.path.dirname(os.path.abspath(output_file))
        os.makedirs(output_dir, exist_ok=True)
        
        # Combine audio files using FFmpeg
        cmd = [
            "ffmpeg",
            "-y",  # Overwrite output file if it exists
            "-f", "concat",
            "-safe", "0",
            "-i", file_list,
            "-c:a", "libmp3lame" if format == "mp3" else "copy",
            "-b:a", bitrate,
            output_file
        ]
        
        logger.debug(f"Running FFmpeg command: {' '.join(cmd)}")
        
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True
        )
        
        # Remove temporary file list
        os.unlink(file_list)
        
        logger.info(f"Combined {len(audio_files)} audio files into {output_file}")
        return True
    
    except subprocess.CalledProcessError as e:
        logger.error(f"FFmpeg error: {e.stderr.decode('utf-8', errors='replace')}")
        raise ProcessingError(f"Failed to combine audio files: {str(e)}")
    
    except Exception as e:
        logger.error(f"Error combining audio files: {str(e)}")
        raise ProcessingError(f"Failed to combine audio files: {str(e)}")

def split_audio_file(input_file, output_dir, segment_length=300, format="mp3", bitrate="192k"):
    """
    Split audio file into segments
    
    Args:
        input_file (str): Input file path
        output_dir (str): Output directory
        segment_length (int): Segment length in seconds
        format (str): Output format (mp3, wav, etc.)
        bitrate (str): Output bitrate (e.g., "192k")
        
    Returns:
        list: List of output file paths
        
    Raises:
        ProcessingError: If audio file cannot be split
    """
    # Check if FFmpeg is installed
    if not check_ffmpeg():
        raise ProcessingError("FFmpeg is not installed. Please install FFmpeg to split audio files.")
    
    try:
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Get input file name without extension
        input_name = Path(input_file).stem
        
        # Split audio file using FFmpeg
        cmd = [
            "ffmpeg",
            "-y",  # Overwrite output files if they exist
            "-i", input_file,
            "-f", "segment",
            "-segment_time", str(segment_length),
            "-c:a", "libmp3lame" if format == "mp3" else "copy",
            "-b:a", bitrate,
            "-map", "0:a",
            f"{output_dir}/{input_name}_%03d.{format}"
        ]
        
        logger.debug(f"Running FFmpeg command: {' '.join(cmd)}")
        
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True
        )
        
        # Get list of output files
        output_files = sorted([
            os.path.join(output_dir, f) 
            for f in os.listdir(output_dir) 
            if f.startswith(f"{input_name}_") and f.endswith(f".{format}")
        ])
        
        logger.info(f"Split audio file {input_file} into {len(output_files)} segments")
        return output_files
    
    except subprocess.CalledProcessError as e:
        logger.error(f"FFmpeg error: {e.stderr.decode('utf-8', errors='replace')}")
        raise ProcessingError(f"Failed to split audio file: {str(e)}")
    
    except Exception as e:
        logger.error(f"Error splitting audio file: {str(e)}")
        raise ProcessingError(f"Failed to split audio file: {str(e)}")

def convert_audio_format(input_file, output_file, format="mp3", bitrate="192k"):
    """
    Convert audio file to different format
    
    Args:
        input_file (str): Input file path
        output_file (str): Output file path
        format (str): Output format (mp3, wav, etc.)
        bitrate (str): Output bitrate (e.g., "192k")
        
    Returns:
        bool: True if successful, False otherwise
        
    Raises:
        ProcessingError: If audio file cannot be converted
    """
    # Check if FFmpeg is installed
    if not check_ffmpeg():
        raise ProcessingError("FFmpeg is not installed. Please install FFmpeg to convert audio files.")
    
    try:
        # Create output directory if it doesn't exist
        output_dir = os.path.dirname(os.path.abspath(output_file))
        os.makedirs(output_dir, exist_ok=True)
        
        # Convert audio file using FFmpeg
        cmd = [
            "ffmpeg",
            "-y",  # Overwrite output file if it exists
            "-i", input_file,
            "-c:a", "libmp3lame" if format == "mp3" else "copy",
            "-b:a", bitrate,
            output_file
        ]
        
        logger.debug(f"Running FFmpeg command: {' '.join(cmd)}")
        
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True
        )
        
        logger.info(f"Converted audio file {input_file} to {output_file}")
        return True
    
    except subprocess.CalledProcessError as e:
        logger.error(f"FFmpeg error: {e.stderr.decode('utf-8', errors='replace')}")
        raise ProcessingError(f"Failed to convert audio file: {str(e)}")
    
    except Exception as e:
        logger.error(f"Error converting audio file: {str(e)}")
        raise ProcessingError(f"Failed to convert audio file: {str(e)}")

def record_audio(output_file, duration=5, format="wav", sample_rate=44100):
    """
    Record audio from microphone
    
    Args:
        output_file (str): Output file path
        duration (int): Recording duration in seconds
        format (str): Output format (wav, mp3, etc.)
        sample_rate (int): Sample rate in Hz
        
    Returns:
        bool: True if successful, False otherwise
        
    Raises:
        ProcessingError: If audio cannot be recorded
    """
    try:
        import sounddevice as sd
        import soundfile as sf
        import numpy as np
    except ImportError:
        raise ProcessingError("sounddevice and soundfile are required for audio recording. Please install them with 'pip install sounddevice soundfile'.")
    
    try:
        # Create output directory if it doesn't exist
        output_dir = os.path.dirname(os.path.abspath(output_file))
        os.makedirs(output_dir, exist_ok=True)
        
        # Record audio
        logger.info(f"Recording audio for {duration} seconds...")
        recording = sd.rec(
            int(duration * sample_rate),
            samplerate=sample_rate,
            channels=1,
            dtype='float32'
        )
        sd.wait()
        
        # Save recording
        sf.write(output_file, recording, sample_rate)
        
        logger.info(f"Audio recorded to {output_file}")
        return True
    
    except Exception as e:
        logger.error(f"Error recording audio: {str(e)}")
        raise ProcessingError(f"Failed to record audio: {str(e)}")

