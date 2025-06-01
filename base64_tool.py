import base64
import os
import json
from io import BytesIO
from datetime import datetime

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QFileDialog, QScrollArea, QMessageBox, QApplication,
    QSizePolicy, QComboBox, QGroupBox, QFrame, QStyle, QFileDialog
)
from PyQt5.QtCore import Qt, QFileInfo
from PyQt5.QtGui import QPixmap, QImage
from PIL import Image


class Base64Tool(QWidget):
    def __init__(self):
        super().__init__()
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.current_image = None
        # Initialize buttons to None to prevent attribute errors
        self.copy_btn = None
        self.download_btn = None
        self.init_ui()
    
    def init_ui(self):
        # Main layout
        main_widget = QWidget()
        main_widget.setObjectName("base64ToolWidget")
        
        layout = QVBoxLayout(main_widget)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)
        
        # Image to Base64 section
        img_to_b64_group = QGroupBox("Image to Base64")
        img_to_b64_group.setObjectName("imgToB64Group")
        img_to_b64_layout = QVBoxLayout(img_to_b64_group)
        img_to_b64_layout.setSpacing(12)
        img_to_b64_layout.setContentsMargins(12, 12, 12, 12)
        
        # Image selection
        img_select_layout = QHBoxLayout()
        
        # Add a frame for the path display
        path_frame = QFrame()
        path_frame.setObjectName("pathFrame")
        path_layout = QHBoxLayout(path_frame)
        path_layout.setContentsMargins(0, 0, 0, 0)
        
        self.img_path_label = QLabel("No image selected")
        self.img_path_label.setObjectName("imgPathLabel")
        self.img_path_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        
        browse_btn = QPushButton("Browse Image")
        browse_btn.setIcon(self.style().standardIcon(getattr(self.style(), 'SP_DialogOpenButton')))
        browse_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        browse_btn.clicked.connect(self.browse_image)
        
        path_layout.addWidget(self.img_path_label)
        path_layout.addWidget(browse_btn)
        
        img_select_layout.addWidget(path_frame)
        img_to_b64_layout.addLayout(img_select_layout)
        
        # Image preview
        self.img_preview = QLabel()
        self.img_preview.setObjectName("imgPreview")
        self.img_preview.setProperty("preview", True)
        self.img_preview.setAlignment(Qt.AlignCenter)
        self.img_preview.setMinimumSize(300, 200)
        self.img_preview.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        img_to_b64_layout.addWidget(self.img_preview, stretch=1)
        
        # Base64 output
        output_group = QGroupBox("Base64 Output")
        output_group.setObjectName("outputGroup")
        output_layout = QVBoxLayout(output_group)
        output_layout.setContentsMargins(0, 12, 0, 0)
        
        self.b64_output = QTextEdit()
        self.b64_output.setObjectName("base64Output")
        self.b64_output.setReadOnly(True)
        self.b64_output.setPlaceholderText("Base64 encoded string will appear here")
        self.b64_output.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        output_layout.addWidget(self.b64_output)
        img_to_b64_layout.addWidget(output_group, stretch=2)
        
        # Format selection and buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(8)
        
        # Format selection
        format_label = QLabel("Output Format:")
        format_label.setObjectName("formatLabel")
        button_layout.addWidget(format_label)
        
        self.format_combo = QComboBox()
        self.format_combo.addItems(["TXT (Plain Text)", "JSON", "HTML"])
        self.format_combo.setObjectName("formatCombo")
        button_layout.addWidget(self.format_combo)
        
        button_layout.addStretch()
        
        # Copy buttons container
        copy_buttons_container = QHBoxLayout()
        copy_buttons_container.setSpacing(8)
        
        # Copy to Clipboard button
        copy_btn = QPushButton("Copy to Clipboard")
        copy_btn.setIcon(self.style().standardIcon(getattr(self.style(), 'SP_DialogSaveButton')))
        copy_btn.clicked.connect(self.copy_to_clipboard)
        
        # Copy HTML Snippet button
        copy_html_btn = QPushButton("Copy HTML Snippet")
        copy_html_btn.setIcon(self.style().standardIcon(getattr(self.style(), 'SP_DialogSaveButton')))
        copy_html_btn.clicked.connect(self.copy_html_snippet)
        
        # Add copy buttons to container
        copy_buttons_container.addWidget(copy_btn)
        copy_buttons_container.addWidget(copy_html_btn)
        
        # Download button
        download_btn = QPushButton("Download")
        download_btn.setIcon(self.style().standardIcon(getattr(self.style(), 'SP_ArrowDown')))
        download_btn.clicked.connect(self.download_base64)
        
        # Add buttons with stretch
        button_layout.addLayout(copy_buttons_container)
        button_layout.addStretch()
        button_layout.addWidget(download_btn)
        
        img_to_b64_layout.addLayout(button_layout)
        
        layout.addWidget(img_to_b64_group, stretch=1)
        
        # Add a separator
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setObjectName("separator")
        layout.addWidget(separator)
        
        # Base64 to Image section
        b64_to_img_group = QGroupBox("Base64 to Image")
        b64_to_img_group.setObjectName("b64ToImgGroup")
        b64_to_img_layout = QVBoxLayout(b64_to_img_group)
        b64_to_img_layout.setSpacing(12)
        b64_to_img_layout.setContentsMargins(12, 12, 12, 12)
        
        # Base64 input
        input_group = QGroupBox("Base64 Input")
        input_group.setObjectName("inputGroup")
        input_layout = QVBoxLayout(input_group)
        input_layout.setContentsMargins(0, 12, 0, 0)
        
        self.b64_input = QTextEdit()
        self.b64_input.setObjectName("base64Input")
        self.b64_input.setPlaceholderText("Paste Base64 encoded string here")
        self.b64_input.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        input_layout.addWidget(self.b64_input)
        b64_to_img_layout.addWidget(input_group, stretch=2)
        
        # Save button
        save_btn = QPushButton("Decode and Save Image")
        save_btn.setIcon(self.style().standardIcon(getattr(self.style(), 'SP_DialogSaveButton')))
        save_btn.clicked.connect(self.save_decoded_image)
        
        # Button container to center the save button
        btn_container = QWidget()
        btn_layout = QHBoxLayout(btn_container)
        btn_layout.setContentsMargins(0, 12, 0, 0)
        btn_layout.addStretch()
        btn_layout.addWidget(save_btn)
        btn_layout.addStretch()
        
        b64_to_img_layout.addWidget(btn_container)
        
        layout.addWidget(b64_to_img_group, stretch=1)
        
        # Set up scroll area
        scroll = QScrollArea()
        scroll.setWidget(main_widget)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)  # Remove the frame
        
        # Set scroll area as the central widget
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll)
    
    def browse_image(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Image", "", "Image Files (*.png *.jpg *.jpeg *.bmp *.gif)")
        if file_path:
            self.img_path_label.setText(os.path.basename(file_path))
            if self.display_image_preview(file_path):
                self.current_image = file_path
                # Encode the image to base64 after loading
                self.encode_to_base64(file_path)
            else:
                self.img_path_label.setText("No image selected")
                self.current_image = None
                self.b64_output.clear()
    
    def encode_to_base64(self, path):
        try:
            with open(path, 'rb') as img_file:
                # Read the image file and encode to base64
                img_data = img_file.read()
                base64_encoded = base64.b64encode(img_data).decode('utf-8')
                
                # Format the output based on the selected format
                format_type = self.format_combo.currentText()
                if format_type == "TXT (Plain Text)":
                    output = base64_encoded
                elif format_type == "JSON":
                    output = json.dumps({
                        "filename": os.path.basename(path),
                        "data": base64_encoded,
                        "mime_type": f"image/{os.path.splitext(path)[1][1:].lower()}"
                    }, indent=2)
                elif format_type == "HTML":
                    mime_type = f"image/{os.path.splitext(path)[1][1:].lower()}"
                    if mime_type == "image/jpg":
                        mime_type = "image/jpeg"
                    output = f'<img src="data:{mime_type};base64,{base64_encoded}" alt="Encoded Image">'
                
                # Update the output text area
                self.b64_output.setPlainText(output)
                
                # Safely enable the copy and download buttons if they exist
                if hasattr(self, 'copy_btn') and self.copy_btn is not None:
                    self.copy_btn.setEnabled(True)
                if hasattr(self, 'download_btn') and self.download_btn is not None:
                    self.download_btn.setEnabled(True)
                
                return True
                
        except Exception as e:
            error_msg = f"Could not encode image: {str(e)}"
            QMessageBox.warning(self, "Error", error_msg)
            import traceback
            print(f"Encoding error: {traceback.format_exc()}")
            return False
    
    def display_image_preview(self, path):
        try:
            # Open image with PIL to handle transparency
            pil_img = Image.open(path)
            
            # Convert to RGBA if not already
            if pil_img.mode != 'RGBA':
                pil_img = pil_img.convert('RGBA')
                
            # Create a white background
            background = Image.new('RGBA', pil_img.size, (255, 255, 255, 255))
            
            # Composite the image onto the white background
            pil_img = Image.alpha_composite(background, pil_img)
            
            # Resize for preview while maintaining aspect ratio
            pil_img.thumbnail((400, 400), Image.Resampling.LANCZOS)
            
            # Convert to QPixmap
            data = pil_img.tobytes('raw', 'RGBA')
            qimg = QImage(data, pil_img.size[0], pil_img.size[1], QImage.Format_RGBA8888)
            pixmap = QPixmap.fromImage(qimg)
            
            # Scale the image to fit the preview while maintaining aspect ratio
            self.img_preview.setPixmap(pixmap.scaled(
                self.img_preview.size(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            ))
            
            return True
            
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Could not load image: {str(e)}")
            import traceback
            print(f"Error details: {traceback.format_exc()}")
            return False
    
    def get_formatted_output(self, format_type=None):
        """Get the Base64 output in the specified format"""
        if format_type is None:
            format_type = self.format_combo.currentText()
        
        base64_str = self.b64_output.toPlainText()
        if not base64_str:
            return None
                
        if format_type.startswith("TXT"):
            return base64_str
        elif format_type == "JSON":
            return json.dumps({
                "filename": os.path.basename(self.img_path_label.text()),
                "timestamp": datetime.now().isoformat(),
                "base64": base64_str,
                "mime_type": f"image/{os.path.splitext(self.img_path_label.text())[1][1:].lower()}"
            }, indent=2)
        elif format_type == "HTML":
            mime_type = f"image/{os.path.splitext(self.img_path_label.text())[1][1:].lower()}"
            if mime_type == "image/jpg":
                mime_type = "image/jpeg"
            return f'<img src="data:{mime_type};base64,{base64_str}" alt="Base64 encoded image">'
        return None
    
    def copy_to_clipboard(self):
        formatted_output = self.get_formatted_output()
        if formatted_output is None:
            self.show_message("Error", "No data to copy", QMessageBox.Warning)
            return
                
        clipboard = QApplication.clipboard()
        clipboard.setText(formatted_output)
        self.show_message("Success", "Content copied to clipboard", QMessageBox.Information)
        
    def copy_html_snippet(self):
        """Copy the base64 data as an HTML img tag to clipboard"""
        if not hasattr(self, 'current_image') or not self.current_image:
            self.show_message("Error", "No image loaded", QMessageBox.Warning)
            return
                
        # Get the base64 string (without any formatting)
        base64_str = self.b64_output.toPlainText()
        if not base64_str:
            self.show_message("Error", "No base64 data available", QMessageBox.Warning)
            return
                
        # Create HTML img tag
        mime_type = f"image/{os.path.splitext(self.current_image)[1][1:].lower()}"
        if mime_type == "image/jpg":
            mime_type = "image/jpeg"
                
        html_snippet = f'<img src="data:{mime_type};base64,{base64_str}" alt="Base64 encoded image">'
            
        # Copy to clipboard
        clipboard = QApplication.clipboard()
        clipboard.setText(html_snippet)
        self.show_message("Success", "HTML snippet copied to clipboard", QMessageBox.Information)
        
    def show_message(self, title, message, icon=QMessageBox.Information):
        msg = QMessageBox()
        msg.setIcon(icon)
        msg.setWindowTitle(title)
        msg.setText(message)
            
        # Apply custom style to the message box
        msg.setStyleSheet("""
            QMessageBox {
                background-color: white;
            }
            QLabel {
                color: #2d3748;
                font-size: 14px;
            }
            QPushButton {
                background-color: #3182ce;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 6px;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #2c5282;
            }
        """)
            
        # Set a proper icon
        if icon == QMessageBox.Warning:
            msg.setIconPixmap(self.style().standardIcon(QStyle.SP_MessageBoxWarning).pixmap(32, 32))
        elif icon == QMessageBox.Information:
            msg.setIconPixmap(self.style().standardIcon(QStyle.SP_MessageBoxInformation).pixmap(32, 32))
                
        msg.exec_()
    
    def save_decoded_image(self):
        """Decode and save the base64 image to a file"""
        b64_str = self.b64_input.toPlainText().strip()
        if not b64_str:
            QMessageBox.warning(self, "Error", "Please enter a Base64 string")
            return
            
        try:
            # Decode Base64
            img_data = base64.b64decode(b64_str)
            img = Image.open(BytesIO(img_data))
            
            # Convert to RGBA if not already
            if img.mode != 'RGBA':
                img = img.convert('RGBA')
                
            # Create a white background
            background = Image.new('RGBA', img.size, (255, 255, 255, 255))
                
            # Composite the image onto the white background
            img = Image.alpha_composite(background, img)
            
            # Show save file dialog
            path, _ = QFileDialog.getSaveFileName(
                self, 
                'Save Decoded Image', 
                os.path.expanduser("~"),
                'PNG (*.png);;JPEG (*.jpg *.jpeg);;BMP (*.bmp);;WEBP (*.webp)'
            )
            
            if path:
                img.save(path)
                QMessageBox.information(self, "Success", f"Image saved to {path}")
                
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Could not decode or save image: {str(e)}")
    
    def download_base64(self):
        """Save the base64 encoded data to a file"""
        if not hasattr(self, 'current_image') or not self.current_image:
            QMessageBox.warning(self, "Error", "No image loaded")
            return
            
        # Get the formatted output based on the selected format
        formatted_output = self.get_formatted_output()
        if not formatted_output:
            QMessageBox.warning(self, "Error", "No data to save")
            return
            
        # Get the base filename without extension
        base_name = os.path.splitext(os.path.basename(self.current_image))[0]
        
        # Determine the file extension based on the format
        format_type = self.format_combo.currentText()
        if format_type == "JSON":
            ext = ".json"
        elif format_type == "HTML":
            ext = ".html"
        else:  # TXT (Plain Text)
            ext = ".txt"
            
        # Set up file dialog
        default_path = os.path.join(os.path.expanduser("~"), f"{base_name}_base64{ext}")
        path, _ = QFileDialog.getSaveFileName(
            self,
            'Save Base64 Data',
            default_path,
            f"{format_type} Files (*{ext});;All Files (*)"
        )
        
        if path:
            try:
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(formatted_output)
                QMessageBox.information(self, "Success", f"Base64 data saved to {path}")
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Could not save file: {str(e)}")
    
    # Removed the old save_decoded_image method as it's been replaced with a combined version