"""
Image Compressor Tool for the Image Master application.

This module provides the CompressorTool class which allows users to compress images
with various quality settings and output formats.
"""
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import os

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QPushButton, QMessageBox, QProgressBar, QCheckBox, QGroupBox,
    QFileDialog
)
from PyQt5.QtCore import Qt, QSize, pyqtSlot

from utils.base_tool import BaseTool
from utils.ui_components import (
    ThumbnailLabel, ImagePreviewGallery, FileControls, OutputDirSelector
)
from utils.image_utils import load_image
from workers.compress_worker import CompressWorker

class CompressorTool(BaseTool):
    """Tool for compressing images with various quality settings and output formats."""
    
    def __init__(self, parent=None):
        """Initialize the CompressorTool with default settings."""
        # Initialize tool-specific attributes before parent's __init__
        self.quality = 85
        self.output_format = "jpeg"
        self.preserve_metadata = True
        self.output_dir = str(Path.home() / "Pictures" / "Compressed")
        
        # Initialize UI components
        self.quality_slider = None
        self.format_combo = None
        self.metadata_check = None
        self.compress_btn = None
        self.progress_bar = None
        self.output_dir_selector = None
        
        # Initialize parent class which will call setup_ui()
        super().__init__("Image Compressor")
        
    def setup_tool_controls(self, control_layout):
        """Set up tool-specific controls.
        
        Args:
            control_layout: The layout to add controls to
        """
        # Quality settings group
        quality_group = QGroupBox("Compression Settings")
        quality_layout = QVBoxLayout(quality_group)
        
        # Quality slider
        quality_slider_layout = QHBoxLayout()
        quality_slider_layout.addWidget(QLabel("Quality:"))
        
        self.quality_slider = QProgressBar()
        self.quality_slider.setRange(1, 100)
        self.quality_slider.setValue(self.quality)
        self.quality_slider.setFormat("%p%")
        self.quality_slider.setTextVisible(True)
        quality_slider_layout.addWidget(self.quality_slider)
        
        quality_layout.addLayout(quality_slider_layout)
        
        # Format selection
        format_layout = QHBoxLayout()
        format_layout.addWidget(QLabel("Output Format:"))
        
        self.format_combo = QComboBox()
        self.format_combo.addItems(["JPEG", "PNG", "WebP"])
        self.format_combo.setCurrentText(self.output_format.upper())
        format_layout.addWidget(self.format_combo)
        
        quality_layout.addLayout(format_layout)
        
        # Metadata option
        self.metadata_check = QCheckBox("Preserve Metadata")
        self.metadata_check.setChecked(self.preserve_metadata)
        quality_layout.addWidget(self.metadata_check)
        
        control_layout.addWidget(quality_group)
        
        # Output directory selection
        self.output_dir_selector = OutputDirSelector()
        control_layout.addWidget(self.output_dir_selector)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        control_layout.addWidget(self.progress_bar)
        
        # Compress button
        self.compress_btn = QPushButton("Compress Images")
        self.compress_btn.clicked.connect(self.start_compression)
        self.compress_btn.setEnabled(False)
        control_layout.addWidget(self.compress_btn)
        
            # Connect signals
        self.quality_slider.valueChanged.connect(self.update_quality)
        self.format_combo.currentTextChanged.connect(self.update_format)
        self.metadata_check.stateChanged.connect(self.update_metadata)
        self.output_dir_selector.directory_changed.connect(self.update_output_dir)
            
    def clear_images(self):
        super().clear_images()
        self.compression_info.clear()
    
    def update_thumbnail_gallery(self) -> None:
        """Update the thumbnail gallery with the current images."""
        super().update_thumbnail_gallery()
    
    def on_thumbnail_clicked(self, path: str) -> None:
        """Handle thumbnail click events.
        
        Args:
            path: Path of the clicked image
        """
        try:
            # Load the image using the base class method
            self.current_path = path
            self.current_preview = load_image(path)
            
            if not self.current_preview:
                raise Exception("Failed to load image")
            
            # Update the main preview
            self.update_main_preview()
            
            # Update compression info if the method exists
            if hasattr(self, 'update_compression_info'):
                self.update_compression_info()
                
        except Exception as e:
            error_msg = f"Error loading preview: {str(e)}"
            print(f"{error_msg} for {path}")
            self.error_occurred.emit(error_msg)
    
    def update_compression_info(self):
        """Update the compression information display."""
        try:
            if not hasattr(self, 'current_path') or not self.current_path:
                return
                
            # Skip if the UI elements aren't initialized yet
            if not all(hasattr(self, attr) for attr in ['quality_slider', 'format_combo']):
                return
                
            # Get current settings
            quality = self.quality_slider.value()
            output_format = self.format_combo.currentText().lower()
            
            # Update status bar if available
            if hasattr(self, 'status_message'):
                self.status_message.emit(
                    f"Quality: {quality}% • Format: {output_format.upper()}"
                )
                
        except Exception as e:
            error_msg = f"Error updating compression info: {str(e)}"
            print(error_msg)
            if hasattr(self, 'error_occurred'):
                self.error_occurred.emit(error_msg)
    
    @pyqtSlot(str)
    def _on_output_dir_changed(self, directory: str) -> None:
        """Handle output directory changes.
        
        Args:
            directory: The new output directory path
        """
        try:
            if directory and directory != self.output_dir:
                # Validate the directory
                if not os.path.exists(directory):
                    os.makedirs(directory, exist_ok=True)
                
                if os.access(directory, os.W_OK):
                    self.output_dir = directory
                    print(f"Output directory changed to: {directory}")
                else:
                    QMessageBox.warning(
                        self,
                        "Invalid Directory",
                        "The selected directory is not writable. Please choose a different directory."
                    )
        except Exception as e:
            error_msg = f"Error changing output directory: {str(e)}"
            print(error_msg)
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to set output directory: {str(e)}"
            )
    
    def update_quality(self, value):
        """Update the quality setting."""
        self.quality = value
        self._update_ui_state()
    
    def update_format(self, format_name):
        """Update the output format."""
        self.output_format = format_name.lower()
        self._update_ui_state()
    
    def update_metadata(self, state):
        """Update the metadata preservation setting."""
        self.preserve_metadata = state == Qt.Checked
        self._update_ui_state()
    
    @pyqtSlot(str)
    def update_output_dir(self, directory):
        """Update the output directory."""
        if directory:
            self.output_dir = directory
            self._update_ui_state()
    
    def _update_ui_state(self):
        """Update the UI state based on current settings."""
        # Enable/disable compress button based on whether we have images and an output directory
        has_images = bool(self.image_paths)
        has_output_dir = bool(self.output_dir)
        self.compress_btn.setEnabled(has_images and has_output_dir)
    
    def start_compression(self):
        """Start the image compression process."""
        if not self.image_paths:
            QMessageBox.warning(self, "No Files", "Please select at least one image file.")
            return
        
        if not self.output_dir:
            QMessageBox.warning(self, "No Output Directory", "Please select an output directory.")
            return
        
        # Disable UI during processing
        self.set_ui_enabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setMaximum(len(self.image_paths))
        self.progress_bar.setValue(0)
        
        # Create and start worker thread
        self.worker = CompressWorker(
            self.image_paths,
            self.output_dir,
            self.quality,
            self.output_format,
            self.preserve_metadata
        )
        
        # Connect worker signals
        self.worker.progress_updated.connect(self._on_compression_progress)
        self.worker.finished.connect(self._on_compression_finished)
        self.worker.error_occurred.connect(self._on_compression_error)
        
        # Start the worker
        self.worker.start()
    
    def set_ui_enabled(self, enabled):
        """Enable or disable UI elements during operations."""
        self.file_controls.setEnabled(enabled)
        self.quality_slider.setEnabled(enabled)
        self.format_combo.setEnabled(enabled)
        self.metadata_check.setEnabled(enabled)
        self.output_dir_selector.setEnabled(enabled)
        self.compress_btn.setEnabled(enabled and bool(self.image_paths) and bool(self.output_dir))
    
    @pyqtSlot(int)
    def _on_compression_progress(self, value):
        """Handle progress updates from the worker thread."""
        self.progress_bar.setValue(value)
    
    @pyqtSlot()
    def _on_compression_finished(self):
        """Handle completion of the compression process."""
        self.set_ui_enabled(True)
        self.progress_bar.setVisible(False)
        QMessageBox.information(
            self, 
            "Compression Complete", 
            f"Successfully compressed {len(self.image_paths)} image(s)."
        )
    
    @pyqtSlot(str)
    def _on_compression_error(self, error_msg):
        """Handle errors during compression."""
        self.set_ui_enabled(True)
        self.progress_bar.setVisible(False)
        QMessageBox.critical(
            self,
            "Compression Error",
            f"An error occurred during compression:\n\n{error_msg}"
        )
    
    def closeEvent(self, event):
        """Handle window close event."""
        # Stop any running worker thread
        if hasattr(self, 'worker') and self.worker is not None:
            self.worker.stop()
            self.worker.wait()
        event.accept()
