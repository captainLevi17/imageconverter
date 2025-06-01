"""
UI Components for Image Master application.

This module contains reusable UI components used across the application.
"""

from PyQt5.QtWidgets import (
    QLabel, QSizePolicy, QScrollArea, QWidget, QGridLayout, QPushButton,
    QVBoxLayout, QGroupBox, QMessageBox
)
from PyQt5.QtCore import Qt, pyqtSignal, pyqtSlot
from PyQt5.QtGui import QPixmap, QImage

from typing import List, Optional, Dict, Any
import os
from pathlib import Path

from .image_utils import load_image, create_thumbnail
from .file_utils import get_file_size


class ThumbnailLabel(QLabel):
    """A QLabel subclass for displaying image thumbnails with a consistent style."""
    
    def __init__(self, parent=None):
        """Initialize the ThumbnailLabel.
        
        Args:
            parent: Parent widget.
        """
        super().__init__(parent)
        self.setAlignment(Qt.AlignCenter)
        self.setMinimumSize(120, 120)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setStyleSheet("""
            border: 1px solid #ddd;
            margin: 2px;
            padding: 2px;
            background-color: #f8f9fa;
        """)
        self.setScaledContents(False)
        self.pixmap = None
    
    def setPixmap(self, pixmap):
        """Override setPixmap to store the original pixmap and scale it properly."""
        self.pixmap = pixmap
        self.updateScaledPixmap()
    
    def resizeEvent(self, event):
        """Handle resize events to update the scaled pixmap."""
        self.updateScaledPixmap()
        super().resizeEvent(event)
    
    def updateScaledPixmap(self):
        """Update the displayed pixmap while maintaining aspect ratio."""
        if self.pixmap:
            scaled = self.pixmap.scaled(
                self.size(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            super().setPixmap(scaled)


class ImagePreviewGallery(QWidget):
    """A scrollable gallery widget for displaying image thumbnails with click handling."""
    
    # Signal emitted when a thumbnail is clicked
    thumbnail_clicked = pyqtSignal(str)  # path to the clicked image
    
    def __init__(self, parent=None):
        """Initialize the ImagePreviewGallery.
        
        Args:
            parent: Parent widget.
        """
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        # Store thumbnails and their widgets
        self.thumbnails = {}  # path -> thumbnail widget
        
        # Create scroll area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        
        # Create container widget for thumbnails
        self.container = QWidget()
        self.container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        # Use grid layout for thumbnails
        self.grid_layout = QGridLayout()
        self.grid_layout.setSpacing(5)
        self.grid_layout.setContentsMargins(5, 5, 5, 5)
        self.container.setLayout(self.grid_layout)
        
        # Set the container as the scroll area's widget
        self.scroll_area.setWidget(self.container)
        
        # Main layout
        main_layout = QGridLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.scroll_area)
    
    def clear(self) -> None:
        """Clear all thumbnails from the gallery."""
        # Clear the layout
        while self.grid_layout.count() > 0:
            item = self.grid_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Clear the thumbnails dictionary
        self.thumbnails.clear()
    
    def add_thumbnail(self, path: str, thumbnail_size: tuple = (120, 120)) -> None:
        """Add a thumbnail for the given image path.
        
        Args:
            path: Path to the image file.
            thumbnail_size: Size of the thumbnail as (width, height).
        """
        if path in self.thumbnails:
            return  # Already added
        
        try:
            # Create a thumbnail label
            thumbnail = ThumbnailLabel()
            
            # Load and set the thumbnail
            img = load_image(path)
            if img:
                # Create a thumbnail
                img.thumbnail(thumbnail_size)
                
                # Convert to QPixmap and set
                data = img.tobytes('raw', img.mode)
                qimage = QImage(data, img.size[0], img.size[1], QImage.Format_RGB888)
                pixmap = QPixmap.fromImage(qimage)
                thumbnail.setPixmap(pixmap)
                
                # Store the path as a property
                thumbnail.path = path
                
                # Connect click event
                thumbnail.mousePressEvent = lambda e, p=path: self.on_thumbnail_clicked(p)
                
                # Add to layout
                position = len(self.thumbnails)
                row = position // 4  # 4 columns
                col = position % 4
                
                self.grid_layout.addWidget(thumbnail, row, col)
                self.thumbnails[path] = thumbnail
                
        except Exception as e:
            print(f"Error creating thumbnail for {path}: {e}")
    
    @pyqtSlot(str)
    def on_thumbnail_clicked(self, path: str) -> None:
        """Handle thumbnail click events.
        
        Args:
            path: Path of the clicked image.
        """
        self.thumbnail_clicked.emit(path)
    
    def update_thumbnails(self, image_paths: List[str]) -> None:
        """Update the gallery with thumbnails for the given image paths.
        
        Args:
            image_paths: List of image file paths.
        """
        self.clear()
        for path in image_paths:
            self.add_thumbnail(path)


class OutputDirSelector(QGroupBox):
    """A widget for selecting and displaying output directory."""
    
    # Signal emitted when the output directory changes
    directory_changed = pyqtSignal(str)  # new directory path
    
    def __init__(self, parent=None):
        """Initialize the OutputDirSelector.
        
        Args:
            parent: Parent widget.
        """
        super().__init__("Output Directory", parent)
        self._directory = None
        
        # Create layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 15, 10, 10)
        
        # Directory selection button
        self.select_btn = QPushButton("Select Output Directory")
        self.select_btn.clicked.connect(self._on_select_clicked)
        
        # Directory label with elided text
        self.dir_label = QLabel("Output: Same as input")
        self.dir_label.setStyleSheet("color: #666;")
        self.dir_label.setTextFormat(Qt.PlainText)
        self.dir_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.dir_label.setWordWrap(True)
        
        # Add widgets to layout
        layout.addWidget(self.select_btn)
        layout.addWidget(self.dir_label)
        
        # Set initial state
        self._update_display()
    
    @property
    def directory(self) -> Optional[str]:
        """Get the current output directory.
        
        Returns:
            Optional[str]: The current output directory, or None if not set.
        """
        return self._directory
    
    @directory.setter
    def directory(self, path: Optional[str]) -> None:
        """Set the output directory.
        
        Args:
            path: Path to the output directory, or None to clear.
        """
        if path != self._directory:
            self._directory = path
            self._update_display()
            if path:
                self.directory_changed.emit(path)
    
    def _on_select_clicked(self) -> None:
        """Handle select directory button click."""
        try:
            from utils.file_utils import select_output_directory
            
            start_dir = self._directory or os.path.expanduser("~")
            result = select_output_directory(start_dir)
            
            # Check if result is a tuple (directory, message) or just a directory
            if isinstance(result, tuple):
                directory, message = result
            else:
                directory, message = result, None
                
            # Only update if a directory was selected (not cancelled)
            if directory:
                self.directory = directory
            elif message:  # Show error message if there was an error (other than cancellation)
                QMessageBox.warning(self, "Directory Selection", message)
        except Exception as e:
            error_msg = f"Error selecting directory: {str(e)}"
            print(error_msg)
            QMessageBox.critical(self, "Error", error_msg)
    
    def _update_display(self) -> None:
        """Update the UI to reflect the current state."""
        if not self._directory:
            self.dir_label.setText("Output: Same as input")
            self.dir_label.setToolTip("")
            self.dir_label.setStyleSheet("color: #666;")
        else:
            # Display a shortened path if it's too long
            display_path = self._directory
            if len(display_path) > 40:
                parts = display_path.split(os.sep)
                if len(parts) > 3:
                    display_path = os.path.join("...", *parts[-3:])
            
            self.dir_label.setText(f"Output: {display_path}")
            self.dir_label.setToolTip(self._directory)
            self.dir_label.setStyleSheet("color: #0066cc;")


class FileControls(QWidget):
    """A widget containing common file operation controls with signals."""
    
    # Signals
    browse_clicked = pyqtSignal()
    clear_clicked = pyqtSignal()
    
    def __init__(self, parent=None):
        """Initialize the FileControls.
        
        Args:
            parent: Parent widget.
        """
        super().__init__(parent)
        
        # Create layout
        layout = QGridLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # File selection buttons
        self.browse_btn = QPushButton("Add Images")
        self.clear_btn = QPushButton("Clear")
        
        # Connect signals
        self.browse_btn.clicked.connect(self._on_browse_clicked)
        self.clear_btn.clicked.connect(self._on_clear_clicked)
        
        # Add to layout
        layout.addWidget(self.browse_btn, 0, 0)
        layout.addWidget(self.clear_btn, 0, 1)
        
        # File count label
        self.file_label = QLabel("No images selected (0)")
        layout.addWidget(self.file_label, 1, 0, 1, 2)
    
    def _on_browse_clicked(self) -> None:
        """Handle browse button click."""
        self.browse_clicked.emit()
    
    def _on_clear_clicked(self) -> None:
        """Handle clear button click."""
        self.clear_clicked.emit()
    
    def update_file_count(self, count: int) -> None:
        """Update the file count display.
        
        Args:
            count: Number of files selected.
        """
        if count == 0:
            self.file_label.setText("No images selected (0)")
        elif count == 1:
            self.file_label.setText("1 image selected")
        else:
            self.file_label.setText(f"{count} images selected")
