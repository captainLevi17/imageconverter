"""
Image Master - A powerful image processing application.

This package provides a collection of tools for image processing tasks
such as resizing, compressing, converting formats, and more.
"""

__version__ = "0.1.0"

# Import main components to make them available at package level
from .main import main, ImageMasterApp

# Export public API
__all__ = [
    'main',
    'ImageMasterApp',
]
