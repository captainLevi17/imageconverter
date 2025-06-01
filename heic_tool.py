import os
import tempfile
from pathlib import Path
from typing import List, Optional, Any
from PyQt5.QtWidgets import (QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFileDialog, QProgressBar, QGroupBox, QMessageBox, QCheckBox,
    QSizePolicy, QComboBox)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PIL import Image
from utils.base_tool import BaseTool
from utils.ui_components import OutputDirSelector, FileControls
from utils.image_utils import ImageData, load_image
from utils.file_utils import create_directory

try:
    import pillow_heif
    HEIC_SUPPORT = True
except ImportError:
    print("Warning: pillow-heif not found. HEIC support will be disabled.")
    HEIC_SUPPORT = False

class HEICConverterTool(BaseTool):
    def __init__(self):
        self.output_dir = str(Path.home() / "Pictures" / "HEIC_Converted")
        self.worker_thread = None
        self.conversion_in_progress = False
        self.heic_supported = HEIC_SUPPORT
        
        if self.heic_supported:
            try:
                pillow_heif.register_heif_opener()
            except Exception as e:
                print(f"Error initializing HEIC support: {e}")
                self.heic_supported = False
        
        super().__init__("HEIC Converter")
        
        # Try to create output directory, fallback to temp if needed
        if not create_directory(self.output_dir)[0]:
            self.output_dir = str(Path(tempfile.gettempdir()) / "imageconverter" / "heic_converted")
            if not create_directory(self.output_dir)[0]:
                self.output_dir = str(Path.home() / "Pictures")
    
    def setup_control_panel(self) -> None:
        """Set up the control panel with tool-specific controls."""
        control_group = QGroupBox("Controls")
        control_group.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        control_layout = QVBoxLayout()
        
        self.file_controls = FileControls()
        self.file_controls.browse_clicked.connect(self.browse_images)
        self.file_controls.clear_clicked.connect(self.clear_images)
        control_layout.addWidget(self.file_controls)
        
        self.setup_tool_controls(control_layout)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        control_layout.addWidget(self.progress_bar)
        
        control_group.setLayout(control_layout)
        self.main_layout.addWidget(control_group, stretch=1)
    
    def setup_tool_controls(self, control_layout):
        """Set up tool-specific controls."""
        self.output_selector = OutputDirSelector()
        self.output_selector.directory_changed.connect(self.set_output_directory)
        control_layout.addWidget(self.output_selector)
        
        settings_group = QGroupBox("Conversion Settings")
        settings_layout = QVBoxLayout()
        
        # Format selection
        format_layout = QHBoxLayout()
        format_layout.addWidget(QLabel("Output Format:"))
        self.format_combo = QComboBox()
        self.format_combo.addItems(["JPEG", "PNG"])
        self.format_combo.currentTextChanged.connect(self.update_convert_button_text)
        format_layout.addWidget(self.format_combo)
        
        # Quality settings
        quality_layout = QHBoxLayout()
        quality_layout.addWidget(QLabel("Quality (1-100):"))
        self.quality_spin = QComboBox()
        self.quality_spin.addItems(["Maximum (100)", "High (90)", "Good (80)", "Medium (70)", "Low (60)"])
        self.quality_spin.setCurrentIndex(1)  # Default to High (90)
        quality_layout.addWidget(self.quality_spin)
        
        self.preserve_metadata = QCheckBox("Preserve metadata")
        self.preserve_metadata.setChecked(True)
        
        settings_layout.addLayout(format_layout)
        settings_layout.addLayout(quality_layout)
        settings_layout.addWidget(self.preserve_metadata)
        settings_group.setLayout(settings_layout)
        
        self.convert_btn = QPushButton()
        self.update_convert_button_text()
        self.convert_btn.setStyleSheet("""
            QPushButton {background-color: #4CAF50; color: white; border: none; padding: 8px 16px;
            border-radius: 4px; font-weight: bold; min-width: 160px; margin: 10px 0;}
            QPushButton:hover {background-color: #45a049;}
            QPushButton:disabled {background-color: #cccccc; color: #666666;}
        """)
        self.convert_btn.clicked.connect(self.convert_images)
        self.convert_btn.setEnabled(False)
        
        control_layout.addWidget(settings_group)
        control_layout.addWidget(self.convert_btn)
        control_layout.addStretch()
    
    def browse_images(self):
        """Handle image selection with HEIC/HEIF file filter."""
        if not self.heic_supported:
            QMessageBox.warning(self, 'HEIC Not Supported', 
                'HEIC support is not available. Please install pillow-heif package.')
            return
            
        # Set file filter to only show HEIC/HEIF files by default
        paths, _ = QFileDialog.getOpenFileNames(
            self, 'Select HEIC Images', '', 
            'HEIC/HEIF Images (*.heic *.heif);;All Files (*)')
            
        if paths:
            self.image_paths = paths
            self.file_controls.update_file_count(len(self.image_paths))
            self.convert_btn.setEnabled(True)
            
            # Update preview with first image
            if self.image_paths:
                self.current_path = self.image_paths[0]
                self.update_thumbnails()
                self.update_main_preview()
    
    def clear_images(self):
        """Clear all selected images and reset tool state."""
        super().clear_images()
        self.image_paths = []
        self.file_controls.update_file_count(0)
        self.convert_btn.setEnabled(False)
        
        # Clear the thumbnail gallery if it exists
        if hasattr(self, 'thumbnail_gallery'):
            self.thumbnail_gallery.clear()
            
        # Clear the preview if it exists
        if hasattr(self, 'preview_label'):
            self.preview_label.clear()
    
    def update_thumbnails(self):
        """Update the thumbnail gallery with current images."""
        if not hasattr(self, 'thumbnail_gallery') or not hasattr(self, 'image_paths') or not self.image_paths:
            return
            
        # Clear existing thumbnails
        self.thumbnail_gallery.clear()
        
        # Add thumbnails for all images
        for path in self.image_paths:
            self.thumbnail_gallery.add_thumbnail(path)
                
    def set_output_directory(self, path: Optional[str] = None) -> None:
        """Set the output directory and update the UI."""
        if path is None:
            path = QFileDialog.getExistingDirectory(self, 'Select Output Directory')
            
        if path:  # User didn't cancel
            self.output_dir = path
            self.output_selector.directory = path
    
    def load_image_data(self, path: str):
        """Load image data from the given path.
        
        Args:
            path: Path to the image file
            
        Returns:
            ImageData object with image information or None if loading fails
        """
        try:
            # Use the image_utils.load_image function which handles HEIC via pillow_heif
            return load_image(path, as_image_data=True)
        except Exception as e:
            print(f"Error loading image {path}: {str(e)}")
            return None
            
    def _create_temp_preview(self, img, suffix: str = '.jpg') -> str:
        """Create a temporary preview file for the given image."""
        fd, temp_path = tempfile.mkstemp(suffix=suffix)
        os.close(fd)
        try:
            img.convert('RGB').save(temp_path, 'JPEG', quality=90)
            return temp_path
        except Exception:
            os.path.exists(temp_path) and os.unlink(temp_path)
            raise
    
    def update_main_preview(self):
        """Update the main preview with the current image."""
        if not hasattr(self, 'current_path') or not self.current_path:
            return
            
        try:
            self.current_preview = self.load_image_data(self.current_path)
            if not self.current_preview:
                raise ValueError("Failed to load image data")
            
            if not str(self.current_path).lower().endswith(('.heic', '.heif')):
                return super().update_main_preview()
                
            temp_path = None
            try:
                temp_path = self._create_temp_preview(self.current_preview.image)
                if temp_path:
                    original_path = self.current_path
                    self.current_path = temp_path
                    super().update_main_preview()
                    self.current_path = original_path
                    from PyQt5.QtCore import QTimer
                    QTimer.singleShot(1000, lambda p=temp_path: os.path.exists(p) and os.unlink(p))
            except Exception as e:
                if temp_path and os.path.exists(temp_path):
                    os.unlink(temp_path)
                raise
                
        except Exception as e:
            error_msg = f"Error updating preview: {str(e)}"
            print(error_msg)
            if hasattr(self, 'main_preview'):
                self.main_preview.setText("Error loading preview")
            if hasattr(self, 'statusBar'):
                self.statusBar().showMessage(error_msg, 5000)
    
    def convert_images(self) -> None:
        """Convert all selected images to the target format."""
        if not hasattr(self, 'image_paths') or not self.image_paths:
            QMessageBox.warning(self, 'No Images', 'Please select at least one image to convert.')
            return
            
        if not hasattr(self, 'output_dir') or not self.output_dir:
            QMessageBox.warning(self, 'No Output Directory', 'Please select an output directory.')
            return
            
        # Get conversion settings
        output_format = self.format_combo.currentText().lower()
        quality = int(self.quality_spin.currentText().split('(')[1].split(')')[0])
        preserve_metadata = self.preserve_metadata.isChecked()
        
        # Disable controls during conversion
        self.set_controls_enabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setMaximum(len(self.image_paths))
        self.progress_bar.setValue(0)
        
        # Create and start worker thread
        self.worker_thread = HEICConversionWorker(
            self.image_paths,
            self.output_dir,
            output_format,
            quality,
            preserve_metadata
        )
        
        # Connect signals
        self.worker_thread.progress_updated.connect(self.update_progress)
        self.worker_thread.finished.connect(self.conversion_finished)
        self.worker_thread.error_occurred.connect(self.show_error)
        
        # Start the worker thread
        self.worker_thread.start()
    
    def set_controls_enabled(self, enabled: bool) -> None:
        """Enable or disable all controls."""
        for control in ['file_controls', 'output_selector', 'format_combo', 'quality_spin', 'preserve_metadata']:
            if hasattr(self, control):
                getattr(self, control).setEnabled(enabled)
        self.convert_btn.setEnabled(enabled and bool(getattr(self, 'image_paths', None)))
        self.conversion_in_progress = not enabled
    
    def update_progress(self, current: int, total: int) -> None:
        """Update progress bar and status."""
        self.progress_bar.setMaximum(total)
        self.progress_bar.setValue(current)
        
        # Update status
        if hasattr(self, 'statusBar'):
            self.statusBar().showMessage(f"Converting image {current} of {total}...")
    
    def update_convert_button_text(self):
        """Update the convert button text based on selected format."""
        if hasattr(self, 'convert_btn') and hasattr(self, 'format_combo'):
            self.convert_btn.setText(f"Convert to {self.format_combo.currentText()}")
    
    def conversion_finished(self) -> None:
        """Handle completion of conversion process."""
        self.set_controls_enabled(True)
        self.progress_bar.setVisible(False)
        
        if hasattr(self, 'statusBar'):
            self.statusBar().showMessage("Conversion completed successfully!", 5000)
        
        QMessageBox.information(self, 'Conversion Complete',
            f'Successfully converted {len(self.image_paths)} image(s) to {self.format_combo.currentText()}.',
            QMessageBox.Ok)
    
    def show_error(self, error_msg: str) -> None:
        """Show error message to the user."""
        self.set_controls_enabled(True)
        self.progress_bar.setVisible(False)
        QMessageBox.critical(self, 'Conversion Error',
            f'An error occurred during conversion:\n{error_msg}',
            QMessageBox.Ok)


class HEICConversionWorker(QThread):
    """Worker thread for HEIC conversion tasks."""
    progress_updated = pyqtSignal(int, int)  # current, total
    finished = pyqtSignal()
    error_occurred = pyqtSignal(str)
    
    def __init__(self, input_files: List[str], output_dir: str, output_format: str,
                 quality: int, preserve_metadata: bool = True):
        super().__init__()
        self.input_files = input_files
        self.output_dir = output_dir
        self.output_format = output_format
        self.quality = quality
        self.preserve_metadata = preserve_metadata
        self.is_running = True
    
    def run(self) -> None:
        """Process all images in the input list."""
        try:
            total = len(self.input_files)
            for i, input_path in enumerate(self.input_files, 1):
                if not self.is_running:
                    break
                try:
                    self.convert_image(input_path)
                    self.progress_updated.emit(i, total)
                except Exception as e:
                    name = os.path.basename(input_path)
                    self.error_occurred.emit(f"Error converting {name}: {e}")
            self.finished.emit()
        except Exception as e:
            self.error_occurred.emit(str(e))
    
    def convert_image(self, input_path: str) -> None:
        """Convert a single image to target format."""
        try:
            filename = f"{os.path.splitext(os.path.basename(input_path))[0]}.{self.output_format}"
            output_path = os.path.join(self.output_dir, filename)
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            with Image.open(input_path) as img:
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                is_jpeg = self.output_format == 'jpeg'
                img.save(output_path, quality=self.quality,
                        progressive=is_jpeg, optimize=is_jpeg)
                        
        except Exception as e:
            raise Exception(f"Failed to convert {input_path}: {e}")
    
    def stop(self) -> None:
        """Stop the conversion process."""
        self.is_running = False
