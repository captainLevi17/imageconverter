import os
import sys
from pathlib import Path
from typing import Optional, List, Dict, Any

from PIL import Image, ImageFile, ExifTags
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QSize
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
                           QFileDialog, QSpinBox, QComboBox, QCheckBox, QProgressBar,
                           QMessageBox, QGroupBox, QSizePolicy, QSpacerItem, QScrollArea,
                           QGridLayout)

# Import utility modules
from utils import (
    ThumbnailLabel,  # Reuse the component from utils
    FileControls,    # Reuse the component from utils
    load_image,      # For loading images
    save_image,      # For saving images
    get_image_info,  # For getting image information
    validate_directory, # For directory validation
    create_directory,  # For creating directories
    get_unique_filename, # For getting unique filenames
    get_file_size,    # For getting file size in human-readable format
    PreviewManager    # For managing previews
)

# ThumbnailLabel is now imported from utils.ui_components

class CompressorTool(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Initialize instance variables
        self.input_files: List[str] = []
        self.current_preview = None
        self.current_path: Optional[str] = None
        self.output_dir = str(Path.home() / "Pictures" / "Compressed")
        
        # Create output directory using utility function
        success, message = create_directory(self.output_dir)
        if not success:
            # If default directory creation fails, try fallback to Pictures
            self.output_dir = str(Path.home() / "Pictures" / "Compressed")
            success, message = create_directory(self.output_dir)
            if not success:
                # If still failing, use system temp directory as last resort
                import tempfile
                self.output_dir = str(Path(tempfile.gettempdir()) / "imageconverter" / "compressed")
                success, message = create_directory(self.output_dir)
                if not success:
                    print(f"Warning: Could not create any output directory: {message}")
                    self.output_dir = str(Path.home())  # Fall back to home directory
        
        # Configure PIL to be more tolerant of image files
        ImageFile.LOAD_TRUNCATED_IMAGES = True
        
        # Initialize preview manager
        self.preview_manager = PreviewManager()
        
        # Initialize UI
        self.setup_ui()
        
    def setup_ui(self):
        # Create the main layout
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(5, 5, 5, 5)
        
        # Left panel - Preview
        preview_group = QGroupBox("Preview Gallery")
        preview_group.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        preview_layout = QVBoxLayout()
        
        # Thumbnail scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        self.thumbnail_container = QWidget()
        self.thumbnail_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.thumbnail_layout = QGridLayout()
        self.thumbnail_layout.setSpacing(5)
        self.thumbnail_layout.setContentsMargins(5, 5, 5, 5)
        self.thumbnail_container.setLayout(self.thumbnail_layout)
        scroll.setWidget(self.thumbnail_container)
        preview_layout.addWidget(scroll, stretch=1)
        
        # Main preview
        self.main_preview = QLabel()
        self.main_preview.setAlignment(Qt.AlignCenter)
        self.main_preview.setMinimumSize(400, 300)
        self.main_preview.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        preview_layout.addWidget(QLabel("Selected Preview:"))
        preview_layout.addWidget(self.main_preview, stretch=2)
        
        # Add info labels below main preview
        self.size_info = QLabel()
        self.size_info.setAlignment(Qt.AlignCenter)
        self.size_info.setStyleSheet("font-size: 11px; color: #555;")
        preview_layout.addWidget(self.size_info)
        
        # Add compression info
        self.compression_info = QLabel()
        self.compression_info.setAlignment(Qt.AlignCenter)
        self.compression_info.setStyleSheet("font-size: 11px; color: #777;")
        preview_layout.addWidget(self.compression_info)
        
        preview_group.setLayout(preview_layout)
        
        # Right panel - Controls
        control_group = QGroupBox("Compression Settings")
        control_group.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        control_layout = QVBoxLayout()
        control_layout.setSpacing(15)
        
        # File selection using FileControls component
        self.file_controls = FileControls(
            on_browse=self.select_files,
            on_clear=self.clear_files
        )
        control_layout.addWidget(self.file_controls)
        
        # Output settings
        
        # Quality setting
        quality_layout = QHBoxLayout()
        quality_layout.addWidget(QLabel("Quality (%):"))
        self.spin_quality = QSpinBox()
        self.spin_quality.setRange(1, 100)
        self.spin_quality.setValue(85)
        self.spin_quality.valueChanged.connect(self.update_compression_info)
        quality_layout.addWidget(self.spin_quality)
        control_layout.addLayout(quality_layout)
        
        # Format selection
        format_layout = QHBoxLayout()
        format_layout.addWidget(QLabel("Output Format:"))
        self.cmb_format = QComboBox()
        self.cmb_format.addItems(["JPEG", "PNG", "WEBP"])
        format_layout.addWidget(self.cmb_format)
        control_layout.addLayout(format_layout)
        
        # Output directory selection
        dir_layout = QHBoxLayout()
        
        # Create directory widgets
        dir_label = QLabel("Output Directory:")
        self.lbl_output_dir = QLabel()
        self.lbl_output_dir.setWordWrap(True)
        self.lbl_output_dir.setText(f"{self.output_dir}")
        
        self.btn_change_dir = QPushButton("Change")
        self.btn_change_dir.clicked.connect(self.change_output_dir)
        
        # Add to directory layout with proper spacing
        dir_layout.addWidget(dir_label)
        dir_layout.addWidget(self.lbl_output_dir, 1)  # Allow the label to expand
        dir_layout.addWidget(self.btn_change_dir)
        
        # Additional options
        self.chk_preserve_metadata = QCheckBox("Preserve metadata")
        self.chk_preserve_metadata.setChecked(True)
        
        # Assemble output layout
        control_layout.addLayout(dir_layout)
        control_layout.addWidget(self.chk_preserve_metadata)
        
        # Progress
        self.progress = QProgressBar()
        self.progress.setVisible(False)
        
        # Compress button
        self.btn_compress = QPushButton("Compress Images")
        self.btn_compress.clicked.connect(self.start_compression)
        
        # Add widgets to main layout
        control_layout.addStretch()
        control_layout.addWidget(self.progress)
        control_layout.addWidget(self.btn_compress)
        
        control_group.setLayout(control_layout)
        
        # Add both panels to main layout
        main_layout.addWidget(preview_group, stretch=2)
        main_layout.addWidget(control_group, stretch=1)
        
        self.setLayout(main_layout)
    
    def select_files(self):
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Select Images",
            "",
            "Images (*.jpg *.jpeg *.png *.webp *.bmp *.tiff);;All Files (*)"
        )
        if files:
            self.input_files = files
            self.update_thumbnails()
            self.file_controls.update_file_count(len(files))
            
    def clear_files(self):
        self.input_files = []
        self.current_preview = None
        self.current_path = None
        self.update_thumbnails()
        self.file_controls.clear()
        self.main_preview.clear()
        self.size_info.clear()
        self.compression_info.clear()
    
    def update_thumbnails(self):
        # Clear existing thumbnails
        for i in reversed(range(self.thumbnail_layout.count())): 
            self.thumbnail_layout.itemAt(i).widget().setParent(None)
        
        # Clear preview if no files
        if not self.input_files:
            self.main_preview.clear()
            self.size_info.clear()
            self.compression_info.clear()
            return
        
        # Create new thumbnails
        for i, path in enumerate(self.input_files):
            try:
                # Create thumbnail container
                thumb_container = QWidget()
                thumb_layout = QVBoxLayout()
                thumb_layout.setContentsMargins(2, 2, 2, 2)
                thumb_layout.setSpacing(2)
                thumb_container.setLayout(thumb_layout)
                
                # Create thumbnail label using preview manager
                thumb_label = ThumbnailLabel()
                thumb_size = QSize(120, 120)
                thumb_pixmap = self.preview_manager.get_thumbnail(path, thumb_size)
                if thumb_pixmap:
                    thumb_label.setPixmap(thumb_pixmap)
                
                # Add filename label
                filename = os.path.basename(path)
                if len(filename) > 15:
                    filename = filename[:12] + '...'
                filename_label = QLabel(filename)
                filename_label.setAlignment(Qt.AlignCenter)
                filename_label.setStyleSheet("font-size: 9px;")
                
                # Add to layout
                thumb_layout.addWidget(thumb_label)
                thumb_layout.addWidget(filename_label)
                
                # Connect click event
                thumb_container.mousePressEvent = lambda e, p=path: self.show_full_preview(p)
                
                # Add to grid
                row = i // 3
                col = i % 3
                self.thumbnail_layout.addWidget(thumb_container, row, col)
                
                # Show first image in main preview
                if i == 0:
                    self.show_full_preview(path)
                    
            except Exception as e:
                print(f"Error loading thumbnail for {path}: {str(e)}")
    
    def show_full_preview(self, path):
        try:
            # Load the image using our utility function
            self.current_preview = load_image(path)
            if not self.current_preview:
                raise Exception("Failed to load image")
                
            self.current_path = path
            
            # Update main preview using preview manager
            success = self.preview_manager.update_preview(
                path, 
                self.main_preview, 
                max_size=QSize(600, 400)
            )
            if not success:
                raise Exception("Failed to update preview")
            
            # Get image info using utility function
            img_info = get_image_info(path)
            if img_info:
                width, height = img_info.get('size', (0, 0))
                file_size = img_info.get('size_bytes', 0) / 1024  # Convert to KB
                
                self.size_info.setText(
                    f"{os.path.basename(path)}\n"
                    f"Dimensions: {width} × {height} px • "
                    f"Size: {file_size:.1f} KB • "
                    f"Format: {img_info.get('format', 'Unknown')}"
                )
            
            # Update compression info
            self.update_compression_info()
            
        except Exception as e:
            print(f"Error loading preview for {path}: {str(e)}")
            self.main_preview.setText("Error loading image")
            self.size_info.clear()
            self.compression_info.clear()
    
    def update_compression_info(self):
        if not self.current_path:
            return
            
        try:
            # Get current settings
            quality = self.spin_quality.value()
            output_format = self.cmb_format.currentText().lower()
            
            # Update compression info
            self.compression_info.setText(
                f"Compression: {quality}% • Output: {output_format.upper()}"
            )
            
        except Exception as e:
            print(f"Error updating compression info: {str(e)}")
            self.compression_info.clear()
    
    def change_output_dir(self):
        try:
            dir_path = QFileDialog.getExistingDirectory(
                self, 
                "Select Output Directory", 
                self.output_dir
            )
            if dir_path:
                # Validate the selected directory
                if validate_directory(dir_path):
                    self.output_dir = dir_path
                    # Update the label with a shortened path if too long
                    display_path = self.output_dir
                    if len(display_path) > 40:
                        display_path = '...' + display_path[-37:]
                    self.lbl_output_dir.setText(f"Output: {display_path}")
                    self.lbl_output_dir.setToolTip(self.output_dir)  # Show full path on hover
                else:
                    QMessageBox.warning(
                        self, 
                        "Invalid Directory", 
                        "The selected directory is not writable. Please choose a different directory."
                    )
        except Exception as e:
            print(f"Error changing output directory: {e}")
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to change output directory: {str(e)}"
            )
    
    def start_compression(self):
        if not self.input_files:
            QMessageBox.warning(self, "No Files Selected", "Please select at least one image file.")
            return
        
        # Disable UI during compression
        self.set_ui_enabled(False)
        self.progress.setVisible(True)
        self.progress.setMaximum(len(self.input_files))
        self.progress.setValue(0)
        
        # Start compression in a separate thread
        self.worker = CompressionWorker(
            self.input_files,
            self.output_dir,
            self.spin_quality.value(),
            self.cmb_format.currentText().lower(),
            self.chk_preserve_metadata.isChecked()
        )
        self.worker.progress_updated.connect(self.update_progress)
        self.worker.finished.connect(self.compression_finished)
        self.worker.error_occurred.connect(self.handle_error)
        self.worker.start()
    
    def update_progress(self, value):
        self.progress.setValue(value)
    
    def compression_finished(self):
        self.set_ui_enabled(True)
        self.progress.setVisible(False)
        QMessageBox.information(self, "Success", "Image compression completed successfully!")
    
    def handle_error(self, error_msg):
        self.set_ui_enabled(True)
        self.progress.setVisible(False)
        QMessageBox.critical(self, "Error", error_msg)
    
    def set_ui_enabled(self, enabled):
        """Enable or disable UI elements during operations."""
        self.file_controls.setEnabled(enabled)
        self.btn_compress.setEnabled(enabled and len(self.input_files) > 0)
        self.btn_change_dir.setEnabled(enabled)
        self.spin_quality.setEnabled(enabled)
        self.cmb_format.setEnabled(enabled)
        self.chk_preserve_metadata.setEnabled(enabled)


class CompressionWorker(QThread):
    progress_updated = pyqtSignal(int)
    finished = pyqtSignal()
    error_occurred = pyqtSignal(str)
    
    def __init__(self, input_files, output_dir, quality, output_format, preserve_metadata=True):
        super().__init__()
        self.input_files = input_files
        self.output_dir = output_dir
        self.quality = quality
        self.output_format = output_format
        self.preserve_metadata = preserve_metadata
        self.is_running = True
    
    def run(self):
        try:
            for i, input_path in enumerate(self.input_files, 1):
                if not self.is_running:
                    break
                    
                try:
                    self.process_image(input_path, i)
                    self.progress_updated.emit(i)
                except Exception as e:
                    self.error_occurred.emit(f"Error processing {os.path.basename(input_path)}: {str(e)}")
                    continue
            
            self.finished.emit()
        except Exception as e:
            self.error_occurred.emit(f"Unexpected error: {str(e)}")
    
    def process_image(self, input_path: str, index: int) -> None:
        """Process and save a single image with compression settings.
        
        Args:
            input_path: Path to the input image file
            index: Index of the current image in the processing queue
            
        Raises:
            Exception: If image processing or saving fails
        """
        img = None
        try:
            print(f"\nProcessing image {index}: {os.path.basename(input_path)}")
            print(f"Original file size: {os.path.getsize(input_path) / 1024:.1f} KB")
            
            # Load the image using our utility function
            img = load_image(input_path)
            if img is None:
                raise Exception("Failed to load image - load_image returned None")
                
            print(f"Image loaded. Mode: {img.mode}, Size: {img.size}, Format: {getattr(img, 'format', 'unknown')}")
            
            # Ensure image is not empty
            if not img.size[0] or not img.size[1]:
                raise Exception(f"Invalid image dimensions: {img.size}")
            
            # Get original size and calculate new size if needed
            original_size = img.size
            max_dimension = 2000  # Maximum width or height
            
            # Calculate new size maintaining aspect ratio if needed
            if max(original_size) > max_dimension:
                ratio = max_dimension / max(original_size)
                new_size = (int(original_size[0] * ratio), int(original_size[1] * ratio))
                print(f"Resizing from {original_size} to {new_size}")
                try:
                    img = img.resize(new_size, Image.Resampling.LANCZOS)
                    print(f"Resize successful. New size: {img.size}")
                except Exception as resize_error:
                    raise Exception(f"Failed to resize image: {str(resize_error)}")
            
            # Prepare output path with unique filename
            filename = os.path.splitext(os.path.basename(input_path))[0]
            output_filename = f"{filename}_compressed.{self.output_format.lower()}"
            output_path = os.path.join(self.output_dir, output_filename)
            print(f"Output path: {output_path}")
            print(f"Output format: {self.output_format.upper()}")
            print(f"Quality: {self.quality}")
            print(f"Preserve metadata: {self.preserve_metadata}")
            
            # Ensure output directory exists
            success, message = create_directory(self.output_dir)
            if not success:
                raise Exception(f"Failed to create output directory: {message}")
            
            # Prepare save options
            save_options = {
                'format': self.output_format.upper(),
                'quality': max(5, min(100, self.quality)),
                'optimize': True
            }
            
            # Add format-specific options
            if self.output_format.upper() == 'JPEG':
                # Convert to RGB mode for JPEG
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                save_options.update({
                    'progressive': True,
                    'subsampling': '4:2:0',
                    'qtables': 'web_low',
                    'dpi': (72, 72),
                    'icc_profile': b''
                })
            elif self.output_format.upper() == 'PNG':
                # Convert to RGBA if image has transparency
                if img.mode == 'P' and 'transparency' in img.info:
                    img = img.convert('RGBA')
                elif img.mode == 'P':
                    img = img.convert('RGB')
                save_options.update({
                    'compress_level': 6,  # Balanced between speed and compression
                    'dpi': (72, 72),
                    'icc_profile': b''
                })
            elif self.output_format.upper() == 'WEBP':
                # Convert to RGB/RGBA for WebP
                if img.mode == 'P':
                    if 'transparency' in img.info:
                        img = img.convert('RGBA')
                    else:
                        img = img.convert('RGB')
                save_options.update({
                    'method': 4,  # Faster encoding with good compression
                    'lossless': False,
                    'icc_profile': b'',
                    'exif': b'',
                    'dpi': (72, 72)
                })
            
            try:
                print("Attempting to save image with options:", save_options)
                
                # First, try saving with the utility function
                if not save_image(img, output_path, **save_options):
                    raise Exception("save_image function returned False")
                
                print(f"Image saved successfully. Output size: {os.path.getsize(output_path) / 1024:.1f} KB")
                
                # Preserve metadata if requested
                if self.preserve_metadata and hasattr(img, 'info') and img.info:
                    try:
                        print("Attempting to preserve metadata...")
                        with Image.open(output_path) as output_img:
                            # Only preserve metadata that's safe to copy
                            safe_metadata = {}
                            for key, value in img.info.items():
                                if key.lower() in ('dpi', 'resolution', 'exif', 'icc_profile'):
                                    safe_metadata[key] = value
                            
                            if safe_metadata:
                                print(f"Preserving metadata: {', '.join(safe_metadata.keys())}")
                                output_img.info = safe_metadata
                                output_img.save(output_path, **save_options)
                                print("Metadata preserved successfully")
                    except Exception as meta_error:
                        print(f"Warning: Could not preserve metadata: {str(meta_error)}")
                
                return  # Success!
                
            except Exception as e:
                print(f"Initial save failed: {str(e)}")
                
                # If initial save fails, try a simpler save with minimal options
                try:
                    print("Trying fallback save method...")
                    simple_options = {
                        'format': self.output_format.upper(),
                        'quality': max(5, min(100, self.quality)),
                        'optimize': True
                    }
                    print("Fallback save options:", simple_options)
                    
                    # Try direct save without the utility function
                    img.save(output_path, **simple_options)
                    print(f"Fallback save successful. Output size: {os.path.getsize(output_path) / 1024:.1f} KB")
                    
                except Exception as save_error:
                    # If all else fails, try converting to RGB and saving
                    try:
                        print("Trying final fallback with RGB conversion...")
                        if img.mode != 'RGB':
                            img = img.convert('RGB')
                        img.save(output_path, format=self.output_format.upper(), quality=max(5, min(100, self.quality)))
                        print(f"Final fallback successful. Output size: {os.path.getsize(output_path) / 1024:.1f} KB")
                    except Exception as final_error:
                        raise Exception(f"All save attempts failed. Last error: {str(final_error)}")
        
        except Exception as e:
            raise Exception(f"Failed to process {os.path.basename(input_path)}: {str(e)}")
    
    def stop(self):
        self.is_running = False
