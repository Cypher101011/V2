"""
Text processing utilities for EPUB2TTS
"""

import re
import logging
from .exceptions import ProcessingError

logger = logging.getLogger(__name__)

def clean_text(text):
    """
    Clean text for TTS processing
    
    Args:
        text (str): Text to clean
        
    Returns:
        str: Cleaned text
    """
    if not text:
        return ""
    
    try:
        # Replace multiple spaces with a single space
        text = re.sub(r'\s+', ' ', text)
        
        # Replace common Unicode characters
        text = text.replace('\u2018', "'").replace('\u2019', "'")  # Smart quotes
        text = text.replace('\u201c', '"').replace('\u201d', '"')  # Smart double quotes
        text = text.replace('\u2013', '-').replace('\u2014', '--')  # En and em dashes
        text = text.replace('\u2026', '...')  # Ellipsis
        
        # Remove non-printable characters
        text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', text)
        
        # Normalize whitespace
        text = text.strip()
        
        return text
    
    except Exception as e:
        logger.error(f"Error cleaning text: {str(e)}")
        raise ProcessingError(f"Failed to clean text: {str(e)}")

def split_text_into_chunks(text, chunk_size=2000, overlap=50):
    """
    Split text into chunks of specified size
    
    Args:
        text (str): Text to split
        chunk_size (int): Maximum chunk size in characters
        overlap (int): Overlap between chunks in characters
        
    Returns:
        list: List of text chunks
    """
    if not text:
        return []
    
    try:
        # Clean text first
        text = clean_text(text)
        
        # If text is smaller than chunk size, return as is
        if len(text) <= chunk_size:
            return [text]
        
        # Split text into sentences
        sentences = split_into_sentences(text)
        
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            # If adding this sentence would exceed chunk size
            if len(current_chunk) + len(sentence) > chunk_size:
                # Add current chunk to chunks list
                chunks.append(current_chunk.strip())
                
                # Start new chunk with overlap from previous chunk
                words = current_chunk.split()
                overlap_text = " ".join(words[-min(len(words), overlap):])
                current_chunk = overlap_text + " " + sentence
            else:
                # Add sentence to current chunk
                if current_chunk:
                    current_chunk += " " + sentence
                else:
                    current_chunk = sentence
        
        # Add the last chunk if not empty
        if current_chunk.strip():
            chunks.append(current_chunk.strip())
        
        return chunks
    
    except Exception as e:
        logger.error(f"Error splitting text into chunks: {str(e)}")
        raise ProcessingError(f"Failed to split text into chunks: {str(e)}")

def split_into_sentences(text):
    """
    Split text into sentences
    
    Args:
        text (str): Text to split
        
    Returns:
        list: List of sentences
    """
    if not text:
        return []
    
    try:
        # Regular expression for sentence splitting
        # This handles common abbreviations and edge cases
        pattern = r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?|\!)\s'
        sentences = re.split(pattern, text)
        
        # Remove empty sentences
        sentences = [s.strip() for s in sentences if s.strip()]
        
        return sentences
    
    except Exception as e:
        logger.error(f"Error splitting text into sentences: {str(e)}")
        raise ProcessingError(f"Failed to split text into sentences: {str(e)}")

def count_words(text):
    """
    Count words in text
    
    Args:
        text (str): Text to count words in
        
    Returns:
        int: Word count
    """
    if not text:
        return 0
    
    try:
        # Split text into words and count
        words = re.findall(r'\b\w+\b', text)
        return len(words)
    
    except Exception as e:
        logger.error(f"Error counting words: {str(e)}")
        raise ProcessingError(f"Failed to count words: {str(e)}")

def estimate_reading_time(text, wpm=150):
    """
    Estimate reading time for text
    
    Args:
        text (str): Text to estimate reading time for
        wpm (int): Words per minute
        
    Returns:
        float: Estimated reading time in minutes
    """
    if not text:
        return 0
    
    try:
        word_count = count_words(text)
        return word_count / wpm
    
    except Exception as e:
        logger.error(f"Error estimating reading time: {str(e)}")
        raise ProcessingError(f"Failed to estimate reading time: {str(e)}")

