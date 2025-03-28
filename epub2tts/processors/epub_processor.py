"""
EPUB processor for EPUB2TTS
"""

import os
import logging
from pathlib import Path
from ..core.exceptions import FileError, ProcessingError
from ..core.text_utils import clean_text

logger = logging.getLogger(__name__)

class EPUBProcessor:
    """Processor for EPUB files"""
    
    def __init__(self, file_path):
        """
        Initialize EPUB processor
        
        Args:
            file_path (str): Path to EPUB file
            
        Raises:
            FileError: If file doesn't exist or is not an EPUB file
        """
        self.file_path = Path(file_path)
        
        if not self.file_path.exists():
            logger.error(f"File not found: {self.file_path}")
            raise FileError(f"File not found: {self.file_path}")
        
        if self.file_path.suffix.lower() != '.epub':
            logger.error(f"Not an EPUB file: {self.file_path}")
            raise FileError(f"Not an EPUB file: {self.file_path}")
        
        self.book = None
        self.spine = []
        self.toc = []
        self.metadata = {}
        
        self._load_epub()
    
    def _load_epub(self):
        """Load EPUB file"""
        try:
            import ebooklib
            from ebooklib import epub
            from bs4 import BeautifulSoup
            
            self.book = epub.read_epub(self.file_path)
            
            # Get spine (reading order)
            self.spine = [item for item in self.book.spine if item[0] == 'nav']
            self.spine.extend([item for item in self.book.spine if item[0] != 'nav'])
            
            # Get table of contents
            self.toc = self.book.toc
            
            # Get metadata
            self._extract_metadata()
            
            logger.debug(f"Loaded EPUB file: {self.file_path}")
        
        except ImportError:
            logger.error("ebooklib and beautifulsoup4 are required for EPUB processing")
            raise FileError("ebooklib and beautifulsoup4 are required for EPUB processing. Please install them with 'pip install ebooklib beautifulsoup4'.")
        
        except Exception as e:
            logger.error(f"Error loading EPUB file: {str(e)}")
            raise FileError(f"Error loading EPUB file: {str(e)}")
    
    def _extract_metadata(self):
        """Extract metadata from EPUB file"""
        try:
            # Get basic metadata
            self.metadata = {
                'title': self.book.get_metadata('DC', 'title'),
                'author': self.book.get_metadata('DC', 'creator'),
                'language': self.book.get_metadata('DC', 'language'),
                'identifier': self.book.get_metadata('DC', 'identifier'),
                'publisher': self.book.get_metadata('DC', 'publisher'),
                'date': self.book.get_metadata('DC', 'date'),
                'rights': self.book.get_metadata('DC', 'rights'),
                'description': self.book.get_metadata('DC', 'description'),
            }
            
            # Clean up metadata
            for key, value in self.metadata.items():
                if isinstance(value, list) and value:
                    if isinstance(value[0], tuple) and len(value[0]) > 0:
                        self.metadata[key] = value[0][0]
                    else:
                        self.metadata[key] = value[0]
                elif not value:
                    self.metadata[key] = None
            
            logger.debug(f"Extracted metadata: {self.metadata}")
        
        except Exception as e:
            logger.error(f"Error extracting metadata: {str(e)}")
            self.metadata = {
                'title': os.path.basename(self.file_path),
                'author': 'Unknown',
                'language': 'en',
            }
    
    def get_metadata(self):
        """
        Get metadata
        
        Returns:
            dict: Metadata dictionary
        """
        return self.metadata
    
    def get_chapters(self):
        """
        Get list of chapters
        
        Returns:
            list: List of chapter items
        """
        try:
            from ebooklib import epub
            
            # Get all HTML items
            chapters = []
            for item_id in self.spine:
                item = self.book.get_item_with_id(item_id[0])
                if item and item.get_type() == ebooklib.ITEM_DOCUMENT:
                    chapters.append(item)
            
            logger.debug(f"Found {len(chapters)} chapters")
            return chapters
        
        except Exception as e:
            logger.error(f"Error getting chapters: {str(e)}")
            raise ProcessingError(f"Error getting chapters: {str(e)}")
    
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
        try:
            from bs4 import BeautifulSoup
            
            chapters = self.get_chapters()
            
            if chapter_index < 0 or chapter_index >= len(chapters):
                logger.error(f"Chapter index out of range: {chapter_index}")
                raise IndexError(f"Chapter index out of range: {chapter_index}")
            
            chapter = chapters[chapter_index]
            content = chapter.get_content().decode('utf-8')
            
            # Parse HTML content
            soup = BeautifulSoup(content, 'html.parser')
            
            # Remove script and style elements
            for element in soup(['script', 'style']):
                element.decompose()
            
            # Get text
            text = soup.get_text()
            
            # Clean text
            text = clean_text(text)
            
            return text
        
        except Exception as e:
            logger.error(f"Error getting chapter text: {str(e)}")
            raise ProcessingError(f"Error getting chapter text: {str(e)}")
    
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
        try:
            from bs4 import BeautifulSoup
            
            chapters = self.get_chapters()
            
            if chapter_index < 0 or chapter_index >= len(chapters):
                logger.error(f"Chapter index out of range: {chapter_index}")
                raise IndexError(f"Chapter index out of range: {chapter_index}")
            
            chapter = chapters[chapter_index]
            content = chapter.get_content().decode('utf-8')
            
            # Parse HTML content
            soup = BeautifulSoup(content, 'html.parser')
            
            # Try to find title in heading elements
            for heading in soup.find_all(['h1', 'h2', 'h3']):
                if heading.text.strip():
                    return heading.text.strip()
            
            # If no heading found, use chapter ID or default title
            if chapter.id:
                return chapter.id
            
            return f"Chapter {chapter_index + 1}"
        
        except Exception as e:
            logger.error(f"Error getting chapter title: {str(e)}")
            return f"Chapter {chapter_index + 1}"
    
    def get_full_text(self):
        """
        Get full text of EPUB file
        
        Returns:
            str: Full text
        """
        try:
            chapters = self.get_chapters()
            texts = []
            
            for i in range(len(chapters)):
                chapter_title = self.get_chapter_title(i)
                chapter_text = self.get_chapter_text(i)
                
                texts.append(f"Chapter: {chapter_title}\n\n{chapter_text}\n\n")
            
            return "\n".join(texts)
        
        except Exception as e:
            logger.error(f"Error getting full text: {str(e)}")
            raise ProcessingError(f"Error getting full text: {str(e)}")

