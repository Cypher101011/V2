"""
Book converter for EPUB2TTS
"""

import os
import logging
import tempfile
import concurrent.futures
from pathlib import Path
from ..core.exceptions import ConversionError
from ..core.text_utils import split_text_into_chunks
from ..core.audio_utils import combine_audio_files

logger = logging.getLogger(__name__)

class BookConverter:
    """Converter for books to audio"""
    
    def __init__(self, ebook, tts_engine, config=None):
        """
        Initialize book converter
        
        Args:
            ebook: Ebook object
            tts_engine: TTS engine object
            config (dict, optional): Configuration dictionary
        """
        self.ebook = ebook
        self.tts_engine = tts_engine
        self.config = config or {}
        self.chunk_size = self.config.get('chunk_size', 2000)
        self.max_workers = self.config.get('max_workers', 4)
        self.temp_dir = self.config.get('temp_dir', None)
        self.keep_temp_files = self.config.get('keep_temp_files', False)
        self.output_format = self.config.get('output_format', 'mp3')
        self.output_quality = self.config.get('output_quality', 192)
    
    def convert_chapter(self, chapter_index, output_file=None, progress_callback=None):
        """
        Convert chapter to audio
        
        Args:
            chapter_index (int): Chapter index
            output_file (str, optional): Output file path
            progress_callback (callable, optional): Progress callback function
            
        Returns:
            str: Output file path
            
        Raises:
            ConversionError: If chapter cannot be converted
        """
        try:
            # Get chapter text
            chapter_text = self.ebook.get_chapter_text(chapter_index)
            chapter_title = self.ebook.get_chapter_title(chapter_index)
            
            if not chapter_text:
                logger.warning(f"Chapter {chapter_index} is empty")
                return None
            
            # Create temporary directory if needed
            temp_dir = self.temp_dir
            if not temp_dir:
                temp_dir = tempfile.mkdtemp(prefix="epub2tts_")
            else:
                os.makedirs(temp_dir, exist_ok=True)
            
            # Determine output file
            if not output_file:
                output_file = os.path.join(
                    temp_dir,
                    f"chapter_{chapter_index + 1}_{chapter_title}.{self.output_format}"
                )
            
            # Create output directory if it doesn't exist
            output_dir = os.path.dirname(os.path.abspath(output_file))
            os.makedirs(output_dir, exist_ok=True)
            
            # Split text into chunks
            chunks = split_text_into_chunks(chapter_text, self.chunk_size)
            
            if not chunks:
                logger.warning(f"No text chunks in chapter {chapter_index}")
                return None
            
            # Process chunks
            if len(chunks) == 1:
                # Single chunk, process directly
                self.tts_engine.save_to_file(chunks[0], output_file)
                
                if progress_callback:
                    progress_callback(1, 1)
                
                logger.info(f"Converted chapter {chapter_index} to {output_file}")
                return output_file
            
            # Multiple chunks, process in parallel
            chunk_files = []
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                # Submit tasks
                future_to_chunk = {
                    executor.submit(
                        self._process_chunk, 
                        chunk, 
                        i, 
                        temp_dir
                    ): i for i, chunk in enumerate(chunks)
                }
                
                # Process results
                for i, future in enumerate(concurrent.futures.as_completed(future_to_chunk)):
                    chunk_index = future_to_chunk[future]
                    
                    try:
                        chunk_file = future.result()
                        if chunk_file:
                            chunk_files.append(chunk_file)
                        
                        if progress_callback:
                            progress_callback(i + 1, len(chunks))
                    
                    except Exception as e:
                        logger.error(f"Error processing chunk {chunk_index}: {str(e)}")
            
            # Combine chunk files
            if chunk_files:
                combine_audio_files(
                    chunk_files, 
                    output_file, 
                    format=self.output_format, 
                    bitrate=f"{self.output_quality}k"
                )
                
                # Clean up chunk files
                if not self.keep_temp_files:
                    for chunk_file in chunk_files:
                        try:
                            os.unlink(chunk_file)
                        except Exception as e:
                            logger.warning(f"Error removing chunk file {chunk_file}: {str(e)}")
                
                logger.info(f"Converted chapter {chapter_index} to {output_file}")
                return output_file
            
            logger.warning(f"No audio chunks generated for chapter {chapter_index}")
            return None
        
        except Exception as e:
            logger.error(f"Error converting chapter {chapter_index}: {str(e)}")
            raise ConversionError(f"Error converting chapter {chapter_index}: {str(e)}")
    
    def _process_chunk(self, chunk, chunk_index, temp_dir):
        """
        Process text chunk
        
        Args:
            chunk (str): Text chunk
            chunk_index (int): Chunk index
            temp_dir (str): Temporary directory
            
        Returns:
            str: Chunk file path
        """
        try:
            # Create chunk file path
            chunk_file = os.path.join(temp_dir, f"chunk_{chunk_index}.{self.output_format}")
            
            # Generate speech
            self.tts_engine.save_to_file(chunk, chunk_file)
            
            return chunk_file
        
        except Exception as e:
            logger.error(f"Error processing chunk {chunk_index}: {str(e)}")
            return None
    
    def convert_book(self, output_file, progress_callback=None, status_callback=None):
        """
        Convert entire book to audio
        
        Args:
            output_file (str): Output file path
            progress_callback (callable, optional): Progress callback function
            status_callback (callable, optional): Status callback function
            
        Returns:
            str: Output file path
            
        Raises:
            ConversionError: If book cannot be converted
        """
        try:
            # Create temporary directory if needed
            temp_dir = self.temp_dir
            if not temp_dir:
                temp_dir = tempfile.mkdtemp(prefix="epub2tts_")
            else:
                os.makedirs(temp_dir, exist_ok=True)
            
            # Create output directory if it doesn't exist
            output_dir = os.path.dirname(os.path.abspath(output_file))
            os.makedirs(output_dir, exist_ok=True)
            
            # Get chapters
            chapters = self.ebook.get_chapters()
            
            if not chapters:
                logger.warning("No chapters found in book")
                if status_callback:
                    status_callback("No chapters found in book")
                return None
            
            # Convert chapters
            chapter_files = []
            
            for i, chapter in enumerate(chapters):
                if status_callback:
                    status_callback(f"Converting chapter {i + 1}/{len(chapters)}")
                
                # Define chapter progress callback
                def chapter_progress(current, total):
                    if progress_callback:
                        # Calculate overall progress
                        overall_progress = (i + current / total) / len(chapters) * 100
                        progress_callback(overall_progress)
                
                # Convert chapter
                chapter_file = self.convert_chapter(i, progress_callback=chapter_progress)
                
                if chapter_file:
                    chapter_files.append(chapter_file)
            
            # Combine chapter files
            if chapter_files:
                if status_callback:
                    status_callback("Combining audio files...")
                
                combine_audio_files(
                    chapter_files, 
                    output_file, 
                    format=self.output_format, 
                    bitrate=f"{self.output_quality}k"
                )
                
                # Clean up chapter files
                if not self.keep_temp_files:
                    for chapter_file in chapter_files:
                        try:
                            os.unlink(chapter_file)
                        except Exception as e:
                            logger.warning(f"Error removing chapter file {chapter_file}: {str(e)}")
                
                # Clean up temporary directory
                if not self.keep_temp_files and not self.temp_dir:
                    try:
                        os.rmdir(temp_dir)
                    except Exception as e:
                        logger.warning(f"Error removing temporary directory {temp_dir}: {str(e)}")
                
                if status_callback:
                    status_callback(f"Book converted to {output_file}")
                
                logger.info(f"Converted book to {output_file}")
                return output_file
            
            logger.warning("No audio chapters generated")
            if status_callback:
                status_callback("No audio chapters generated")
            
            return None
        
        except Exception as e:
            logger.error(f"Error converting book: {str(e)}")
            if status_callback:
                status_callback(f"Error: {str(e)}")
            
            raise ConversionError(f"Error converting book: {str(e)}")

