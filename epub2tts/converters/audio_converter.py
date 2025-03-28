"""
Audio converter for EPUB2TTS
"""

import os
import logging
from pathlib import Path
from ..core.exceptions import ConversionError
from ..core.audio_utils import convert_audio_format, split_audio_file

logger = logging.getLogger(__name__)

class AudioConverter:
    """Converter for audio files"""
    
    def __init__(self, config=None):
        """
        Initialize audio converter
        
        Args:
            config (dict, optional): Configuration dictionary
        """
        self.config = config or {}
        self.output_format = self.config.get('output_format', 'mp3')
        self.output_quality = self.config.get('output_quality', 192)
        self.output_sample_rate = self.config.get('output_sample_rate', 44100)
    
    def convert_format(self, input_file, output_file=None, format=None):
        """
        Convert audio file to different format
        
        Args:
            input_file (str): Input file path
            output_file (str, optional): Output file path
            format (str, optional): Output format
            
        Returns:
            str: Output file path
            
        Raises:
            ConversionError: If audio file cannot be converted
        """
        try:
            # Determine output format
            if not format:
                format = self.output_format
            
            # Determine output file
            if not output_file:
                input_path = Path(input_file)
                output_file = str(input_path.with_suffix(f".{format}"))
            
            # Create output directory if it doesn't exist
            output_dir = os.path.dirname(os.path.abspath(output_file))
            os.makedirs(output_dir, exist_ok=True)
            
            # Convert audio file
            convert_audio_format(
                input_file, 
                output_file, 
                format=format, 
                bitrate=f"{self.output_quality}k"
            )
            
            logger.info(f"Converted {input_file} to {output_file}")
            return output_file
        
        except Exception as e:
            logger.error(f"Error converting audio file: {str(e)}")
            raise ConversionError(f"Error converting audio file: {str(e)}")
    
    def split_audio(self, input_file, output_dir=None, segment_length=300, format=None):
        """
        Split audio file into segments
        
        Args:
            input_file (str): Input file path
            output_dir (str, optional): Output directory
            segment_length (int): Segment length in seconds
            format (str, optional): Output format
            
        Returns:
            list: List of output file paths
            
        Raises:
            ConversionError: If audio file cannot be split
        """
        try:
            # Determine output format
            if not format:
                format = self.output_format
            
            # Determine output directory
            if not output_dir:
                input_path = Path(input_file)
                output_dir = str(input_path.parent / f"{input_path.stem}_segments")
            
            # Create output directory if it doesn't exist
            os.makedirs(output_dir, exist_ok=True)
            
            # Split audio file
            output_files = split_audio_file(
                input_file, 
                output_dir, 
                segment_length=segment_length, 
                format=format, 
                bitrate=f"{self.output_quality}k"
            )
            
            logger.info(f"Split {input_file} into {len(output_files)} segments")
            return output_files
        
        except Exception as e:
            logger.error(f"Error splitting audio file: {str(e)}")
            raise ConversionError(f"Error splitting audio file: {str(e)}")

