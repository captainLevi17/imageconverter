import os
import sys
from pathlib import Path
from PIL import Image, ImageFile, ExifTags
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
                           QFileDialog, QSpinBox, QComboBox, QCheckBox, QProgressBar,
                           QMessageBox, QGroupBox, QSizePolicy, QSpacerItem, QScrollArea,
                           QGridLayout)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QImage, QPixmap

class ThumbnailLabel(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignCenter)
        self.setMinimumSize(100, 100)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setStyleSheet("""
            border: 1px solid #ddd;
            margin: 2px;
            padding: 2px;
            background: #f8f8f8;
        """)

class CompressorTool(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Initialize instance variables
        self.input_files = []
        self.current_preview = None
        self.current_path = None
        self.output_dir = str(Path.home() / "Pictures" / "Compressed")
        
        # Try to create the output directory
        try:
            os.makedirs(self.output_dir, exist_ok=True)
        except Exception as e:
            print(f"Error creating output directory: {e}")
            # Fallback to Pictures directory
            self.output_dir = str(Path.home() / "Pictures")
            try:
                os.makedirs(self.output_dir, exist_ok=True)
            except Exception as e:
                print(f"Error creating fallback directory: {e}")
                # Last resort: use current working directory
                self.output_dir = os.getcwd()
        
        # Configure PIL to be more tolerant of image files
        ImageFile.LOAD_TRUNCATED_IMAGES = True
        
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
        
        # File selection
        self.file_label = QLabel("No images selected (0)")
        
        file_btn_layout = QHBoxLayout()
        self.btn_select_files = QPushButton("Add Images")
        self.btn_clear_files = QPushButton("Clear")
        self.btn_select_files.clicked.connect(self.select_files)
        self.btn_clear_files.clicked.connect(self.clear_files)
        file_btn_layout.addWidget(self.btn_select_files)
        file_btn_layout.addWidget(self.btn_clear_files)
        
        control_layout.addWidget(self.file_label)
        control_layout.addLayout(file_btn_layout)
        
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
            self.file_label.setText(f"{len(files)} image(s) selected")
            
    def clear_files(self):
        self.input_files = []
        self.current_preview = None
        self.current_path = None
        self.update_thumbnails()
        self.file_label.setText("No images selected (0)")
        self.main_preview.clear()
        self.size_info.clear()
        self.compression_info.clear()
    
    def update_thumbnails(self):
        # Clear existing thumbnails
        for i in reversed(range(self.thumbnail_layout.count())): 
            self.thumbnail_layout.itemAt(i).widget().setParent(None)
        
        # Create new thumbnails
        for i, path in enumerate(self.input_files):
            try:
                # Create thumbnail container
                thumb_container = QWidget()
                thumb_layout = QVBoxLayout()
                thumb_container.setLayout(thumb_layout)
                
                # Create thumbnail label
                thumb_label = ThumbnailLabel()
                
                # Load and resize image for thumbnail
                img = Image.open(path)
                img.thumbnail((100, 100), Image.Resampling.LANCZOS)
                
                # Convert to QPixmap
                if img.mode == 'RGBA':
                    img = img.convert('RGBA')
                    data = img.tobytes('raw', 'RGBA')
                    qimg = QImage(data, img.width, img.height, QImage.Format_RGBA8888)
                else:
                    img = img.convert('RGB')
                    data = img.tobytes('raw', 'RGB')
                    qimg = QImage(data, img.width, img.height, QImage.Format_RGB888)
                
                pixmap = QPixmap.fromImage(qimg)
                thumb_label.setPixmap(pixmap)
                
                # Add filename label
                filename = os.path.basename(path)
                if len(filename) > 15:
                    filename = filename[:12] + '...'
                filename_label = QLabel(filename)
                filename_label.setAlignment(Qt.AlignCenter)
                filename_label.setStyleSheet("font-size: 9px; margin-top: 2px;")
                
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
            self.current_preview = Image.open(path)
            self.current_path = path
            
            # Update main preview
            preview_img = self.current_preview.copy()
            preview_img.thumbnail((600, 400), Image.Resampling.LANCZOS)
            
            # Convert to QPixmap
            if preview_img.mode == 'RGBA':
                preview_img = preview_img.convert('RGBA')
                data = preview_img.tobytes('raw', 'RGBA')
                qimg = QImage(data, preview_img.width, preview_img.height, QImage.Format_RGBA8888)
            else:
                preview_img = preview_img.convert('RGB')
                data = preview_img.tobytes('raw', 'RGB')
                qimg = QImage(data, preview_img.width, preview_img.height, QImage.Format_RGB888)
            
            pixmap = QPixmap.fromImage(qimg)
            self.main_preview.setPixmap(pixmap)
            
            # Update info
            orig_width, orig_height = self.current_preview.size
            file_size = os.path.getsize(path) / 1024  # KB
            
            self.size_info.setText(
                f"{os.path.basename(path)}\n"
                f"Dimensions: {orig_width} × {orig_height} px • "
                f"Size: {file_size:.1f} KB"
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
            dir_path = QFileDialog.getExistingDirectory(self, "Select Output Directory", self.output_dir)
            if dir_path:
                self.output_dir = dir_path
                self.lbl_output_dir.setText(f"Output: {self.output_dir}")
        except Exception as e:
            print(f"Error changing output directory: {e}")
    
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
        self.btn_select_files.setEnabled(enabled)
        self.btn_compress.setEnabled(enabled)
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
    
    def process_image(self, input_path, index):
        try:
            # Import PIL here to ensure it's available in this scope
            from PIL import Image, ImageFile
            
            # Open the image
            with Image.open(input_path) as img:
                # Get original size
                original_size = img.size
                max_dimension = 2000  # Maximum width or height
                
                # Calculate new size maintaining aspect ratio
                if max(original_size) > max_dimension:
                    ratio = max_dimension / max(original_size)
                    new_size = (int(original_size[0] * ratio), int(original_size[1] * ratio))
                    img = img.resize(new_size, Image.Resampling.LANCZOS)
                
                # Convert to appropriate color mode
                if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
                    img = img.convert('RGBA')
                else:
                    img = img.convert('RGB')
                
                # Preserve transparency for PNG and WebP
                if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
                    img = img.convert('RGBA')
                else:
                    img = img.convert('RGB')
                
                # Prepare output path
                filename = os.path.splitext(os.path.basename(input_path))[0]
                output_path = os.path.join(
                    self.output_dir,
                    f"{filename}_compressed.{self.output_format.lower()}"
                )
                
                # Handle format-specific saving with optimized compression
                save_kwargs = {}
                quality = max(5, min(100, self.quality))  # Ensure quality is between 5-100
                
                if self.output_format.upper() == 'JPEG':
                    save_kwargs = {
                        'quality': quality,
                        'optimize': True,
                        'progressive': True,
                        'subsampling': '4:2:0',  # Always use 4:2:0 for better compression
                        'qtables': 'web_low',  # More aggressive compression
                        'dpi': (72, 72),  # Standard screen DPI
                        'icc_profile': b''  # Remove ICC profile to save space
                    }
                elif self.output_format.upper() == 'PNG':
                    # For PNG, we'll convert to 8-bit color if possible
                    if img.mode == 'RGBA' or img.mode == 'RGB':
                        img = img.convert('P', palette=Image.ADAPTIVE, colors=256)
                    save_kwargs = {
                        'optimize': True,
                        'compress_level': 9,  # Maximum compression
                        'dpi': (72, 72),
                        'icc_profile': b''  # Remove ICC profile
                    }
                elif self.output_format.upper() == 'WEBP':
                    save_kwargs = {
                        'quality': max(5, quality - 10),  # Slightly lower quality for better compression
                        'method': 4,  # Faster encoding with good compression
                        'lossless': False,
                        'icc_profile': b'',  # Remove ICC profile
                        'exif': b'',  # Remove EXIF data
                        'dpi': (72, 72)
                    }
                
                # Save the image
                img.save(output_path, **save_kwargs)
                
                # Preserve metadata if requested
                if self.preserve_metadata and hasattr(img, 'info') and img.info:
                    try:
                        # Reopen the image to update metadata
                        with Image.open(output_path) as output_img:
                            # Copy relevant metadata
                            output_img.info = img.info.copy()
                            output_img.save(output_path, **save_kwargs)
                    except Exception as e:
                        print(f"Warning: Could not preserve metadata: {str(e)}")
        
        except Exception as e:
            raise Exception(f"Failed to process {os.path.basename(input_path)}: {str(e)}")
    
    def stop(self):
        self.is_running = False
