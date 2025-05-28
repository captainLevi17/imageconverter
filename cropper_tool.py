"""
Image Cropper Tool for Image Master

This module provides functionality for cropping images with various aspect ratios
and options. It allows users to select a region of interest and save the cropped
image in different formats.
"""
import os
from pathlib import Path
from typing import Tuple, Optional
import traceback
import numpy as np
from PIL import Image

# Import PyQt5 modules
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, 
    QPushButton, QFileDialog, QComboBox, QGroupBox, 
    QRadioButton, QButtonGroup, QSizePolicy, QScrollArea, 
    QGridLayout, QFrame, QCheckBox, QSpinBox, QProgressBar,
    QMessageBox, QSizeGrip, QApplication, QStyle, 
    QStyleOptionSlider, QToolTip, QToolButton, QSplitter, 
    QTabWidget, QLabel, QLineEdit
)
from PyQt5.QtCore import (
    Qt, QPoint, QRect, QRectF, QSize, pyqtSignal, QPointF, QTimer,
    QThread, QObject, QEvent, QMarginsF, QBuffer, QByteArray, # Ensure QBuffer and QByteArray are here
    QUrl, QMimeData, QStandardPaths, QFileInfo, QDir, 
    QCoreApplication
)
from PyQt5.QtGui import (
    QPixmap, QImage, QPainter, QPen, QColor, QImageReader,
    QCursor, QIcon, QFont, QFontMetrics, QPainterPath, QBrush, QMouseEvent, QTransform
)

# Import PIL for image processing
try:
    from PIL import Image, ImageQt
except ImportError as e:
    raise ImportError(
        f"Failed to import required modules: {e}\n"
        "Please make sure Pillow is installed with Qt support:\n"
        "pip install pillow pyqt5"
    )

CROPPER_THUMB_IMG_WIDTH = 120  # For the image part of the new thumbnail item
CROPPER_THUMB_IMG_HEIGHT = 120 # For the image part of the new thumbnail item
CROPPER_THUMB_ITEM_WIDTH = 140 # Overall width of the thumbnail item widget
CROPPER_THUMB_ITEM_HEIGHT = 170 # Overall height of the thumbnail item widget
THUMBNAIL_GRID_COLUMNS = 4 # Number of columns in the thumbnail grid

class CropArea(QLabel):
    """Custom widget for selecting crop area with mouse interaction."""
    crop_changed = pyqtSignal(QRect)
    
    def __init__(self, parent=None):
        # Set up the widget
        super().__init__(parent)
        self.setMinimumSize(400, 300)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setStyleSheet("""
            CropArea {
                background-color: #f8f9fa;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
            }
            CropArea QToolButton {
                background-color: #4f46e5;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px 12px;
                margin: 2px;
            }
            CropArea QToolButton:hover {
                background-color: #4338ca;
            }
            CropArea QToolButton:pressed {
                background-color: #3730a3;
            }
            CropArea QLabel {
                color: #4b5563;
                font-size: 12px;
                margin: 4px 0;
            }
        """)
        self.setMouseTracking(True)
        self.setAlignment(Qt.AlignCenter)
        self.setFocusPolicy(Qt.StrongFocus)  # Enable keyboard focus
        
        # Image properties
        self.original_pixmap = None
        self.scaled_pixmap = None
        self.scale_factor = 1.0
        
        # Crop area properties
        self.start_pos = QPoint()
        self.end_pos = QPoint()
        self.is_drawing = False
        self.is_moving = False
        self.is_resizing = False
        self.resize_handle_being_dragged = None # Stores which handle, e.g., 'top_left', 'bottom_right'
        self.move_start_pos = QPoint() # For calculating drag offset
        self.original_selection_rect_on_drag_start = QRect() # Store selection rect when move/resize starts
        self.aspect_ratio = 0  # 0 means free form
        self.fixed_size = QSize(300, 300)  # Default fixed size
        self.min_size = 20  # Minimum crop size
        
        # Visual guides
        self.show_guides = True
        self.guide_style = 'grid'  # 'grid' or 'rule_of_thirds'
        
        # Aspect ratio presets
        self.aspect_ratio_presets = [
            (1, 1),       # 1:1
            (4, 3),       # 4:3
            (16, 9),      # 16:9
            (3, 2),       # 3:2
            (5, 4),       # 5:4
            (2, 3),       # 2:3 (Portrait)
            (9, 16)       # 9:16 (Story/Reels)
        ]
        self.current_aspect_ratio_index = 0
        
        # Set cursor
        self.setCursor(Qt.CrossCursor)
        
        # Timer for continuous key press
        self.key_repeat_timer = QTimer(self)
        self.key_repeat_timer.setInterval(30)  # ~33 FPS
        self.key_repeat_timer.timeout.connect(self.handle_key_repeat)
        self.active_keys = set()
        self.last_key_event = None
    
    def set_pixmap(self, pixmap):
        """Set the image to be cropped."""
        # Reset all display-related properties
        self.original_pixmap = pixmap
        self.offset_x = 0
        self.offset_y = 0
        self.start_pos = QPoint()
        self.end_pos = QPoint()
        
        if pixmap:
            # Calculate initial scale to fit the image in the available space
            available_size = self.size()
            img_size = pixmap.size()
            
            # Calculate the scale factor to fit the image in the available space
            x_scale = (available_size.width() - 40) / img_size.width()  # 20px padding on each side
            y_scale = (available_size.height() - 40) / img_size.height()
            self.scale_factor = min(x_scale, y_scale, 1.0)  # Don't scale up beyond 100%
            
            self.update_scaled_pixmap()
            # Instead of reset_selection, always recenter crop box if aspect ratio is set
            if self.aspect_ratio > 0:
                # Use previous aspect ratio
                self.set_aspect_ratio(*self.get_aspect_ratio_tuple())
            else:
                self.reset_selection()
        else:
            self.scaled_pixmap = None
            self.scale_factor = 1.0
            self.reset_selection()
        self.update()

    def get_aspect_ratio_tuple(self):
        """Return the aspect ratio as (width, height) tuple."""
        if self.aspect_ratio > 0:
            # Try to find a matching preset
            for w, h in self.aspect_ratio_presets:
                if abs((w / h) - self.aspect_ratio) < 0.01:
                    return (w, h)
            # Otherwise, approximate
            return (int(self.aspect_ratio * 100), 100)
        return (0, 0)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.original_pixmap:  # Only proceed if there's an image
            self.update_scaled_pixmap()  # Update scaled pixmap first based on new widget size
            # Recenter crop box on image when widget is resized
            if self.aspect_ratio > 0:
                self.set_aspect_ratio(*self.get_aspect_ratio_tuple())
            # else: # If no aspect ratio, selection might still need update if image moved
                # self.reset_selection() # Or adjust based on new image position
        self.update()

    def clear_pixmap(self):
        """Clear the current pixmap and reset the widget."""
        self.original_pixmap = None
        self.scaled_pixmap = None
        self.scale_factor = 1.0
        self.offset_x = 0
        self.offset_y = 0
        self.start_pos = QPoint()
        self.end_pos = QPoint()
        self.update()
    
    def update_scaled_pixmap(self):
        """Update the scaled pixmap when the widget is resized or image changes."""
        if not self.original_pixmap:
            self.scaled_pixmap = None # Ensure scaled_pixmap is None if original is None
            self.update()
            return
        
        # Get available size (accounting for margins)
        margin = 20  # pixels margin
        available_width = self.width() - margin * 2
        available_height = self.height() - margin * 2

        if available_width <= 0 or available_height <= 0:
            # If available space is invalid, create a minimal or empty pixmap
            self.scaled_pixmap = QPixmap(1, 1) 
            self.scaled_pixmap.fill(Qt.transparent)
            self.update()
            return
        
        available_size = QSize(available_width, available_height)
        
        # Calculate scaled size maintaining aspect ratio
        scaled_size = self.original_pixmap.size()
        scaled_size.scale(available_size, Qt.KeepAspectRatio)
        
        # Scale the pixmap
        self.scaled_pixmap = self.original_pixmap.scaled(
            scaled_size,
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )
        
        # Update the display
        self.update()
        
    def set_aspect_ratio(self, width: int, height: int, keep_current_center=False):
        """Set the aspect ratio for the crop selection."""
        if width > 0 and height > 0:
            self.aspect_ratio = width / height
        else:
            self.aspect_ratio = 0  # Free form

        # Recalculate and recenter the crop box based on the new aspect ratio
        img_rect = self.get_image_rect() # This is the rect of the scaled image within the widget
        # print(f"[set_aspect_ratio] Received img_rect: L{img_rect.left()} T{img_rect.top()} W{img_rect.width()} H{img_rect.height()}")

        if img_rect.isEmpty() or not self.original_pixmap:
            self.reset_selection()
            return
        
        # Calculate dimensions based on aspect ratio, fitting within the image_rect
        if self.aspect_ratio > 0:
            if img_rect.width() / self.aspect_ratio <= img_rect.height():
                crop_width = img_rect.width() * 0.8  # Default to 80% of image width
                crop_height = crop_width / self.aspect_ratio
            else:
                crop_height = img_rect.height() * 0.8 # Default to 80% of image height
                crop_width = crop_height * self.aspect_ratio
        else: # Free form, default to 80% of the smaller dimension of the image_rect
            side = min(img_rect.width(), img_rect.height()) * 0.8
            crop_width = side
            crop_height = side
        
        # print(f"[set_aspect_ratio] Calculated crop_width: {crop_width:.2f}, crop_height: {crop_height:.2f}")

        # Center the new crop box within the image_rect
        center_x = img_rect.left() + img_rect.width() / 2
        center_y = img_rect.top() + img_rect.height() / 2
        # print(f"[set_aspect_ratio] Image Center: ({center_x:.2f}, {center_y:.2f})")

        half_crop_width = crop_width / 2
        half_crop_height = crop_height / 2
        # print(f"[set_aspect_ratio] Half Crop Dims: ({half_crop_width:.2f}, {half_crop_height:.2f})")

        start_x = center_x - half_crop_width
        start_y = center_y - half_crop_height
        end_x = center_x + half_crop_width
        end_y = center_y + half_crop_height
        # print(f"[set_aspect_ratio] Raw start_pos: ({start_x:.2f}, {start_y:.2f}), Raw end_pos: ({end_x:.2f}, {end_y:.2f})")

        # Ensure the crop box is within the image_rect boundaries
        # This logic might need refinement if we want to allow parts of crop box outside image initially
        start_x = max(img_rect.left(), start_x)
        start_y = max(img_rect.top(), start_y)
        end_x = min(img_rect.right(), end_x)
        end_y = min(img_rect.bottom(), end_y)

        # Ensure minimum size
        if crop_width < self.min_size:
            crop_width = self.min_size
        if crop_height < self.min_size:
            crop_height = self.min_size
        
        # print(f"[set_aspect_ratio] Final crop_width: {crop_width}x{crop_height} (after min_size check)")

        # Update start_pos and end_pos
        self.start_pos = QPoint(int(start_x), int(start_y))
        self.end_pos = QPoint(int(start_x + crop_width), int(start_y + crop_height))
        # print(f"[set_aspect_ratio] Final start_pos: {self.start_pos}, Final end_pos: {self.end_pos}")

        self.crop_changed.emit(QRect(self.start_pos, self.end_pos).normalized())
        self.update() # Ensure the widget repaints to show the new/updated crop box
    
    def get_image_rect(self) -> QRect:
        """Calculate the rectangle where the scaled image is actually drawn within the widget."""
        if not self.scaled_pixmap:
            return QRect(0, 0, self.width(), self.height()) # Return widget rect if no image

        widget_w, widget_h = self.width(), self.height()
        scaled_w, scaled_h = self.scaled_pixmap.width(), self.scaled_pixmap.height()

        offset_x = (widget_w - scaled_w) // 2
        offset_y = (widget_h - scaled_h) // 2
        
        # print(f"[get_image_rect] Widget: {self.width()}x{self.height()}, ScaledPixmap: {scaled_w}x{scaled_h}, Offset: ({offset_x}, {offset_y})")
        return QRect(offset_x, offset_y, scaled_w, scaled_h)

    def paintEvent(self, event):
        """Handle paint events."""
        super().paintEvent(event) 
        painter = QPainter(self) # Initialize painter here

        if not self.scaled_pixmap:
            painter.fillRect(self.rect(), QColor("#e0e0e0"))
            painter.setPen(Qt.black)
            painter.drawText(self.rect(), Qt.AlignCenter, "No image loaded")
            painter.end() # End painter if no image
            return
        
        img_rect = self.get_image_rect()
        # print(f"[paintEvent] Widget: {self.width()}x{self.height()}, ScaledPixmap: {self.scaled_pixmap.width()}x{self.scaled_pixmap.height()}, Image draw offset: ({img_rect.x()}, {img_rect.y()})")
        painter.drawPixmap(img_rect.topLeft(), self.scaled_pixmap)
        
        if not self.start_pos.isNull() and not self.end_pos.isNull():
            sel_rect = QRect(self.start_pos, self.end_pos).normalized()
            # print(f"[paintEvent] Drawing crop box from {self.start_pos} to {self.end_pos}, Normalized: {sel_rect}")
            
            # Draw semi-transparent overlay outside selection
            overlay_path = QPainterPath()
            overlay_path.setFillRule(Qt.OddEvenFill) # Ensures the inner rect creates a hole
            overlay_path.addRect(QRectF(self.rect())) # Covers the whole widget
            overlay_path.addRect(QRectF(sel_rect)) # This creates a hole for the selection
            painter.fillPath(overlay_path, QColor(0, 0, 0, 128)) # Semi-transparent black
            
            # Draw the selection rectangle border
            pen = QPen(Qt.white, 1, Qt.SolidLine) # Changed to solid for now, easier to see
            painter.setPen(pen)
            painter.drawRect(sel_rect)
            
            # Draw resize handles
            handle_size = 8
            if sel_rect.width() > handle_size * 2 and sel_rect.height() > handle_size * 2:
                painter.setBrush(Qt.white)
                painter.setPen(Qt.black) # Border for handles
                handle_visual_rects = self.get_handle_rects(sel_rect, handle_size)
                for r in handle_visual_rects.values():
                    painter.drawRect(r)
            
            # Draw guides if enabled (placeholder for now)
            if self.show_guides:
                pen.setStyle(Qt.DashLine)
                pen.setColor(QColor(255,255,255,100))
                painter.setPen(pen)
                # Basic rule of thirds example
                third_w = sel_rect.width() / 3.0
                third_h = sel_rect.height() / 3.0
                painter.drawLine(int(sel_rect.left() + third_w), sel_rect.top(), int(sel_rect.left() + third_w), sel_rect.bottom())
                painter.drawLine(int(sel_rect.left() + 2 * third_w), sel_rect.top(), int(sel_rect.left() + 2 * third_w), sel_rect.bottom())
                painter.drawLine(sel_rect.left(), int(sel_rect.top() + third_h), sel_rect.right(), int(sel_rect.top() + third_h))
                painter.drawLine(sel_rect.left(), int(sel_rect.top() + 2 * third_h), sel_rect.right(), int(sel_rect.top() + 2 * third_h))

        painter.end() # Moved to the very end

    def selection_rect(self):
        """Return the current selection rectangle in image coordinates."""
        if self.start_pos.isNull() or self.end_pos.isNull() or not self.original_pixmap:
            return QRect()
            
        img_rect = self.get_image_rect()
        if img_rect.isNull() or img_rect.width() == 0 or img_rect.height() == 0:
            return QRect()
            
        scale_x = self.original_pixmap.width() / img_rect.width()
        scale_y = self.original_pixmap.height() / img_rect.height()
        
        x1 = round((min(self.start_pos.x(), self.end_pos.x()) - img_rect.x()) * scale_x)
        y1 = round((min(self.start_pos.y(), self.end_pos.y()) - img_rect.y()) * scale_y)
        x2 = round((max(self.start_pos.x(), self.end_pos.x()) - img_rect.x()) * scale_x)
        y2 = round((max(self.start_pos.y(), self.end_pos.y()) - img_rect.y()) * scale_y)
        
        width = max(1, x2 - x1)
        height = max(1, y2 - y1)
        
        return QRect(x1, y1, width, height)

    def reset_selection(self):
        """Reset the selection area."""
        self.start_pos = QPoint()
        self.end_pos = QPoint()
        self.update()
        self.crop_changed.emit(QRect())

    def keyPressEvent(self, event):
        """Handle key press events for keyboard shortcuts."""
        key = event.key()
        self.active_keys.add(key)
        self.last_key_event = event
        
        if key == Qt.Key_Escape:
            self.reset_selection()
        elif key in (Qt.Key_Return, Qt.Key_Enter, Qt.Key_Space):
            # Check if parent exists and has the crop_and_save_action method
            parent_widget = self.parent()
            if parent_widget and hasattr(parent_widget, 'crop_and_save_action'):
                parent_widget.crop_and_save_action()
        elif key == Qt.Key_Plus or key == Qt.Key_Equal:
            self.adjust_zoom(1.1)
        elif key == Qt.Key_Minus or key == Qt.Key_Underscore:
            self.adjust_zoom(0.9)
        
        if not self.key_repeat_timer.isActive() and self.active_keys:
            self.key_repeat_timer.start()
    
    def keyReleaseEvent(self, event):
        """Handle key release events."""
        key = event.key()
        if key in self.active_keys:
            self.active_keys.remove(key)
        
        if not self.active_keys and self.key_repeat_timer.isActive():
            self.key_repeat_timer.stop()
    
    def handle_key_repeat(self):
        """Handle continuous key press events."""
        if not self.active_keys or not self.last_key_event:
            return
            
        move_step = 5
        resize_step = 2
        
        # Create a copy of active_keys for safe iteration if modification occurs
        for key in list(self.active_keys):
            if key == Qt.Key_Left:
                if Qt.Key_Shift in self.active_keys:
                    self.resize_crop_area(-resize_step, 0)    
                else:
                    self.move_crop_area(-move_step, 0)
            elif key == Qt.Key_Right:
                if Qt.Key_Shift in self.active_keys:
                    self.resize_crop_area(resize_step, 0)
                else:
                    self.move_crop_area(move_step, 0)
            elif key == Qt.Key_Up:
                if Qt.Key_Shift in self.active_keys:
                    self.resize_crop_area(0, -resize_step)
                else:
                    self.move_crop_area(0, -move_step)
            elif key == Qt.Key_Down:
                if Qt.Key_Shift in self.active_keys:
                    self.resize_crop_area(0, resize_step)
                else:
                    self.move_crop_area(0, move_step)
            # Shift key alone doesn't do anything, it modifies arrow keys

    def move_crop_area(self, dx, dy):
        """Move the crop area by the specified delta in widget coordinates."""
        if self.start_pos.isNull() or self.end_pos.isNull():
            return

        img_rect = self.get_image_rect()
        if img_rect.isNull():
            return

        new_start_pos = self.start_pos + QPoint(dx, dy)
        new_end_pos = self.end_pos + QPoint(dx, dy)

        # Create a potential new selection rectangle to check its bounds
        potential_sel_rect = QRect(new_start_pos, new_end_pos).normalized()

        # Check if the new selection rectangle is within the image rectangle
        # We need to ensure all corners of the potential_sel_rect are within img_rect
        if (img_rect.contains(potential_sel_rect.topLeft()) and
            img_rect.contains(potential_sel_rect.bottomRight()) and
            img_rect.contains(potential_sel_rect.topRight()) and
            img_rect.contains(potential_sel_rect.bottomLeft())):
            self.start_pos = new_start_pos
            self.end_pos = new_end_pos
            self.update()
            self.crop_changed.emit(self.selection_rect())

    def resize_crop_area(self, dw, dh):
        """Resize the crop area by the specified delta, maintaining aspect ratio if set."""
        if self.start_pos.isNull() or self.end_pos.isNull():
            return

        img_rect = self.get_image_rect()
        if img_rect.isNull():
            return

        current_rect = QRect(self.start_pos, self.end_pos).normalized()
        new_width = current_rect.width() + dw
        new_height = current_rect.height() + dh
        
        # Ensure minimum size
        min_dim = 20 
        new_width = max(min_dim, new_width)
        new_height = max(min_dim, new_height)

        if self.aspect_ratio > 0:
            if dw != 0: # Width changed primarily
                new_height = new_width / self.aspect_ratio
            elif dh != 0: # Height changed primarily
                new_width = new_height * self.aspect_ratio
        
        # Anchor is top-left for now, adjust end_pos
        # More sophisticated resizing would consider which handle is 'dragged'
        new_end_x = self.start_pos.x() + new_width
        new_end_y = self.start_pos.y() + new_height
        
        potential_new_end_pos = QPoint(int(round(new_end_x)), int(round(new_end_y)))

        if img_rect.contains(self.start_pos) and img_rect.contains(potential_new_end_pos):
            self.end_pos = potential_new_end_pos
            self.update()
            self.crop_changed.emit(self.selection_rect())

    def adjust_zoom(self, factor):
        """Adjust the zoom level of the image."""
        if not self.original_pixmap:
            return
            
        old_scale = self.scale_factor
        self.scale_factor = max(0.1, min(10.0, self.scale_factor * factor))
        
        if self.scale_factor != old_scale:
            self.update_scaled_pixmap()
            # After zoom, the crop box might need recentering or revalidation
            if not self.start_pos.isNull() and self.aspect_ratio > 0:
                 self.set_aspect_ratio(int(self.aspect_ratio * 100), 100) # Re-apply aspect to recenter/resize
            else:
                self.update() # General update if no aspect ratio set

    def get_handle_rects(self, sel_rect: QRect, handle_size: int) -> dict:
        """Calculate rectangles for all 8 resize handles."""
        half_handle = handle_size // 2
        handles = {}
        handles['top_left'] = QRect(sel_rect.left() - half_handle, sel_rect.top() - half_handle, handle_size, handle_size)
        handles['top_right'] = QRect(sel_rect.right() - half_handle, sel_rect.top() - half_handle, handle_size, handle_size)
        handles['bottom_left'] = QRect(sel_rect.left() - half_handle, sel_rect.bottom() - half_handle, handle_size, handle_size)
        handles['bottom_right'] = QRect(sel_rect.right() - half_handle, sel_rect.bottom() - half_handle, handle_size, handle_size)
        handles['top_middle'] = QRect(sel_rect.center().x() - half_handle, sel_rect.top() - half_handle, handle_size, handle_size)
        handles['bottom_middle'] = QRect(sel_rect.center().x() - half_handle, sel_rect.bottom() - half_handle, handle_size, handle_size)
        handles['left_middle'] = QRect(sel_rect.left() - half_handle, sel_rect.center().y() - half_handle, handle_size, handle_size)
        handles['right_middle'] = QRect(sel_rect.right() - half_handle, sel_rect.center().y() - half_handle, handle_size, handle_size)
        return handles

    def determine_resize_handle(self, pos: QPoint) -> str:
        """Check if the mouse position is over any resize handle."""
        if self.start_pos.isNull() or self.end_pos.isNull():
            return None
        sel_rect = QRect(self.start_pos, self.end_pos).normalized()
        handle_size = 10 # Make handle detection area slightly larger than visual
        
        handles = self.get_handle_rects(sel_rect, handle_size)
        for name, rect in handles.items():
            if rect.contains(pos):
                return name
        return None

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() != Qt.LeftButton or not self.scaled_pixmap:
            return

        img_rect = self.get_image_rect()
        if not img_rect.contains(event.pos()): # Click outside displayed image
            # Optionally, could reset selection here if preferred
            # self.reset_selection()
            return

        self.resize_handle_being_dragged = self.determine_resize_handle(event.pos())
        current_selection_rect = QRect(self.start_pos, self.end_pos).normalized()

        if self.resize_handle_being_dragged:
            self.is_resizing = True
            self.move_start_pos = event.pos()
            self.original_selection_rect_on_drag_start = current_selection_rect
        elif current_selection_rect.contains(event.pos()):
            self.is_moving = True
            self.move_start_pos = event.pos()
            self.original_selection_rect_on_drag_start = current_selection_rect
        else: # Start new selection
            self.is_drawing = True
            self.start_pos = event.pos()
            self.end_pos = event.pos()
            # Ensure new selection starts within image bounds if logic requires it
            # For now, raw widget coordinates are fine, will be clamped or adjusted in move
        self.update()

    def mouseMoveEvent(self, event: QMouseEvent):
        if not self.scaled_pixmap:
            self.setCursor(Qt.ArrowCursor)
            return

        img_rect = self.get_image_rect()
        mouse_pos = event.pos()

        if not (self.is_drawing or self.is_moving or self.is_resizing):
            handle = self.determine_resize_handle(mouse_pos)
            if handle:
                if handle in ['top_left', 'bottom_right']:
                    self.setCursor(Qt.SizeFDiagCursor)
                elif handle in ['top_right', 'bottom_left']:
                    self.setCursor(Qt.SizeBDiagCursor)
                elif handle in ['top_middle', 'bottom_middle']:
                    self.setCursor(Qt.SizeVerCursor)
                elif handle in ['left_middle', 'right_middle']:
                    self.setCursor(Qt.SizeHorCursor)
            elif QRect(self.start_pos, self.end_pos).normalized().contains(mouse_pos):
                self.setCursor(Qt.SizeAllCursor)
            else:
                self.setCursor(Qt.CrossCursor if img_rect.contains(mouse_pos) else Qt.ArrowCursor)
            return

        delta = mouse_pos - self.move_start_pos

        if self.is_drawing:
            self.end_pos = mouse_pos
            # Clamp self.end_pos to img_rect boundaries
            self.end_pos.setX(max(img_rect.left(), min(self.end_pos.x(), img_rect.right())))
            self.end_pos.setY(max(img_rect.top(), min(self.end_pos.y(), img_rect.bottom())))

        elif self.is_moving:
            orig_rect = self.original_selection_rect_on_drag_start
            new_top_left = orig_rect.topLeft() + delta
            new_bottom_right = orig_rect.bottomRight() + delta
            
            # Keep selection within image bounds while moving
            new_rect_width = orig_rect.width()
            new_rect_height = orig_rect.height()

            new_top_left.setX(max(img_rect.left(), min(new_top_left.x(), img_rect.right() - new_rect_width)))
            new_top_left.setY(max(img_rect.top(), min(new_top_left.y(), img_rect.bottom() - new_rect_height)))
            
            self.start_pos = new_top_left
            self.end_pos = QPoint(new_top_left.x() + new_rect_width, new_top_left.y() + new_rect_height)

        elif self.is_resizing:
            # Basic free-form resizing for now. Aspect ratio constraint will be added later.
            orig_rect = self.original_selection_rect_on_drag_start
            new_rect = QRect(orig_rect) # Make a copy

            if self.resize_handle_being_dragged == 'top_left':
                new_rect.setTopLeft(orig_rect.topLeft() + delta)
            elif self.resize_handle_being_dragged == 'top_right':
                new_rect.setTopRight(orig_rect.topRight() + delta)
            elif self.resize_handle_being_dragged == 'bottom_left':
                new_rect.setBottomLeft(orig_rect.bottomLeft() + delta)
            elif self.resize_handle_being_dragged == 'bottom_right':
                new_rect.setBottomRight(orig_rect.bottomRight() + delta)
            elif self.resize_handle_being_dragged == 'top_middle':
                new_rect.setTop(orig_rect.top() + delta.y())
            elif self.resize_handle_being_dragged == 'bottom_middle':
                new_rect.setBottom(orig_rect.bottom() + delta.y())
            elif self.resize_handle_being_dragged == 'left_middle':
                new_rect.setLeft(orig_rect.left() + delta.x())
            elif self.resize_handle_being_dragged == 'right_middle':
                new_rect.setRight(orig_rect.right() + delta.x())
            
            # Ensure rect stays within image_rect and has min size
            new_rect.setLeft(max(img_rect.left(), new_rect.left()))
            new_rect.setTop(max(img_rect.top(), new_rect.top()))
            new_rect.setRight(min(img_rect.right(), new_rect.right()))
            new_rect.setBottom(min(img_rect.bottom(), new_rect.bottom()))
            
            min_dim = 10 # Minimum dimension for selection
            if new_rect.width() < min_dim: new_rect.setWidth(min_dim)
            if new_rect.height() < min_dim: new_rect.setHeight(min_dim)

            self.start_pos = new_rect.topLeft()
            self.end_pos = new_rect.bottomRight()
            
            # TODO: Add aspect ratio constraint here if self.aspect_ratio > 0
            # self.constrain_selection_aspect_ratio_on_resize()

        self.update()

    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            if self.is_drawing or self.is_moving or self.is_resizing:
                self.crop_changed.emit(self.selection_rect())
            
            self.is_drawing = False
            self.is_moving = False
            self.is_resizing = False
            self.resize_handle_being_dragged = None
            self.setCursor(Qt.ArrowCursor) # Reset cursor
            self.update()
    
    def paintEvent(self, event):
        """Handle paint events."""
        super().paintEvent(event) 
        painter = QPainter(self) # Initialize painter here

        if not self.scaled_pixmap:
            painter.fillRect(self.rect(), QColor("#e0e0e0"))
            painter.setPen(Qt.black)
            painter.drawText(self.rect(), Qt.AlignCenter, "No image loaded")
            painter.end() # End painter if no image
            return
        
        img_rect = self.get_image_rect()
        # print(f"[paintEvent] Widget: {self.width()}x{self.height()}, ScaledPixmap: {self.scaled_pixmap.width()}x{self.scaled_pixmap.height()}, Image draw offset: ({img_rect.x()}, {img_rect.y()})")
        painter.drawPixmap(img_rect.topLeft(), self.scaled_pixmap)
        
        if not self.start_pos.isNull() and not self.end_pos.isNull():
            sel_rect = QRect(self.start_pos, self.end_pos).normalized()
            # print(f"[paintEvent] Drawing crop box from {self.start_pos} to {self.end_pos}, Normalized: {sel_rect}")
            
            # Draw semi-transparent overlay outside selection
            overlay_path = QPainterPath()
            overlay_path.setFillRule(Qt.OddEvenFill) # Ensures the inner rect creates a hole
            overlay_path.addRect(QRectF(self.rect())) # Covers the whole widget
            overlay_path.addRect(QRectF(sel_rect)) # This creates a hole for the selection
            painter.fillPath(overlay_path, QColor(0, 0, 0, 128)) # Semi-transparent black
            
            # Draw the selection rectangle border
            pen = QPen(Qt.white, 1, Qt.SolidLine) # Changed to solid for now, easier to see
            painter.setPen(pen)
            painter.drawRect(sel_rect)
            
            # Draw resize handles
            handle_size = 8
            if sel_rect.width() > handle_size * 2 and sel_rect.height() > handle_size * 2:
                painter.setBrush(Qt.white)
                painter.setPen(Qt.black) # Border for handles
                handle_visual_rects = self.get_handle_rects(sel_rect, handle_size)
                for r in handle_visual_rects.values():
                    painter.drawRect(r)
            
            # Draw guides if enabled (placeholder for now)
            if self.show_guides:
                pen.setStyle(Qt.DashLine)
                pen.setColor(QColor(255,255,255,100))
                painter.setPen(pen)
                # Basic rule of thirds example
                third_w = sel_rect.width() / 3.0
                third_h = sel_rect.height() / 3.0
                painter.drawLine(int(sel_rect.left() + third_w), sel_rect.top(), int(sel_rect.left() + third_w), sel_rect.bottom())
                painter.drawLine(int(sel_rect.left() + 2 * third_w), sel_rect.top(), int(sel_rect.left() + 2 * third_w), sel_rect.bottom())
                painter.drawLine(sel_rect.left(), int(sel_rect.top() + third_h), sel_rect.right(), int(sel_rect.top() + third_h))
                painter.drawLine(sel_rect.left(), int(sel_rect.top() + 2 * third_h), sel_rect.right(), int(sel_rect.top() + 2 * third_h))

        painter.end() # Moved to the very end

    def rotate_image(self, angle):
        """Rotate the original_pixmap by the given angle (degrees)."""
        if not self.original_pixmap:
            return
            
        # Store current aspect ratio settings
        current_ar = self.aspect_ratio
        ar_tuple = self.get_aspect_ratio_tuple()
        
        # Rotate the image
        transform = QTransform().rotate(angle)
        self.original_pixmap = self.original_pixmap.transformed(transform, Qt.SmoothTransformation)
        
        # Update the scaled pixmap and reset selection
        self.update_scaled_pixmap()
        
        # Re-apply aspect ratio if one was set
        if current_ar > 0:
            # Swap width/height for 90/270 degree rotations
            if abs(angle) % 180 == 90:
                ar_tuple = (ar_tuple[1], ar_tuple[0])
            self.set_aspect_ratio(*ar_tuple, keep_current_center=True)
        else:
            self.reset_selection()
            
        self.update()
        self.crop_changed.emit(self.selection_rect())
        
        # Notify parent to update the PIL image
        if hasattr(self.parent(), '_update_pil_image_safely'):
            self.parent()._update_pil_image_safely()

    def flip_horizontal_image(self):
        """Flip the original_pixmap horizontally."""
        if not self.original_pixmap:
            return
            
        # Store current selection
        current_sel = self.selection_rect()
        
        # Flip the image
        qimage = self.original_pixmap.toImage()
        flipped_qimage = qimage.mirrored(True, False)
        self.original_pixmap = QPixmap.fromImage(flipped_qimage)
        
        # Update display and selection
        self.update_scaled_pixmap()
        self.update()
        
        # Maintain the same selection area (flipped)
        if not current_sel.isNull():
            img_rect = self.get_image_rect()
            new_x = img_rect.right() - current_sel.right() + img_rect.left()
            self.start_pos = QPoint(new_x, current_sel.top())
            self.end_pos = QPoint(new_x + current_sel.width(), current_sel.bottom())
        
        self.crop_changed.emit(self.selection_rect())
        
        # Notify parent to update the PIL image
        if hasattr(self.parent(), '_update_pil_image_safely'):
            self.parent()._update_pil_image_safely()

    def flip_vertical_image(self):
        """Flip the original_pixmap vertically."""
        if not self.original_pixmap:
            return
            
        # Store current selection
        current_sel = self.selection_rect()
        
        # Flip the image
        qimage = self.original_pixmap.toImage()
        flipped_qimage = qimage.mirrored(False, True)
        self.original_pixmap = QPixmap.fromImage(flipped_qimage)
        
        # Update display and selection
        self.update_scaled_pixmap()
        self.update()
        
        # Maintain the same selection area (flipped)
        if not current_sel.isNull():
            img_rect = self.get_image_rect()
            new_y = img_rect.bottom() - current_sel.bottom() + img_rect.top()
            self.start_pos = QPoint(current_sel.left(), new_y)
            self.end_pos = QPoint(current_sel.right(), new_y + current_sel.height())
        
        self.crop_changed.emit(self.selection_rect())
        
        # Notify parent to update the PIL image
        if hasattr(self.parent(), '_update_pil_image_safely'):
            self.parent()._update_pil_image_safely()

class CropperThumbnailItem(QWidget):
    """Custom widget for displaying a single thumbnail in the CropperTool gallery."""
    clicked = pyqtSignal(str)  # Emits image path when clicked

    def __init__(self, image_path, parent=None):
        super().__init__(parent)
        self.image_path = image_path
        self.is_selected = False

        self.setFixedSize(CROPPER_THUMB_ITEM_WIDTH, CROPPER_THUMB_ITEM_HEIGHT)
        self.setStyleSheet("""
            CropperThumbnailItem {
                border: 1px solid #ddd;
                margin: 2px;
                padding: 5px;
                background-color: white;
                border-radius: 4px;
            }
            CropperThumbnailItem[selected="true"] {
                border: 2px solid #007bff; /* Blue border for selected */
                background-color: #e7f3ff; /* Light blue background for selected */
            }
            CropperThumbnailItem QLabel#imageLabel {
                border: 1px solid #eee;
                background-color: #f8f8f8; /* Light gray for image background */
            }
            CropperThumbnailItem QLabel#nameLabel {
                font-size: 9pt; /* Slightly smaller font for filename */
                color: #333;
            }
        """)

        item_layout = QVBoxLayout(self)
        item_layout.setContentsMargins(0, 0, 0, 0) # Margins are handled by padding in stylesheet
        item_layout.setSpacing(4)

        self.image_label = QLabel()
        self.image_label.setObjectName("imageLabel") # For specific styling
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setFixedSize(CROPPER_THUMB_IMG_WIDTH, CROPPER_THUMB_IMG_HEIGHT)
        self.image_label.setText("...") # Placeholder while loading
        item_layout.addWidget(self.image_label, 0, Qt.AlignCenter)

        self.name_label = QLabel(os.path.basename(image_path))
        self.name_label.setObjectName("nameLabel")
        self.name_label.setAlignment(Qt.AlignCenter)
        self.name_label.setWordWrap(True)
        # Ensure name_label can expand horizontally but has limited height
        self.name_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.name_label.setMaximumHeight(self.fontMetrics().height() * 2 + 4) # Max 2 lines
        item_layout.addWidget(self.name_label)
        
        item_layout.addStretch(1) # Pushes content up if there's extra space

        self.setLayout(item_layout)
        self.set_thumbnail_pixmap()

    def set_thumbnail_pixmap(self):
        try:
            img = Image.open(self.image_path)
            img.thumbnail((CROPPER_THUMB_IMG_WIDTH, CROPPER_THUMB_IMG_HEIGHT), Image.Resampling.LANCZOS)
            
            # Convert PIL Image to QPixmap safely
            # Ensure image is in a mode that QImage can handle directly or convert it
            if img.mode == 'P': # Palette mode, often needs conversion
                img = img.convert('RGBA')
            elif img.mode == 'LA': # Luminance Alpha
                 img = img.convert('RGBA')
            elif img.mode not in ['RGB', 'RGBA']:
                img = img.convert('RGB') # Fallback to RGB for other modes

            if img.mode == 'RGBA':
                q_image = QImage(img.tobytes("raw", "RGBA"), img.width, img.height, QImage.Format_RGBA8888)
            elif img.mode == 'RGB':
                q_image = QImage(img.tobytes("raw", "RGB"), img.width, img.height, QImage.Format_RGB888)
            else: # Should not happen due to conversions above
                print(f"Unsupported image mode {img.mode} for {self.image_path}")
                self.image_label.setText("Error")
                return

            if q_image.isNull():
                print(f"Failed to create QImage for {self.image_path}")
                self.image_label.setText("Error")
                return

            pixmap = QPixmap.fromImage(q_image)
            if not pixmap.isNull():
                self.image_label.setPixmap(pixmap.scaled(CROPPER_THUMB_IMG_WIDTH, CROPPER_THUMB_IMG_HEIGHT, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            else:
                self.image_label.setText("Error")
        except Exception as e:
            print(f"Error creating thumbnail for {self.image_path}: {e}")
            traceback.print_exc() # Add traceback for more details
            self.image_label.setText("Error")

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.image_path)
        super().mousePressEvent(event)

    def set_selected(self, selected: bool):
        self.is_selected = selected
        self.setProperty("selected", "true" if selected else "false") # Use string for property
        self.style().unpolish(self)
        self.style().polish(self)
        # self.update() # update is implicitly called by polish

class CropperTool(QWidget):
    """Main widget for the Image Cropper tool."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        # Initialize variables
        self.image_paths = [] # Will be populated from list widget items if needed, or can be removed
        # self.current_image_index = -1 # No longer needed, selection driven by list widget
        self.current_pil_image = None # Store the current PIL image for cropping
        self.output_dir = None
        self.thumbnail_items = [] # To store CropperThumbnailItem instances
        self.current_selected_thumbnail_item = None # To track the currently selected item
        
        # Initialize UI
        self.init_ui()
    
    def init_ui(self):
        """Initialize the user interface."""
        # Set up the main layout with proper spacing
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(12)
        
        # Left panel - Image cropping area
        preview_group = QGroupBox("Preview & Crop")
        preview_group.setStyleSheet("""
            QGroupBox {
                border: 1px solid #ccc;
                border-radius: 4px;
                margin-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 3px;
            }
        """)
        preview_layout = QVBoxLayout(preview_group)
        preview_layout.setContentsMargins(4, 16, 4, 4)
        preview_layout.setSpacing(8)
        
        # Thumbnail gallery at the top
        thumbnail_group = QGroupBox("Images")
        thumbnail_group.setStyleSheet("""
            QGroupBox {
                border: 1px solid #e0e0e0;
                border-radius: 4px;
                margin-top: 10px;
                padding: 4px 0 8px 0;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        thumbnail_group_layout = QVBoxLayout(thumbnail_group)
        thumbnail_group_layout.setContentsMargins(4, 14, 4, 4)
        
        # Buttons for adding/clearing images
        btn_layout = QHBoxLayout()
        btn_layout.setContentsMargins(4, 0, 4, 4)
        
        self.add_images_button = QPushButton(QIcon.fromTheme("list-add"), "Add Images")
        self.add_images_button.clicked.connect(self.browse_images)
        self.clear_button = QPushButton(QIcon.fromTheme("list-remove"), "Clear")
        self.clear_button.clicked.connect(self.clear_images)
        
        btn_layout.addWidget(self.add_images_button)
        btn_layout.addWidget(self.clear_button)
        btn_layout.addStretch()
        
        # Scroll area for thumbnails
        self.thumbnail_scroll = QScrollArea()
        self.thumbnail_scroll.setWidgetResizable(True)
        self.thumbnail_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.thumbnail_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.thumbnail_scroll.setFixedHeight(150)  # Fixed height for horizontal scrolling
        
        # Container widget for the thumbnails
        self.thumbnail_container = QWidget()
        self.thumbnail_layout = QHBoxLayout(self.thumbnail_container)
        self.thumbnail_layout.setContentsMargins(5, 5, 5, 5)
        self.thumbnail_layout.setSpacing(5)
        self.thumbnail_layout.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        
        # Add a stretch to keep thumbnails left-aligned
        self.thumbnail_layout.addStretch()
        
        self.thumbnail_scroll.setWidget(self.thumbnail_container)
        
        # Add widgets to thumbnail group
        thumbnail_group_layout.addLayout(btn_layout)
        thumbnail_group_layout.addWidget(self.thumbnail_scroll)
        
        # Add thumbnail group to preview layout
        preview_layout.addWidget(thumbnail_group)
        
        # Crop area (the only widget that displays the image)
        self.crop_area = CropArea()
        self.crop_area.crop_changed.connect(self.on_crop_changed)
        preview_layout.addWidget(self.crop_area, 1)
        
        # Right panel - Controls
        control_group = QWidget()
        control_group.setMinimumWidth(280)
        control_group.setMaximumWidth(350)
        control_layout = QVBoxLayout(control_group)
        control_layout.setContentsMargins(0, 0, 0, 0)
        control_layout.setSpacing(12)
        
        # Scroll area for controls
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(2, 2, 10, 2)
        scroll_layout.setSpacing(12)
        
        scroll.setWidget(scroll_content)
        control_layout.addWidget(scroll)
        
        # Apply styles to all group boxes
        group_style = """
            QGroupBox {
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 8px 6px 12px 6px;
                margin-top: 1ex;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 8px;
                padding: 0 5px;
            }
        """
        
        # Output settings group
        output_group = QGroupBox("Output Settings")
        output_group.setStyleSheet(group_style)
        output_layout = QVBoxLayout(output_group)
        output_layout.setContentsMargins(8, 16, 8, 8)
        output_layout.setSpacing(8)
        
        # Format and quality settings
        format_quality_layout = QHBoxLayout()
        
        # Format selection
        format_layout = QHBoxLayout()
        format_layout.addWidget(QLabel("Format:"))
        self.format_combo = QComboBox()
        self.format_combo.addItems(["JPEG", "PNG", "WebP"])
        self.format_combo.setCurrentText("JPEG")
        format_layout.addWidget(self.format_combo, 1)
        format_quality_layout.addLayout(format_layout)
        
        # Quality setting
        quality_layout = QHBoxLayout()
        quality_layout.addWidget(QLabel("Quality:"))
        self.quality_slider = QSpinBox()
        self.quality_slider.setRange(1, 100)
        self.quality_slider.setValue(90)
        self.quality_slider.setSuffix("%")
        quality_layout.addWidget(self.quality_slider, 1)
        format_quality_layout.addLayout(quality_layout)
        
        output_layout.addLayout(format_quality_layout)
        
        # Filename options
        filename_layout = QGridLayout()
        filename_layout.setColumnStretch(1, 1)
        
        self.filename_prefix_input = QLineEdit()
        self.filename_suffix_input = QLineEdit("_cropped")
        self.overwrite_checkbox = QCheckBox("Overwrite existing files")
        
        filename_layout.addWidget(QLabel("Prefix:"), 0, 0)
        filename_layout.addWidget(self.filename_prefix_input, 0, 1)
        filename_layout.addWidget(QLabel("Suffix:"), 1, 0)
        filename_layout.addWidget(self.filename_suffix_input, 1, 1)
        filename_layout.addWidget(self.overwrite_checkbox, 2, 0, 1, 2)
        
        # Output directory selection
        output_dir_layout = QHBoxLayout()
        self.output_dir_button = QPushButton("Choose Output Directory")
        self.output_dir_button.clicked.connect(self.choose_output_dir)
        self.output_dir_label = QLabel("Not Set")
        self.output_dir_label.setWordWrap(True)
        self.output_dir_label.setStyleSheet("color: #666;")
        
        output_dir_layout.addWidget(QLabel("Save to:"))
        output_dir_layout.addWidget(self.output_dir_label, 1)
        output_dir_layout.addWidget(self.output_dir_button)
        
        # Add all widgets to the output group
        output_layout.addLayout(filename_layout)
        output_layout.addLayout(output_dir_layout)
        output_layout.addStretch(1)
        
        # Aspect ratio presets
        aspect_group = QGroupBox("Aspect Ratio")
        aspect_group.setStyleSheet(group_style)
        aspect_layout = QVBoxLayout(aspect_group)
        aspect_layout.setContentsMargins(6, 16, 6, 6)
        aspect_layout.setSpacing(6)
        
        self.aspect_buttons = QButtonGroup()
        self.aspect_buttons.setExclusive(True)
        
        ratios = [
            ("Free Form", 0, 0),
            ("1:1 Square", 1, 1),
            ("4:3 Standard", 4, 3),
            ("16:9 Widescreen", 16, 9),
            ("3:2 Film", 3, 2),
            ("5:4 Classic", 5, 4),
            ("2:3 Portrait", 2, 3),
            ("9:16 Story/Reels", 9, 16),
            ("Custom", -1, -1)
        ]
        
        for text, w, h in ratios:
            btn = QRadioButton(text)
            btn.w = w
            btn.h = h
            btn.toggled.connect(self.on_aspect_ratio_changed)
            aspect_layout.addWidget(btn)
            self.aspect_buttons.addButton(btn)
        
        custom_layout = QHBoxLayout()
        self.custom_width = QSpinBox()
        self.custom_width.setRange(1, 10000)
        self.custom_width.setValue(16)
        self.custom_height = QSpinBox()
        self.custom_height.setRange(1, 10000)
        self.custom_height.setValue(9)
        self.custom_width.valueChanged.connect(self.update_custom_aspect_ratio)
        self.custom_height.valueChanged.connect(self.update_custom_aspect_ratio)
        
        custom_layout.addWidget(QLabel("Custom:"))
        custom_layout.addWidget(self.custom_width)
        custom_layout.addWidget(QLabel("×"))
        custom_layout.addWidget(self.custom_height)
        custom_layout.addStretch()
        aspect_layout.addLayout(custom_layout)
        aspect_group.setLayout(aspect_layout)
        
        # Transformation controls
        transform_group = QGroupBox("Transform")
        transform_group.setStyleSheet(group_style)
        transform_layout = QGridLayout(transform_group)
        transform_layout.setContentsMargins(8, 20, 8, 8)
        transform_layout.setSpacing(6)
        
        # Button style - updated to match main UI buttons
        btn_style = """
            QPushButton {
                padding: 6px 12px;
                min-width: 80px;
                max-width: 100px;
                font-size: 12px;
                font-weight: 500;
                color: #333333;
                border: 1px solid #0078d7;
                border-radius: 4px;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                          stop:0 #f8f8f8, stop:1 #e0e0e0);
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                          stop:0 #e0f0ff, stop:1 #c0dfff);
                border: 1px solid #0078d7;
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                          stop:0 #d0e0f0, stop:1 #b0d0f0);
                padding-top: 7px;
                padding-bottom: 5px;
            }
            QPushButton:disabled {
                color: #999999;
                border: 1px solid #cccccc;
                background: #f0f0f0;
            }
        """
        
        # Rotate buttons
        self.rotate_left_button = QPushButton("Rotate L")
        self.rotate_left_button.clicked.connect(self._handle_rotate_left)
        self.rotate_left_button.setToolTip("Rotate 90° counter-clockwise")
        self.rotate_left_button.setStyleSheet(btn_style)
        
        self.rotate_right_button = QPushButton("Rotate R")
        self.rotate_right_button.clicked.connect(self._handle_rotate_right)
        self.rotate_right_button.setToolTip("Rotate 90° clockwise")
        self.rotate_right_button.setStyleSheet(btn_style)
        
        # Flip buttons
        self.flip_horizontal_button = QPushButton("Flip H")
        self.flip_horizontal_button.clicked.connect(self._handle_flip_horizontal)
        self.flip_horizontal_button.setToolTip("Flip horizontally")
        self.flip_horizontal_button.setStyleSheet(btn_style)
        
        self.flip_vertical_button = QPushButton("Flip V")
        self.flip_vertical_button.clicked.connect(self._handle_flip_vertical)
        self.flip_vertical_button.setToolTip("Flip vertically")
        self.flip_vertical_button.setStyleSheet(btn_style)
        
        # Add buttons to layout in a 2x2 grid
        transform_layout.addWidget(self.rotate_left_button, 0, 0)
        transform_layout.addWidget(self.rotate_right_button, 0, 1)
        transform_layout.addWidget(self.flip_horizontal_button, 1, 0)
        transform_layout.addWidget(self.flip_vertical_button, 1, 1)
        
        transform_group.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        control_layout.addWidget(transform_group, 0, Qt.AlignTop)

        # Style for action buttons
        action_btn_style = """
            QPushButton {
                padding: 12px 24px;
                font-size: 14px;
                font-weight: bold;
                border: none;
                border-radius: 4px;
                background-color: #4CAF50;
                color: white;
                min-width: 180px;
                margin: 10px 0;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
                padding-top: 13px;
                padding-bottom: 11px;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """
        
        # Create action buttons group
        actions_group = QGroupBox("Actions")
        actions_group.setStyleSheet(group_style)
        actions_layout = QVBoxLayout(actions_group)
        actions_layout.setContentsMargins(8, 20, 8, 8)
        
        self.crop_button = QPushButton(QIcon.fromTheme("image-crop"), "Crop & Save")
        self.crop_button.setStyleSheet(action_btn_style)
        self.crop_button.clicked.connect(self.crop_and_save)
        actions_layout.addWidget(self.crop_button, 0, Qt.AlignCenter)
        
        # Add all groups to the scroll layout
        scroll_layout.addWidget(aspect_group)
        scroll_layout.addWidget(transform_group)
        scroll_layout.addWidget(output_group)
        scroll_layout.addWidget(actions_group)
        scroll_layout.addStretch(1)  # Pushes controls to the top
        
        # Set up main layout
        main_layout.addWidget(preview_group, 1)  # Preview takes remaining space
        main_layout.addWidget(control_group, 0)  # Controls take minimum space
        self.setLayout(main_layout)
        
        # Set initial states
        if self.aspect_buttons.buttons(): 
            self.aspect_buttons.buttons()[0].setChecked(True)  # Default to 'Free Form'
        
        if self.output_dir is None:
            self.output_dir = QStandardPaths.writableLocation(QStandardPaths.PicturesLocation)
        
        self.update_ui_state()

    def update_ui_state(self):
        """Update the UI state based on current settings."""
        has_images = len(self.thumbnail_items) > 0
        self.clear_button.setEnabled(has_images)
        
        current_item_selected = self.current_selected_thumbnail_item is not None
        has_valid_selection = has_images and current_item_selected and hasattr(self, 'crop_area') and self.crop_area.selection_rect().isValid()
        
        # Enable/disable controls based on selection
        self.crop_button.setEnabled(has_valid_selection and self.output_dir is not None)
        self.format_combo.setEnabled(has_valid_selection)
        self.quality_slider.setEnabled(has_valid_selection)
        self.filename_prefix_input.setEnabled(has_valid_selection)
        self.filename_suffix_input.setEnabled(has_valid_selection)
        self.overwrite_checkbox.setEnabled(has_valid_selection)
        self.output_dir_button.setEnabled(True)  # Always enabled
        
        # Update output directory display
        if hasattr(self, 'output_dir_label') and self.output_dir:
            # Show just the last part of the path if it's long
            display_path = self.output_dir
            if len(display_path) > 30:
                display_path = '...' + display_path[-27:]
            self.output_dir_label.setText(display_path)
            self.output_dir_label.setToolTip(self.output_dir)
        elif hasattr(self, 'output_dir_label'):
            self.output_dir_label.setText("Not Set")
            self.output_dir_label.setToolTip("")
            
        # Show warning if no valid selection
        if has_images and current_item_selected and not hasattr(self, 'crop_area'):
            self.crop_button.setToolTip("Draw a selection on the image")
        elif not has_valid_selection:
            self.crop_button.setToolTip("Select an image and draw a crop area")
        else:
            self.crop_button.setToolTip("Crop and save the selected area")

    def browse_images(self):
        """Open file dialog to select images."""
        file_dialog = QFileDialog()
        file_dialog.setFileMode(QFileDialog.ExistingFiles)
        file_dialog.setNameFilter("Images (*.png *.jpg *.jpeg *.bmp *.gif *.tif *.tiff *.webp)")
        
        if file_dialog.exec_():
            files = file_dialog.selectedFiles()
            if files:
                self.clear_images() # Clear existing thumbnails and state first
                self.image_paths = files # Store all paths
                for path in files:
                    self._add_thumbnail_to_gallery(path)
                
                if self.thumbnail_items: # If any thumbnails were successfully added
                    # Select and load the first image
                    self._on_cropper_thumbnail_clicked(self.thumbnail_items[0].image_path)
        self.update_ui_state()

    def _add_thumbnail_to_gallery(self, image_path):
        """Creates a thumbnail and adds it to the gallery."""
        try:
            item = CropperThumbnailItem(image_path, self.thumbnail_container)
            item.clicked.connect(self._on_cropper_thumbnail_clicked)
            self.thumbnail_items.append(item)
            
            # Insert before the stretch item to keep thumbnails left-aligned
            if hasattr(self, 'thumbnail_layout') and self.thumbnail_layout is not None:
                # Remove the stretch temporarily
                stretch = self.thumbnail_layout.takeAt(self.thumbnail_layout.count() - 1)
                # Add the new item
                self.thumbnail_layout.addWidget(item)
                # Add the stretch back
                self.thumbnail_layout.addItem(stretch)
            
            # Update the container's minimum size to fit all thumbnails
            self.thumbnail_container.adjustSize()
            
            # Ensure the container has a minimum width to show all thumbnails
            min_width = (CROPPER_THUMB_ITEM_WIDTH + 10) * len(self.thumbnail_items)
            self.thumbnail_container.setMinimumWidth(min_width)

        except Exception as e:
            print(f"Error creating thumbnail item for {image_path}: {e}")
            traceback.print_exc()
            # Add error placeholder
            try:
                error_label = QLabel(f"Error loading:\n{os.path.basename(image_path)}", self.thumbnail_container)
                error_label.setWordWrap(True)
                error_label.setStyleSheet("color: red; border: 1px solid red; padding: 5px;")
                error_label.setFixedSize(CROPPER_THUMB_ITEM_WIDTH, CROPPER_THUMB_ITEM_HEIGHT)
                
                # Insert before the stretch item
                if hasattr(self, 'thumbnail_layout') and self.thumbnail_layout is not None:
                    # Remove the stretch temporarily
                    stretch = self.thumbnail_layout.takeAt(self.thumbnail_layout.count() - 1)
                    # Add the error label
                    self.thumbnail_layout.addWidget(error_label)
                    # Add the stretch back
                    self.thumbnail_layout.addItem(stretch)
                    
            except Exception as inner_e:
                print(f"Error creating error label: {inner_e}")
                traceback.print_exc()

    def _on_cropper_thumbnail_clicked(self, image_path: str):
        """Handles thumbnail clicks from CropperThumbnailItem instances."""
        clicked_item = None
        for item in self.thumbnail_items:
            if item.image_path == image_path:
                clicked_item = item
                break
        
        if not clicked_item:
            print(f"_on_cropper_thumbnail_clicked: Could not find item for path {image_path}")
            return

        if self.current_selected_thumbnail_item:
            self.current_selected_thumbnail_item.set_selected(False)
        
        clicked_item.set_selected(True)
        self.current_selected_thumbnail_item = clicked_item
        self.load_image_into_cropper(image_path)
        self.update_ui_state()

    def load_image_into_cropper(self, image_path: str):
        """Loads the specified image path into the crop_area and stores its PIL version."""
        if not image_path or not os.path.exists(image_path):
            QMessageBox.critical(self, "Error", f"Image file not found: {image_path}")
            self.crop_area.clear_pixmap()
            self.current_pil_image = None
            return
            
        # Store the current image path
        self.current_image_path = image_path
            
        try:
            if hasattr(self, 'crop_area') and self.crop_area is not None:
                self.crop_area.clear_pixmap()
            
            # Load with PIL
            pil_image_loaded = Image.open(image_path)
            
            # Store the original PIL image (or a working copy) for cropping later
            # Ensure it's in a common format like RGB or RGBA before storing
            if pil_image_loaded.mode not in ('RGB', 'RGBA'):
                self.current_pil_image = pil_image_loaded.convert('RGBA') 
            else:
                self.current_pil_image = pil_image_loaded.copy() # Use a copy

            # For display in QPixmap, convert to RGBA then to QImage
            display_pil_image = self.current_pil_image
            if display_pil_image.mode != 'RGBA': # Should already be RGBA from above
                 display_pil_image = display_pil_image.convert('RGBA')
            
            data = display_pil_image.tobytes('raw', 'RGBA')
            qimage = QImage(data, display_pil_image.size[0], display_pil_image.size[1], QImage.Format_RGBA8888)
            pixmap = QPixmap.fromImage(qimage)

            if hasattr(self, 'crop_area') and self.crop_area is not None:
                self.crop_area.set_pixmap(pixmap)
            
        except Exception as e:
            QMessageBox.critical(self, "Error Loading Image", f"Could not load image: {image_path}\n{e}")
            self.crop_area.clear_pixmap()
            self.current_pil_image = None
        self.update_ui_state()

    def crop_and_save(self):
        """Crop and save the current image with the selected area."""
        try:
            if not hasattr(self, 'current_pil_image') or not self.current_pil_image or not hasattr(self, 'crop_area') or not self.crop_area.original_pixmap:
                QMessageBox.warning(self, "Cannot Crop", "No image loaded or selection area is not ready.")
                return

            # Get the selection rectangle in original image coordinates
            selection_rect = self.crop_area.selection_rect()
            if not selection_rect.isValid() or selection_rect.width() <= 0 or selection_rect.height() <= 0:
                QMessageBox.warning(self, "Cannot Crop", "Please select a valid area to crop.")
                return

            # Get the current image dimensions
            img_width = self.current_pil_image.width
            img_height = self.current_pil_image.height

            # Calculate crop box in PIL coordinates (left, upper, right, lower)
            left = max(0, selection_rect.left())
            upper = max(0, selection_rect.top())
            right = min(img_width, selection_rect.left() + selection_rect.width())
            lower = min(img_height, selection_rect.top() + selection_rect.height())

            # Ensure valid dimensions
            if left >= right or upper >= lower:
                QMessageBox.warning(self, "Cannot Crop", "Invalid crop dimensions. Please try again.")
                return

            # Perform the crop
            cropped_image = self.current_pil_image.crop((left, upper, right, lower))

            # Get output directory
            if not hasattr(self, 'output_dir') or not self.output_dir:
                self.choose_output_dir()
                if not hasattr(self, 'output_dir') or not self.output_dir:
                    return  # User cancelled directory selection

            # Generate output filename
            if hasattr(self, 'current_image_path') and self.current_image_path:
                base_name = os.path.splitext(os.path.basename(self.current_image_path))[0]
            else:
                base_name = "cropped_image"
                
            if hasattr(self, 'filename_prefix_input') and self.filename_prefix_input.text():
                base_name = f"{self.filename_prefix_input.text()}{base_name}"
            if hasattr(self, 'filename_suffix_input') and self.filename_suffix_input.text():
                base_name = f"{base_name}{self.filename_suffix_input.text()}"

            # Get selected format and quality
            file_format = 'jpeg'  # Default
            quality = 95  # Default quality
            
            if hasattr(self, 'format_combo'):
                file_format = self.format_combo.currentText().lower()
                if file_format == 'jpg':
                    file_format = 'jpeg'
            
            if hasattr(self, 'quality_slider'):
                quality = self.quality_slider.value()

            # Set file extension
            ext = file_format if file_format != 'jpeg' else 'jpg'
            output_path = os.path.join(self.output_dir, f"{base_name}_cropped.{ext}")

            # Handle file overwrite
            if os.path.exists(output_path):
                reply = QMessageBox.question(
                    self, 
                    'File Exists', 
                    f'File {os.path.basename(output_path)} already exists. Overwrite?',
                    QMessageBox.Yes | QMessageBox.No, 
                    QMessageBox.No
                )
                if reply == QMessageBox.No:
                    return

            # Save options
            save_kwargs = {}
            if file_format in ['jpeg', 'jpg', 'webp']:
                save_kwargs['quality'] = quality
            if file_format == 'png':
                save_kwargs['compress_level'] = 9 - (quality // 11)  # Map 0-100 to 9-0

            # Convert to RGB for JPEG if needed
            if file_format == 'jpeg' and cropped_image.mode in ('RGBA', 'LA'):
                background = Image.new('RGB', cropped_image.size, (255, 255, 255))
                background.paste(cropped_image, mask=cropped_image.split()[-1])
                cropped_image = background
            elif cropped_image.mode == 'P':
                cropped_image = cropped_image.convert('RGB')

            # Save the image
            cropped_image.save(output_path, format=file_format.upper(), **save_kwargs)
            
            # Show success message
            QMessageBox.information(self, "Success", f"Image successfully saved to:\n{output_path}")
            
            # Update the current PIL image to the cropped version
            self.current_pil_image = cropped_image
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save cropped image: {str(e)}")
            print(f"Error in crop_and_save: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def on_aspect_ratio_changed(self, checked):
        """Handle aspect ratio radio button toggled."""
        if not checked:
            return
            
        btn = self.sender()
        if btn.text() == "Free Form":
            # No fixed aspect ratio
            self.crop_area.set_aspect_ratio(0, 0)
        elif btn.text() == "Custom":
            # Use custom values
            width = self.custom_width.value()
            height = self.custom_height.value()
            self.crop_area.set_aspect_ratio(width, height)
        else:
            # Use preset values from the button's w and h attributes
            if hasattr(btn, 'w') and hasattr(btn, 'h'):
                self.crop_area.set_aspect_ratio(btn.w, btn.h)
    
    def update_custom_aspect_ratio(self):
        """Update aspect ratio when custom values change."""
        custom_btn = None
        for btn in self.aspect_buttons.buttons():
            if btn.text() == "Custom":
                custom_btn = btn
                break
                
        if custom_btn and custom_btn.isChecked():
            width = self.custom_width.value()
            height = self.custom_height.value()
            self.crop_area.set_aspect_ratio(width, height)
    
    def choose_output_dir(self):
        """Open dialog to choose output directory."""
        dir_path = QFileDialog.getExistingDirectory(
            self, 
            "Choose Output Directory", 
            self.output_dir or QStandardPaths.writableLocation(QStandardPaths.PicturesLocation)
        )
        if dir_path:
            self.output_dir = dir_path
            self.output_dir_label.setText(f"Output: {self.output_dir}")
            self.output_dir_label.setToolTip(dir_path)
            self.update_ui_state()

    def on_crop_changed(self, rect):
        """Handle crop area changed event."""
        self.update_ui_state()

    # --- Transformation Handlers ---
    def _handle_rotate_left(self):
        if hasattr(self, 'crop_area') and self.crop_area.original_pixmap:
            self.crop_area.rotate_image(-90) # Counter-clockwise
            self._update_pil_image_safely()

    def _handle_rotate_right(self):
        if hasattr(self, 'crop_area') and self.crop_area.original_pixmap:
            self.crop_area.rotate_image(90) # Clockwise
            self._update_pil_image_safely()

    def _handle_flip_horizontal(self):
        if hasattr(self, 'crop_area') and self.crop_area.original_pixmap:
            self.crop_area.flip_horizontal_image()
            self._update_pil_image_safely()

    def _handle_flip_vertical(self):
        if hasattr(self, 'crop_area') and self.crop_area.original_pixmap:
            self.crop_area.flip_vertical_image()
            self._update_pil_image_safely()
            
    def _update_pil_image_safely(self):
        """Safely update the PIL image from the current QPixmap."""
        if not hasattr(self, 'crop_area') or not self.crop_area.original_pixmap:
            self.current_pil_image = None
            return
            
        try:
            # Get the current image path if available
            current_path = getattr(self, 'current_image_path', None)
            if current_path and os.path.exists(current_path):
                # Reload from original file for better quality
                self.current_pil_image = Image.open(current_path)
                return
                
            # Fallback to QPixmap conversion if no file path is available
            qimage = self.crop_area.original_pixmap.toImage()
            if qimage.isNull():
                self.current_pil_image = None
                return
                
            # Convert to ARGB32 format for reliable processing
            qimage = qimage.convertToFormat(QImage.Format_ARGB32)
            
            # Get image data
            width = qimage.width()
            height = qimage.height()
            ptr = qimage.bits()
            
            # Ensure we have valid image data
            if not ptr or width <= 0 or height <= 0:
                self.current_pil_image = None
                return
                
            # Convert QImage to numpy array
            try:
                # For PyQt5
                ptr.setsize(qimage.byteCount())
            except AttributeError:
                # For PySide2 or other bindings
                ptr.setsize(height * qimage.bytesPerLine())
                
            arr = np.frombuffer(ptr, np.uint8).reshape((height, width, 4))  # RGBA
            
            # Create PIL image and ensure it's in RGB/RGBA mode
            pil_image = Image.fromarray(arr, 'RGBA')
            if pil_image.mode == 'RGBA' and not pil_image.getextrema()[3] == (255, 255):
                # If no alpha channel is used, convert to RGB
                pil_image = pil_image.convert('RGB')
            
            # Store the PIL image
            self.current_pil_image = pil_image
            
        except Exception as e:
            print(f"Error updating PIL image: {str(e)}")
            import traceback
            traceback.print_exc()
            self.current_pil_image = None
    
    def _update_pil_image_from_crop_area(self):
        """Legacy method that now just calls the safe update method."""
        self._update_pil_image_safely()
        
    def clear_images(self):
        """Clear all thumbnails and reset the crop area."""
        # Clear the current selection
        self.current_selected_thumbnail_item = None
        
        # Clear the crop area
        if hasattr(self, 'crop_area') and self.crop_area is not None:
            self.crop_area.clear_pixmap()
        
        # Clear the PIL image reference
        self.current_pil_image = None
        
        # Clear the thumbnail items
        for item in self.thumbnail_items:
            item.setParent(None)
            item.deleteLater()
        self.thumbnail_items.clear()
        
        # Reset the image paths
        self.image_paths = []
        
        # Reset the container's minimum width
        if hasattr(self, 'thumbnail_container'):
            self.thumbnail_container.setMinimumWidth(0)
        
        # Update the UI state
        self.update_ui_state()
