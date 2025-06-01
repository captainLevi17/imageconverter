"""
Image Resizer Tool for the Image Master application.

This module provides the ResizerTool class which allows users to resize images
with various options like maintaining aspect ratio, presets, and output formats.
"""
from typing import Dict, List, Optional, Tuple
from pathlib import Path

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QPushButton, QMessageBox, QProgressBar, QSizePolicy, QApplication
)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QImage, QPixmap
from PIL import Image
import os
import sys

from utils.base_tool import BaseTool
from utils.ui_components import ThumbnailLabel, ImagePreviewGallery, FileControls, OutputDirSelector
from utils.dimension_controls import DimensionControls
from utils.image_processing import process_single_image
from workers.resize_worker import ResizeWorker

class ResizerTool(BaseTool):
    """Tool for resizing images with various options."""
    
    def __init__(self):
        """Initialize the ResizerTool with default presets and settings."""
        # Initialize presets before parent's __init__ to ensure it's available during UI setup
        self.presets = self._get_presets()
        self.original_size = None
        self.output_dir = None
        self.output_dir_selector = None
        self.format_combo = None
        self.preview_label = None
        super().__init__("Image Resizer")
    
    def _get_presets(self) -> Dict[str, Tuple[int, int]]:
        """Get the available dimension presets.
        
        Returns:
            Dict mapping preset names to (width, height) tuples.
        """
        return {
            "Custom": (0, 0),
            "HD (1280x720)": (1280, 720),
            "Full HD (1920x1080)": (1920, 1080),
            "4K UHD (3840x2160)": (3840, 2160),
            "Instagram Post (1080x1080)": (1080, 1080),
            "Instagram Story (1080x1920)": (1080, 1920),
            "Facebook Post (1200x630)": (1200, 630),
            "Twitter Post (1200x675)": (1200, 675),
            "LinkedIn Post (1200x627)": (1200, 627),
            "Pinterest Pin (1000x1500)": (1000, 1500),
            "A4 (2480x3508 @ 300dpi)": (2480, 3508),
            "Letter (2550x3300 @ 300dpi)": (2550, 3300)
        }
    
    def setup_tool_controls(self, layout):
        """Set up the resizer-specific controls.
        
        Args:
            layout: The layout to add controls to.
        """
        # Create main container widget and layout
        container = QWidget()
        container_layout = QVBoxLayout(container)
        
        # File info label
        self.file_label = QLabel("No file selected")
        container_layout.addWidget(self.file_label)
        
        # Create dimension controls
        self.dimension_controls = DimensionControls(self.presets)
        container_layout.addWidget(self.dimension_controls)
        
        # Output format selection
        format_layout = QHBoxLayout()
        format_layout.addWidget(QLabel("Output Format:"))
        self.format_combo = QComboBox()
        self.format_combo.addItems(['JPEG', 'PNG', 'WEBP'])
        format_layout.addWidget(self.format_combo)
        container_layout.addLayout(format_layout)
        
        # Add output directory selector
        self.output_dir_selector = OutputDirSelector()
        self.output_dir_selector.directory_changed.connect(self._on_output_dir_changed)
        container_layout.addWidget(self.output_dir_selector)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        container_layout.addWidget(self.progress_bar)
        
        # Resize button
        self.resize_btn = QPushButton("Resize Images")
        self.resize_btn.clicked.connect(self.resize_images)
        container_layout.addWidget(self.resize_btn)
        
        # Add container to the main layout
        layout.addWidget(container)
    
    def _on_output_dir_changed(self, directory: str) -> None:
        """Handle output directory changes.
        
        Args:
            directory: The new output directory path.
        """
        self.output_dir = directory
        print(f"Output directory changed to: {directory}")
        
    
    def on_selected_image_changed(self, current_path: str) -> None:
        """Handle selected image changes."""
        super().on_selected_image_changed(current_path)
        self.original_size = None
            
        if current_path:
            try:
                with Image.open(current_path) as img:
                    self.original_size = img.size
            except Exception as e:
                print(f"Error loading image {current_path}: {str(e)}")
    

    def resize_images(self):
        """Process all selected images with the current settings."""
        if not hasattr(self, 'image_paths') or not self.image_paths:
            QMessageBox.warning(self, "No Images", "No images selected for resizing.")
            return
            
        # Get output directory
        output_dir = self.output_dir if self.output_dir else os.path.dirname(self.image_paths[0])
        
        # Show progress
        if hasattr(self, 'progress_bar'):
            self.progress_bar.setMaximum(len(self.image_paths))
            self.progress_bar.setValue(0)
            self.progress_bar.setVisible(True)
        
        # Get current settings
        width, height = self.dimension_controls.get_dimensions()
        output_format = self.format_combo.currentText()
        maintain_aspect = self.dimension_controls.maintain_aspect_ratio
        allow_enlarge = self.dimension_controls.allow_image_enlarge
        
        # Process images in a separate thread
        self.worker = ResizeWorker(
            self.image_paths,
            output_dir,
            width,
            height,
            output_format,
            maintain_aspect,
            allow_enlarge
        )
        
        if hasattr(self, 'progress_bar'):
            self.worker.progress_updated.connect(self.update_progress)
        
        self.worker.finished.connect(self.on_resize_complete)
        self.worker.error_occurred.connect(self.on_resize_error)
        
        self.worker.start()

    def update_progress(self, value: int) -> None:
        """Update the progress bar with the current progress.
        
        Args:
            value: Progress value (0-100)
        """
        if hasattr(self, 'progress_bar'):
            self.progress_bar.setValue(value)
    
    def on_resize_complete(self, output_paths: list) -> None:
        """Handle completion of image resizing.
        
        Args:
            output_paths: List of paths to the resized images
        """
        if hasattr(self, 'progress_bar'):
            self.progress_bar.setVisible(False)
        
        if not output_paths:
            QMessageBox.warning(
                self,
                "Processing Complete",
                "No images were processed. Please check for any error messages."
            )
            return
        
        # Show success message
        output_dir = os.path.dirname(output_paths[0]) if output_paths else ""
        msg = f"Successfully processed {len(output_paths)} image(s)"
        if output_dir:
            msg += f" to:\n{output_dir}"
        
        self.file_label.setText(msg)
        self.file_label.setStyleSheet("color: #009900; font-weight: bold;")
        
        # Show completion dialog
        QMessageBox.information(
            self,
            "Processing Complete",
            msg
        )
        
        # Open the output directory if available
        if output_dir and os.path.isdir(output_dir):
            try:
                if sys.platform == 'win32':
                    os.startfile(output_dir)
                elif sys.platform == 'darwin':
                    import subprocess
                    subprocess.Popen(['open', output_dir])
                else:
                    import subprocess
                    subprocess.Popen(['xdg-open', output_dir])
            except Exception as e:
                print(f"Error opening output directory: {e}")
    
    def on_resize_error(self, error_msg: str) -> None:
        """Handle errors during image resizing.
        
        Args:
            error_msg: Error message to display
        """
        if hasattr(self, 'progress_bar'):
            self.progress_bar.setVisible(False)
        
        QMessageBox.critical(
            self,
            "Error",
            error_msg
        )
    

    