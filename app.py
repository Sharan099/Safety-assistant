"""
Hugging Face Spaces Entry Point
This file is an alias for ui.py to work with Hugging Face Spaces
"""
import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

# Import and run the Streamlit app
from ui import *

