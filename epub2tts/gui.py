"""
Graphical user interface for EPUB2TTS
"""

import os
import sys
import time
import logging
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
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

class EPUB2TTSGUI:
    """Main GUI class for EPUB2TTS"""
    
    def __init__(self, root):
        """
        Initialize GUI
        
        Args:
            root: Tkinter root window
        """
        self.root = root
        self.root.title(f"EPUB2TTS v{__version__}")
        self.root.geometry("800x600")
        self.root.minsize(600, 400)
        
        # Set up exception handler
        self.root.report_callback_exception = self.handle_exception
        
        # Load configuration
        self.config = Config()
        
        # Initialize variables
        self.ebook = None
        self.tts_engine = None
        self.converter = None
        self.transcriber = None
        self.conversion_thread = None
        self.is_converting = False
        self.stop_requested = False
        
        # Create GUI elements
        self.create_menu()
        self.create_notebook()
        self.create_status_bar()
        
        # Apply theme
        self.theme_var = tk.StringVar(value=self.config.get('theme', 'system'))
        self.apply_theme()
        
        # Load engines and voices
        self.load_engines()
        self.load_voices()
        
        # Set up closing handler
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Set status
        self.set_status("Ready")
    
    def create_menu(self):
        """Create menu bar"""
        self.menu_bar = tk.Menu(self.root)
        
        # File menu
        self.file_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.file_menu.add_command(label="Open Ebook", command=self.open_ebook)
        self.file_menu.add_command(label="Save Text", command=self.save_text)
        self.file_menu.add_separator()
        self.file_menu.add_command(label="Exit", command=self.on_closing)
        self.menu_bar.add_cascade(label="File", menu=self.file_menu)
        
        # Tools menu
        self.tools_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.tools_menu.add_command(label="Record Audio", command=self.record_audio)
        self.tools_menu.add_command(label="Transcribe Audio", command=self.transcribe_audio)
        self.menu_bar.add_cascade(label="Tools", menu=self.tools_menu)
        
        # Settings menu
        self.settings_menu = tk.Menu(self.menu_bar, tearoff=0)
        
        # Theme submenu
        self.theme_menu = tk.Menu(self.settings_menu, tearoff=0)
        self.theme_menu.add_radiobutton(label="System", variable=self.theme_var, value="system", command=self.apply_theme)
        self.theme_menu.add_radiobutton(label="Light", variable=self.theme_var, value="light", command=self.apply_theme)
        self.theme_menu.add_radiobutton(label="Dark", variable=self.theme_var, value="dark", command=self.apply_theme)
        self.settings_menu.add_cascade(label="Theme", menu=self.theme_menu)
        
        self.settings_menu.add_separator()
        self.settings_menu.add_command(label="Save Settings", command=self.save_settings)
        self.menu_bar.add_cascade(label="Settings", menu=self.settings_menu)
        
        # Help menu
        self.help_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.help_menu.add_command(label="About", command=self.show_about)
        self.menu_bar.add_cascade(label="Help", menu=self.help_menu)
        
        self.root.config(menu=self.menu_bar)
    
    def create_notebook(self):
        """Create notebook with tabs"""
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create tabs
        self.create_convert_tab()
        self.create_text_tab()
        self.create_settings_tab()
    
    def create_convert_tab(self):
        """Create convert tab"""
        self.convert_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.convert_tab, text="Convert")
        
        # Input file
        ttk.Label(self.convert_tab, text="Input File:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        
        self.input_file_var = tk.StringVar()
        self.input_file_entry = ttk.Entry(self.convert_tab, textvariable=self.input_file_var, width=50)
        self.input_file_entry.grid(row=0, column=1, sticky=tk.W+tk.E, padx=5, pady=5)
        
        self.browse_button = ttk.Button(self.convert_tab, text="Browse", command=self.browse_input_file)
        self.browse_button.grid(row=0, column=2, sticky=tk.W, padx=5, pady=5)
        
        # Output file
        ttk.Label(self.convert_tab, text="Output File:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        
        self.output_file_var = tk.StringVar()
        self.output_file_entry = ttk.Entry(self.convert_tab, textvariable=self.output_file_var, width=50)
        self.output_file_entry.grid(row=1, column=1, sticky=tk.W+tk.E, padx=5, pady=5)
        
        self.output_browse_button = ttk.Button(self.convert_tab, text="Browse", command=self.browse_output_file)
        self.output_browse_button.grid(row=1, column=2, sticky=tk.W, padx=5, pady=5)
        
        # TTS Engine
        ttk.Label(self.convert_tab, text="TTS Engine:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        
        self.engine_var = tk.StringVar(value=self.config.get('tts_engine', 'edge'))
        self.engine_combobox = ttk.Combobox(self.convert_tab, textvariable=self.engine_var, state="readonly")
        self.engine_combobox.grid(row=2, column=1, sticky=tk.W+tk.E, padx=5, pady=5)
        self.engine_combobox.bind("<<ComboboxSelected>>", self.on_engine_change)
        
        # Voice
        ttk.Label(self.convert_tab, text="Voice:").grid(row=3, column=0, sticky=tk.W, padx=5, pady=5)
        
        self.voice_var = tk.StringVar(value=self.config.get('voice', ''))
        self.voice_combobox = ttk.Combobox(self.convert_tab, textvariable=self.voice_var, state="readonly")
        self.voice_combobox.grid(row=3, column=1, sticky=tk.W+tk.E, padx=5, pady=5)
        
        # Language
        ttk.Label(self.convert_tab, text="Language:").grid(row=4, column=0, sticky=tk.W, padx=5, pady=5)
        
        self.language_var = tk.StringVar(value=self.config.get('language', 'en'))
        self.language_entry = ttk.Entry(self.convert_tab, textvariable=self.language_var)
        self.language_entry.grid(row=4, column=1, sticky=tk.W+tk.E, padx=5, pady=5)
        
        # Voice sample (for XTTS)
        ttk.Label(self.convert_tab, text="Voice Sample:").grid(row=5, column=0, sticky=tk.W, padx=5, pady=5)
        
        self.voice_sample_var = tk.StringVar(value=self.config.get('voice_sample', ''))
        self.voice_sample_entry = ttk.Entry(self.convert_tab, textvariable=self.voice_sample_var)
        self.voice_sample_entry.grid(row=5, column=1, sticky=tk.W+tk.E, padx=5, pady=5)
        
        self.voice_sample_button = ttk.Button(self.convert_tab, text="Browse", command=self.browse_voice_sample)
        self.voice_sample_button.grid(row=5, column=2, sticky=tk.W, padx=5, pady=5)
        
        # Options frame
        self.options_frame = ttk.LabelFrame(self.convert_tab, text="Options")
        self.options_frame.grid(row=6, column=0, columnspan=3, sticky=tk.W+tk.E, padx=5, pady=5)
        
        # Chunk size
        ttk.Label(self.options_frame, text="Chunk Size:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        
        self.chunk_size_var = tk.IntVar(value=self.config.get('chunk_size', 2000))
        self.chunk_size_spinbox = ttk.Spinbox(self.options_frame, from_=100, to=10000, increment=100, textvariable=self.chunk_size_var)
        self.chunk_size_spinbox.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        
        # Processes
        ttk.Label(self.options_frame, text="Processes:").grid(row=0, column=2, sticky=tk.W, padx=5, pady=5)
        
        self.processes_var = tk.IntVar(value=self.config.get('max_workers', 4))
        self.processes_spinbox = ttk.Spinbox(self.options_frame, from_=1, to=16, increment=1, textvariable=self.processes_var)
        self.processes_spinbox.grid(row=0, column=3, sticky=tk.W, padx=5, pady=5)
        
        # Text only checkbox
        self.text_only_var = tk.BooleanVar(value=False)
        self.text_only_check = ttk.Checkbutton(self.options_frame, text="Extract Text Only", variable=self.text_only_var)
        self.text_only_check.grid(row=1, column=0, columnspan=2, sticky=tk.W, padx=5, pady=5)
        
        # Keep temp files checkbox
        self.keep_temp_var = tk.BooleanVar(value=self.config.get('keep_temp_files', False))
        self.keep_temp_check = ttk.Checkbutton(self.options_frame, text="Keep Temporary Files", variable=self.keep_temp_var)
        self.keep_temp_check.grid(row=1, column=2, columnspan=2, sticky=tk.W, padx=5, pady=5)
        
        # Progress bar
        ttk.Label(self.convert_tab, text="Progress:").grid(row=7, column=0, sticky=tk.W, padx=5, pady=5)
        
        self.progress_var = tk.DoubleVar(value=0)
        self.progress_bar = ttk.Progressbar(self.convert_tab, variable=self.progress_var, maximum=100)
        self.progress_bar.grid(row=7, column=1, columnspan=2, sticky=tk.W+tk.E, padx=5, pady=5)
        
        # Buttons frame
        self.buttons_frame = ttk.Frame(self.convert_tab)
        self.buttons_frame.grid(row=8, column=0, columnspan=3, sticky=tk.W+tk.E, padx=5, pady=5)
        
        # Convert button
        self.convert_button = ttk.Button(self.buttons_frame, text="Convert", command=self.convert)
        self.convert_button.pack(side=tk.LEFT, padx=5, pady=5)
        
        # Stop button
        self.stop_button = ttk.Button(self.buttons_frame, text="Stop", command=self.stop_conversion, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=5, pady=5)
        
        # Configure grid
        self.convert_tab.columnconfigure(1, weight=1)
    
    def create_text_tab(self):
        """Create text tab"""
        self.text_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.text_tab, text="Text")
        
        # Text area
        self.text_area = tk.Text(self.text_tab, wrap=tk.WORD)
        self.text_area.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Scrollbar
        self.text_scrollbar = ttk.Scrollbar(self.text_area, command=self.text_area.yview)
        self.text_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.text_area.config(yscrollcommand=self.text_scrollbar.set)
    
    def create_settings_tab(self):
        """Create settings tab"""
        self.settings_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.settings_tab, text="Settings")
        
        # TTS Settings
        self.tts_frame = ttk.LabelFrame(self.settings_tab, text="TTS Settings")
        self.tts_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Speed
        ttk.Label(self.tts_frame, text="Speed:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        
        self.speed_var = tk.IntVar(value=self.config.get('speed', 150))
        self.speed_scale = ttk.Scale(self.tts_frame, from_=50, to=300, variable=self.speed_var, orient=tk.HORIZONTAL)
        self.speed_scale.grid(row=0, column=1, sticky=tk.W+tk.E, padx=5, pady=5)
        
        self.speed_label = ttk.Label(self.tts_frame, text=  padx=5, pady=5)
        
        self.speed_label = ttk.Label(self.tts_frame, text=str(self.speed_var.get()))
        self.speed_label.grid(row=0, column=2, sticky=tk.W, padx=5, pady=5)
        self.speed_scale.config(command=lambda val: self.speed_label.config(text=str(int(float(val)))))
        
        # Volume
        ttk.Label(self.tts_frame, text="Volume:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        
        self.volume_var = tk.IntVar(value=self.config.get('volume', 100))
        self.volume_scale = ttk.Scale(self.tts_frame, from_=0, to=200, variable=self.volume_var, orient=tk.HORIZONTAL)
        self.volume_scale.grid(row=1, column=1, sticky=tk.W+tk.E, padx=5, pady=5)
        
        self.volume_label = ttk.Label(self.tts_frame, text=str(self.volume_var.get()))
        self.volume_label.grid(row=1, column=2, sticky=tk.W, padx=5, pady=5)
        self.volume_scale.config(command=lambda val: self.volume_label.config(text=str(int(float(val)))))
        
        # Pitch
        ttk.Label(self.tts_frame, text="Pitch:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        
        self.pitch_var = tk.IntVar(value=self.config.get('pitch', 0))
        self.pitch_scale = ttk.Scale(self.tts_frame, from_=-50, to=50, variable=self.pitch_var, orient=tk.HORIZONTAL)
        self.pitch_scale.grid(row=2, column=1, sticky=tk.W+tk.E, padx=5, pady=5)
        
        self.pitch_label = ttk.Label(self.tts_frame, text=str(self.pitch_var.get()))
        self.pitch_label.grid(row=2, column=2, sticky=tk.W, padx=5, pady=5)
        self.pitch_scale.config(command=lambda val: self.pitch_label.config(text=str(int(float(val)))))
        
        # Output Settings
        self.output_frame = ttk.LabelFrame(self.settings_tab, text="Output Settings")
        self.output_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Output format
        ttk.Label(self.output_frame, text="Format:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        
        self.format_var = tk.StringVar(value=self.config.get('output_format', 'mp3'))
        self.format_combobox = ttk.Combobox(self.output_frame, textvariable=self.format_var, values=['mp3', 'wav', 'ogg'], state="readonly")
        self.format_combobox.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        
        # Output quality
        ttk.Label(self.output_frame, text="Quality (kbps):").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        
        self.quality_var = tk.IntVar(value=self.config.get('output_quality', 192))
        self.quality_combobox = ttk.Combobox(self.output_frame, textvariable=self.quality_var, values=[64, 128, 192, 256, 320], state="readonly")
        self.quality_combobox.grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)
        
        # Sample rate
        ttk.Label(self.output_frame, text="Sample Rate (Hz):").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        
        self.sample_rate_var = tk.IntVar(value=self.config.get('output_sample_rate', 44100))
        self.sample_rate_combobox = ttk.Combobox(self.output_frame, textvariable=self.sample_rate_var, values=[8000, 16000, 22050, 44100, 48000], state="readonly")
        self.sample_rate_combobox.grid(row=2, column=1, sticky=tk.W, padx=5, pady=5)
        
        # Whisper Settings
        self.whisper_frame = ttk.LabelFrame(self.settings_tab, text="Whisper Settings")
        self.whisper_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Whisper model
        ttk.Label(self.whisper_frame, text="Model:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        
        self.whisper_model_var = tk.StringVar(value=self.config.get('whisper_model', 'base'))
        self.whisper_model_combobox = ttk.Combobox(self.whisper_frame, textvariable=self.whisper_model_var, values=['tiny', 'base', 'small', 'medium', 'large'], state="readonly")
        self.whisper_model_combobox.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        
        # Whisper language
        ttk.Label(self.whisper_frame, text="Language:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        
        self.whisper_language_var = tk.StringVar(value=self.config.get('whisper_language', ''))
        self.whisper_language_entry = ttk.Entry(self.whisper_frame, textvariable=self.whisper_language_var)
        self.whisper_language_entry.grid(row=1, column=1, sticky=tk.W+tk.E, padx=5, pady=5)
        
        # Save button
        self.save_settings_button = ttk.Button(self.settings_tab, text="Save Settings", command=self.save_settings)
        self.save_settings_button.pack(padx=5, pady=5)
        
        # Configure grid
        self.tts_frame.columnconfigure(1, weight=1)
        self.output_frame.columnconfigure(1, weight=1)
        self.whisper_frame.columnconfigure(1, weight=1)
    
    def create_status_bar(self):
        """Create status bar"""
        self.status_var = tk.StringVar(value="Ready")
        self.status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def apply_theme(self):
        """Apply theme to GUI"""
        theme = self.theme_var.get()
        
        if theme == "system":
            # Try to detect system theme
            try:
                import darkdetect
                theme = "dark" if darkdetect.isDark() else "light"
            except ImportError:
                # Default to light theme if darkdetect is not available
                theme = "light"
        
        if theme == "dark":
            # Apply dark theme
            self.root.tk_setPalette(
                background='#2d2d2d',
                foreground='#ffffff',
                activeBackground='#4d4d4d',
                activeForeground='#ffffff'
            )
            
            # Configure ttk styles
            style = ttk.Style()
            
            # Try to use a dark theme if available
            try:
                style.theme_use("clam")
            except tk.TclError:
                pass
            
            # Configure colors
            style.configure("TLabel", background='#2d2d2d', foreground='#ffffff')
            style.configure("TFrame", background='#2d2d2d')
            style.configure("TButton", background='#4d4d4d', foreground='#ffffff')
            style.configure("TCheckbutton", background='#2d2d2d', foreground='#ffffff')
            style.configure("TRadiobutton", background='#2d2d2d', foreground='#ffffff')
            style.configure("TLabelframe", background='#2d2d2d', foreground='#ffffff')
            style.configure("TLabelframe.Label", background='#2d2d2d', foreground='#ffffff')
            style.configure("TNotebook", background='#2d2d2d', foreground='#ffffff')
            style.configure("TNotebook.Tab", background='#4d4d4d', foreground='#ffffff')
            
            # Configure text area
            if hasattr(self, 'text_area'):
                self.text_area.config(bg='#2d2d2d', fg='#ffffff', insertbackground='#ffffff')
        else:
            # Apply light theme (system default)
            self.root.tk_setPalette(background=None, foreground=None)
            
            # Reset ttk styles
            style = ttk.Style()
            
            # Try to use the default theme
            try:
                style.theme_use("default")
            except tk.TclError:
                pass
            
            # Configure text area
            if hasattr(self, 'text_area'):
                self.text_area.config(bg='white', fg='black', insertbackground='black')
        
        # Save theme setting
        self.config.set('theme', self.theme_var.get())
    
    def load_engines(self):
        """Load available TTS engines"""
        try:
            engines = list_engines()
            self.engine_combobox['values'] = engines
            
            if not engines:
                messagebox.showwarning("No TTS Engines", "No TTS engines found. Please install at least one TTS engine.")
                self.set_status("No TTS engines found")
            elif self.engine_var.get() not in engines:
                self.engine_var.set(engines[0])
        except Exception as e:
            logger.error(f"Error loading TTS engines: {str(e)}")
            self.set_status(f"Error loading TTS engines: {str(e)}")
    
    def load_voices(self):
        """Load available voices for selected TTS engine"""
        try:
            engine = self.engine_var.get()
            voices = list_voices(engine)
            self.voice_combobox['values'] = voices
            
            if not voices:
                self.set_status(f"No voices found for {engine}")
            elif self.voice_var.get() not in voices and voices:
                self.voice_var.set(voices[0])
        except Exception as e:
            logger.error(f"Error loading voices: {str(e)}")
            self.set_status(f"Error loading voices: {str(e)}")
    
    def on_engine_change(self, event=None):
        """Handle TTS engine change"""
        self.load_voices()
        
        # Show/hide voice sample field based on engine
        if self.engine_var.get() == "xtts":
            self.voice_sample_entry.config(state=tk.NORMAL)
            self.voice_sample_button.config(state=tk.NORMAL)
        else:
            self.voice_sample_entry.config(state=tk.DISABLED)
            self.voice_sample_button.config(state=tk.DISABLED)
    
    def browse_input_file(self):
        """Browse for input file"""
        filetypes = [
            ("Ebook files", "*.epub *.pdf *.txt"),
            ("EPUB files", "*.epub"),
            ("PDF files", "*.pdf"),
            ("Text files", "*.txt"),
            ("All files", "*.*")
        ]
        
        filename = filedialog.askopenfilename(
            title="Select Ebook File",
            filetypes=filetypes,
            initialdir=self.config.get('last_directory')
        )
        
        if filename:
            self.input_file_var.set(filename)
            
            # Set default output file
            input_path = Path(filename)
            output_path = input_path.with_suffix(f".{self.format_var.get()}")
            self.output_file_var.set(str(output_path))
            
            # Save last directory
            self.config.set('last_directory', str(input_path.parent))
            
            # Load ebook
            self.load_ebook(filename)
    
    def browse_output_file(self):
        """Browse for output file"""
        filetypes = [
            ("MP3 files", "*.mp3"),
            ("WAV files", "*.wav"),
            ("OGG files", "*.ogg"),
            ("Text files", "*.txt"),
            ("All files", "*.*")
        ]
        
        filename = filedialog.asksaveasfilename(
            title="Select Output File",
            filetypes=filetypes,
            initialdir=self.config.get('last_directory'),
            initialfile=Path(self.output_file_var.get()).name if self.output_file_var.get() else None
        )
        
        if filename:
            self.output_file_var.set(filename)
            
            # Save last directory
            self.config.set('last_directory', str(Path(filename).parent))
    
    def browse_voice_sample(self):
        """Browse for voice sample file"""
        filetypes = [
            ("Audio files", "*.wav *.mp3 *.ogg"),
            ("WAV files", "*.wav"),
            ("MP3 files", "*.mp3"),
            ("OGG files", "*.ogg"),
            ("All files", "*.*")
        ]
        
        filename = filedialog.askopenfilename(
            title="Select Voice Sample",
            filetypes=filetypes,
            initialdir=self.config.get('last_directory')
        )
        
        if filename:
            self.voice_sample_var.set(filename)
            
            # Save last directory
            self.config.set('last_directory', str(Path(filename).parent))
    
    def load_ebook(self, filename):
        """Load ebook file"""
        try:
            self.set_status(f"Loading {filename}...")
            self.ebook = Ebook(filename)
            
            # Display ebook metadata
            metadata = self.ebook.get_metadata()
            title = metadata.get('title', Path(filename).name)
            author = metadata.get('author', 'Unknown')
            
            self.set_status(f"Loaded {title} by {author}")
            
            # Extract text
            self.extract_text()
        except EPUB2TTSError as e:
            logger.error(f"Error loading ebook: {str(e)}")
            messagebox.showerror("Error Loading Ebook", str(e))
            self.set_status(f"Error loading ebook: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error loading ebook: {str(e)}")
            messagebox.showerror("Unexpected Error", f"An unexpected error occurred: {str(e)}")
            self.set_status(f"Unexpected error: {str(e)}")
    
    def extract_text(self):
        """Extract text from ebook"""
        if not self.ebook:
            return
        
        try:
            self.set_status("Extracting text...")
            text = self.ebook.get_full_text()
            
            # Display text
            self.text_area.delete(1.0, tk.END)
            self.text_area.insert(tk.END, text)
            
            self.set_status("Text extracted successfully")
            
            # Switch to text tab
            self.notebook.select(1)
        except EPUB2TTSError as e:
            logger.error(f"Error extracting text: {str(e)}")
            messagebox.showerror("Error Extracting Text", str(e))
            self.set_status(f"Error extracting text: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error extracting text: {str(e)}")
            messagebox.showerror("Unexpected Error", f"An unexpected error occurred: {str(e)}")
            self.set_status(f"Unexpected error: {str(e)}")
    
    def save_text(self):
        """Save extracted text to file"""
        if not self.text_area.get(1.0, tk.END).strip():
            messagebox.showwarning("No Text", "No text to save.")
            return
        
        filetypes = [
            ("Text files", "*.txt"),
            ("All files", "*.*")
        ]
        
        filename = filedialog.asksaveasfilename(
            title="Save Text",
            filetypes=filetypes,
            initialdir=self.config.get('last_directory'),
            defaultextension=".txt"
        )
        
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(self.text_area.get(1.0, tk.END))
                
                self.set_status(f"Text saved to {filename}")
                
                # Save last directory
                self.config.set('last_directory', str(Path(filename).parent))
            except Exception as e:
                logger.error(f"Error saving text: {str(e)}")
                messagebox.showerror("Error Saving Text", f"Error saving text: {str(e)}")
                self.set_status(f"Error saving text: {str(e)}")
    
    def convert(self):
        """Convert ebook to audiobook"""
        if self.is_converting:
            messagebox.showwarning("Conversion in Progress", "A conversion is already in progress.")
            return
        
        if not self.input_file_var.get():
            messagebox.showwarning("No Input File", "Please select an input file.")
            return
        
        if not self.output_file_var.get():
            messagebox.showwarning("No Output File", "Please select an output file.")
            return
        
        # Update configuration from GUI
        self.update_config_from_gui()
        
        # Start conversion in a separate thread
        self.conversion_thread = threading.Thread(target=self.conversion_worker)
        self.conversion_thread.daemon = True
        self.conversion_thread.start()
        
        # Update UI
        self.is_converting = True
        self.stop_requested = False
        self.convert_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.set_status("Converting...")
    
    def conversion_worker(self):
        """Worker function for conversion thread"""
        try:
            # Load ebook if not already loaded
            if not self.ebook or self.ebook.file_path != Path(self.input_file_var.get()):
                self.ebook = Ebook(self.input_file_var.get())
            
            # Get TTS engine
            self.tts_engine = get_tts_engine(
                self.engine_var.get(),
                {
                    'voice': self.voice_var.get(),
                    'language': self.language_var.get(),
                    'voice_sample': self.voice_sample_var.get(),
                    'speed': self.speed_var.get(),
                    'volume': self.volume_var.get(),
                    'pitch': self.pitch_var.get()
                }
            )
            
            # Create converter
            self.converter = BookConverter(
                self.ebook,
                self.tts_engine,
                {
                    'chunk_size': self.chunk_size_var.get(),
                    'max_workers': self.processes_var.get(),
                    'keep_temp_files': self.keep_temp_var.get(),
                    'output_format': self.format_var.get(),
                    'output_quality': self.quality_var.get(),
                    'output_sample_rate': self.sample_rate_var.get()
                }
            )
            
            # Define progress callback
            def progress_callback(progress):
                if not self.stop_requested:
                    self.progress_var.set(progress)
            
            # Define status callback
            def status_callback(status):
                if not self.stop_requested:
                    self.set_status(status)
            
            if self.text_only_var.get():
                # Extract text only
                text = self.ebook.get_full_text()
                
                with open(self.output_file_var.get(), 'w', encoding='utf-8') as f:
                    f.write(text)
                
                self.set_status(f"Text extracted to {self.output_file_var.get()}")
            else:
                # Convert to audio
                self.converter.convert_book(
                    self.output_file_var.get(),
                    progress_callback,
                    status_callback
                )
                
                self.set_status(f"Conversion completed: {self.output_file_var.get()}")
            
            # Show success message
            if not self.stop_requested:
                messagebox.showinfo("Conversion Complete", "Conversion completed successfully.")
        
        except EPUB2TTSError as e:
            logger.error(f"Error during conversion: {str(e)}")
            if not self.stop_requested:
                messagebox.showerror("Conversion Error", str(e))
                self.set_status(f"Error: {str(e)}")
        
        except Exception as e:
            logger.error(f"Unexpected error during conversion: {str(e)}")
            if not self.stop_requested:
                messagebox.showerror("Unexpected Error", f"An unexpected error occurred: {str(e)}")
                self.set_status(f"Unexpected error: {str(e)}")
        
        finally:
            # Reset UI
            self.is_converting = False
            self.convert_button.config(state=tk.NORMAL)
            self.stop_button.config(state=tk.DISABLED)
            
            if self.stop_requested:
                self.set_status("Conversion stopped")
                self.stop_requested = False
    
    def stop_conversion(self):
        """Stop conversion"""
        if not self.is_converting:
            return
        
        self.stop_requested = True
        self.set_status("Stopping conversion...")
        
        # Stop TTS engine
        if self.tts_engine:
            try:
                self.tts_engine.stop()
            except Exception as e:
                logger.error(f"Error stopping TTS engine: {str(e)}")
    
    def update_config_from_gui(self):
        """Update configuration from GUI values"""
        self.config.set('tts_engine', self.engine_var.get())
        self.config.set('voice', self.voice_var.get())
        self.config.set('language', self.language_var.get())
        self.config.set('voice_sample', self.voice_sample_var.get())
        self.config.set('speed', self.speed_var.get())
        self.config.set('volume', self.volume_var.get())
        self.config.set('pitch', self.pitch_var.get())
        self.config.set('chunk_size', self.chunk_size_var.get())
        self.config.set('max_workers', self.processes_var.get())
        self.config.set('keep_temp_files', self.keep_temp_var.get())
        self.config.set('output_format', self.format_var.get())
        self.config.set('output_quality', self.quality_var.get())
        self.config.set('output_sample_rate', self.sample_rate_var.get())
        self.config.set('whisper_model', self.whisper_model_var.get())
        self.config.set('whisper_language', self.whisper_language_var.get())
    
    def save_settings(self):
        """Save settings to configuration file"""
        try:
            self.update_config_from_gui()
            self.config.save()
            self.set_status("Settings saved successfully")
            messagebox.showinfo("Settings Saved", "Settings saved successfully.")
        except Exception as e:
            logger.error(f"Error saving settings: {str(e)}")
            messagebox.showerror("Error Saving Settings", f"Error saving settings: {str(e)}")
            self.set_status(f"Error saving settings: {str(e)}")
    
    def record_audio(self):
        """Record audio"""
        # Create dialog
        dialog = tk.Toplevel(self.root)
        dialog.title("Record Audio")
        dialog.geometry("400x200")
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Output file
        ttk.Label(dialog, text="Output File:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        
        output_var = tk.StringVar()
        output_entry = ttk.Entry(dialog, textvariable=output_var, width=30)
        output_entry.grid(row=0, column=1, sticky=tk.W+tk.E, padx=5, pady=5)
        
        browse_button = ttk.Button(
            dialog, 
            text="Browse", 
            command=lambda: output_var.set(filedialog.asksaveasfilename(
                title="Save Recording",
                filetypes=[("WAV files", "*.wav"), ("All files", "*.*")],
                initialdir=self.config.get('last_directory'),
                defaultextension=".wav"
            ))
        )
        browse_button.grid(row=0, column=2, sticky=tk.W, padx=5, pady=5)
        
        # Duration
        ttk.Label(dialog, text="Duration (seconds):").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        
        duration_var = tk.IntVar(value=5)
        duration_spinbox = ttk.Spinbox(dialog, from_=1, to=60, increment=1, textvariable=duration_var)
        duration_spinbox.grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)
        
        # Transcribe checkbox
        transcribe_var = tk.BooleanVar(value=False)
        transcribe_check = ttk.Checkbutton(dialog, text="Transcribe Recording", variable=transcribe_var)
        transcribe_check.grid(row=2, column=0, columnspan=2, sticky=tk.W, padx=5, pady=5)
        
        # Status label
        status_var = tk.StringVar(value="Ready to record")
        status_label = ttk.Label(dialog, textvariable=status_var)
        status_label.grid(row=3, column=0, columnspan=3, sticky=tk.W, padx=5, pady=5)
        
        # Buttons
        button_frame = ttk.Frame(dialog)
        button_frame.grid(row=4, column=0, columnspan=3, pady=10)
        
        record_button = ttk.Button(
            button_frame, 
            text="Record", 
            command=lambda: self.record_audio_worker(
                output_var.get(), 
                duration_var.get(), 
                transcribe_var.get(), 
                status_var, 
                record_button
            )
        )
        record_button.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(button_frame, text="Close", command=dialog.destroy).pack(side=tk.LEFT, padx=5)
        
        # Configure grid
        dialog.columnconfigure(1, weight=1)
    
    def record_audio_worker(self, output_file, duration, transcribe, status_var, record_button):
        """Worker function for audio recording"""
        if not output_file:
            messagebox.showwarning("No Output File", "Please select an output file.")
            return
        
        # Disable record button
        record_button.config(state=tk.DISABLED)
        
        # Start recording in a separate thread
        threading.Thread(
            target=self._record_audio_thread,
            args=(output_file, duration, transcribe, status_var, record_button),
            daemon=True
        ).start()
    
    def _record_audio_thread(self, output_file, duration, transcribe, status_var, record_button):
        """Thread function for audio recording"""
        try:
            from .core.audio_utils import record_audio
            
            # Update status
            status_var.set(f"Recording for {duration} seconds...")
            
            # Record audio
            record_audio(output_file, duration)
            
            # Transcribe if requested
            if transcribe:
                status_var.set("Transcribing...")
                
                # Initialize transcriber
                transcriber = WhisperTranscriber(
                    self.whisper_model_var.get(),
                    self.whisper_language_var.get()
                )
                
                # Transcribe audio
                text = transcriber.transcribe(output_file)
                
                # Save transcription
                text_file = Path(output_file).with_suffix('.txt')
                with open(text_file, 'w', encoding='utf-8') as f:
                    f.write(text)
                
                status_var.set(f"Transcription saved to {text_file}")
            else:
                status_var.set(f"Recording saved to {output_file}")
            
            # Save last directory
            self.config.set('last_directory', str(Path(output_file).parent))
        
        except EPUB2TTSError as e:
            logger.error(f"Error recording audio: {str(e)}")
            status_var.set(f"Error: {str(e)}")
            messagebox.showerror("Recording Error", str(e))
        
        except Exception as e:
            logger.error(f"Unexpected error recording audio: {str(e)}")
            status_var.set(f"Unexpected error: {str(e)}")
            messagebox.showerror("Unexpected Error", f"An unexpected error occurred: {str(e)}")
        
        finally:
            # Enable record button
            record_button.config(state=tk.NORMAL)
    
    def transcribe_audio(self):
        """Transcribe audio file"""
        # Create dialog
        dialog = tk.Toplevel(self.root)
        dialog.title("Transcribe Audio")
        dialog.geometry("400x200")
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Input file
        ttk.Label(dialog, text="Input File:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        
        input_var = tk.StringVar()
        input_entry = ttk.Entry(dialog, textvariable=input_var, width=30)
        input_entry.grid(row=0, column=1, sticky=tk.W+tk.E, padx=5, pady=5)
        
        browse_button = ttk.Button(
            dialog, 
            text="Browse", 
            command=lambda: input_var.set(filedialog.askopenfilename(

                title="Select Audio File",
                filetypes=[
                    ("Audio files", "*.wav *.mp3 *.ogg"),
                    ("WAV files", "*.wav"),
                    ("MP3 files", "*.mp3"),
                    ("OGG files", "*.ogg"),
                    ("All files", "*.*")
                ],
                initialdir=self.config.get('last_directory')
            ))
        )
        browse_button.grid(row=0, column=2, sticky=tk.W, padx=5, pady=5)
        
        # Output file
        ttk.Label(dialog, text="Output File:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        
        output_var = tk.StringVar()
        output_entry = ttk.Entry(dialog, textvariable=output_var, width=30)
        output_entry.grid(row=1, column=1, sticky=tk.W+tk.E, padx=5, pady=5)
        
        output_browse_button = ttk.Button(
            dialog, 
            text="Browse", 
            command=lambda: output_var.set(filedialog.asksaveasfilename(
                title="Save Transcription",
                filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
                initialdir=self.config.get('last_directory'),
                defaultextension=".txt"
            ))
        )
        output_browse_button.grid(row=1, column=2, sticky=tk.W, padx=5, pady=5)
        
        # Model
        ttk.Label(dialog, text="Model:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        
        model_var = tk.StringVar(value=self.whisper_model_var.get())
        model_combobox = ttk.Combobox(dialog, textvariable=model_var, values=['tiny', 'base', 'small', 'medium', 'large'], state="readonly")
        model_combobox.grid(row=2, column=1, sticky=tk.W, padx=5, pady=5)
        
        # Language
        ttk.Label(dialog, text="Language:").grid(row=3, column=0, sticky=tk.W, padx=5, pady=5)
        
        language_var = tk.StringVar(value=self.whisper_language_var.get())
        language_entry = ttk.Entry(dialog, textvariable=language_var)
        language_entry.grid(row=3, column=1, sticky=tk.W+tk.E, padx=5, pady=5)
        
        # Status label
        status_var = tk.StringVar(value="Ready to transcribe")
        status_label = ttk.Label(dialog, textvariable=status_var)
        status_label.grid(row=4, column=0, columnspan=3, sticky=tk.W, padx=5, pady=5)
        
        # Buttons
        button_frame = ttk.Frame(dialog)
        button_frame.grid(row=5, column=0, columnspan=3, pady=10)
        
        transcribe_button = ttk.Button(
            button_frame, 
            text="Transcribe", 
            command=lambda: self.transcribe_audio_worker(
                input_var.get(), 
                output_var.get(), 
                model_var.get(), 
                language_var.get(), 
                status_var, 
                transcribe_button
            )
        )
        transcribe_button.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(button_frame, text="Close", command=dialog.destroy).pack(side=tk.LEFT, padx=5)
        
        # Configure grid
        dialog.columnconfigure(1, weight=1)
    
    def transcribe_audio_worker(self, input_file, output_file, model, language, status_var, transcribe_button):
        """Worker function for audio transcription"""
        if not input_file:
            messagebox.showwarning("No Input File", "Please select an input file.")
            return
        
        # Disable transcribe button
        transcribe_button.config(state=tk.DISABLED)
        
        # Start transcription in a separate thread
        threading.Thread(
            target=self._transcribe_audio_thread,
            args=(input_file, output_file, model, language, status_var, transcribe_button),
            daemon=True
        ).start()
    
    def _transcribe_audio_thread(self, input_file, output_file, model, language, status_var, transcribe_button):
        """Thread function for audio transcription"""
        try:
            # Update status
            status_var.set("Transcribing...")
            
            # Initialize transcriber
            transcriber = WhisperTranscriber(model, language)
            
            # Transcribe audio
            text = transcriber.transcribe(input_file, output_file)
            
            if output_file:
                status_var.set(f"Transcription saved to {output_file}")
            else:
                # Create a dialog to display the transcription
                result_dialog = tk.Toplevel(self.root)
                result_dialog.title("Transcription Result")
                result_dialog.geometry("600x400")
                result_dialog.transient(self.root)
                result_dialog.grab_set()
                
                # Text area
                text_area = tk.Text(result_dialog, wrap=tk.WORD)
                text_area.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
                text_area.insert(tk.END, text)
                
                # Scrollbar
                scrollbar = ttk.Scrollbar(text_area, command=text_area.yview)
                scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
                text_area.config(yscrollcommand=scrollbar.set)
                
                # Close button
                ttk.Button(result_dialog, text="Close", command=result_dialog.destroy).pack(pady=5)
                
                status_var.set("Transcription completed")
            
            # Save last directory
            self.config.set('last_directory', str(Path(input_file).parent))
        
        except EPUB2TTSError as e:
            logger.error(f"Error transcribing audio: {str(e)}")
            status_var.set(f"Error: {str(e)}")
            messagebox.showerror("Transcription Error", str(e))
        
        except Exception as e:
            logger.error(f"Unexpected error transcribing audio: {str(e)}")
            status_var.set(f"Unexpected error: {str(e)}")
            messagebox.showerror("Unexpected Error", f"An unexpected error occurred: {str(e)}")
        
        finally:
            # Enable transcribe button
            transcribe_button.config(state=tk.NORMAL)
    
    def show_about(self):
        """Show about dialog"""
        about_text = f"""EPUB2TTS v{__version__}

A tool for converting ebooks to audiobooks using various Text-to-Speech engines.

Features:
- Multiple file formats (EPUB, PDF, TXT)
- Multiple TTS engines (Edge TTS, Google TTS, XTTS)
- Whisper speech recognition
- Graphical user interface

License: MIT
"""
        
        messagebox.showinfo("About EPUB2TTS", about_text)
    
    def set_status(self, status):
        """Set status bar text"""
        self.status_var.set(status)
        self.root.update_idletasks()
    
    def handle_exception(self, exc_type, exc_value, exc_traceback):
        """Handle uncaught exceptions"""
        logger.error("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))
        messagebox.showerror("Unexpected Error", f"An unexpected error occurred: {str(exc_value)}")
    
    def on_closing(self):
        """Handle window closing"""
        if self.is_converting:
            if messagebox.askyesno("Quit", "A conversion is in progress. Are you sure you want to quit?"):
                self.stop_conversion()
                self.root.destroy()
        else:
            self.root.destroy()

def main():
    """Main entry point for GUI"""
    try:
        root = tk.Tk()
        app = EPUB2TTSGUI(root)
        root.mainloop()
        return 0
    except Exception as e:
        logger.error(f"Error starting GUI: {str(e)}")
        print(f"Error starting GUI: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())

