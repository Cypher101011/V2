"""
Simple test script for EPUB2TTS
"""

import os
import sys
import argparse
from pathlib import Path

# Add the parent directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from epub2tts import __version__
from epub2tts.core.logger import setup_logger
from epub2tts.core.ebook import Ebook
from epub2tts.core.tts_engines import get_tts_engine, list_engines
from epub2tts.converters.book_converter import BookConverter

# Setup logger
logger = setup_logger()

def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description=f"EPUB2TTS Test Script v{__version__}"
    )
    
    parser.add_argument(
        'input_file',
        help="Input ebook file (EPUB, PDF, TXT)"
    )
    
    parser.add_argument(
        '-o', '--output',
        help="Output audio file",
        default="output.mp3"
    )
    
    parser.add_argument(
        '-e', '--engine',
        help="TTS engine (default: edge)",
        default="edge"
    )
    
    parser.add_argument(
        '-t', '--text-only',
        help="Extract text only",
        action="store_true"
    )
    
    args = parser.parse_args()
    
    try:
        # List available engines
        available_engines = list_engines()
        print(f"Available TTS engines: {', '.join(available_engines)}")
        
        if args.engine not in available_engines:
            print(f"Warning: Selected engine '{args.engine}' is not available.")
            if available_engines:
                args.engine = available_engines[0]
                print(f"Using '{args.engine}' instead.")
            else:
                print("No TTS engines available. Please install at least one TTS engine.")
                return 1
        
        # Load ebook
        print(f"Loading ebook: {args.input_file}")
        ebook = Ebook(args.input_file)
        
        print(f"Title: {ebook.title}")
        print(f"Author: {ebook.author}")
        print(f"Format: {ebook.format}")
        
        # Get chapters
        chapters = ebook.get_chapters()
        print(f"Found {len(chapters)} chapters")
        
        if args.text_only:
            # Extract text only
            print("Extracting text...")
            text = ebook.get_full_text()
            
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(text)
            
            print(f"Text extracted to {args.output}")
        else:
            # Convert to audio
            print(f"Initializing TTS engine: {args.engine}")
            tts_engine = get_tts_engine(args.engine)
            
            print(f"Converting {ebook.title} to audio...")
            converter = BookConverter(ebook, tts_engine)
            
            # Define progress callback
            def progress_callback(progress):
                sys.stdout.write(f"\rProgress: {progress:.1f}%")
                sys.stdout.flush()
            
            # Define status callback
            def status_callback(status):
                print(f"\n{status}")
            
            converter.convert_book(args.output, progress_callback, status_callback)
            print(f"\nAudiobook saved to {args.output}")
        
        return 0
    
    except Exception as e:
        print(f"Error: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())

