from setuptools import setup, find_packages

setup(
    name="epub2tts",
    version="2.0.0",
    description="Convert ebooks to audiobooks using various TTS engines",
    author="Your Name",
    author_email="your.email@example.com",
    url="https://github.com/yourusername/epub2tts",
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            "epub2tts=epub2tts.cli:main",
        ],
    },
    install_requires=[
        "ebooklib",
        "beautifulsoup4",
    ],
    extras_require={
        "pdf": ["pdfplumber"],
        "edge": ["edge-tts"],
        "gtts": ["gtts", "pygame"],
        "xtts": ["torch", "torchaudio", "TTS"],
        "whisper": ["openai-whisper"],
        "gui": ["tkinter"],
        "all": [
            "pdfplumber",
            "edge-tts",
            "gtts",
            "pygame",
            "torch",
            "torchaudio",
            "TTS",
            "openai-whisper",
            "sounddevice",
            "soundfile",
            "psutil",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Topic :: Multimedia :: Sound/Audio :: Speech",
        "Topic :: Text Processing :: Markup",
    ],
    python_requires=">=3.8",
)

