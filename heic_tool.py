import os
import sys
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
                            QFileDialog, QProgressBar, QScrollArea, QGridLayout, 
                            QSizePolicy, QComboBox, QGroupBox, QMessageBox, QCheckBox)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QPixmap, QImage
from PIL import Image

# Try to import pillow_heif but don't initialize it yet
HEIC_SUPPORT = False
try:
    import pillow_heif
    HEIC_SUPPORT = True
except ImportError:
    print("Warning: pillow-heif not found. HEIC support will be disabled.")

import io

class ThumbnailLabel(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignCenter)
        self.setMinimumSize(120, 120)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setStyleSheet("""
            border: 1px solid #ddd;
            margin: 2px;
            padding: 2px;
        """)

class HEICConverterTool(QWidget):
    def __init__(self):
        super().__init__()
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.image_paths = []
        self.current_preview = None
        self.current_path = None
        self.output_dir = None
        self.heic_supported = HEIC_SUPPORT
        
        # Initialize pillow_heif if available
        if self.heic_supported:
            try:
                pillow_heif.register_heif_opener()
            except Exception as e:
                print(f"Error initializing HEIC support: {e}")
                self.heic_supported = False
                
        self.init_ui()
    
    def init_ui(self):
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
        self.size_info.setStyleSheet("font-size: 10px; color: #555;")
        preview_layout.addWidget(self.size_info)
        
        preview_group.setLayout(preview_layout)
        
        # Right panel - Controls
        control_group = QGroupBox("HEIC to JPG Converter")
        control_group.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        control_layout = QVBoxLayout()
        
        # File selection
        self.file_label = QLabel("No HEIC images selected (0)")
        
        file_btn_layout = QHBoxLayout()
        browse_btn = QPushButton("Add HEIC Images")
        browse_btn.clicked.connect(self.browse_heic_images)
        clear_btn = QPushButton("Clear")
        clear_btn.clicked.connect(self.clear_images)
        file_btn_layout.addWidget(browse_btn)
        file_btn_layout.addWidget(clear_btn)
        
        # Output format selection
        format_layout = QHBoxLayout()
        format_layout.addWidget(QLabel("Output Format:"))
        self.format_combo = QComboBox()
        self.format_combo.addItems(["JPEG", "PNG"])
        self.format_combo.setCurrentIndex(0)  # Default to JPEG
        format_layout.addWidget(self.format_combo)
        
        # Quality settings
        quality_layout = QHBoxLayout()
        quality_layout.addWidget(QLabel("Quality (1-100):"))
        self.quality_spin = QComboBox()
        self.quality_spin.addItems(["Maximum (100)", "High (90)", "Good (80)", "Medium (70)", "Low (60)"])
        self.quality_spin.setCurrentIndex(1)  # Default to High (90)
        quality_layout.addWidget(self.quality_spin)
        
        # Output directory
        self.output_dir_btn = QPushButton("Select Output Directory")
        self.output_dir_btn.clicked.connect(self.select_output_dir)
        self.output_dir_label = QLabel("Output: Same as input")
        
        # Options
        self.preserve_metadata = QCheckBox("Preserve metadata")
        self.preserve_metadata.setChecked(True)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        
        # Convert button
        self.convert_btn = QPushButton("Convert to JPG")
        self.convert_btn.clicked.connect(self.convert_images)
        self.convert_btn.setEnabled(False)
        
        # Add to control layout
        control_layout.addWidget(self.file_label)
        control_layout.addLayout(file_btn_layout)
        control_layout.addWidget(self.output_dir_btn)
        control_layout.addWidget(self.output_dir_label)
        control_layout.addSpacing(10)
        control_layout.addLayout(format_layout)
        control_layout.addLayout(quality_layout)
        control_layout.addWidget(self.preserve_metadata)
        control_layout.addStretch()
        control_layout.addWidget(self.progress_bar)
        control_layout.addWidget(self.convert_btn)
        
        control_group.setLayout(control_layout)
        
        # Add to main layout
        main_layout.addWidget(preview_group, 70)
        main_layout.addWidget(control_group, 30)
        self.setLayout(main_layout)
    
    def browse_heic_images(self):
        if not self.heic_supported:
            QMessageBox.warning(self, 'HEIC Not Supported', 
                'HEIC support is not available. Please install pillow-heif package.')
            return
            
        paths, _ = QFileDialog.getOpenFileNames(
            self, 'Select HEIC Images', '', 
            'HEIC Images (*.heic *.heif);;All Files (*)')
            
        if paths:
            self.image_paths = paths
            self.file_label.setText(f"Selected: {len(self.image_paths)} HEIC images")
            self.convert_btn.setEnabled(True)
            self.update_thumbnails()
    
    def clear_images(self):
        self.image_paths = []
        self.current_preview = None
        self.current_path = None
        self.file_label.setText("No HEIC images selected (0)")
        self.convert_btn.setEnabled(False)
        self.clear_thumbnails()
    
    def clear_thumbnails(self):
        # Clear existing thumbnails
        for i in reversed(range(self.thumbnail_layout.count())): 
            widget = self.thumbnail_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)
        
        # Clear main preview if it exists
        if hasattr(self, 'main_preview'):
            self.main_preview.clear()
        if hasattr(self, 'size_info'):
            self.size_info.clear()
    
    def update_thumbnails(self):
        if not self.heic_supported:
            return
            
        self.clear_thumbnails()
        
        # Create new thumbnails
        for i, path in enumerate(self.image_paths):
            try:
                # Create thumbnail container
                thumb_container = QWidget()
                thumb_layout = QVBoxLayout(thumb_container)
                
                # Create thumbnail label
                thumb_label = ThumbnailLabel()
                
                # Load HEIC image using pillow_heif
                try:
                    image = Image.open(path)
                    # Ensure image is in RGB mode for display
                    if image.mode != 'RGB':
                        image = image.convert('RGB')
                    
                    # Create thumbnail
                    thumb_size = QSize(100, 100)
                    thumb = image.copy()
                    thumb.thumbnail((thumb_size.width(), thumb_size.height()))
                    
                    # Convert to QPixmap and set to label
                    data = thumb.tobytes("raw", thumb.mode)
                    qim = QImage(data, thumb.size[0], thumb.size[1], QImage.Format_RGB888)
                    pix = QPixmap.fromImage(qim)
                    thumb_label.setPixmap(pix)
                    
                except Exception as e:
                    print(f"Error loading image {path}: {str(e)}")
                    error_label = QLabel("Error loading image")
                    error_label.setAlignment(Qt.AlignCenter)
                    error_label.setStyleSheet("color: red;")
                    thumb_layout.addWidget(error_label)
                
                # Set click event
                thumb_label.mousePressEvent = lambda e, p=path: self.show_preview(p)
                
                # Add filename label
                filename = os.path.basename(path)
                filename_label = QLabel(filename)
                filename_label.setAlignment(Qt.AlignCenter)
                filename_label.setStyleSheet("font-size: 10px;")
                filename_label.setWordWrap(True)
                
                # Add to layout
                thumb_layout.addWidget(thumb_label)
                thumb_layout.addWidget(filename_label)
                
                # Calculate position in grid (2 columns)
                row = i // 2
                col = i % 2
                self.thumbnail_layout.addWidget(thumb_container, row, col)
                
                # Show first image in preview
                if i == 0:
                    self.show_preview(path)
                    
            except Exception as e:
                print(f"Error creating thumbnail for {path}: {str(e)}")
    
    def select_output_dir(self):
        dir_path = QFileDialog.getExistingDirectory(self, 'Select Output Directory')
        if dir_path:
            self.output_dir = dir_path
            self.output_dir_label.setText(f"Output: {os.path.basename(dir_path)}")
    
    def show_preview(self, path):
        try:
            # Load the image
            image = Image.open(path)
            
            # Ensure image is in RGB mode for display
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Resize for preview (max 800x600 while maintaining aspect ratio)
            max_size = QSize(800, 600)
            image.thumbnail((max_size.width(), max_size.height()))
            
            # Convert to QPixmap and set to label
            data = image.tobytes("raw", image.mode)
            qim = QImage(data, image.size[0], image.size[1], QImage.Format_RGB888)
            pix = QPixmap.fromImage(qim)
            
            # Update preview
            self.main_preview.setPixmap(pix)
            self.main_preview.setAlignment(Qt.AlignCenter)
            
            # Show image info
            img_size = os.path.getsize(path) / (1024 * 1024)  # Size in MB
            self.size_info.setText(
                f"{os.path.basename(path)}\n"
                f"Dimensions: {image.width} x {image.height}\n"
                f"Size: {img_size:.2f} MB\n"
                f"Format: {image.format if hasattr(image, 'format') else 'Unknown'}"
            )
            
            # Update current preview path
            self.current_path = path
            
        except Exception as e:
            print(f"Error loading preview for {path}: {str(e)}")
            self.main_preview.setText("Error loading image")
            self.size_info.clear()
    
    def convert_images(self):
        if not self.image_paths:
            return
            
        # Get output format and quality
        output_format = self.format_combo.currentText().lower()
        quality_map = {
            "Maximum (100)": 100,
            "High (90)": 90,
            "Good (80)": 80,
            "Medium (70)": 70,
            "Low (60)": 60
        }
        quality = quality_map.get(self.quality_spin.currentText(), 90)
        
        # Set up progress bar
        self.progress_bar.setMaximum(len(self.image_paths))
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(True)
        
        # Process each image
        converted_count = 0
        for i, path in enumerate(self.image_paths):
            try:
                # Update progress
                self.progress_bar.setValue(i + 1)
                QApplication.processEvents()  # Keep UI responsive
                
                # Determine output path
                if self.output_dir:
                    output_dir = self.output_dir
                else:
                    output_dir = os.path.dirname(path)
                
                # Create output filename
                base_name = os.path.splitext(os.path.basename(path))[0]
                output_path = os.path.join(output_dir, f"{base_name}.{output_format}")
                
                # Convert and save the image
                image = Image.open(path)
                
                # Preserve metadata if requested
                save_kwargs = {'quality': quality}
                if output_format == 'png':
                    save_kwargs['compress_level'] = 9 - int((quality / 100) * 9)  # Map 0-100 to 9-0
                
                # Convert to RGB if saving as JPEG
                if output_format == 'jpg' and image.mode != 'RGB':
                    image = image.convert('RGB')
                
                # Save the image
                image.save(output_path, **save_kwargs)
                converted_count += 1
                
            except Exception as e:
                print(f"Error converting {path}: {str(e)}")
        
        # Show completion message
        self.progress_bar.setVisible(False)
        QMessageBox.information(
            self, 'Conversion Complete',
            f'Successfully converted {converted_count} of {len(self.image_paths)} images.'
        )
