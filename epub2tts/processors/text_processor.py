"""
Text processor for EPUB2TTS
"""

import os
import logging
from pathlib import Path
from ..core.exceptions import FileError, ProcessingError
from ..core.text_utils import clean_text, split_into_sentences

logger = logging.getLogger(__name__)

class TextProcessor:
    """Processor for text files"""
    
    def __init__(self, file_path):
        """
        Initialize text processor
        
        Args:
            file_path (str): Path to text file
            
        Raises:
            FileError: If file doesn't exist or is not a text file
        """
        self.file_path = Path(file_path)
        
        if not self.file_path.exists():
            logger.error(f"File not found: {self.file_path}")
            raise FileError(f"File not found: {self.file_path}")
        
        if self.file_path.suffix.lower() != '.txt':
            logger.error(f"Not a text file: {self.file_path}")
            raise FileError(f"Not a text file: {self.file_path}")
        
        self.text = None
        self.metadata = {}
        self.chapters = []
        
        self._load_text()
    
    def _load_text(self):
        """Load text file"""
        try:
            # Read text file
            with open(self.file_path, 'r', encoding='utf-8') as f:
                self.text = f.read()
            
            # Set metadata
            self.metadata = {
                'title': os.path.basename(self.file_path),
                'author': 'Unknown',
                'language': 'en',
            }
            
            # Extract chapters
            self._extract_chapters()
            
            logger.debug(f"Loaded text file: {self.file_path}")
        
        except Exception as e:
            logger.error(f"Error loading text file: {str(e)}")
            raise FileError(f"Error loading text file: {str(e)}")
    
    def _extract_chapters(self):
        """Extract chapters from text file"""
        try:
            # Split text into lines
            lines = self.text.split('\n')
            
            # Look for chapter markers
            chapter_markers = [
                'chapter', 'section', 'part', 'book', 'volume',
                'prologue', 'epilogue', 'introduction', 'conclusion',
                'appendix', 'preface', 'foreword', 'afterword',
            ]
            
            chapter_indices = []
            
            for i, line in enumerate(lines):
                line_lower = line.lower().strip()
                
                # Check if line starts with a chapter marker
                if any(line_lower.startswith(marker) for marker in chapter_markers):
                    chapter_indices.append(i)
                
                # Check if line is a short line with chapter-like content
                elif (len(line.strip()) < 50 and 
                      any(marker in line_lower for marker in chapter_markers)):
                    chapter_indices.append(i)
            
            # If no chapters found, create default chapters
            if not chapter_indices:
                self._create_default_chapters()
                return
            
            # Create chapters
            for i, start_idx in enumerate(chapter_indices):
                # Determine end index
                if i < len(chapter_indices) - 1:
                    end_idx = chapter_indices[i + 1] - 1
                else:
                    end_idx = len(lines) - 1
                
                # Get chapter title
                title = lines[start_idx].strip()
                
                # Add chapter
                self.chapters.append({
                    'title': title,
                    'start_idx': start_idx,
                    'end_idx': end_idx,
                })
            
            logger.debug(f"Extracted {len(self.chapters)} chapters")
        
        except Exception as e:
            logger.error(f"Error extracting chapters: {str(e)}")
            self._create_default_chapters()
    
    def _create_default_chapters(self):
        """Create default chapters based on text length"""
        try:
            # Split text into sentences
            sentences = split_into_sentences(self.text)
            
            # Determine chapter size (sentences per chapter)
            total_sentences = len(sentences)
            
            if total_sentences <= 50:
                # For small texts, one chapter
                chapter_size = total_sentences
            elif total_sentences <= 200:
                # For medium texts, 50 sentences per chapter
                chapter_size = 50
            else:
                # For large texts, 100 sentences per chapter
                chapter_size = 100
            
            # Create chapters
            for i in range(0, total_sentences, chapter_size):
                start_idx = i
                end_idx = min(i + chapter_size - 1, total_sentences - 1)
                
                self.chapters.append({
                    'title': f"Section {i // chapter_size + 1}",
                    'start_idx': start_idx,
                    'end_idx': end_idx,
                    'is_sentence_index': True,
                })
            
            logger.debug(f"Created {len(self.chapters)} default chapters")
        
        except Exception as e:
            logger.error(f"Error creating default chapters: {str(e)}")
            
            # Fallback: create a single chapter
            self.chapters = [{
                'title': 'Full Text',
                'start_idx': 0,
                'end_idx': 0,
                'is_full_text': True,
            }]
    
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
            
            # Handle full text chapter
            if chapter.get('is_full_text', False):
                return clean_text(self.text)
            
            # Handle sentence-based chapters
            if chapter.get('is_sentence_index', False):
                sentences = split_into_sentences(self.text)
                start_idx = chapter['start_idx']
                end_idx = chapter['end_idx']
                
                if start_idx < 0 or end_idx >= len(sentences):
                    logger.error(f"Sentence index out of range: {start_idx}-{end_idx}")
                    return ""
                
                chapter_text = " ".join(sentences[start_idx:end_idx + 1])
                return clean_text(chapter_text)
            
            # Handle line-based chapters
            lines = self.text.split('\n')
            start_idx = chapter['start_idx']
            end_idx = chapter['end_idx']
            
            if start_idx < 0 or end_idx >= len(lines):
                logger.error(f"Line index out of range: {start_idx}-{end_idx}")
                return ""
            
            chapter_text = "\n".join(lines[start_idx:end_idx + 1])
            return clean_text(chapter_text)
        
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
        Get full text of text file
        
        Returns:
            str: Full text
        """
        return clean_text(self.text)

