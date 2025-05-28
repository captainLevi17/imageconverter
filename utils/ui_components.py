"""
UI Components for Image Master application.

This module contains reusable UI components used across the application.
"""

from PyQt5.QtWidgets import (QLabel, QSizePolicy, QScrollArea, QWidget, QGridLayout, QPushButton)
from PyQt5.QtCore import Qt


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
    """A scrollable gallery widget for displaying image thumbnails."""
    
    def __init__(self, parent=None):
        """Initialize the ImagePreviewGallery.
        
        Args:
            parent: Parent widget.
        """
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        # Create scroll area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        
        # Create container widget for thumbnails
        self.container = QWidget()
        self.container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        # Use grid layout for thumbnails
        self.layout = QGridLayout()
        self.layout.setSpacing(5)
        self.layout.setContentsMargins(5, 5, 5, 5)
        self.container.setLayout(self.layout)
        
        # Set the container as the scroll area's widget
        self.scroll_area.setWidget(self.container)
        
        # Main layout
        main_layout = QGridLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.scroll_area)
    
    def clear(self):
        """Clear all thumbnails from the gallery."""
        while self.layout.count():
            item = self.layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
    
    def add_thumbnail(self, widget, row, col):
        """Add a thumbnail widget to the gallery at the specified position.
        
        Args:
            widget: The widget to add (usually a ThumbnailLabel).
            row: Row position in the grid.
            col: Column position in the grid.
        """
        self.layout.addWidget(widget, row, col)


class FileControls(QWidget):
    """A widget containing common file operation controls."""
    
    def __init__(self, on_browse=None, on_clear=None, parent=None):
        """Initialize the FileControls.
        
        Args:
            on_browse: Callback for browse button click.
            on_clear: Callback for clear button click.
            parent: Parent widget.
        """
        super().__init__(parent)
        
        # Create layout
        layout = QGridLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # File selection buttons
        self.browse_btn = QPushButton("Add Images")
        self.clear_btn = QPushButton("Clear")
        
        # Connect signals if callbacks are provided
        if on_browse:
            self.browse_btn.clicked.connect(on_browse)
        if on_clear:
            self.clear_btn.clicked.connect(on_clear)
        
        # Add to layout
        layout.addWidget(self.browse_btn, 0, 0)
        layout.addWidget(self.clear_btn, 0, 1)
        
        # File count label
        self.file_label = QLabel("No images selected (0)")
        layout.addWidget(self.file_label, 1, 0, 1, 2)
    
    def update_file_count(self, count):
        """Update the file count display.
        
        Args:
            count: Number of files selected.
        """
        if count == 0:
            self.file_label.setText("No images selected (0)")
        else:
            self.file_label.setText(f"{count} image{'s' if count > 1 else ''} selected")
