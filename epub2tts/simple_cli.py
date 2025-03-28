"""
Simple command-line interface for EPUB2TTS
"""

import os
import sys
import argparse
from pathlib import Path

from . import __version__
from .core.ebook import Ebook
from .core.tts_engines import get_tts_engine, list_engines
from .converters.book_converter import BookConverter

def main():
    """Main entry point for simple CLI"""
    parser = argparse.ArgumentParser(
        description=f"EPUB2TTS Simple CLI v{__version__}"
    )
    
    parser.add_argument(
        'input_file',
        help="Input ebook file (EPUB, PDF, TXT)"
    )
    
    parser.add_argument(
        'output_file',
        help="Output audio file"
    )
    
    parser.add_argument(
        '-e', '--engine',
        help="TTS engine (default: edge)",
        default="edge"
    )
    
    parser.add_argument(
        '-v', '--voice',
        help="Voice to use"
    )
    
    parser.add_argument(
        '-l', '--language',
        help="Language code (default: en)",
        default="en"
    )
    
    parser.add_argument(
        '-t', '--text-only',
        help="Extract text only",
        action="store_true"
    )
    
    args = parser.parse_args()
    
    try:
        # Check if input file exists
        if not os.path.exists(args.input_file):
            print(f"Error: Input file '{args.input_file}' not found.")
            return 1
        
        # Check if TTS engine is available
        available_engines = list_engines()
        if args.engine not in available_engines:
            print(f"Error: TTS engine '{args.engine}' is not available.")
            print(f"Available engines: {', '.join(available_engines)}")
            return 1
        
        # Load ebook
        print(f"Loading ebook: {args.input_file}")
        ebook = Ebook(args.input_file)
        
        # Extract text only if requested
        if args.text_only:
            print("Extracting text...")
            text = ebook.get_full_text()
            
            with open(args.output_file, 'w', encoding='utf-8') as f:
                f.write(text)
            
            print(f"Text extracted to {args.output_file}")
            return 0
        
        # Get TTS engine
        print(f"Initializing TTS engine: {args.engine}")
        tts_config = {
            'language': args.language
        }
        
        if args.voice:
            tts_config['voice'] = args.voice
        
        tts_engine = get_tts_engine(args.engine, tts_config)
        
        # Create converter
        converter = BookConverter(ebook, tts_engine)
        
        # Define progress callback
        def progress_callback(progress):
            sys.stdout.write(f"\rProgress: {progress:.1f}%")
            sys.stdout.flush()
        
        # Define status callback
        def status_callback(status):
            print(f"\n{status}")
        
        # Convert book
        print(f"Converting {ebook.title} to audio...")
        converter.convert_book(args.output_file, progress_callback, status_callback)
        
        print(f"\nAudiobook saved to {args.output_file}")
        return 0
    
    except Exception as e:
        print(f"Error: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())

