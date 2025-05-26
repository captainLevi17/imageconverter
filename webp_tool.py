import os
from pathlib import Path
from PIL import Image, ImageFile
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
                           QFileDialog, QSpinBox, QComboBox, QCheckBox, QProgressBar,
                           QMessageBox, QGroupBox, QSizePolicy, QSpacerItem, QRadioButton,
                           QButtonGroup)
from PyQt5.QtCore import Qt, QThread, pyqtSignal

class WebPConverterTool(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Initialize instance variables
        self.input_files = []
        self.output_dir = str(Path.home() / "Pictures" / "WebP_Converted")
        
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
        layout = QVBoxLayout()
        layout.setSpacing(15)
        
        # Input selection
        input_group = QGroupBox("Input")
        input_layout = QVBoxLayout()
        
        self.btn_select_files = QPushButton("Select Image(s)")
        self.btn_select_files.clicked.connect(self.select_files)
        self.lbl_selected_files = QLabel("No files selected")
        self.lbl_selected_files.setWordWrap(True)
        
        input_layout.addWidget(self.btn_select_files)
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
        
        # Add widgets to main layout
        layout.addWidget(input_group)
        layout.addWidget(settings_group)
        layout.addWidget(self.progress)
        layout.addWidget(self.btn_convert)
        layout.addStretch()
        
        self.setLayout(layout)
        
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
    
    def select_files(self):
        if self.radio_to_webp.isChecked():
            file_filter = "Images (*.jpg *.jpeg *.png *.bmp *.tiff);;All Files (*)"
        else:
            file_filter = "WebP Images (*.webp);;All Files (*)"
            
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
    
    def set_ui_enabled(self, enabled):
        self.btn_select_files.setEnabled(enabled)
        self.btn_convert.setEnabled(enabled)
        self.btn_change_dir.setEnabled(enabled)
        self.spin_quality.setEnabled(enabled and not self.chk_lossless.isChecked())
        self.cmb_format.setEnabled(enabled and not self.radio_to_webp.isChecked())
        self.chk_preserve_metadata.setEnabled(enabled)
        self.chk_lossless.setEnabled(enabled and self.radio_to_webp.isChecked())
        self.radio_to_webp.setEnabled(enabled)
        self.radio_from_webp.setEnabled(enabled)


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
