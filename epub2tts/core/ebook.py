"""
Ebook handling for EPUB2TTS
"""

import os
import logging
from pathlib import Path
from .exceptions import FileError

logger = logging.getLogger(__name__)

class Ebook:
    """Ebook class for handling different ebook formats"""
    
    def __init__(self, file_path):
        """
        Initialize ebook
        
        Args:
            file_path (str): Path to ebook file
            
        Raises:
            FileError: If file doesn't exist or has unsupported format
        """
        self.file_path = Path(file_path)
        
        if not self.file_path.exists():
            logger.error(f"File not found: {self.file_path}")
            raise FileError(f"File not found: {self.file_path}")
        
        self.format = self.file_path.suffix.lower()
        
        if self.format not in ['.epub', '.pdf', '.txt']:
            logger.error(f"Unsupported file format: {self.format}")
            raise FileError(f"Unsupported file format: {self.format}")
        
        self.title = None
        self.author = None
        self.language = None
        self.chapters = []
        self.metadata = {}
        self.processor = None
        
        self._load_processor()
        self._load_metadata()
    
    def _load_processor(self):
        """Load appropriate processor for file format"""
        try:
            if self.format == '.epub':
                from ..processors.epub_processor import EPUBProcessor
                self.processor = EPUBProcessor(self.file_path)
            elif self.format == '.pdf':
                from ..processors.pdf_processor import PDFProcessor
                self.processor = PDFProcessor(self.file_path)
            elif self.format == '.txt':
                from ..processors.text_processor import TextProcessor
                self.processor = TextProcessor(self.file_path)
            
            logger.debug(f"Loaded processor for {self.format} file")
        
        except Exception as e:
            logger.error(f"Error loading processor: {str(e)}")
            raise FileError(f"Error loading processor: {str(e)}")
    
    def _load_metadata(self):
        """Load metadata from file"""
        try:
            self.metadata = self.processor.get_metadata()
            self.title = self.metadata.get('title', os.path.basename(self.file_path))
            self.author = self.metadata.get('author', 'Unknown')
            self.language = self.metadata.get('language', 'en')
            
            logger.debug(f"Loaded metadata: {self.metadata}")
        
        except Exception as e:
            logger.error(f"Error loading metadata: {str(e)}")
            self.title = os.path.basename(self.file_path)
            self.author = 'Unknown'
            self.language = 'en'
    
    def get_chapters(self):
        """
        Get list of chapters
        
        Returns:
            list: List of chapters
        """
        if not self.chapters:
            try:
                self.chapters = self.processor.get_chapters()
                logger.debug(f"Loaded {len(self.chapters)} chapters")
            except Exception as e:
                logger.error(f"Error loading chapters: {str(e)}")
                raise FileError(f"Error loading chapters: {str(e)}")
        
        return self.chapters
    
    def get_chapter_text(self, chapter_index):
        """
        Get text for specific chapter
        
        Args:
            chapter_index (int): Chapter index
            
        Returns:
            str: Chapter text
            
        Raises:
            IndexError: If chapter index is out of range
        """
        chapters = self.get_chapters()
        
        if chapter_index < 0 or chapter_index >= len(chapters):
            logger.error(f"Chapter index out of range: {chapter_index}")
            raise IndexError(f"Chapter index out of range: {chapter_index}")
        
        try:
            return self.processor.get_chapter_text(chapter_index)
        except Exception as e:
            logger.error(f"Error getting chapter text: {str(e)}")
            raise FileError(f"Error getting chapter text: {str(e)}")
    
    def get_chapter_title(self, chapter_index):
        """
        Get title for specific chapter
        
        Args:
            chapter_index (int): Chapter index
            
        Returns:
            str: Chapter title
            
        Raises:
            IndexError: If chapter index is out of range
        """
        chapters = self.get_chapters()
        
        if chapter_index < 0 or chapter_index >= len(chapters):
            logger.error(f"Chapter index out of range: {chapter_index}")
            raise IndexError(f"Chapter index out of range: {chapter_index}")
        
        try:
            return self.processor.get_chapter_title(chapter_index)
        except Exception as e:
            logger.error(f"Error getting chapter title: {str(e)}")
            return f"Chapter {chapter_index + 1}"
    
    def get_full_text(self):
        """
        Get full text of ebook
        
        Returns:
            str: Full text
        """
        try:
            return self.processor.get_full_text()
        except Exception as e:
            logger.error(f"Error getting full text: {str(e)}")
            raise FileError(f"Error getting full text: {str(e)}")
    
    def __str__(self):
        """String representation of ebook"""
        return f"{self.title} by {self.author} ({self.format})"

