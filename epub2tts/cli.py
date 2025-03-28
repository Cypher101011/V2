"""
Command-line interface for EPUB2TTS
"""

import os
import sys
import logging
import argparse
from pathlib import Path

from . import __version__
from .core.logger import setup_logger
from .core.config import Config
from .core.ebook import Ebook
from .core.tts_engines import get_tts_engine, list_engines, list_voices
from .converters.book_converter import BookConverter
from .whisper.transcriber import WhisperTranscriber
from .core.exceptions import EPUB2TTSError

# Setup logger
logger = setup_logger()

def convert_command(args):
    """
    Handle convert command
    
    Args:
        args: Command-line arguments
        
    Returns:
        int: Exit code
    """
    try:
        # Load configuration
        config = Config()
        
        # Override configuration with command-line arguments
        config.set('tts_engine', args.engine)
        config.set('voice', args.voice)
        config.set('language', args.language)
        config.set('chunk_size', args.chunk_size)
        config.set('max_workers', args.processes)
        config.set('keep_temp_files', args.keep_temp)
        
        if args.voice_sample:
            config.set('voice_sample', args.voice_sample)
        
        # Load ebook
        logger.info(f"Loading ebook: {args.input_file}")
        ebook = Ebook(args.input_file)
        
        # Get TTS engine
        logger.info(f"Initializing TTS engine: {args.engine}")
        tts_engine = get_tts_engine(args.engine, config)
        
        # Create converter
        converter = BookConverter(ebook, tts_engine, config)
        
        # Define progress callback
        def progress_callback(progress):
            sys.stdout.write(f"\rProgress: {progress:.1f}%")
            sys.stdout.flush()
        
        # Define status callback
        def status_callback(status):
            print(f"\n{status}")
        
        # Convert book
        if args.text_only:
            # Extract text only
            text = ebook.get_full_text()
            
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(text)
            
            print(f"Text extracted to {args.output}")
        else:
            # Convert to audio
            print(f"Converting {ebook.title} to audio...")
            converter.convert_book(args.output, progress_callback, status_callback)
            print(f"\nAudiobook saved to {args.output}")
        
        return 0
    
    except EPUB2TTSError as e:
        logger.error(str(e))
        print(f"Error: {str(e)}")
        return 1
    
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        print(f"Unexpected error: {str(e)}")
        return 1

def extract_command(args):
    """
    Handle extract command
    
    Args:
        args: Command-line arguments
        
    Returns:
        int: Exit code
    """
    try:
        # Load ebook
        logger.info(f"Loading ebook: {args.input_file}")
        ebook = Ebook(args.input_file)
        
        # Extract text
        text = ebook.get_full_text()
        
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(text)
        
        print(f"Text extracted to {args.output}")
        return 0
    
    except EPUB2TTSError as e:
        logger.error(str(e))
        print(f"Error: {str(e)}")
        return 1
    
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        print(f"Unexpected error: {str(e)}")
        return 1

def transcribe_command(args):
    """
    Handle transcribe command
    
    Args:
        args: Command-line arguments
        
    Returns:
        int: Exit code
    """
    try:
        # Initialize transcriber
        logger.info(f"Initializing Whisper transcriber with model: {args.model}")
        transcriber = WhisperTranscriber(args.model, args.language)
        
        # Transcribe audio
        logger.info(f"Transcribing audio: {args.audio_file}")
        text = transcriber.transcribe(args.audio_file, args.output)
        
        if not args.output:
            print(text)
        else:
            print(f"Transcription saved to {args.output}")
        
        return 0
    
    except EPUB2TTSError as e:
        logger.error(str(e))
        print(f"Error: {str(e)}")
        return 1
    
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        print(f"Unexpected error: {str(e)}")
        return 1

def record_command(args):
    """
    Handle record command
    
    Args:
        args: Command-line arguments
        
    Returns:
        int: Exit code
    """
    try:
        # Initialize transcriber
        if args.transcribe:
            logger.info(f"Initializing Whisper transcriber with model: {args.model}")
            transcriber = WhisperTranscriber(args.model, args.language)
            
            # Record and transcribe
            logger.info(f"Recording and transcribing audio for {args.duration} seconds")
            text = transcriber.record_and_transcribe(args.duration, args.output, args.text_output)
            
            if not args.text_output:
                print(text)
            else:
                print(f"Transcription saved to {args.text_output}")
        else:
            # Record audio only
            from .core.audio_utils import record_audio
            
            logger.info(f"Recording audio for {args.duration} seconds")
            record_audio(args.output, args.duration)
            
            print(f"Audio recorded to {args.output}")
        
        return 0
    
    except EPUB2TTSError as e:
        logger.error(str(e))
        print(f"Error: {str(e)}")
        return 1
    
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        print(f"Unexpected error: {str(e)}")
        return 1

def list_command(args):
    """
    Handle list command
    
    Args:
        args: Command-line arguments
        
    Returns:
        int: Exit code
    """
    try:
        if args.what == "engines":
            # List TTS engines
            engines = list_engines()
            print("Available TTS engines:")
            for engine in engines:
                print(f"- {engine}")
        
        elif args.what == "voices":
            # List voices for TTS engine
            voices = list_voices(args.engine)
            print(f"Available voices for {args.engine}:")
            for voice in voices:
                print(f"- {voice}")
        
        elif args.what == "models":
            # List Whisper models
            try:
                transcriber = WhisperTranscriber()
                models = transcriber.list_models()
                print("Available Whisper models:")
                for model in models:
                    print(f"- {model}")
            except EPUB2TTSError:
                print("Whisper is not installed. Please install it with 'pip install openai-whisper'.")
        
        return 0
    
    except EPUB2TTSError as e:
        logger.error(str(e))
        print(f"Error: {str(e)}")
        return 1
    
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        print(f"Unexpected error: {str(e)}")
        return 1

def gui_command(args):
    """
    Handle GUI command
    
    Args:
        args: Command-line arguments
        
    Returns:
        int: Exit code
    """
    try:
        from .gui import main as gui_main
        
        logger.info("Starting GUI")
        return gui_main()
    
    except ImportError:
        logger.error("tkinter is required for GUI. Please install it.")
        print("Error: tkinter is required for GUI. Please install it.")
        return 1
    
    except EPUB2TTSError as e:
        logger.error(str(e))
        print(f"Error: {str(e)}")
        return 1
    
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        print(f"Unexpected error: {str(e)}")
        return 1

def main():
    """Main entry point for command-line interface"""
    parser = argparse.ArgumentParser(
        description=f"EPUB2TTS v{__version__} - Convert ebooks to audiobooks"
    )
    
    # Add version argument
    parser.add_argument(
        '--version', 
        action='version', 
        version=f"EPUB2TTS v{__version__}"
    )
    
    # Add verbose argument
    parser.add_argument(
        '-v', '--verbose', 
        action='store_true', 
        help="Enable verbose output"
    )
    
    # Create subparsers for commands
    subparsers = parser.add_subparsers(dest='command', help="Command to run")
    
    # Convert command
    convert_parser = subparsers.add_parser('convert', help="Convert ebook to audiobook")
    convert_parser.add_argument('input_file', help="Input ebook file (EPUB, PDF, TXT)")
    convert_parser.add_argument('output', help="Output audio file")
    convert_parser.add_argument('-e', '--engine', default='edge', help="TTS engine (default: edge)")
    convert_parser.add_argument('-v', '--voice', help="Voice to use")
    convert_parser.add_argument('-l', '--language', default='en', help="Language code (default: en)")
    convert_parser.add_argument('-s', '--voice-sample', help="Voice sample file for XTTS")
    convert_parser.add_argument('-c', '--chunk-size', type=int, default=2000, help="Text chunk size (default: 2000)")
    convert_parser.add_argument('-p', '--processes', type=int, default=4, help="Number of processes (default: 4)")
    convert_parser.add_argument('-t', '--text-only', action='store_true', help="Extract text only")
    convert_parser.add_argument('-k', '--keep-temp', action='store_true', help="Keep temporary files")
    
    # Extract command
    extract_parser = subparsers.add_parser('extract', help="Extract text from ebook")
    extract_parser.add_argument('input_file', help="Input ebook file (EPUB, PDF, TXT)")
    extract_parser.add_argument('output', help="Output text file")
    
    # Transcribe command
    transcribe_parser = subparsers.add_parser('transcribe', help="Transcribe audio file")
    transcribe_parser.add_argument('audio_file', help="Input audio file")
    transcribe_parser.add_argument('output', nargs='?', help="Output text file")
    transcribe_parser.add_argument('-m', '--model', default='base', help="Whisper model (default: base)")
    transcribe_parser.add_argument('-l', '--language', help="Language code")
    
    # Record command
    record_parser = subparsers.add_parser('record', help="Record audio")
    record_parser.add_argument('output', help="Output audio file")
    record_parser.add_argument('-d', '--duration', type=int, default=5, help="Recording duration in seconds (default: 5)")
    record_parser.add_argument('-t', '--transcribe', action='store_true', help="Transcribe recording")
    record_parser.add_argument('-o', '--text-output', help="Output text file for transcription")
    record_parser.add_argument('-m', '--model', default='base', help="Whisper model for transcription (default: base)")
    record_parser.add_argument('-l', '--language', help="Language code for transcription")
    
    # List command
    list_parser = subparsers.add_parser('list', help="List available engines, voices, or models")
    list_parser.add_argument('what', choices=['engines', 'voices', 'models'], help="What to list")
    list_parser.add_argument('-e', '--engine', default='edge', help="TTS engine for listing voices (default: edge)")
    
    # GUI command
    gui_parser = subparsers.add_parser('gui', help="Start graphical user interface")
    
    # Parse arguments
    args = parser.parse_args()
    
    # Set logging level
    if args.verbose:
        logger.setLevel(logging.DEBUG)
    
    # Handle commands
    if args.command == 'convert':
        return convert_command(args)
    elif args.command == 'extract':
        return extract_command(args)
    elif args.command == 'transcribe':
        return transcribe_command(args)
    elif args.command == 'record':
        return record_command(args)
    elif args.command == 'list':
        return list_command(args)
    elif args.command == 'gui':
        return gui_command(args)
    else:
        # No command specified, show help
        parser.print_help()
        return 0

if __name__ == '__main__':
    sys.exit(main())

