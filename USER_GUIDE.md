# EPUB2TTS User Guide

EPUB2TTS is a powerful tool for converting ebooks (EPUB, PDF, and TXT files) to audiobooks using various Text-to-Speech (TTS) engines. This guide will help you get started with EPUB2TTS and explain its features and usage.

## Table of Contents

1. [Installation](#installation)
2. [Features](#features)
3. [Command-Line Interface](#command-line-interface)
4. [Graphical User Interface](#graphical-user-interface)
5. [TTS Engines](#tts-engines)
6. [Whisper Speech Recognition](#whisper-speech-recognition)
7. [Configuration](#configuration)
8. [Troubleshooting](#troubleshooting)

## Installation

### Prerequisites

- Python 3.8 or higher
- FFmpeg (for audio processing)
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

