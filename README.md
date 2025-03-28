<<<<<<< HEAD
# V2
epub
=======
# EPUB2TTS v2

A user-friendly tool for converting ebooks (EPUB, PDF, and TXT files) to audiobooks using various Text-to-Speech engines, with Whisper speech recognition and a graphical user interface.

## Features

- **Multiple File Formats**:
  - EPUB
  - PDF (with pdfplumber)
  - TXT

- **Multiple TTS Engines**:
  - XTTS-v2 (Coqui TTS) with voice cloning
  - Edge TTS (Microsoft) - fast online TTS
  - Google TTS - simple online TTS

- **Speech Recognition**:
  - OpenAI Whisper for transcribing audio
  - Record and transcribe functionality
  - Voice sample recording for XTTS

- **User-Friendly Interface**:
  - Graphical User Interface (GUI)
  - Command-line Interface (CLI)
  - Dark mode support
  - Progress tracking
  - Configuration saving

## Installation

### Prerequisites

- Python 3.8+
- FFmpeg
- tkinter (for GUI)

### Installation Steps

```bash
# Install system dependencies
# For Arch Linux:
sudo pacman -S python python-pip ffmpeg tk

# For Ubuntu/Debian:
sudo apt install python3 python3-pip ffmpeg python3-tk

# For Windows:
# Download and install Python from python.org (make sure to check "Add Python to PATH")
# Download and install FFmpeg from ffmpeg.org

# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Clone the repository
git clone https://github.com/yourusername/epub2tts.git
cd epub2tts

# Install the package with basic dependencies
pip install -e .

# Install additional dependencies based on your needs
# For PDF support:
pip install -e ".[pdf]"

# For XTTS support:
pip install -e ".[xtts]"

# For Edge TTS support (recommended for speed):
pip install -e ".[edge]"

# For Google TTS support:
pip install -e ".[gtts]"

# For Whisper speech recognition:
pip install -e ".[whisper]"

# For GUI:
pip install -e ".[gui]"

# For all features:
pip install -e ".[all]"

>>>>>>> 5856711 (Initial commit)
