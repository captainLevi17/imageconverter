"""
Worker thread for image resizing operations.

This module provides the ResizeWorker class which handles image resizing
in a separate thread to keep the UI responsive.
"""
import os
from pathlib import Path
from typing import List, Tuple, Optional

from PyQt5.QtCore import QThread, pyqtSignal, pyqtSlot
from PIL import Image

from utils.image_processing import process_single_image


class ResizeWorker(QThread):
    """Worker thread for processing image resizing operations."""
    
    # Signals
    progress_updated = pyqtSignal(int)  # Progress percentage
    finished = pyqtSignal(list)  # List of output paths
    error_occurred = pyqtSignal(str)  # Error message
    
    def __init__(
        self,
        image_paths: List[str],
        output_dir: str,
        width: int,
        height: int,
        output_format: str,
        maintain_aspect: bool = True,
        allow_enlarge: bool = False
    ):
        """Initialize the worker with resizing parameters.
        
        Args:
            image_paths: List of input image paths
            output_dir: Output directory for resized images
            width: Target width in pixels
            height: Target height in pixels
            output_format: Output format (JPEG, PNG, WEBP)
            maintain_aspect: Whether to maintain aspect ratio
            allow_enlarge: Whether to allow enlarging images
        """
        super().__init__()
        self.image_paths = image_paths
        self.output_dir = output_dir
        self.width = width
        self.height = height
        self.output_format = output_format.upper()
        self.maintain_aspect = maintain_aspect
        self.allow_enlarge = allow_enlarge
        self._is_running = True
    
    def run(self):
        """Process all images in the queue."""
        try:
            processed_paths = []
            total = len(self.image_paths)
            
            for i, image_path in enumerate(self.image_paths, 1):
                if not self._is_running:
                    break
                    
                try:
                    # Process the image
                    output_path = process_single_image(
                        image_path,
                        self.output_dir,
                        self.width,
                        self.height,
                        self.output_format,
                        self.maintain_aspect,
                        self.allow_enlarge
                    )
                    
                    if output_path and os.path.exists(output_path):
                        processed_paths.append(output_path)
                    
                    # Update progress
                    progress = int((i / total) * 100)
                    self.progress_updated.emit(progress)
                    
                except Exception as e:
                    self.error_occurred.emit(f"Error processing {os.path.basename(image_path)}: {str(e)}")
            
            self.finished.emit(processed_paths)
            
        except Exception as e:
            self.error_occurred.emit(f"Failed to process images: {str(e)}")
    
    def stop(self):
        """Stop the worker thread."""
        self._is_running = False
        self.wait()
