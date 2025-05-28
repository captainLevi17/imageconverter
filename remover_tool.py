import os
import io
import sys
import traceback
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                            QPushButton, QFileDialog, QCheckBox, QGroupBox, 
                            QProgressBar, QScrollArea, QGridLayout, QComboBox,
                            QSizePolicy, QRadioButton, QButtonGroup, QMessageBox,
                            QApplication, QColorDialog, QFrame)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QPixmap, QImage
from PIL import Image

# Initialize rembg related variables
REMBG_AVAILABLE = False
REMBG_ERROR = ""
remove_bg = None
session = None

# Try to import rembg and its dependencies
try:
    # First try to import onnxruntime with error handling
    try:
        import onnxruntime as ort
        
        # Try to get version info with fallback
        try:
            ort_version = getattr(ort, '__version__', 'unknown')
            print(f"ONNX Runtime version: {ort_version}")
            
            # Try to get available providers with fallback
            try:
                providers = ort.get_available_providers()
                print(f"Available providers: {providers}")
                
                # Set environment variable to use CPU if CUDA is not available
                if 'CUDAExecutionProvider' not in providers and 'DmlExecutionProvider' not in providers:
                    import os
                    os.environ['CUDA_VISIBLE_DEVICES'] = '-1'  # Force CPU
                    print("CUDA not available, falling back to CPU")
                
            except Exception as e:
                print(f"Could not get providers: {e}")
                import os
                os.environ['CUDA_VISIBLE_DEVICES'] = '-1'  # Force CPU as fallback
                
            # Now try to import rembg
            from rembg import new_session, remove as remove_bg_func
            
            # Test with a small model
            print("Creating new session with u2net model...")
            session = new_session('u2net')
            if session is not None:
                remove_bg = remove_bg_func
                REMBG_AVAILABLE = True
                print("Background Remover: Successfully initialized rembg with onnxruntime")
                
        except Exception as e:
            REMBG_ERROR = f"Failed to initialize rembg model: {str(e)}"
            print(f"rembg initialization error: {REMBG_ERROR}")
            traceback.print_exc()
            
    except ImportError as e:
        REMBG_ERROR = f"Failed to import onnxruntime: {str(e)}"
        print(f"onnxruntime import error: {REMBG_ERROR}")
        traceback.print_exc()
        
except Exception as e:
    REMBG_ERROR = f"Unexpected error: {str(e)}"
    print(f"Error initializing Background Remover: {REMBG_ERROR}")
    traceback.print_exc()

# If we couldn't initialize, provide more detailed error info
if not REMBG_AVAILABLE:
    if "No module named 'onnxruntime'" in REMBG_ERROR or "onnxruntime" in str(REMBG_ERROR).lower():
        REMBG_ERROR = ("onnxruntime is not properly installed. Try these commands:\n"
                      "pip uninstall -y onnxruntime onnxruntime-gpu\n"
                      "pip install onnxruntime==1.15.1\n"
                      "pip install rembg==2.0.50")
    elif "No module named 'rembg'" in REMBG_ERROR:
        REMBG_ERROR = "rembg is not installed. Please install it with: pip install rembg==2.0.50"
    
    print(f"\nBackground Remover is not available: {REMBG_ERROR}")

# Function to remove background using the Python API
def remove_background_pil(image, model_name='u2net'):
    """Remove background using rembg Python API"""
    global session
    
    if not REMBG_AVAILABLE or remove_bg is None:
        print("Background remover not available or not initialized")
        return None
        
    try:
        # Convert to bytes and process
        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format='PNG')
        img_byte_arr = img_byte_arr.getvalue()
        
        # Ensure we have a valid session
        if session is None:
            print("Creating new rembg session...")
            from rembg import new_session as create_new_session
            session = create_new_session(model_name)
        
        # Remove background
        print("Removing background...")
        result = remove_bg(img_byte_arr, session=session)
        
        if result is None:
            print("Failed to remove background - no result returned")
            return None
            
        # Convert back to PIL Image
        return Image.open(io.BytesIO(result)).convert('RGBA')
        
    except Exception as e:
        print(f"Error in remove_background_pil: {e}")
        traceback.print_exc()
        return None

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

class RemoverTool(QWidget):
    def __init__(self):
        super().__init__()
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.image_paths = []
        self.current_preview = None
        self.current_path = None
        self.output_dir = None
        
        # Initialize UI first
        self.init_ui()
        
        # Show error if rembg is not available
        if not REMBG_AVAILABLE:
            # Use a single-shot timer to show the error message after the UI is fully initialized
            from PyQt5.QtCore import QTimer
            QTimer.singleShot(100, self.show_initialization_error)
    
    def show_initialization_error(self):
        """Show initialization error message"""
        self.show_error_message(
            "Background Remover Not Available",
            f"The Background Remover tool requires additional dependencies.\n\n"
            f"Error: {REMBG_ERROR}\n\n"
            "Please make sure you have installed the required dependencies using:\n"
            "pip install rembg onnxruntime\n\n"
            "The tool will be available after restarting the application."
        )
    
    def show_error_message(self, title, message):
        """Show an error message dialog"""
        try:
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Critical)
            msg.setWindowTitle(title)
            msg.setText(message)
            msg.setStandardButtons(QMessageBox.Ok)
            msg.exec_()
        except Exception as e:
            print(f"Error showing message dialog: {e}")
    
    def show_success_message(self, title, message):
        """Show a success message dialog"""
        try:
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Information)
            msg.setWindowTitle(title)
            msg.setText(message)
            msg.setStandardButtons(QMessageBox.Ok)
            msg.exec_()
        except Exception as e:
            print(f"Error showing message dialog: {e}")
    
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
        control_group = QGroupBox("Background Removal Settings")
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
        
        # Output format selection
        format_layout = QHBoxLayout()
        format_layout.addWidget(QLabel("Output Format:"))
        self.format_combo = QComboBox()
        self.format_combo.addItems(["PNG", "JPEG", "WebP"])
        self.format_combo.setCurrentIndex(0)  # Default to PNG for transparency
        format_layout.addWidget(self.format_combo)
        
        # Background options
        bg_group = QGroupBox("Background Options")
        bg_layout = QVBoxLayout()
        
        self.bg_transparent = QRadioButton("Transparent (PNG only)")
        self.bg_white = QRadioButton("White")
        self.bg_black = QRadioButton("Black")
        self.bg_custom = QRadioButton("Custom Color")
        
        self.bg_white.setChecked(True)
        
        # Custom color selection
        self.custom_color = (255, 0, 0, 255)  # Default to red
        self.color_preview = QFrame()
        self.color_preview.setFixedSize(24, 24)
        self.color_preview.setStyleSheet("background-color: rgb(255, 0, 0); border: 1px solid #999;")
        
        self.select_color_btn = QPushButton("Choose Color")
        self.select_color_btn.clicked.connect(self.select_custom_color)
        self.select_color_btn.setEnabled(False)  # Disabled by default
        
        # Connect radio buttons to enable/disable color picker
        self.bg_custom.toggled.connect(lambda checked: self.select_color_btn.setEnabled(checked))
        
        # Layout for custom color selection
        custom_color_layout = QHBoxLayout()
        custom_color_layout.addWidget(self.bg_custom)
        custom_color_layout.addWidget(self.color_preview)
        custom_color_layout.addWidget(self.select_color_btn)
        custom_color_layout.addStretch()
        
        bg_layout.addWidget(self.bg_transparent)
        bg_layout.addWidget(self.bg_white)
        bg_layout.addWidget(self.bg_black)
        bg_layout.addLayout(custom_color_layout)
        bg_group.setLayout(bg_layout)
        
        # Model selection
        model_layout = QHBoxLayout()
        model_layout.addWidget(QLabel("Model:"))
        self.model_combo = QComboBox()
        self.model_combo.addItems(["u2net", "u2netp", "u2net_human_seg", "u2net_cloth_seg", "silueta"])
        self.model_combo.setCurrentIndex(0)  # Default to u2net
        model_layout.addWidget(self.model_combo)
        
        # Output directory
        self.output_dir_btn = QPushButton("Select Output Directory")
        self.output_dir_btn.clicked.connect(self.select_output_dir)
        self.output_dir_label = QLabel("Output: Same as input")
        
        # Process button
        process_btn = QPushButton("Remove Backgrounds")
        process_btn.clicked.connect(self.process_images)
        process_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 8px 16px;
                font-weight: bold;
                border-radius: 4px;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        
        # Add widgets to control layout
        control_layout.addWidget(self.file_label)
        control_layout.addLayout(file_btn_layout)
        control_layout.addSpacing(10)
        control_layout.addLayout(format_layout)
        control_layout.addSpacing(10)
        control_layout.addWidget(bg_group)
        control_layout.addSpacing(10)
        control_layout.addLayout(model_layout)
        control_layout.addSpacing(10)
        control_layout.addWidget(self.output_dir_btn)
        control_layout.addWidget(self.output_dir_label)
        control_layout.addStretch()
        control_layout.addWidget(process_btn)
        control_layout.addWidget(self.progress_bar)
        
        control_group.setLayout(control_layout)
        
        # Add panels to main layout
        main_layout.addWidget(preview_group, stretch=2)
        main_layout.addWidget(control_group, stretch=1)
        
        self.setLayout(main_layout)
    
    def browse_images(self):
        """Open file dialog to select images"""
        files, _ = QFileDialog.getOpenFileNames(
            self, "Select Images", "", 
            "Images (*.png *.jpg *.jpeg *.bmp *.tiff *.webp);;All Files (*)")
        
        if files:
            self.image_paths = list(set(self.image_paths + files))  # Remove duplicates
            self.update_thumbnails()
            self.update_file_label()
    
    def clear_images(self):
        """Clear all selected images"""
        self.image_paths = []
        self.current_preview = None
        self.current_path = None
        self.update_thumbnails()
        self.update_file_label()
        self.main_preview.clear()
        self.main_preview.setText("No image selected")
        self.size_info.clear()
    
    def update_thumbnails(self):
        """Update the thumbnail gallery"""
        # Clear existing thumbnails
        for i in reversed(range(self.thumbnail_layout.count())): 
            self.thumbnail_layout.itemAt(i).widget().setParent(None)
        
        # Add new thumbnails
        for i, path in enumerate(self.image_paths):
            try:
                # Create thumbnail (resize to 100px width, maintain aspect ratio)
                img = Image.open(path)
                img.thumbnail((100, 100), Image.Resampling.LANCZOS)
                
                # Convert PIL Image to QPixmap directly
                if img.mode != 'RGBA':
                    img = img.convert('RGBA')
                data = img.tobytes('raw', 'RGBA')
                qimage = QImage(data, img.size[0], img.size[1], QImage.Format_RGBA8888)
                pixmap = QPixmap.fromImage(qimage)

                # Create thumbnail label
                thumb = ThumbnailLabel()
                thumb.setPixmap(pixmap)
                thumb.setToolTip(os.path.basename(path))
                
                # Connect click event - pass only path to show_preview
                thumb.mousePressEvent = lambda e, p=path: self.show_preview(p)
                
                # Add to layout (2 columns)
                row = i // 2
                col = i % 2
                self.thumbnail_layout.addWidget(thumb, row, col)
                
            except Exception as e:
                print(f"Error loading thumbnail for {path}: {e}")
    
    def show_preview(self, path):
        """Show the selected image in the main preview"""
        self.current_path = path
        
        try:
            # Always load the original image for the main preview
            original_img = Image.open(path)
            original_width, original_height = original_img.size
            
            # Create a copy for manipulation as img.thumbnail modifies in-place
            img_to_display = original_img.copy()
            
            # Update main preview
            preview_widget_size = self.main_preview.size()
            
            # Calculate target size for the preview, ensuring it fits within the label
            # and maintains aspect ratio. Subtract some padding.
            target_width = preview_widget_size.width() - 20  # 10px padding on each side
            target_height = preview_widget_size.height() - 20 # 10px padding on top/bottom

            if target_width <= 0 or target_height <= 0:
                # If preview area is too small, use a fixed small thumbnail or show error
                print(f"Warning: Preview area ({preview_widget_size.width()}x{preview_widget_size.height()}) is too small for {path}. Using 100x100 thumbnail.")
                img_to_display.thumbnail((100, 100), Image.Resampling.LANCZOS)
            else:
                img_to_display.thumbnail((target_width, target_height), 
                                     Image.Resampling.LANCZOS)
            
            # Ensure the image is in a compatible mode (e.g., RGBA)
            if img_to_display.mode != 'RGBA':
                img_to_display = img_to_display.convert('RGBA')

            # Convert to QPixmap directly
            data = img_to_display.tobytes('raw', 'RGBA')
            qimage = QImage(data, img_to_display.size[0], img_to_display.size[1], QImage.Format_RGBA8888)
            pixmap_to_set = QPixmap.fromImage(qimage)

            if pixmap_to_set.isNull():
                print(f"Error: Created QPixmap is null for {path}")
                self.main_preview.setText(f"Error loading preview for\n{os.path.basename(path)}")
                self.size_info.setText(f"{original_width} × {original_height} px | Error")
                return

            self.main_preview.setPixmap(pixmap_to_set)
            
            # Update info with original image dimensions
            self.size_info.setText(f"{original_width} × {original_height} px | {os.path.basename(path)}")

        except FileNotFoundError:
            print(f"Error: File not found for preview {path}")
            self.main_preview.setText(f"File Not Found:\n{os.path.basename(path)}")
            self.size_info.setText("File Not Found")
        except Exception as e:
            print(f"Error loading preview for {path}: {e}")
            import traceback
            traceback.print_exc() # Print full traceback for debugging
            self.main_preview.setText(f"Error loading preview for\n{os.path.basename(path)}")
            self.size_info.setText("Error loading preview")
    
    def select_output_dir(self):
        """Select output directory for processed images"""
        dir_path = QFileDialog.getExistingDirectory(self, "Select Output Directory")
        if dir_path:
            self.output_dir = dir_path
            self.output_dir_label.setText(f"Output: {dir_path}")
    
    def select_custom_color(self):
        """Open color dialog to select a custom background color"""
        color = QColorDialog.getColor()
        if color.isValid():
            # Convert QColor to RGBA tuple
            self.custom_color = (color.red(), color.green(), color.blue(), 255)
            # Update color preview
            self.color_preview.setStyleSheet(
                f"background-color: rgb{self.custom_color[:3]}; "
                "border: 1px solid #999;"
            )
    
    def process_images(self):
        """Process all selected images to remove background"""
        if not REMBG_AVAILABLE:
            self.show_error_message(
                "Dependencies Not Found",
                "The Background Remover tool requires 'rembg' and 'onnxruntime' to be installed.\n\n"
                "Please install them using:\n"
                "pip install rembg onnxruntime\n\n"
                f"Error: {REMBG_ERROR}"
            )
            return
            
        if not self.image_paths:
            return
        
        # Get output format
        output_format = self.format_combo.currentText().lower()
        if self.bg_transparent.isChecked():
            output_format = 'png'  # Force PNG for transparency
        
        # Get model
        model_name = self.model_combo.currentText()
        
        # Process each image
        self.progress_bar.setMaximum(len(self.image_paths))
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(True)
        
        success_count = 0
        
        for i, img_path in enumerate(self.image_paths):
            try:
                # Update progress
                self.progress_bar.setValue(i + 1)
                QApplication.processEvents()  # Update UI
                
                # Load the image
                try:
                    image = Image.open(img_path).convert('RGB')
                except Exception as e:
                    print(f"Error loading image {img_path}: {e}")
                    continue
                
                # Process image using rembg
                output = remove_background_pil(image, model_name)
                
                if output is None:
                    print(f"Failed to process {img_path}")
                    continue
                
                # Apply background if needed
                if not self.bg_transparent.isChecked():
                    if self.bg_white.isChecked():
                        bg_color = (255, 255, 255, 255)
                    elif self.bg_black.isChecked():
                        bg_color = (0, 0, 0, 255)
                    else:  # Custom color
                        bg_color = self.custom_color
                    
                    background = Image.new('RGBA', output.size, bg_color)
                    output = Image.alpha_composite(background, output)
                
                # Save the result
                output_path = self.get_output_path(img_path, output_format)
                output.save(output_path, output_format.upper(), quality=95)
                
                success_count += 1
                
            except Exception as e:
                print(f"Error processing {img_path}: {e}")
                import traceback
                traceback.print_exc()
        
        self.progress_bar.setVisible(False)
        
        # Show completion message
        if success_count > 0:
            self.show_success_message(
                "Processing Complete", 
                f"Successfully processed {success_count} out of {len(self.image_paths)} images."
            )
        else:
            self.show_error_message(
                "Processing Failed",
                "Failed to process any images. Please check the console for error messages."
            )
        
        # Notify user
        # TODO: Add a notification or status message
    
    def remove_background(self, image_path, model_name):
        """Remove background using rembg"""
        with open(image_path, 'rb') as f:
            img_data = f.read()
        
        # Remove background
        output_data = remove_bg(img_data, model_name=model_name)
        
        # Convert to PIL Image
        return Image.open(io.BytesIO(output_data)).convert("RGBA")
    
    def get_output_path(self, input_path, output_format):
        """Generate output path for the processed image"""
        base_name = os.path.splitext(os.path.basename(input_path))[0]
        output_name = f"{base_name}_nobg.{output_format}"
        
        if self.output_dir:
            return os.path.join(self.output_dir, output_name)
        else:
            # Save in the same directory as input
            dir_name = os.path.dirname(input_path)
            return os.path.join(dir_name, output_name)
    
    def update_file_label(self):
        """Update the file count label"""
        count = len(self.image_paths)
        self.file_label.setText(f"{count} image{'s' if count != 1 else ''} selected")
        
        # Update process button state
        process_btn = self.findChild(QPushButton, "processButton")
        if process_btn:
            process_btn.setEnabled(count > 0)
