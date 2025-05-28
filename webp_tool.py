import os
import sys
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple

from PIL import Image, ImageFile
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QSize, QTimer, QBuffer
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
                           QFileDialog, QSpinBox, QComboBox, QCheckBox, QProgressBar,
                           QMessageBox, QGroupBox, QSizePolicy, QSpacerItem, QScrollArea,
                           QGridLayout, QRadioButton, QButtonGroup, QSplitter)

# Import utility modules
from utils.ui_components import ThumbnailLabel, FileControls, ImagePreviewGallery
from utils.preview import PreviewManager
from utils.image_utils import (
    load_image,
    save_image,
    get_image_info,
)
from utils.file_utils import (
    get_file_size,
    create_directory
)

class WebPConverterTool(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Initialize instance variables
        self.input_files: List[str] = []
        self.current_preview = None
        self.current_path: Optional[str] = None
        self.output_dir = str(Path.home() / "Pictures" / "WebP_Converted")
        
        # Create output directory using utility function
        success, message = create_directory(self.output_dir)
        if not success:
            # If default directory creation fails, try fallback to Pictures
            self.output_dir = str(Path.home() / "Pictures" / "WebP_Converted")
            success, message = create_directory(self.output_dir)
            if not success:
                # If still failing, use system temp directory as last resort
                import tempfile
                self.output_dir = str(Path(tempfile.gettempdir()) / "imageconverter" / "webp_converted")
                success, message = create_directory(self.output_dir)
                if not success:
                    print(f"Warning: Could not create output directory: {message}")
        
        # Initialize preview manager
        self.preview_manager = PreviewManager()
        
        self.init_ui()
        
    def init_ui(self):
        """Initialize the user interface."""
        # Main layout
        main_layout = QHBoxLayout(self)
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
        
        # File info
        self.file_info_label = QLabel("No file selected")
        self.file_info_label.setAlignment(Qt.AlignCenter)
        self.file_info_label.setStyleSheet("font-size: 11px; color: #555;")
        preview_layout.addWidget(self.file_info_label)
        
        # Add conversion info
        self.conversion_info = QLabel()
        self.conversion_info.setAlignment(Qt.AlignCenter)
        self.conversion_info.setStyleSheet("font-size: 11px; color: #777;")
        preview_layout.addWidget(self.conversion_info)
        
        preview_group.setLayout(preview_layout)
        
        # Right panel - Controls
        control_group = QGroupBox("WebP Conversion Settings")
        control_layout = QVBoxLayout(control_group)
        control_layout.setSpacing(15)
        
        # File controls
        self.file_controls = FileControls(
            on_browse=self.add_files,
            on_clear=self.clear_files,
            parent=self
        )
        control_layout.addWidget(self.file_controls)
        
        # Conversion direction
        direction_group = QGroupBox("Conversion Direction")
        direction_layout = QVBoxLayout(direction_group)
        
        self.to_webp_radio = QRadioButton("To WebP")
        self.from_webp_radio = QRadioButton("From WebP")
        self.to_webp_radio.setChecked(True)
        
        direction_layout.addWidget(self.to_webp_radio)
        direction_layout.addWidget(self.from_webp_radio)
        
        # Format selection (for From WebP)
        self.format_group = QGroupBox("Output Format")
        format_layout = QHBoxLayout(self.format_group)
        
        self.format_combo = QComboBox()
        self.format_combo.addItems(["PNG", "JPEG", "BMP", "TIFF"])
        format_layout.addWidget(QLabel("Format:"))
        format_layout.addWidget(self.format_combo)
        
        # Quality settings
        quality_group = QGroupBox("Quality Settings")
        quality_layout = QVBoxLayout(quality_group)
        
        self.quality_slider = QSpinBox()
        self.quality_slider.setRange(1, 100)
        self.quality_slider.setValue(90)
        self.quality_slider.setSuffix("%")
        
        quality_layout.addWidget(QLabel("Quality:"))
        quality_layout.addWidget(self.quality_slider)
        
        # Lossless option (WebP only)
        self.lossless_check = QCheckBox("Lossless")
        quality_layout.addWidget(self.lossless_check)
        
        # Metadata options
        self.metadata_check = QCheckBox("Preserve Metadata")
        self.metadata_check.setChecked(True)
        
        # Add widgets to control layout
        control_layout.addWidget(direction_group)
        control_layout.addWidget(self.format_group)
        control_layout.addWidget(quality_group)
        control_layout.addWidget(self.metadata_check)
        control_layout.addStretch()
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        
        # Convert button
        self.convert_btn = QPushButton("Convert")
        self.convert_btn.clicked.connect(self.start_conversion)
        self.convert_btn.setEnabled(False)
        
        # Add panels to main layout with stretch factors
        main_layout.addWidget(preview_group, 3)  # 3/4 width for preview
        main_layout.addWidget(control_group, 1)  # 1/4 width for controls
        main_layout.addWidget(self.progress_bar)
        main_layout.addWidget(self.convert_btn)
        
        # Connect signals
        self.to_webp_radio.toggled.connect(self.update_ui_state)
        self.from_webp_radio.toggled.connect(self.update_ui_state)
        
        # Initial UI state
        self.update_ui_state()
    
    def update_ui_state(self):
        """Update UI elements based on current state."""
        is_to_webp = self.to_webp_radio.isChecked()
        self.format_group.setVisible(not is_to_webp)
        self.lossless_check.setVisible(is_to_webp)
    
    def add_files(self):
        """Open file dialog to select images."""
        file_dialog = QFileDialog()
        file_dialog.setFileMode(QFileDialog.ExistingFiles)
        file_dialog.setNameFilter("Images (*.png *.jpg *.jpeg *.webp *.bmp)")
        
        if file_dialog.exec_():
            file_paths = file_dialog.selectedFiles()
            if file_paths:
                self.input_files = file_paths
                self.current_path = file_paths[0]  # Show first file in preview
                self.update_thumbnails()
                self.update_preview()
                self.convert_btn.setEnabled(True)
                self.file_controls.update_file_count(len(file_paths))
    
    def update_thumbnails(self):
        """Update the thumbnail gallery with current images."""
        # Clear existing thumbnails
        while self.thumbnail_layout.count():
            item = self.thumbnail_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Add new thumbnails
        for i, path in enumerate(self.input_files):
            try:
                # Create thumbnail container
                thumb_container = QWidget()
                thumb_layout = QVBoxLayout()
                thumb_container.setLayout(thumb_layout)
                
                # Create thumbnail using PreviewManager
                thumbnail = ThumbnailLabel()
                
                # Get image info
                img = load_image(path)
                if img:
                    width, height = img.size
                    file_size = os.path.getsize(path) / 1024  # KB
                    
                    # Create thumbnail
                    thumb_img = img.copy()
                    thumb_img.thumbnail((100, 100), Image.Resampling.LANCZOS)
                    
                    # Convert to QPixmap
                    thumb_img = thumb_img.convert("RGBA")
                    data = thumb_img.tobytes("raw", "RGBA")
                    qimg = QImage(data, thumb_img.size[0], thumb_img.size[1], QImage.Format_RGBA8888)
                    pixmap = QPixmap.fromImage(qimg)
                    thumbnail.setPixmap(pixmap)
                    
                    # Add info label
                    info_label = QLabel(f"{width}x{height}\n{file_size:.1f} KB")
                    info_label.setAlignment(Qt.AlignCenter)
                    info_label.setStyleSheet("font-size: 9px; color: #666;")
                    
                    # Add to container
                    thumb_layout.addWidget(thumbnail)
                    thumb_layout.addWidget(info_label)
                    
                    # Make clickable
                    thumb_container.mousePressEvent = lambda e, p=path: self.thumbnail_clicked(p)
                    thumb_container.setToolTip(
                        f"{os.path.basename(path)}\n"
                        f"{width}x{height} pixels\n"
                        f"{file_size:.1f} KB"
                    )
                    
                    # Highlight current selection
                    if path == self.current_path:
                        thumb_container.setStyleSheet("border: 2px solid #0078d7;")
                    
                    # Add to grid (3 columns)
                    row = i // 3
                    col = i % 3
                    self.thumbnail_layout.addWidget(thumb_container, row, col)
                    
                    # Show first image in main preview
                    if i == 0 and self.current_path is None:
                        self.thumbnail_clicked(path)
                        
            except Exception as e:
                print(f"Error creating thumbnail for {path}: {e}")
    
    def thumbnail_clicked(self, path):
        """Handle thumbnail click event."""
        self.current_path = path
        self.update_thumbnails()  # Update highlights
        self.update_preview()

    def update_preview(self):
        """Update the preview with the current image."""
        if not self.current_path or not os.path.exists(self.current_path):
            self.main_preview.clear()
            self.main_preview.setText("No preview available")
            self.file_info_label.setText("No file selected")
            return

        try:
            with Image.open(self.current_path) as img:
                width, height = img.size
                file_size = os.path.getsize(self.current_path) / 1024  # KB
                img_format = img.format or 'Unknown'
                
                # Display info
                self.file_info_label.setText(
                    f"{os.path.basename(self.current_path)}"
                    f"\n{width} × {height} • {file_size:.1f} KB • {img_format}"
                )
                
                # Create preview image that fits in the preview area
                preview_size = self.main_preview.size()
                if preview_size.isValid() and preview_size.width() > 1 and preview_size.height() > 1:
                    # Calculate size to maintain aspect ratio
                    preview_width = preview_size.width() - 20
                    preview_height = preview_size.height() - 20
                    
                    # Calculate aspect ratio
                    img_ratio = width / height
                    preview_ratio = preview_width / preview_height
                    
                    if img_ratio > preview_ratio:
                        # Image is wider than preview area
                        new_width = preview_width
                        new_height = int(new_width / img_ratio)
                    else:
                        # Image is taller than preview area
                        new_height = preview_height
                        new_width = int(new_height * img_ratio)
                    
                    # Create preview image
                    preview_img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                    
                    # Convert to QPixmap
                    preview_img = preview_img.convert("RGBA")
                    data = preview_img.tobytes("raw", "RGBA")
                    qimg = QImage(data, preview_img.size[0], preview_img.size[1], QImage.Format_RGBA8888)
                    pixmap = QPixmap.fromImage(qimg)
                    
                    # Set the pixmap
                    self.main_preview.setPixmap(pixmap)
                    
        except Exception as e:
            print(f"Error updating preview: {e}")
            self.main_preview.clear()
            self.main_preview.setText("Error loading preview")
            self.file_info_label.setText(f"Error: {str(e)}")
    
    
    def clear_files(self):
        """Clear all selected files."""
        self.input_files = []
        self.current_path = None
        self.preview_label.clear()
        self.file_info_label.setText("No file selected")
        self.convert_btn.setEnabled(False)
        self.progress_bar.setValue(0)
    
    def get_output_path(self, input_path):
        """Generate output path based on input path and selected format."""
        base_name = os.path.splitext(os.path.basename(input_path))[0]
        
        if self.to_webp_radio.isChecked():
            ext = ".webp"
        else:
            ext = f".{self.format_combo.currentText().lower()}"
            
        output_path = os.path.join(self.output_dir, f"{base_name}{ext}")
        return get_unique_filename(output_path)
    
    def start_conversion(self):
        """Start the conversion process."""
        if not self.input_files:
            QMessageBox.warning(self, "No Files", "Please select files to convert.")
            return
            
        # Disable UI during conversion
        self.set_ui_enabled(False)
        self.progress_bar.setRange(0, len(self.input_files))
        self.progress_bar.setValue(0)
        
        # Get conversion parameters
        to_webp = self.to_webp_radio.isChecked()
        quality = self.quality_slider.value()
        lossless = self.lossless_check.isChecked()
        preserve_metadata = self.metadata_check.isChecked()
        output_format = self.format_combo.currentText().upper() if not to_webp else "WEBP"
        
        # Create and start worker thread
        self.worker = WebPConversionWorker(
            input_files=self.input_files,
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
        
        # Start the worker thread
        self.worker.start()
    
    def set_ui_enabled(self, enabled):
        """Enable or disable UI elements during conversion."""
        self.file_controls.setEnabled(enabled)
        self.convert_btn.setEnabled(enabled and bool(self.input_files))
        self.to_webp_radio.setEnabled(enabled)
        self.from_webp_radio.setEnabled(enabled)
        self.format_combo.setEnabled(enabled)
        self.quality_slider.setEnabled(enabled)
        self.lossless_check.setEnabled(enabled)
        self.metadata_check.setEnabled(enabled)
    
    def update_progress(self, value):
        """Update progress bar value."""
        self.progress_bar.setValue(value)
    
    def conversion_finished(self):
        """Handle completion of conversion process."""
        self.set_ui_enabled(True)
        QMessageBox.information(self, "Conversion Complete", 
                              f"Successfully converted {len(self.input_files)} files.")
    
    def show_error(self, message):
        """Show error message to the user."""
        QMessageBox.critical(self, "Conversion Error", message)
        self.set_ui_enabled(True)


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
            for i, input_path in enumerate(self.input_files, 1):
                if not self.is_running:
                    break
                    
                try:
                    if self.to_webp:
                        self.convert_to_webp(input_path, i)
                    else:
                        self.convert_from_webp(input_path, i)
                except Exception as e:
                    self.error_occurred.emit(f"Error processing {os.path.basename(input_path)}: {str(e)}")
                
                self.progress_updated.emit(i)
            
            if self.is_running:
                self.finished.emit()
                
        except Exception as e:
            self.error_occurred.emit(f"Unexpected error: {str(e)}")
    
    def convert_to_webp(self, input_path, index):
        """Convert an image to WebP format."""
        try:
            # Load the image
            img = load_image(input_path)
            if img is None:
                raise Exception("Failed to load image")
            
            # Get output path
            base_name = os.path.splitext(os.path.basename(input_path))[0]
            output_path = os.path.join(self.output_dir, f"{base_name}.webp")
            output_path = get_unique_filename(output_path)
            
            # Prepare save options
            save_options = {
                'quality': self.quality,
                'lossless': self.lossless,
                'method': 6  # Default method (0=fast, 6=slower but better)
            }
            
            # Preserve metadata if requested
            if self.preserve_metadata and hasattr(img, 'info'):
                save_options.update(img.info)
            
            # Save as WebP
            if not save_image(img, output_path, format='WEBP', **save_options):
                raise Exception("Failed to save WebP image")
                
        except Exception as e:
            raise Exception(f"Error converting to WebP: {str(e)}")
    
    def convert_from_webp(self, input_path, index):
        """Convert a WebP image to another format."""
        try:
            # Load the WebP image
            img = load_image(input_path)
            if img is None:
                raise Exception("Failed to load WebP image")
            
            # Get output path with new extension
            base_name = os.path.splitext(os.path.basename(input_path))[0]
            output_path = os.path.join(self.output_dir, f"{base_name}.{self.output_format.lower()}")
            output_path = get_unique_filename(output_path)
            
            # Prepare save options
            save_options = {'quality': self.quality}
            
            # Preserve metadata if requested
            if self.preserve_metadata and hasattr(img, 'info'):
                save_options.update(img.info)
            
            # Save in target format
            if not save_image(img, output_path, format=self.output_format, **save_options):
                raise Exception(f"Failed to save as {self.output_format}")
                
        except Exception as e:
            raise Exception(f"Error converting from WebP: {str(e)}")
    
    def stop(self):
        """Stop the conversion process."""
        self.is_running = False
        self.wait()

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
        main_layout = QHBoxLayout()
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(5, 5, 5, 5)
        
        # Left panel - Preview
        preview_group = QGroupBox("Preview Gallery")
        preview_group.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        preview_layout = QVBoxLayout()
        
        # Thumbnail scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)  # Disable horizontal scroll
        
        self.thumbnail_container = QWidget()
        self.thumbnail_container.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        
        # Thumbnail container with grid layout
        self.thumbnail_container = QWidget()
        self.thumbnail_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.thumbnail_layout = QGridLayout()
        self.thumbnail_layout.setSpacing(5)
        self.thumbnail_layout.setContentsMargins(5, 5, 5, 5)
        self.thumbnail_container.setLayout(self.thumbnail_layout)
        
        # Add container to scroll area
        scroll.setWidget(self.thumbnail_container)
        preview_layout.addWidget(scroll, stretch=1)
        
        # Main preview
        self.main_preview = QLabel()
        self.main_preview.setAlignment(Qt.AlignCenter)
        self.main_preview.setMinimumSize(300, 250)
        self.main_preview.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.main_preview.setStyleSheet("""
            background-color: #f5f5f5;
            border: 1px solid #ddd;
            border-radius: 4px;
        """)
        preview_layout.addWidget(QLabel("Selected Preview:"))
        preview_layout.addWidget(self.main_preview, stretch=2)
        
        # Add info labels below main preview
        self.size_info = QLabel()
        self.size_info.setAlignment(Qt.AlignCenter)
        self.size_info.setStyleSheet("font-size: 10px; color: #555;")
        preview_layout.addWidget(self.size_info)
        
        # Add format info
        self.format_info = QLabel()
        self.format_info.setAlignment(Qt.AlignCenter)
        self.format_info.setStyleSheet("font-size: 10px; color: #777;")
        preview_layout.addWidget(self.format_info)
        
        preview_group.setLayout(preview_layout)
        
        # Right panel - Controls
        control_group = QGroupBox("Controls")
        control_layout = QVBoxLayout()
        
        # Input selection
        input_group = QGroupBox("Input")
        input_layout = QVBoxLayout()
        
        btn_layout = QHBoxLayout()
        self.btn_select_files = QPushButton("Select Image(s)")
        self.btn_select_files.clicked.connect(self.select_files)
        self.btn_clear_files = QPushButton("Clear")
        self.btn_clear_files.clicked.connect(self.clear_files)
        
        btn_layout.addWidget(self.btn_select_files)
        btn_layout.addWidget(self.btn_clear_files)
        
        self.lbl_selected_files = QLabel("No files selected")
        self.lbl_selected_files.setWordWrap(True)
        
        input_layout.addLayout(btn_layout)
        input_layout.addWidget(self.lbl_selected_files)
        input_group.setLayout(input_layout)
        
        # Conversion settings
        settings_group = QGroupBox("Conversion Settings")
        settings_layout = QVBoxLayout()
        
        # Conversion direction
        direction_group = QGroupBox("Conversion Direction")
        direction_layout = QHBoxLayout()
        
        self.btn_group_direction = QButtonGroup(self)
        self.radio_to_webp = QRadioButton("To WebP")
        self.radio_to_webp.setChecked(True)
        self.radio_from_webp = QRadioButton("From WebP")
        
        self.btn_group_direction.addButton(self.radio_to_webp)
        self.btn_group_direction.addButton(self.radio_from_webp)
        
        direction_layout.addWidget(self.radio_to_webp)
        direction_layout.addWidget(self.radio_from_webp)
        direction_group.setLayout(direction_layout)
        
        # Quality settings
        quality_layout = QHBoxLayout()
        quality_layout.addWidget(QLabel("Quality (%):"))
        self.spin_quality = QSpinBox()
        self.spin_quality.setRange(1, 100)
        self.spin_quality.setValue(80)
        quality_layout.addWidget(self.spin_quality)
        
        # Output format (when converting from WebP)
        format_layout = QHBoxLayout()
        format_layout.addWidget(QLabel("Output Format:"))
        self.cmb_format = QComboBox()
        self.cmb_format.addItems(["JPEG", "PNG"])
        format_layout.addWidget(self.cmb_format)
        
        # Output directory
        dir_layout = QHBoxLayout()
        
        # Create widgets
        self.lbl_output_dir = QLabel()
        self.btn_change_dir = QPushButton("Change")
        
        # Configure widgets
        self.lbl_output_dir.setWordWrap(True)
        self.lbl_output_dir.setText(f"Output: {self.output_dir}")
        self.btn_change_dir.clicked.connect(self.change_output_dir)
        
        # Add to layout
        dir_layout.addWidget(QLabel("Output Directory:"))
        dir_layout.addWidget(self.lbl_output_dir, 1)
        dir_layout.addWidget(self.btn_change_dir)
        
        # Options
        self.chk_preserve_metadata = QCheckBox("Preserve metadata")
        self.chk_preserve_metadata.setChecked(True)
        
        self.chk_lossless = QCheckBox("Lossless compression")
        self.chk_lossless.stateChanged.connect(self.toggle_lossless)
        
        settings_layout.addWidget(direction_group)
        settings_layout.addLayout(quality_layout)
        settings_layout.addLayout(format_layout)
        settings_layout.addLayout(dir_layout)
        settings_layout.addWidget(self.chk_preserve_metadata)
        settings_layout.addWidget(self.chk_lossless)
        settings_group.setLayout(settings_layout)
        
        # Progress
        self.progress = QProgressBar()
        self.progress.setVisible(False)
        
        # Convert button
        self.btn_convert = QPushButton("Convert Images")
        self.btn_convert.clicked.connect(self.start_conversion)
        
        # Add widgets to control layout
        control_layout.addWidget(input_group)
        control_layout.addWidget(settings_group)
        control_layout.addWidget(self.progress)
        control_layout.addWidget(self.btn_convert)
        control_layout.addStretch()
        
        # Set up control group
        control_group.setLayout(control_layout)
        control_group.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        
        # Add both panels to main layout
        main_layout.addWidget(preview_group, stretch=2)
        main_layout.addWidget(control_group, stretch=1)
        
        self.setLayout(main_layout)
        
        # Update UI based on initial state
        self.update_ui_for_conversion()
        
        # Connect signals
        self.radio_to_webp.toggled.connect(self.update_ui_for_conversion)
    
    def toggle_lossless(self, state):
        self.spin_quality.setEnabled(state == Qt.Unchecked)
    
    def update_ui_for_conversion(self):
        to_webp = self.radio_to_webp.isChecked()
        self.cmb_format.setEnabled(not to_webp)
        
        if to_webp:
            self.chk_lossless.setEnabled(True)
            self.chk_lossless.setChecked(False)
            self.spin_quality.setEnabled(True)
        else:
            self.chk_lossless.setEnabled(False)
            self.chk_lossless.setChecked(False)
            self.spin_quality.setEnabled(True)
        
        # Update file filter and clear current selection
        self.input_files = []
        self.lbl_selected_files.setText("No files selected")
        self.clear_thumbnails()
    
    def clear_thumbnails(self):
        # Clear existing thumbnails
        for i in reversed(range(self.thumbnail_layout.count())):
            item = self.thumbnail_layout.itemAt(i)
            if item.widget():
                item.widget().deleteLater()
        
        self.current_preview = None
        self.current_path = None
        self.main_preview.clear()
        self.size_info.clear()
        self.format_info.clear()
    
    def clear_files(self):
        self.input_files = []
        self.lbl_selected_files.setText("No files selected")
        self.clear_thumbnails()
        
    def select_files(self):
        # Get file filter based on conversion direction
        if self.radio_to_webp.isChecked():
            file_filter = "Images (*.png *.jpg *.jpeg *.bmp *.tiff *.gif)"
        else:
            file_filter = "WebP Images (*.webp)"
            
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Select Images",
            "",
            file_filter
        )
        
        if files:
            self.input_files = files
            file_count = len(files)
            if file_count == 1:
                self.lbl_selected_files.setText(f"1 file selected: {os.path.basename(files[0])}")
            else:
                self.lbl_selected_files.setText(f"{file_count} files selected")
            
            # Update the thumbnails
            self.update_thumbnail_layout()
            
            # Select first image by default
            if files:
                self.thumbnail_clicked(files[0])
    
    def update_preview(self, image_path):
        try:
            # Update main preview
            pixmap = QPixmap(image_path)
            if not pixmap.isNull():
                # Scale the pixmap to fit the preview area while maintaining aspect ratio
                scaled_pixmap = pixmap.scaled(
                    self.main_preview.width(),
                    self.main_preview.height(),
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
                )
                self.main_preview.setPixmap(scaled_pixmap)
                self.main_preview.setAlignment(Qt.AlignCenter)
                
                # Update image info
                img = Image.open(image_path)
                width, height = img.size
                self.size_info.setText(f"{width} × {height} px • {os.path.getsize(image_path) / 1024:.1f} KB")
                self.format_info.setText(f"Format: {img.format}" if img.format else "Format: Unknown")
                
                self.current_path = image_path
                return True
        except Exception as e:
            print(f"Error loading preview: {e}")
        return False
    
    def thumbnail_clicked(self, path):
        if self.update_preview(path):
            # Update selection
            for i in range(self.thumbnail_layout.count()):
                item = self.thumbnail_layout.itemAt(i)
                if item and item.widget():
                    item.widget().setStyleSheet(
                        "border: 2px solid #2196F3;" if item.widget().property("path") == path 
                        else "border: 1px solid #ddd;"
                    )
    
    def update_thumbnail_layout(self):
        # Clear existing thumbnails
        for i in reversed(range(self.thumbnail_layout.count())): 
            self.thumbnail_layout.itemAt(i).widget().setParent(None)
        
        # Create new thumbnails
        for i, path in enumerate(self.input_files):
            try:
                # Get image info
                img = Image.open(path)
                width, height = img.size
                file_size = os.path.getsize(path) / 1024  # KB
                
                # Create thumbnail container
                thumb_container = QWidget()
                thumb_container.setStyleSheet("""
                    QWidget {
                        background: transparent;
                        margin: 2px;
                        padding: 4px;
                    }
                """)
                thumb_layout = QVBoxLayout()
                thumb_layout.setContentsMargins(0, 0, 0, 0)
                thumb_layout.setSpacing(4)
                thumb_layout.setAlignment(Qt.AlignCenter)
                thumb_container.setLayout(thumb_layout)
                
                # Create thumbnail image
                thumb_img = img.copy()
                thumb_img.thumbnail((120, 120))  # Fixed thumbnail size
                
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
                info_label = QLabel(f"{width}×{height} • {file_size:.1f} KB")
                info_label.setAlignment(Qt.AlignCenter)
                info_label.setStyleSheet("""
                    QLabel {
                        font-size: 9px; 
                        color: #666;
                        background: transparent;
                        padding: 2px 0;
                    }
                """)
                thumb_layout.addWidget(info_label, alignment=Qt.AlignCenter)
                
                # Make clickable
                thumb_container.mousePressEvent = lambda e, p=path: self.thumbnail_clicked(p)
                thumb_container.setToolTip(f"{os.path.basename(path)}\n{width}×{height} pixels\n{file_size:.1f} KB")
                
                # Add to grid (3 columns)
                row = i // 3
                col = i % 3
                self.thumbnail_layout.addWidget(thumb_container, row, col)
                
                # Show first image in main preview
                if i == 0:
                    self.thumbnail_clicked(path)
                    
            except Exception as e:
                print(f"Error loading thumbnail for {path}: {str(e)}")
    
    def create_thumbnail(self, image_path, index):
        # Just add the file to input_files and update the layout
        if image_path not in self.input_files:
            self.input_files.append(image_path)
        self.update_thumbnail_layout()
        
        # Select first image by default
        if index == 0:
            self.thumbnail_clicked(image_path)
            
    def change_output_dir(self):
        try:
            dir_path = QFileDialog.getExistingDirectory(self, "Select Output Directory", self.output_dir)
            if dir_path:
                self.output_dir = dir_path
                self.lbl_output_dir.setText(f"Output: {self.output_dir}")
        except Exception as e:
            print(f"Error changing output directory: {e}")
    
    def start_conversion(self):
        if not self.input_files:
            QMessageBox.warning(self, "No Files Selected", "Please select at least one image file.")
            return
        
        # Disable UI during conversion
        self.set_ui_enabled(False)
        self.progress.setVisible(True)
        self.progress.setMaximum(len(self.input_files))
        self.progress.setValue(0)
        
        # Start conversion in a separate thread
        self.worker = WebPConversionWorker(
            self.input_files,
            self.output_dir,
            self.radio_to_webp.isChecked(),
            self.spin_quality.value(),
            self.cmb_format.currentText().lower(),
            self.chk_preserve_metadata.isChecked(),
            self.chk_lossless.isChecked()
        )
        self.worker.progress_updated.connect(self.update_progress)
        self.worker.finished.connect(self.conversion_finished)
        self.worker.error_occurred.connect(self.handle_error)
        self.worker.start()
    
    def update_progress(self, value):
        self.progress.setValue(value)
    
    def conversion_finished(self):
        self.set_ui_enabled(True)
        self.progress.setVisible(False)
        QMessageBox.information(self, "Success", "Image conversion completed successfully!")
    
    def handle_error(self, error_msg):
        self.set_ui_enabled(True)
        self.progress.setVisible(False)
        QMessageBox.critical(self, "Error", error_msg)
    
    def update_progress(self, value):
        self.progress.setValue(value)
    
    def conversion_finished(self):
        self.set_ui_enabled(True)
        self.progress.setVisible(False)
        QMessageBox.information(self, "Success", "Image conversion completed successfully!")
    
    def set_ui_enabled(self, enabled):
        self.btn_select_files.setEnabled(enabled)
        self.btn_clear_files.setEnabled(enabled)
        self.btn_convert.setEnabled(enabled)
        self.radio_to_webp.setEnabled(enabled)
        self.radio_from_webp.setEnabled(enabled)
        self.spin_quality.setEnabled(enabled and not self.chk_lossless.isChecked())
        self.cmb_format.setEnabled(enabled and not self.radio_to_webp.isChecked())
        self.chk_preserve_metadata.setEnabled(enabled)
        self.chk_lossless.setEnabled(enabled and self.radio_to_webp.isChecked())
        self.btn_change_dir.setEnabled(enabled)


class WebPConversionWorker(QThread):
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
        try:
            for i, input_path in enumerate(self.input_files, 1):
                if not self.is_running:
                    break
                    
                try:
                    if self.to_webp:
                        self.convert_to_webp(input_path, i)
                    else:
                        self.convert_from_webp(input_path, i)
                    self.progress_updated.emit(i)
                except Exception as e:
                    self.error_occurred.emit(f"Error processing {os.path.basename(input_path)}: {str(e)}")
                    continue
            
            self.finished.emit()
        except Exception as e:
            self.error_occurred.emit(f"Unexpected error: {str(e)}")
    
    def convert_to_webp(self, input_path, index):
        try:
            # Open the image
            with Image.open(input_path) as img:
                # Preserve transparency if needed
                if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
                    img = img.convert('RGBA')
                else:
                    img = img.convert('RGB')
                
                # Prepare output path
                filename = os.path.splitext(os.path.basename(input_path))[0]
                output_path = os.path.join(self.output_dir, f"{filename}.webp")
                
                # Handle duplicate filenames
                counter = 1
                while os.path.exists(output_path):
                    output_path = os.path.join(self.output_dir, f"{filename}_{counter}.webp")
                    counter += 1
                
                # Save as WebP
                save_kwargs = {
                    'quality': self.quality,
                    'method': 6,  # Best quality, slower
                    'lossless': self.lossless
                }
                
                if self.lossless:
                    save_kwargs.pop('quality', None)
                
                # Preserve metadata if requested and possible
                if self.preserve_metadata and hasattr(img, 'info') and img.info:
                    save_kwargs['save_all'] = True
                
                img.save(output_path, **save_kwargs)
                
        except Exception as e:
            raise Exception(f"Failed to convert {os.path.basename(input_path)} to WebP: {str(e)}")
    
    def convert_from_webp(self, input_path, index):
        try:
            # Open the WebP image
            with Image.open(input_path) as img:
                # Prepare output path
                filename = os.path.splitext(os.path.basename(input_path))[0]
                output_path = os.path.join(self.output_dir, f"{filename}.{self.output_format.lower()}")
                
                # Handle duplicate filenames
                counter = 1
                while os.path.exists(output_path):
                    output_path = os.path.join(
                        self.output_dir, 
                        f"{filename}_{counter}.{self.output_format.lower()}"
                    )
                    counter += 1
                
                # Save in the target format
                save_kwargs = {}
                if self.output_format.upper() == 'JPEG':
                    save_kwargs = {
                        'quality': self.quality,
                        'optimize': True,
                        'progressive': True
                    }
                    # Convert to RGB if saving as JPEG
                    if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
                        background = Image.new('RGB', img.size, (255, 255, 255))
                        background.paste(img, mask=img.split()[3] if img.mode == 'RGBA' else None)
                        img = background
                    else:
                        img = img.convert('RGB')
                elif self.output_format.upper() == 'PNG':
                    save_kwargs = {
                        'optimize': True,
                        'compress_level': 9 - int((self.quality / 100) * 9)  # Map 1-100 to 9-0
                    }
                
                # Save the image
                img.save(output_path, **save_kwargs)
                
        except Exception as e:
            raise Exception(f"Failed to convert {os.path.basename(input_path)} from WebP: {str(e)}")
    
    def stop(self):
        self.is_running = False
