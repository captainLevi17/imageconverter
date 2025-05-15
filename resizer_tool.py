from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                            QPushButton, QFileDialog, QSpinBox, QCheckBox,
                            QGroupBox, QProgressBar, QScrollArea, QGridLayout,
                            QSizePolicy)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QPixmap, QImage
from PIL import Image
import os

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

class ResizerTool(QWidget):
    def __init__(self):
        super().__init__()
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.image_paths = []
        self.current_preview = None
        self.current_path = None
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
        
        # Add scaling indicator
        self.scaling_info = QLabel()
        self.scaling_info.setAlignment(Qt.AlignCenter)
        self.scaling_info.setStyleSheet("font-size: 10px; color: #777;")
        preview_layout.addWidget(self.scaling_info)
        
        preview_group.setLayout(preview_layout)
        
        # Right panel - Controls
        control_group = QGroupBox("Controls")
        control_group.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        control_layout = QVBoxLayout()
        
        # File selection
        self.file_label = QLabel("No images selected (0)")
        
        file_btn_layout = QHBoxLayout()
        browse_btn = QPushButton("Add Images")
        browse_btn.clicked.connect(self.browse_images)
        clear_btn = QPushButton("Clear")
        clear_btn.clicked.connect(self.clear_images)
        file_btn_layout.addWidget(browse_btn)
        file_btn_layout.addWidget(clear_btn)
        
        # Output directory
        self.output_dir_btn = QPushButton("Select Output Directory")
        self.output_dir_btn.clicked.connect(self.select_output_dir)
        self.output_dir_label = QLabel("Output: Same as input")
        self.output_dir = None
        
        # Resize options
        options_layout = QVBoxLayout()
        
        # Width/Height controls
        size_layout = QHBoxLayout()
        size_layout.addWidget(QLabel("Width:"))
        self.width_spin = QSpinBox()
        self.width_spin.setRange(1, 10000)
        self.width_spin.setValue(800)
        self.width_spin.valueChanged.connect(self.update_preview)
        size_layout.addWidget(self.width_spin)
        
        size_layout.addWidget(QLabel("Height:"))
        self.height_spin = QSpinBox()
        self.height_spin.setRange(1, 10000)
        self.height_spin.setValue(600)
        self.height_spin.valueChanged.connect(self.update_preview)
        size_layout.addWidget(self.height_spin)
        
        self.keep_aspect = QCheckBox("Maintain aspect ratio")
        self.keep_aspect.setChecked(True)
        self.keep_aspect.stateChanged.connect(self.update_preview)
        
        # Add checkbox for enlarging images
        self.allow_enlarge = QCheckBox("Enlarge smaller images")
        self.allow_enlarge.setChecked(False)
        control_layout.addWidget(self.allow_enlarge)
        
        # Presets
        presets_layout = QHBoxLayout()
        presets = [
            ("Small (800x600)", 800, 600),
            ("Medium (1280x720)", 1280, 720),
            ("HD (1920x1080)", 1920, 1080)
        ]
        
        for text, w, h in presets:
            btn = QPushButton(text)
            btn.clicked.connect(lambda _, w=w, h=h: self.set_preset(w, h))
            presets_layout.addWidget(btn)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        
        # Action buttons
        btn_layout = QHBoxLayout()
        self.resize_btn = QPushButton("Resize Images")
        self.resize_btn.clicked.connect(self.resize_images)
        self.resize_btn.setEnabled(False)
        btn_layout.addWidget(self.resize_btn)
        
        # Add to control layout
        control_layout.addWidget(self.file_label)
        control_layout.addLayout(file_btn_layout)
        control_layout.addWidget(self.output_dir_btn)
        control_layout.addWidget(self.output_dir_label)
        control_layout.addLayout(size_layout)
        control_layout.addWidget(self.keep_aspect)
        control_layout.addLayout(presets_layout)
        control_layout.addWidget(self.progress_bar)
        control_layout.addLayout(btn_layout)
        control_layout.addStretch()
        control_group.setLayout(control_layout)
        
        # Add to main layout
        main_layout.addWidget(preview_group, 70)
        main_layout.addWidget(control_group, 30)
        self.setLayout(main_layout)
    
    def browse_images(self):
        paths, _ = QFileDialog.getOpenFileNames(
            self, 'Select Images', '', 
            'Image Files (*.png *.jpg *.jpeg *.bmp *.webp)')
        if paths:
            self.image_paths = paths  # Replace existing selection
            self.file_label.setText(f"Selected: {len(self.image_paths)} images")
            self.resize_btn.setEnabled(True)
            self.update_thumbnails()
    
    def update_thumbnails(self):
        # Clear existing thumbnails
        for i in reversed(range(self.thumbnail_layout.count())): 
            self.thumbnail_layout.itemAt(i).widget().setParent(None)
        
        # Create new thumbnails
        for i, path in enumerate(self.image_paths):
            try:
                # Get image info
                img = Image.open(path)
                width, height = img.size
                file_size = os.path.getsize(path) / 1024  # KB
                
                # Create thumbnail container
                thumb_container = QWidget()
                thumb_layout = QVBoxLayout()
                thumb_container.setLayout(thumb_layout)
                
                # Create thumbnail image
                thumb_img = img.copy()
                thumb_img.thumbnail((100, 100))
                
                # Convert to QPixmap
                thumb_img = thumb_img.convert("RGBA")
                data = thumb_img.tobytes("raw", "RGBA")
                qimg = QImage(data, thumb_img.size[0], thumb_img.size[1], QImage.Format_RGBA8888)
                pixmap = QPixmap.fromImage(qimg)
                
                # Create thumbnail label
                thumb = ThumbnailLabel()
                thumb.setPixmap(pixmap)
                thumb_layout.addWidget(thumb)
                
                # Add info label
                info_label = QLabel(f"{width}x{height}\n{file_size:.1f} KB")
                info_label.setAlignment(Qt.AlignCenter)
                info_label.setStyleSheet("font-size: 9px; color: #666;")
                thumb_layout.addWidget(info_label)
                
                # Make clickable
                thumb_container.mousePressEvent = lambda e, p=path: self.show_full_preview(p)
                thumb_container.setToolTip(f"{os.path.basename(path)}\n{width}x{height} pixels\n{file_size:.1f} KB")
                
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
        """Show full-size preview of selected image"""
        try:
            self.current_preview = Image.open(path)
            self.current_path = path
            self.update_preview()
            
            # Update info labels
            orig_width, orig_height = self.current_preview.size
            file_size = os.path.getsize(path) / 1024  # KB
            
            self.size_info.setText(
                f"Original: {orig_width}×{orig_height} px • "
                f"Size: {file_size:.1f} KB"
            )
            
            self.main_preview.setToolTip(
                f"File: {os.path.basename(path)}\n"
                f"Original: {orig_width}×{orig_height} px\n"
                f"Size: {file_size:.1f} KB"
            )
        except Exception as e:
            print(f"Error loading preview for {path}: {str(e)}")
    
    def resize_image(self, img, width, height):
        """Helper method to handle resizing logic"""
        orig_width, orig_height = img.size
        
        if not self.allow_enlarge.isChecked():
            # Constrain to original dimensions if not allowed to enlarge
            width = min(width, orig_width)
            height = min(height, orig_height)
        
        if self.keep_aspect.isChecked():
            # Calculate target size maintaining aspect ratio
            orig_ratio = orig_width / orig_height
            target_ratio = width / height
            
            if orig_ratio >= target_ratio:
                # Fit to width
                new_width = width
                new_height = int(width / orig_ratio)
            else:
                # Fit to height
                new_height = height
                new_width = int(height * orig_ratio)
                
            return img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        else:
            # Direct resize without maintaining aspect
            return img.resize((width, height), Image.Resampling.LANCZOS)
    
    def update_preview(self):
        if not self.current_preview:
            return
            
        orig_width, orig_height = self.current_preview.size
        width = self.width_spin.value()
        height = self.height_spin.value()
        
        # Create preview image
        preview_img = self.resize_image(self.current_preview.copy(), width, height)
        new_width, new_height = preview_img.size
        
        # Update scaling info
        scaling_factor = max(new_width/orig_width, new_height/orig_height)
        if scaling_factor > 1:
            scale_text = f"Enlarged: {scaling_factor:.1f}x"
        elif scaling_factor < 1:
            scale_text = f"Reduced: {scaling_factor:.1f}x"
        else:
            scale_text = "Original size"
            
        self.scaling_info.setText(
            f"Output: {new_width}×{new_height} px • {scale_text}"
        )
        
        # Convert to QPixmap and display
        preview_img = preview_img.convert("RGBA")
        data = preview_img.tobytes("raw", "RGBA")
        qimg = QImage(data, preview_img.size[0], preview_img.size[1], QImage.Format_RGBA8888)
        pixmap = QPixmap.fromImage(qimg)
        
        scaled_pixmap = pixmap.scaled(
            self.main_preview.size(), 
            Qt.KeepAspectRatio, 
            Qt.SmoothTransformation)
        
        self.main_preview.setPixmap(scaled_pixmap)
    
    def clear_images(self):
        self.image_paths = []
        self.current_preview = None
        self.current_path = None
        self.file_label.setText("No images selected (0)")
        self.main_preview.clear()
        self.resize_btn.setEnabled(False)
        self.update_thumbnails()
    
    def select_output_dir(self):
        dir_path = QFileDialog.getExistingDirectory(self, 'Select Output Directory')
        if dir_path:
            self.output_dir = dir_path
            self.output_dir_label.setText(f"Output: {dir_path}")
            self.output_dir_label.setStyleSheet("color: #0066cc; font-weight: bold;")
            self.output_dir_label.setToolTip(f"Resized images will be saved to:\n{dir_path}")
        else:
            self.output_dir = None
            self.output_dir_label.setText("Output: Same folder as originals")
            self.output_dir_label.setStyleSheet("color: #666;")
            self.output_dir_label.setToolTip("Resized images will be saved in the same folder as originals\nwith '_resized' suffix")
    
    def set_preset(self, width, height):
        self.width_spin.setValue(width)
        self.height_spin.setValue(height)
    
    def resize_images(self):
        if not self.image_paths:
            return
            
        self.progress_bar.setVisible(True)
        self.progress_bar.setMaximum(len(self.image_paths))
        self.progress_bar.setValue(0)
        
        width = self.width_spin.value()
        height = self.height_spin.value()
        
        # Create output directory if it doesn't exist
        if self.output_dir and not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
        
        for i, path in enumerate(self.image_paths, 1):
            try:
                img = Image.open(path)
                resized_img = self.resize_image(img, width, height)
                
                # Determine output path
                if self.output_dir:
                    filename = os.path.basename(path)
                    base, ext = os.path.splitext(filename)
                    output_path = os.path.join(self.output_dir, f"{base}_resized{ext}")
                else:
                    base, ext = os.path.splitext(path)
                    output_path = f"{base}_resized{ext}"
                
                resized_img.save(output_path)
                self.progress_bar.setValue(i)
                
            except Exception as e:
                print(f"Error processing {path}: {str(e)}")
        
        self.progress_bar.setVisible(False)
        
        # Show completion message with output info
        if self.output_dir:
            msg = f"Processed {len(self.image_paths)} images to:\n{self.output_dir}"
        else:
            msg = f"Processed {len(self.image_paths)} images to original folders"
            
        self.file_label.setText(msg)
        self.file_label.setStyleSheet("color: #009900; font-weight: bold;")
    
    def resizeEvent(self, event):
        # Update preview when window is resized
        self.update_preview()
        super().resizeEvent(event)
