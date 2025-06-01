"""
WebP Converter Tool for the Image Master application.

This module provides the WebPConverterTool class which allows users to convert
images to and from WebP format with various options.
"""
import os
import sys
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple

from PIL import Image, ImageFile
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QSize, QTimer, QBuffer, pyqtSlot
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFileDialog, QSpinBox, QComboBox, QCheckBox, QProgressBar,
    QMessageBox, QGroupBox, QSizePolicy, QScrollArea, QSlider,
    QGridLayout, QRadioButton, QButtonGroup, QLayoutItem, QApplication,
    QStackedWidget
)

# Import base tool and utility components
from utils.base_tool import BaseTool
from utils.ui_components import (
    ThumbnailLabel, FileControls, ImagePreviewGallery, OutputDirSelector
)
from utils.image_utils import load_image, save_image, get_image_info
from utils.file_utils import get_file_size, create_directory

class WebPConverterTool(BaseTool):
    """Tool for converting images to and from WebP format."""
    
    def __init__(self, parent=None):
        """Initialize the WebP converter with default settings."""
        # Initialize instance variables first
        self.to_webp_radio = None
        self.from_webp_radio = None
        self.quality_slider = None
        self.lossless_check = None
        self.metadata_check = None
        self.convert_btn = None
        self.output_dir = str(Path.home() / "Pictures" / "WebP_Converted")
        
        # Initialize parent class which will call setup_ui and setup_tool_controls
        super().__init__("WebP Converter")
        
        # Setup output directory
        success, message = create_directory(self.output_dir)
        if not success:
            # If default directory creation fails, use system temp directory
            import tempfile
            self.output_dir = str(Path(tempfile.gettempdir()) / "imageconverter" / "webp_converted")
            success, message = create_directory(self.output_dir)
            if not success:
                print(f"Warning: Could not create output directory: {message}")
                self.output_dir = str(Path.home() / "Pictures")
        
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
        
        # Skip the format selection from base class
        
        # Add tool-specific controls
        self.setup_tool_controls(control_layout)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        control_layout.addWidget(self.progress_bar)
        
        control_group.setLayout(control_layout)
        self.main_layout.addWidget(control_group, stretch=1)
    
    def setup_ui(self):
        """Set up the user interface with responsive layout."""
        # Set window properties first
        self.setWindowTitle("WebP Converter")
        self.setMinimumSize(1000, 700)  # Slightly larger minimum size
        
        # Set initial size (70% of screen size)
        screen = QApplication.primaryScreen().availableGeometry()
        self.resize(int(screen.width() * 0.8), int(screen.height() * 0.8))
        
        # Set size policies for better resizing
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        # Call parent's setup_ui after setting our properties
        super().setup_ui()
        
    def setup_tool_controls(self, control_layout):
        """Set up tool-specific controls.
        
        Args:
            control_layout: The layout to add controls to
        """
        # Create a main layout for the control panel
        main_control_layout = QVBoxLayout()
        main_control_layout.setContentsMargins(0, 0, 0, 0)
        main_control_layout.setSpacing(10)
        
        # Create a scroll area for the controls
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        # Create a container widget for the scroll area
        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(10)
        container_layout.setAlignment(Qt.AlignTop)
        
        # Conversion direction
        direction_group = QGroupBox("Conversion Direction")
        direction_group.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        direction_layout = QHBoxLayout(direction_group)
        direction_layout.setContentsMargins(10, 8, 10, 8)  # Reduced top and bottom padding
        direction_layout.setSpacing(15)
        
        # Initialize radio buttons with consistent sizing
        self.to_webp_radio = QRadioButton("To WebP")
        self.from_webp_radio = QRadioButton("From WebP")
        self.to_webp_radio.setChecked(True)
        
        # Style radio buttons
        radio_style = """
            QRadioButton {
                padding: 6px;
                font-size: 12px;
            }
            QRadioButton::indicator {
                width: 16px;
                height: 16px;
            }
        """
        self.to_webp_radio.setStyleSheet(radio_style)
        self.from_webp_radio.setStyleSheet(radio_style)
        
        # Add radio buttons to layout with spacing
        direction_layout.addWidget(self.to_webp_radio, 1)
        direction_layout.addWidget(self.from_webp_radio, 1)
        direction_layout.addStretch()  # Push buttons to the left
        
        container_layout.addWidget(direction_group)
        container_layout.addSpacing(5)  # Add some space after the group
        
        # Output format (only shown when converting from WebP)
        self.format_group = QGroupBox("Output Format")
        self.format_group.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.format_layout = QVBoxLayout(self.format_group)
        self.format_layout.setContentsMargins(10, 15, 10, 10)
        
        # Create a new format combo (not using the one from base class)
        self.format_combo = QComboBox()
        self.format_combo.addItems(['PNG', 'JPEG', 'BMP', 'TIFF'])
        self.format_combo.setStyleSheet("""
            QComboBox {
                padding: 5px;
                border: 1px solid #ccc;
                border-radius: 3px;
                min-width: 120px;
            }
            QComboBox::drop-down {
                border: 0px;
            }
        """)
        self.format_layout.addWidget(self.format_combo)
        
        # Add format group to layout (initially hidden, will be shown by update_ui_state)
        container_layout.addWidget(self.format_group)
        container_layout.addSpacing(5)  # Add some space after the group
        
        # Initially hide the format group (it will be shown by update_ui_state if needed)
        self.format_group.hide()
        
        # Quality settings
        quality_group = QGroupBox("Quality Settings")
        quality_group.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        quality_layout = QVBoxLayout(quality_group)
        quality_layout.setContentsMargins(10, 15, 10, 10)
        quality_layout.setSpacing(12)
        
        # Quality slider with better layout
        quality_slider_layout = QHBoxLayout()
        quality_slider_layout.setSpacing(8)
        
        quality_label = QLabel("Quality:")
        quality_label.setFixedWidth(60)  # Fixed width for alignment
        quality_slider_layout.addWidget(quality_label)
        
        self.quality_slider = QSlider(Qt.Horizontal)
        self.quality_slider.setRange(1, 100)
        self.quality_slider.setValue(80)
        self.quality_slider.setTickPosition(QSlider.TicksBelow)
        self.quality_slider.setTickInterval(10)
        self.quality_slider.setPageStep(10)
        self.quality_slider.setStyleSheet("""
            QSlider::handle:horizontal {
                width: 16px;
                margin: -6px 0;
                border-radius: 8px;
                background: #4a90e2;
            }
        """)
        quality_slider_layout.addWidget(self.quality_slider, 1)  # Allow to expand
        
        self.quality_value = QLabel("80%")
        self.quality_value.setFixedWidth(40)
        self.quality_value.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        quality_slider_layout.addWidget(self.quality_value)
        
        quality_layout.addLayout(quality_slider_layout)
        
        # Checkboxes with consistent spacing
        checkbox_style = """
            QCheckBox {
                spacing: 6px;
                padding: 4px 0;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
            }
        """
        
        # Lossless compression (only for WebP)
        self.lossless_check = QCheckBox("Lossless Compression")
        self.lossless_check.setStyleSheet(checkbox_style)
        quality_layout.addWidget(self.lossless_check)
        
        # Preserve metadata
        self.metadata_check = QCheckBox("Preserve Metadata")
        self.metadata_check.setChecked(True)
        self.metadata_check.setStyleSheet(checkbox_style)
        quality_layout.addWidget(self.metadata_check)
        
        container_layout.addWidget(quality_group)
        container_layout.addSpacing(10)  # Add some space after the group
        
        # Convert button with consistent styling and spacing
        self.convert_btn = QPushButton("Convert to WebP")
        self.convert_btn.setMinimumHeight(42)
        self.convert_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
                min-width: 160px;
                margin: 10px 0;  /* Add some vertical margin */
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        self.convert_btn.clicked.connect(self.start_conversion)
        container_layout.addWidget(self.convert_btn, 0, Qt.AlignCenter)
        
        # Output directory selector
        self.output_dir_selector = OutputDirSelector()
        self.output_dir_selector.directory_changed.connect(self._on_output_dir_changed)
        container_layout.addWidget(self.output_dir_selector)
        
        # Add stretch to push everything to the top
        container_layout.addStretch()
        
        # Set the container as the scroll area's widget
        scroll.setWidget(container)
        
        # Add the scroll area to the main layout with stretch
        main_control_layout.addWidget(scroll, 1)  # Use stretch factor 1 to allow expansion
        
        # Add the main layout to the control layout
        control_layout.addLayout(main_control_layout, 1)
        
        # Connect signals (only once)
        self.to_webp_radio.toggled.connect(self.update_ui_state)
        self.from_webp_radio.toggled.connect(self.update_ui_state)
        
        # Set initial UI state (this will handle the format group visibility)
        self.update_ui_state(force=True)  # Force initial update
    
    def update_ui_state(self, *args, force=False):
        """Update UI state based on conversion direction.
        
        Args:
            *args: Ignored arguments from signal connections
            force: If True, force update even if the state appears unchanged
        """
        try:
            # Safely get conversion direction
            to_webp = True  # Default to True if radio buttons not available
            if hasattr(self, 'to_webp_radio') and self.to_webp_radio is not None:
                to_webp = self.to_webp_radio.isChecked()
            
            # Skip if no change and not forced
            if hasattr(self, '_last_to_webp') and self._last_to_webp == to_webp and not force:
                return
                
            # Update the last known state
            self._last_to_webp = to_webp
            
            # Show/hide format group based on conversion direction
            if hasattr(self, 'format_group'):
                self.format_group.setVisible(not to_webp)
            
            # Update quality slider if it exists
            if hasattr(self, 'quality_slider') and self.quality_slider is not None:
                self.quality_slider.setEnabled(True)
                
            # Update lossless checkbox (only for WebP output)
            if hasattr(self, 'lossless_check') and self.lossless_check is not None:
                self.lossless_check.setEnabled(to_webp)
                
            # Update convert button text and tooltip if it exists
            if hasattr(self, 'convert_btn') and self.convert_btn is not None:
                try:
                    if to_webp:
                        # When converting TO WebP
                        self.convert_btn.setText("Convert to WebP")
                        self.convert_btn.setToolTip("Convert selected images to WebP format")
                    else:
                        # When converting FROM WebP
                        format_text = 'PNG'  # Default format
                        if hasattr(self, 'format_combo') and self.format_combo is not None:
                            format_text = self.format_combo.currentText().upper()
                        
                        # Update button text and tooltip
                        self.convert_btn.setText(f"Convert to {format_text}")
                        self.convert_btn.setToolTip(
                            f"Convert selected WebP images to {format_text} format"
                        )
                    
                    # Force update the button state
                    self.convert_btn.update()
                    
                except Exception as e:
                    print(f"Error updating convert button: {str(e)}")
                    
            # Force update the UI
            self.update()
                    
        except Exception as e:
            print(f"Error in update_ui_state: {str(e)}")
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
                        "Permission Denied",
                        f"You don't have write permissions for: {directory}"
                    )
        except Exception as e:
            error_msg = f"Error setting output directory: {str(e)}"
            print(error_msg)
            QMessageBox.critical(self, "Error", error_msg)
    
    def browse_images(self):
        """Open a file dialog to select images.
        
        Shows only WebP files when in 'From WebP' mode, and all supported
        image formats when in 'To WebP' mode.
        """
        file_dialog = QFileDialog()
        file_dialog.setFileMode(QFileDialog.ExistingFiles)
        
        # Set file filters based on conversion direction
        if hasattr(self, 'from_webp_radio') and self.from_webp_radio.isChecked():
            # In 'From WebP' mode, only show WebP files
            file_dialog.setNameFilter("WebP Images (*.webp);;All Files (*)")
        else:
            # In 'To WebP' mode, show all supported image formats
            file_dialog.setNameFilter("Images (*.png *.jpg *.jpeg *.bmp);;All Files (*)")
        
        if file_dialog.exec_():
            file_paths = file_dialog.selectedFiles()
            if file_paths:
                self.add_image_paths(file_paths)
                if hasattr(self, 'convert_btn'):
                    self.convert_btn.setEnabled(True)
                self.update_ui_state()
    
    def start_conversion(self):
        """Start the image conversion process."""
        try:
            # Check if UI elements are properly initialized
            if not hasattr(self, 'to_webp_radio') or self.to_webp_radio is None:
                QMessageBox.critical(self, "Error", "UI not properly initialized. Please restart the application.")
                return
                
            # Check if there are any files to convert
            if not hasattr(self, 'input_files') or not self.input_files:
                QMessageBox.warning(self, "No Files", "Please add files to convert first.")
                return
                
            # Check if output directory is set and writable
            if not hasattr(self, 'output_dir') or not os.path.isdir(self.output_dir):
                QMessageBox.warning(self, "Invalid Directory", "Please select a valid output directory.")
                return
                
            # Disable UI during conversion
            self.set_ui_enabled(False)
            
            # Get conversion settings with proper error checking
            to_webp = True  # Default to True if radio buttons not available
            if hasattr(self, 'to_webp_radio') and self.to_webp_radio is not None:
                to_webp = self.to_webp_radio.isChecked()
                
            quality = 90  # Default quality
            if hasattr(self, 'quality_slider') and self.quality_slider is not None:
                quality = self.quality_slider.value()
                
            lossless = False
            if hasattr(self, 'lossless_check') and self.lossless_check is not None:
                lossless = self.lossless_check.isChecked()
                
            preserve_metadata = True
            if hasattr(self, 'metadata_check') and self.metadata_check is not None:
                preserve_metadata = self.metadata_check.isChecked()
                
            output_format = 'png'  # Default format
            if hasattr(self, 'format_combo') and self.format_combo is not None:
                output_format = self.format_combo.currentText().lower()
            
            # Create the worker
            self.worker = WebPConversionWorker(
                input_files=self.input_files,
                output_dir=self.output_dir,
                to_webp=to_webp,
                quality=quality,
                output_format=output_format,
                lossless=lossless,
                preserve_metadata=preserve_metadata
            )
            
            # Connect worker signals
            self.worker.progress_updated.connect(self.update_progress)
            self.worker.finished.connect(self.conversion_finished)
            self.worker.error_occurred.connect(self.show_error)
            
            # Start the worker
            self.worker.start()
            
        except Exception as e:
            self.show_error(f"Error starting conversion: {str(e)}")
            self.set_ui_enabled(True)
    
    def thumbnail_clicked(self, path):
        """Handle thumbnail click event."""
        self.current_path = path
        self.update_preview()

    def update_main_preview(self):
        """Update the main preview with the current image."""
        super().update_main_preview()
        
        if self.current_path and os.path.exists(self.current_path):
            try:
                with Image.open(self.current_path) as img:
                    width, height = img.size
                    file_size = os.path.getsize(self.current_path) / 1024  # KB
                    img_format = img.format or 'Unknown'
                    
                    # Update file info in the base class's status label
                    if hasattr(self, 'size_info'):
                        self.size_info.setText(
                            f"{os.path.basename(self.current_path)} • "
                            f"{width} × {height} • {file_size:.1f} KB • {img_format.upper()}"
                        )
            except Exception as e:
                if hasattr(self, 'size_info'):
                    self.size_info.setText(f"Error loading image info: {str(e)}")
    
    def clear_files(self):
        """Clear all selected files and reset the UI."""
        super().clear_files()
        if hasattr(self, 'convert_btn'):
            self.convert_btn.setEnabled(False)
        self.update_ui_state()
    
    def start_conversion(self):
        """Start the conversion process."""
        if not hasattr(self, 'image_paths') or not self.image_paths:
            QMessageBox.warning(self, "No Files", "Please select at least one file to convert.")
            return
            
        # Get conversion settings
        to_webp = self.to_webp_radio.isChecked()
        quality = self.quality_slider.value()
        lossless = self.lossless_check.isChecked()
        preserve_metadata = self.metadata_check.isChecked()
        output_format = self.format_combo.currentText().lower() if not to_webp else 'webp'
        
        # Create output directory if it doesn't exist
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Create and start worker thread
        self.worker = WebPConversionWorker(
            input_files=self.image_paths,
            output_dir=self.output_dir,
            to_webp=to_webp,
            quality=quality,
            output_format=output_format,
            preserve_metadata=preserve_metadata,
            lossless=lossless
        )
        
        # Connect signals
        self.worker.progress_updated.connect(self.update_progress)
        self.worker.finished.connect(self.conversion_finished)
        self.worker.error_occurred.connect(self.show_error)
        
        # Disable UI during conversion
        self.set_ui_enabled(False)
        
        # Show progress bar
        if hasattr(self, 'progress_bar'):
            self.progress_bar.setValue(0)
            self.progress_bar.setVisible(True)
        
        # Start conversion
        self.worker.start()
    
    def set_ui_enabled(self, enabled):
        """Enable or disable UI elements during conversion."""
        # Enable/disable file controls and radio buttons based on enabled state
        self.file_controls.setEnabled(enabled)
        self.to_webp_radio.setEnabled(enabled)
        self.from_webp_radio.setEnabled(enabled)
        
        # Enable/disable format combo based on conversion direction and enabled state
        if hasattr(self, 'format_combo'):
            self.format_combo.setEnabled(enabled and not self.to_webp_radio.isChecked())
        
        # Enable/disable other controls based on enabled state
        self.quality_slider.setEnabled(enabled)
        self.lossless_check.setEnabled(enabled and self.to_webp_radio.isChecked())
        self.metadata_check.setEnabled(enabled)
        
        # Enable/disable convert button based on enabled state and whether there are files to convert
        has_files = hasattr(self, 'image_paths') and bool(self.image_paths)
        if hasattr(self, 'convert_btn'):
            self.convert_btn.setEnabled(enabled and has_files)
    
    def update_progress(self, value):
        """Update progress bar value."""
        self.progress_bar.setValue(value)
    
    def conversion_finished(self):
        """Handle completion of conversion process."""
        self.set_ui_enabled(True)
        
        # Count the number of files in the output directory
        try:
            output_files = []
            for ext in ['.webp', '.png', '.jpg', '.jpeg', '.bmp', '.tiff']:
                output_files.extend(list(Path(self.output_dir).glob(f'*{ext}')))
            
            # Filter to only include files modified in the last minute to avoid counting old files
            import time
            now = time.time()
            recent_files = [f for f in output_files if (now - f.stat().st_mtime) < 60]
            
            # Show the number of recently created files as the processed count
            processed_count = len(recent_files)
            QMessageBox.information(
                self,
                "Conversion Complete",
                f"Successfully converted {processed_count} images.\n"
                f"Output directory: {self.output_dir}"
            )
        except Exception as e:
            # Fallback to input files count if there's an error
            QMessageBox.information(
                self,
                "Conversion Complete",
                f"Successfully processed {len(self.input_files)} images.\n"
                f"Output directory: {self.output_dir}"
            )
    
    def show_error(self, error_message):
        """Show error message to the user."""
        try:
            # Log the error
            print(f"Error: {error_message}")
            
            # Show error message
            msg = QMessageBox(
                QMessageBox.Critical,
                "Conversion Error",
                str(error_message),
                parent=self
            )
            
            # Add copy to clipboard button
            copy_btn = msg.addButton("Copy Error", QMessageBox.ActionRole)
            msg.addButton(QMessageBox.Ok)
            
            # Show the message box
            msg.exec_()
            
            # Handle copy button click
            if msg.clickedButton() == copy_btn:
                clipboard = QApplication.clipboard()
                clipboard.setText(str(error_message))
                
        except Exception as e:
            print(f"Error showing error message: {e}")
            QMessageBox.critical(self, "Error", str(error_message))


class WebPConversionWorker(QThread):
    """Worker thread for WebP conversion tasks."""
    progress_updated = pyqtSignal(int)
    finished = pyqtSignal()
    error_occurred = pyqtSignal(str)
    
    def __init__(self, input_files, output_dir, to_webp, quality, output_format, 
                 preserve_metadata=True, lossless=False):
        super().__init__()
        self.input_files = input_files
        self.output_dir = output_dir
        self.to_webp = to_webp
        self.quality = quality
        self.output_format = output_format
        self.preserve_metadata = preserve_metadata
        self.lossless = lossless
        self.is_running = True
    
    def run(self):
        """Main worker method."""
        try:
            total_files = len(self.input_files)
            for i, input_file in enumerate(self.input_files):
                if not self.is_running:
                    break
                    
                try:
                    if self.to_webp:
                        self.convert_to_webp(input_file, i)
                    else:
                        self.convert_from_webp(input_file, i)
                    
                    # Update progress
                    progress = int((i + 1) / total_files * 100)
                    self.progress_updated.emit(progress)
                    
                except Exception as e:
                    error_msg = f"Error processing {os.path.basename(input_file)}: {str(e)}"
                    self.error_occurred.emit(error_msg)
            
            self.finished.emit()
            
        except Exception as e:
            self.error_occurred.emit(f"Conversion error: {str(e)}")
            self.finished.emit()
    
    def convert_to_webp(self, input_path, index):
        """Convert an image to WebP format."""
        try:
            # Open the image
            with Image.open(input_path) as img:
                # Convert to RGB if needed
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Create output filename
                filename = os.path.splitext(os.path.basename(input_path))[0] + '.webp'
                output_path = os.path.join(self.output_dir, filename)
                
                # Save as WebP
                img.save(
                    output_path,
                    'WEBP',
                    quality=self.quality,
                    lossless=self.lossless,
                    method=6  # Best quality encoding
                )
                
        except Exception as e:
            raise Exception(f"Failed to convert {os.path.basename(input_path)} to WebP: {str(e)}")
    
    def convert_from_webp(self, input_path, index):
        """Convert a WebP image to another format."""
        try:
            # Open the WebP image
            with Image.open(input_path) as img:
                # Create output filename
                filename = os.path.splitext(os.path.basename(input_path))[0] + f'.{self.output_format.lower()}'
                output_path = os.path.join(self.output_dir, filename)
                
                # Save in the target format
                img.save(output_path, self.output_format.upper(), quality=self.quality)
                
        except Exception as e:
            raise Exception(f"Failed to convert {os.path.basename(input_path)} from WebP: {str(e)}")
    
    def stop(self):
        """Stop the conversion process."""
        self.is_running = False


def update_thumbnail_layout(self):
    # Clear existing thumbnails
    for i in reversed(range(self.thumbnail_layout.count())): 
        widget = self.thumbnail_layout.itemAt(i).widget()
        if widget:
            widget.setParent(None)
    
    # Add thumbnails for all input files
    for i, path in enumerate(self.input_files):
        try:
            thumb_container = QWidget()
            thumb_layout = QVBoxLayout(thumb_container)
            
            # Create thumbnail label
            thumb_label = ThumbnailLabel()
            thumb_label.setProperty("path", path)
            thumb_label.setAlignment(Qt.AlignCenter)
            
            # Load and set thumbnail
            pixmap = QPixmap(path)
            if not pixmap.isNull():
                # Scale the pixmap to fit the thumbnail while maintaining aspect ratio
                scaled_pixmap = pixmap.scaled(
                    150, 150,
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
                )
                thumb_label.setPixmap(scaled_pixmap)
            
            # Add file name label
            file_name = os.path.basename(path)
            name_label = QLabel(file_name)
            name_label.setAlignment(Qt.AlignCenter)
            name_label.setWordWrap(True)
            
            # Add to layout
            thumb_layout.addWidget(thumb_label)
            thumb_layout.addWidget(name_label)
            
            # Connect click event
            thumb_label.clicked.connect(lambda checked, p=path: self.thumbnail_clicked(p))
            
            # Add to grid (3 columns)
            row = i // 3
            col = i % 3
            self.thumbnail_layout.addWidget(thumb_container, row, col)
            
        except Exception as e:
            print(f"Error creating thumbnail for {path}: {str(e)}")
    
    # Update the UI state
    self.update_ui_state()

    # Disable UI during conversion
    self.set_ui_enabled(False)
    if hasattr(self, 'progress'):
        self.progress.setVisible(True)
        self.progress.setMaximum(len(self.input_files))
        self.progress.setValue(0)

    # Start conversion in a separate thread
    self.worker = WebPConversionWorker(
        self.input_files,
        self.output_dir,
        self.to_webp_radio.isChecked() if hasattr(self, 'to_webp_radio') and self.to_webp_radio else True,
        self.quality_slider.value() if hasattr(self, 'quality_slider') else 90,
        self.format_combo.currentText().lower() if hasattr(self, 'format_combo') else 'png',
        self.metadata_check.isChecked() if hasattr(self, 'metadata_check') and self.metadata_check else True,
        self.lossless_check.isChecked() if hasattr(self, 'lossless_check') and self.lossless_check else False
    )
    self.worker.progress_updated.connect(self.update_progress)
    self.worker.finished.connect(self.conversion_finished)
    self.worker.error_occurred.connect(self.show_error)
    self.worker.start()

def update_progress(self, current, total):
    """Update progress bar with current progress."""
    try:
        if hasattr(self, 'progress_bar'):
            self.progress_bar.setMaximum(max(1, total))  # Avoid division by zero
            self.progress_bar.setValue(current)
            
            # Update progress text if available
            if hasattr(self, 'progress_label'):
                percent = int((current / total) * 100) if total > 0 else 0
                self.progress_label.setText(f"Processing: {current} of {total} ({percent}%)")
                
    except Exception as e:
        print(f"Error updating progress: {e}")

def conversion_finished(self):
    """Handle completion of conversion process."""
    self.set_ui_enabled(True)
    if hasattr(self, 'progress'):
        self.progress.setVisible(False)
    QMessageBox.information(self, "Success", "Image conversion completed successfully!")

def show_error(self, error_msg):
    """Show error message to the user."""
    self.set_ui_enabled(True)
    if hasattr(self, 'progress'):
        self.progress.setVisible(False)
        QMessageBox.critical(self, "Error", error_msg)



