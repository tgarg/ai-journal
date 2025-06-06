#!/usr/bin/env python3
"""
AI Journal CLI Entry Point

Simple entry point script that imports and runs the CLI interface.
"""

import sys
from pathlib import Path

# Add current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

# Import and run CLI from src package
from src.cli import main

if __name__ == '__main__':
    main()