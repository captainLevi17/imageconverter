#!/usr/bin/env python3
"""
Main entry point for the Image Master application.
This allows the package to be run with `python -m imagemaster`
"""

import sys

try:
    from .main import main
except ImportError:
    # If running as a script, use direct import
    from main import main

if __name__ == "__main__":
    sys.exit(main())
