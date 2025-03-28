"""
PDF processor for EPUB2TTS
"""

import os
import logging
from pathlib import Path
from ..core.exceptions import FileError, ProcessingError
from ..core.text_utils import clean_text

logger = logging.getLogger(__name__)

class PDFProcessor:
    """Processor for PDF files"""
    
    def __init__(self, file_path):
        """
        Initialize PDF processor
        
        Args:
            file_path (str): Path to PDF file
            
        Raises:
            FileError: If file doesn't exist or is not a PDF file
        """
        self.file_path = Path(file_path)
        
        if not self.file_path.exists():
            logger.error(f"File not found: {self.file_path}")
            raise FileError(f"File not found: {self.file_path}")
        
        if self.file_path.suffix.lower() != '.pdf':
            logger.error(f"Not a PDF file: {self.file_path}")
            raise FileError(f"Not a PDF file: {self.file_path}")
        
        self.pdf = None
        self.metadata = {}
        self.pages = []
        self.chapters = []
        
        self._load_pdf()
    
    def _load_pdf(self):
        """Load PDF file"""
        try:
            import pdfplumber
            
            self.pdf = pdfplumber.open(self.file_path)
            self.pages = self.pdf.pages
            
            # Extract metadata
            self._extract_metadata()
            
            # Extract chapters
            self._extract_chapters()
            
            logger.debug(f"Loaded PDF file: {self.file_path}")
        
        except ImportError:
            logger.error("pdfplumber is required for PDF processing")
            raise FileError("pdfplumber is required for PDF processing. Please install it with 'pip install pdfplumber'.")
        
        except Exception as e:
            logger.error(f"Error loading PDF file: {str(e)}")
            raise FileError(f"Error loading PDF file: {str(e)}")
    
    def _extract_metadata(self):
        """Extract metadata from PDF file"""
        try:
            # Get metadata from PDF
            pdf_metadata = self.pdf.metadata
            
            if pdf_metadata:
                self.metadata = {
                    'title': pdf_metadata.get('Title'),
                    'author': pdf_metadata.get('Author'),
                    'creator': pdf_metadata.get('Creator'),
                    'producer': pdf_metadata.get('Producer'),
                    'subject': pdf_metadata.get('Subject'),
                    'keywords': pdf_metadata.get('Keywords'),
                    'created': pdf_metadata.get('CreationDate'),
                    'modified': pdf_metadata.get('ModDate'),
                }
            else:
                self.metadata = {
                    'title': os.path.basename(self.file_path),
                    'author': 'Unknown',
                }
            
            # Clean up metadata
            for key, value in self.metadata.items():
                if not value:
                    self.metadata[key] = None
            
            logger.debug(f"Extracted metadata: {self.metadata}")
        
        except Exception as e:
            logger.error(f"Error extracting metadata: {str(e)}")
            self.metadata = {
                'title': os.path.basename(self.file_path),
                'author': 'Unknown',
            }
    
    def _extract_chapters(self):
        """Extract chapters from PDF file"""
        try:
            # Check if PDF has outline (table of contents)
            outline = self.pdf.outline
            
            if outline:
                # Process outline to get chapters
                self._process_outline(outline)
            else:
                # If no outline, create chapters based on page count
                self._create_default_chapters()
            
            logger.debug(f"Extracted {len(self.chapters)} chapters")
        
        except Exception as e:
            logger.error(f"Error extracting chapters: {str(e)}")
            self._create_default_chapters()
    
    def _process_outline(self, outline, level=0):
        """
        Process PDF outline to extract chapters
        
        Args:
            outline (list): PDF outline
            level (int): Nesting level
        """
        for item in outline:
            # Check if item is a dictionary (leaf node)
            if isinstance(item, dict):
                # Extract page number and title
                page_num = item.get('page_number', 0)
                title = item.get('title', f"Chapter {len(self.chapters) + 1}")
                
                # Add chapter
                self.chapters.append({
                    'title': title,
                    'page_start': page_num,
                    'page_end': None,
                    'level': level,
                })
            
            # Check if item is a list (has children)
            elif isinstance(item, list) and len(item) == 2:
                # First item is parent, second is list of children
                parent, children = item
                
                # Process parent
                if isinstance(parent, dict):
                    page_num = parent.get('page_number', 0)
                    title = parent.get('title', f"Chapter {len(self.chapters) + 1}")
                    
                    # Add chapter
                    self.chapters.append({
                        'title': title,
                        'page_start': page_num,
                        'page_end': None,
                        'level': level,
                    })
                
                # Process children
                if isinstance(children, list):
                    self._process_outline(children, level + 1)
        
        # Set page_end for chapters
        for i in range(len(self.chapters) - 1):
            self.chapters[i]['page_end'] = self.chapters[i + 1]['page_start'] - 1
        
        # Set page_end for last chapter
        if self.chapters and self.chapters[-1]['page_end'] is None:
            self.chapters[-1]['page_end'] = len(self.pages) - 1
    
    def _create_default_chapters(self):
        """Create default chapters based on page count"""
        # Get total pages
        total_pages = len(self.pages)
        
        # Determine chapter size (pages per chapter)
        if total_pages <= 10:
            # For small PDFs, one chapter per page
            chapter_size = 1
        elif total_pages <= 50:
            # For medium PDFs, 5 pages per chapter
            chapter_size = 5
        else:
            # For large PDFs, 10 pages per chapter
            chapter_size = 10
        
        # Create chapters
        for i in range(0, total_pages, chapter_size):
            page_start = i
            page_end = min(i + chapter_size - 1, total_pages - 1)
            
            self.chapters.append({
                'title': f"Pages {page_start + 1}-{page_end + 1}",
                'page_start': page_start,
                'page_end': page_end,
                'level': 0,
            })
        
        logger.debug(f"Created {len(self.chapters)} default chapters")
    
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
            list: List of chapter dictionaries
        """
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
        try:
            if chapter_index < 0 or chapter_index >= len(self.chapters):
                logger.error(f"Chapter index out of range: {chapter_index}")
                raise IndexError(f"Chapter index out of range: {chapter_index}")
            
            chapter = self.chapters[chapter_index]
            page_start = chapter['page_start']
            page_end = chapter['page_end']
            
            # Extract text from pages
            texts = []
            for i in range(page_start, page_end + 1):
                if i < len(self.pages):
                    page_text = self.pages[i].extract_text()
                    if page_text:
                        texts.append(page_text)
            
            # Join texts and clean
            text = "\n\n".join(texts)
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
            if chapter_index < 0 or chapter_index >= len(self.chapters):
                logger.error(f"Chapter index out of range: {chapter_index}")
                raise IndexError(f"Chapter index out of range: {chapter_index}")
            
            return self.chapters[chapter_index]['title']
        
        except Exception as e:
            logger.error(f"Error getting chapter title: {str(e)}")
            return f"Chapter {chapter_index + 1}"
    
    def get_full_text(self):
        """
        Get full text of PDF file
        
        Returns:
            str: Full text
        """
        try:
            texts = []
            
            for i in range(len(self.chapters)):
                chapter_title = self.get_chapter_title(i)
                chapter_text = self.get_chapter_text(i)
                
                texts.append(f"Chapter: {chapter_title}\n\n{chapter_text}\n\n")
            
            return "\n".join(texts)
        
        except Exception as e:
            logger.error(f"Error getting full text: {str(e)}")
            raise ProcessingError(f"Error getting full text: {str(e)}")

