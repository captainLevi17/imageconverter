"""
Base tool class that provides common functionality for all image processing tools.
"""
import os
from typing import List, Optional, Dict, Any, Tuple
from pathlib import Path

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                           QPushButton, QGroupBox, QScrollArea, QGridLayout,
                           QSizePolicy, QComboBox, QCheckBox, QSpinBox, 
                           QDoubleSpinBox, QProgressBar, QFileDialog)
from PyQt5.QtCore import Qt, QSize, pyqtSignal
from PyQt5.QtGui import QPixmap, QImage

from .image_utils import ImageData, load_image, save_image, create_thumbnail
from .file_utils import (
    validate_directory, 
    create_directory, 
    get_unique_filename, 
    get_file_size
)
from .ui_components import (
    ThumbnailLabel,
    ImagePreviewGallery,
    FileControls
)

class BaseTool(QWidget):
    """Base class for all image processing tools."""
    
    # Signals
    progress_updated = pyqtSignal(int, int)  # current, total
    status_message = pyqtSignal(str)  # status message
    error_occurred = pyqtSignal(str)  # error message
    
    def __init__(self, tool_name: str, parent: Optional[QWidget] = None):
        """Initialize the base tool.
        
        Args:
            tool_name: Name of the tool (for UI display)
            parent: Parent widget
        """
        super().__init__(parent)
        self.tool_name = tool_name
        self.image_paths: List[str] = []
        self.current_preview: Optional[ImageData] = None
        self.current_path: Optional[str] = None
        self.output_dir: Optional[str] = None
        self.output_format: str = "JPEG"
        self.setup_ui()
    
    def setup_ui(self) -> None:
        """Set up the user interface."""
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        # Main layout
        self.main_layout = QHBoxLayout()
        self.main_layout.setContentsMargins(5, 5, 5, 5)
        self.setLayout(self.main_layout)
        
        # Left panel - Preview gallery
        self.setup_preview_panel()
        
        # Right panel - Controls
        self.setup_control_panel()
    
    def setup_preview_panel(self) -> None:
        """Set up the preview panel with gallery and main preview."""
        preview_group = QGroupBox("Preview Gallery")
        preview_group.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        preview_layout = QVBoxLayout()
        
        # Thumbnail gallery
        self.thumbnail_gallery = ImagePreviewGallery()
        self.thumbnail_gallery.thumbnail_clicked.connect(self.on_thumbnail_clicked)
        preview_layout.addWidget(self.thumbnail_gallery)
        
        # Main preview
        self.main_preview = QLabel()
        self.main_preview.setAlignment(Qt.AlignCenter)
        self.main_preview.setMinimumSize(400, 300)
        self.main_preview.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        preview_layout.addWidget(QLabel("Selected Preview:"))
        preview_layout.addWidget(self.main_preview, stretch=2)
        
        # Info labels
        self.size_info = QLabel()
        self.size_info.setAlignment(Qt.AlignCenter)
        self.size_info.setStyleSheet("font-size: 10px; color: #555;")
        preview_layout.addWidget(self.size_info)
        
        preview_group.setLayout(preview_layout)
        self.main_layout.addWidget(preview_group, stretch=2)
    
    def setup_control_panel(self) -> None:
        """Set up the control panel with tool-specific controls."""
        control_group = QGroupBox("Controls")
        control_group.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        control_layout = QVBoxLayout()
        
        # File controls
        self.file_controls = FileControls()
        self.file_controls.browse_clicked.connect(self.browse_images)
        self.file_controls.clear_clicked.connect(self.clear_images)
        control_layout.addWidget(self.file_controls)
        
        # Output format selection
        format_layout = QHBoxLayout()
        format_layout.addWidget(QLabel("Output Format:"))
        self.format_combo = QComboBox()
        self.format_combo.addItems(["JPEG", "PNG", "WebP"])
        format_layout.addWidget(self.format_combo)
        control_layout.addLayout(format_layout)
        
        # Tool-specific controls (to be implemented by subclasses)
        self.setup_tool_controls(control_layout)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        control_layout.addWidget(self.progress_bar)
        
        control_group.setLayout(control_layout)
        self.main_layout.addWidget(control_group, stretch=1)
    
    def setup_tool_controls(self, layout: QVBoxLayout) -> None:
        """Set up tool-specific controls.
        
        Args:
            layout: The layout to add controls to
        """
        raise NotImplementedError("Subclasses must implement setup_tool_controls")
    
    def browse_images(self) -> None:
        """Open a file dialog to select images."""
        file_dialog = QFileDialog()
        file_dialog.setFileMode(QFileDialog.ExistingFiles)
        file_dialog.setNameFilter("Images (*.png *.jpg *.jpeg *.webp *.bmp *.tiff);;All Files (*)")
        
        if file_dialog.exec_():
            new_paths = file_dialog.selectedFiles()
            self.add_image_paths(new_paths)
    
    def add_image_paths(self, paths: List[str]) -> None:
        """Add image paths to the current selection.
        
        Args:
            paths: List of file paths to add
        """
        for path in paths:
            if path not in self.image_paths:
                self.image_paths.append(path)
        self.update_thumbnail_gallery()
    
    def clear_images(self) -> None:
        """Clear all selected images."""
        self.image_paths = []
        self.current_preview = None
        self.current_path = None
        self.thumbnail_gallery.clear()
        self.main_preview.clear()
        self.size_info.clear()
    
    def update_thumbnail_gallery(self) -> None:
        """Update the thumbnail gallery with the current images."""
        self.thumbnail_gallery.update_thumbnails(self.image_paths)
    
    def on_thumbnail_clicked(self, path: str) -> None:
        """Handle thumbnail click events.
        
        Args:
            path: Path of the clicked image
        """
        try:
            self.current_path = path
            self.current_preview = load_image(path)
            self.update_main_preview()
        except Exception as e:
            self.error_occurred.emit(f"Error loading image: {str(e)}")
    
    def update_main_preview(self) -> None:
        """Update the main preview with the current image.
        
        This method handles image scaling and display, ensuring the preview looks good
        at any window size while maintaining the image's aspect ratio.
        """
        if self.current_preview is None or self.current_path is None:
            return
            
        try:
            # Get the available size for the preview (accounting for margins)
            available_size = self.main_preview.size()
            if available_size.width() <= 1 or available_size.height() <= 1:
                return  # Not ready to render yet
                
            # Load the image
            pixmap = QPixmap(self.current_path)
            if pixmap.isNull():
                self.main_preview.setText("Failed to load image")
                return
                
            # Calculate the scaled size maintaining aspect ratio
            pixmap_size = pixmap.size()
            pixmap_size.scale(available_size, Qt.KeepAspectRatio)
            
            # Only scale if necessary to avoid unnecessary scaling operations
            if pixmap_size != pixmap.size():
                pixmap = pixmap.scaled(
                    available_size,
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
                )
            
            # Set the pixmap
            self.main_preview.setPixmap(pixmap)
            
            # Update size and file info
            img = self.current_preview
            file_size = os.path.getsize(self.current_path) / 1024  # Convert to KB
            size_info = (
                f"{img.width} × {img.height} px • {file_size:.1f} KB • {img.mode.upper()}"
            )
            self.size_info.setText(size_info)
            
        except Exception as e:
            self.error_occurred.emit(f"Error updating preview: {str(e)}")
            self.size_info.setText("Error loading image")
    
    def process_images(self) -> None:
        """Process all selected images."""
        if not self.image_paths:
            self.status_message.emit("No images selected")
            return
            
        # Get output directory
        output_dir = QFileDialog.getExistingDirectory(
            self,
            "Select Output Directory",
            self.output_dir or str(Path.home() / "Pictures")
        )
        
        if not output_dir:
            return  # User cancelled
            
        self.output_dir = output_dir
        
        # Process each image
        self.progress_bar.setVisible(True)
        self.progress_bar.setMaximum(len(self.image_paths))
        
        for i, path in enumerate(self.image_paths, 1):
            try:
                self.status_message.emit(f"Processing {Path(path).name}...")
                self.process_single_image(path, output_dir)
                self.progress_bar.setValue(i)
            except Exception as e:
                self.error_occurred.emit(f"Error processing {path}: {str(e)}")
        
        self.progress_bar.setVisible(False)
        self.status_message.emit(f"Processed {len(self.image_paths)} images")
    
    def process_single_image(self, input_path: str, output_dir: str) -> str:
        """Process a single image.
        
        Args:
            input_path: Path to the input image
            output_dir: Directory to save the processed image
            
        Returns:
            Path to the processed image
            
        Raises:
            Exception: If processing fails
        """
        raise NotImplementedError("Subclasses must implement process_single_image")
    
    def resizeEvent(self, event):
        """Handle window resize events."""
        super().resizeEvent(event)
        self.update_main_preview()
    
    def get_output_path(self, input_path: str, output_dir: str, suffix: str = "") -> str:
        """Generate an output path for the processed image.
        
        Args:
            input_path: Path to the input image
            output_dir: Directory to save the processed image
            suffix: Optional suffix to add to the filename
            
        Returns:
            Full path to the output file
        """
        input_path = Path(input_path)
        output_ext = self.format_combo.currentText().lower()
        
        # Create the output filename
        if suffix:
            output_stem = f"{input_path.stem}_{suffix}"
        else:
            output_stem = input_path.stem
            
        output_filename = f"{output_stem}.{output_ext}"
        output_path = Path(output_dir) / output_filename
        
        # Ensure the filename is unique
        return str(get_unique_filename(str(output_dir), output_filename))
