"""
Preview management for Image Master application.

This module provides functionality for managing image previews and thumbnails.
"""

import os
from typing import Optional, Dict, Any, Tuple
from PyQt5.QtCore import Qt, QSize, QRect, QPoint, QPointF
from PyQt5.QtGui import QPixmap, QImage, QPainter, QPen, QColor, QTransform
from PyQt5.QtWidgets import QLabel, QGraphicsView, QGraphicsScene, QGraphicsPixmapItem

from .image_utils import load_image


class PreviewManager:
    """Manages image previews and thumbnails."""
    
    def __init__(self, thumbnail_size: QSize = QSize(120, 120)):
        """Initialize the PreviewManager.
        
        Args:
            thumbnail_size: Default size for thumbnails.
        """
        self.thumbnail_size = thumbnail_size
        self._preview_cache = {}
    
    def clear_cache(self):
        """Clear the preview cache."""
        self._preview_cache.clear()
    
    def get_thumbnail(
        self, 
        image_path: str, 
        size: Optional[QSize] = None,
        use_cache: bool = True
    ) -> Optional[QPixmap]:
        """Get a thumbnail for the specified image.
        
        Args:
            image_path: Path to the image file.
            size: Size of the thumbnail. If None, uses the default size.
            use_cache: Whether to use cached thumbnails.
            
        Returns:
            QPixmap: The thumbnail pixmap, or None if loading failed.
        """
        if not image_path or not os.path.isfile(image_path):
            return None
            
        size = size or self.thumbnail_size
        cache_key = f"{image_path}_{size.width()}_{size.height()}"
        
        # Return cached thumbnail if available
        if use_cache and cache_key in self._preview_cache:
            return self._preview_cache[cache_key]
        
        # Load the image
        image = load_image(image_path)
        if image is None:
            return None
        
        # Convert to QImage
        if image.mode == 'RGB':
            qimage = QImage(
                image.tobytes(), 
                image.width, 
                image.height, 
                image.width * 3, 
                QImage.Format_RGB888
            )
        elif image.mode == 'RGBA':
            qimage = QImage(
                image.tobytes(), 
                image.width, 
                image.height, 
                image.width * 4, 
                QImage.Format_RGBA8888
            )
        else:
            # Convert to RGB for other modes
            image = image.convert('RGB')
            qimage = QImage(
                image.tobytes(), 
                image.width, 
                image.height, 
                image.width * 3, 
                QImage.Format_RGB888
            )
        
        # Scale to thumbnail size
        qimage = qimage.scaled(
            size, 
            Qt.KeepAspectRatio, 
            Qt.SmoothTransformation
        )
        
        # Convert to QPixmap and cache
        pixmap = QPixmap.fromImage(qimage)
        if use_cache:
            self._preview_cache[cache_key] = pixmap
            
        return pixmap
    
    def update_preview(
        self, 
        image_path: str, 
        preview_label: QLabel, 
        max_size: QSize = QSize(800, 600)
    ) -> bool:
        """Update a QLabel with a preview of the specified image.
        
        Args:
            image_path: Path to the image file.
            preview_label: QLabel to display the preview in.
            max_size: Maximum size for the preview.
            
        Returns:
            bool: True if the preview was updated successfully, False otherwise.
        """
        if not image_path or not os.path.isfile(image_path):
            return False
        
        # Load the image
        image = load_image(image_path)
        if image is None:
            return False
        
        # Convert to QImage
        if image.mode == 'RGB':
            qimage = QImage(
                image.tobytes(), 
                image.width, 
                image.height, 
                image.width * 3, 
                QImage.Format_RGB888
            )
        elif image.mode == 'RGBA':
            qimage = QImage(
                image.tobytes(), 
                image.width, 
                image.height, 
                image.width * 4, 
                QImage.Format_RGBA8888
            )
        else:
            # Convert to RGB for other modes
            image = image.convert('RGB')
            qimage = QImage(
                image.tobytes(), 
                image.width, 
                image.height, 
                image.width * 3, 
                QImage.Format_RGB888
            )
        
        # Scale to fit while maintaining aspect ratio
        qimage = qimage.scaled(
            max_size, 
            Qt.KeepAspectRatio, 
            Qt.SmoothTransformation
        )
        
        # Update the preview label
        preview_label.setPixmap(QPixmap.fromImage(qimage))
        return True


class ImageViewer(QGraphicsView):
    """A widget for viewing and interacting with images."""
    
    def __init__(self, parent=None):
        """Initialize the ImageViewer.
        
        Args:
            parent: Parent widget.
        """
        super().__init__(parent)
        self._zoom = 0
        self._empty = True
        self._scene = QGraphicsScene(self)
        self._photo = QGraphicsPixmapItem()
        self._scene.addItem(self._photo)
        self.setScene(self._scene)
        
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setBackgroundBrush(QColor(240, 240, 240))
        self.setFrameShape(QGraphicsView.NoFrame)
        
        # For panning
        self._pan = False
        self._pan_start = QPoint()
    
    def has_photo(self) -> bool:
        """Check if the viewer has an image loaded.
        
        Returns:
            bool: True if an image is loaded, False otherwise.
        """
        return not self._empty
    
    def fit_in_view(self, scale: bool = True) -> None:
        """Fit the image in the view.
        
        Args:
            scale: Whether to scale the image to fit.
        """
        if self._empty:
            return
            
        rect = self.sceneRect()
        if not rect.isNull():
            unity = self.transform().mapRect(QRectF(0, 0, 1, 1))
            self.scale(1 / unity.width(), 1 / unity.height())
            view_rect = self.viewport().rect()
            scene_rect = self.transform().mapRect(rect)
            factor = min(
                view_rect.width() / scene_rect.width(),
                view_rect.height() / scene_rect.height()
            )
            self.scale(factor, factor)
            self._zoom = 0
    
    def set_photo(self, pixmap: Optional[QPixmap] = None) -> None:
        """Set the photo to display.
        
        Args:
            pixmap: The pixmap to display, or None to clear.
        """
        self._zoom = 0
        if pixmap and not pixmap.isNull():
            self._empty = False
            self.setDragMode(QGraphicsView.ScrollHandDrag)
            self._photo.setPixmap(pixmap)
        else:
            self._empty = True
            self.setDragMode(QGraphicsView.NoDrag)
            self._photo.setPixmap(QPixmap())
        
        self.fit_in_view()
    
    def wheelEvent(self, event):
        """Handle mouse wheel events for zooming."""
        if self.has_photo():
            if event.angleDelta().y() > 0:
                factor = 1.25
                self._zoom += 1
            else:
                factor = 0.8
                self._zoom -= 1
            
            if self._zoom > 0:
                self.scale(factor, factor)
            elif self._zoom == 0:
                self.fit_in_view()
            else:
                self._zoom = 0
    
    def mousePressEvent(self, event):
        """Handle mouse press events for panning."""
        if event.button() == Qt.LeftButton and self.dragMode() == QGraphicsView.ScrollHandDrag:
            self._pan = True
            self._pan_start = event.pos()
            self.setCursor(Qt.ClosedHandCursor)
        super().mousePressEvent(event)
    
    def mouseReleaseEvent(self, event):
        """Handle mouse release events for panning."""
        if event.button() == Qt.LeftButton and self._pan:
            self._pan = False
            self.setCursor(Qt.ArrowCursor)
        super().mouseReleaseEvent(event)
    
    def mouseMoveEvent(self, event):
        """Handle mouse move events for panning."""
        if self._pan and self.dragMode() == QGraphicsView.ScrollHandDrag:
            delta = event.pos() - self._pan_start
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - delta.x())
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() - delta.y())
            self._pan_start = event.pos()
        super().mouseMoveEvent(event)
