import base64
import os
import json
from io import BytesIO
from datetime import datetime
from utils.base_tool import BaseTool

from PyQt5.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QFileDialog, QScrollArea, QMessageBox, QApplication,
    QSizePolicy, QComboBox, QGroupBox, QFrame, QStyle
)
from PyQt5.QtCore import Qt, QFileInfo
from PyQt5.QtGui import QPixmap, QImage
from PIL import Image


class Base64Tool(BaseTool):
    def __init__(self):
        super().__init__("Base64 Tool")
        self.current_image = None
        
        # Initialize UI elements
        self.img_path_label = None
        self.img_preview = None
        self.b64_output = None
        self.copy_btn = None
        self.download_btn = None
        self.b64_input = None
        self.convert_btn = None
        self.preview_label = None
        self.save_btn = None
        
    def clear_images(self):
        """Clear the current image and reset the UI."""
        super().clear_images()
        self.current_image = None
        if hasattr(self, 'b64_output') and self.b64_output:
            self.b64_output.clear()
        if hasattr(self, 'img_preview') and self.img_preview:
            self.img_preview.clear()
        if hasattr(self, 'img_path_label') and self.img_path_label:
            self.img_path_label.setText("No image selected")
    
    def setup_tool_controls(self, control_layout):
        """Set up the tool-specific controls."""
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
        self.copy_btn = QPushButton("Copy to Clipboard")
        self.copy_btn.setIcon(self.style().standardIcon(getattr(self.style(), 'SP_DialogSaveButton')))
        self.copy_btn.clicked.connect(self.copy_to_clipboard)
        
        # Copy HTML Snippet button
        self.copy_html_btn = QPushButton("Copy HTML Snippet")
        self.copy_html_btn.setIcon(self.style().standardIcon(getattr(self.style(), 'SP_DialogSaveButton')))
        self.copy_html_btn.clicked.connect(self.copy_html_snippet)
        
        # Add copy buttons to container
        copy_buttons_container.addWidget(self.copy_btn)
        copy_buttons_container.addWidget(self.copy_html_btn)
        
        # Download button
        self.download_btn = QPushButton("Download")
        self.download_btn.setIcon(self.style().standardIcon(getattr(self.style(), 'SP_ArrowDown')))
        self.download_btn.clicked.connect(self.download_base64)
        
        # Add buttons with stretch
        button_layout.addLayout(copy_buttons_container)
        button_layout.addStretch()
        button_layout.addWidget(self.download_btn)
        
        img_to_b64_layout.addLayout(button_layout)
        
        # Add to control layout
        control_layout.addWidget(img_to_b64_group, stretch=1)
        
        # Add a separator
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setObjectName("separator")
        control_layout.addWidget(separator)
        
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
        
        # Decode button
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.convert_btn = QPushButton("Decode and Preview")
        self.convert_btn.setIcon(self.style().standardIcon(getattr(self.style(), 'SP_MediaPlay')))
        self.convert_btn.clicked.connect(self.decode_base64)
        button_layout.addWidget(self.convert_btn)
        
        b64_to_img_layout.addLayout(button_layout)
        
        # Decoded image preview
        preview_group = QGroupBox("Preview")
        preview_group.setObjectName("previewGroup")
        preview_layout = QVBoxLayout(preview_group)
        preview_layout.setContentsMargins(0, 12, 0, 0)
        
        self.preview_label = QLabel()
        self.preview_label.setObjectName("decodedPreview")
        self.preview_label.setProperty("preview", True)
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setMinimumSize(300, 200)
        self.preview_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        preview_layout.addWidget(self.preview_label)
        
        # Save button
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.save_btn = QPushButton("Save Image")
        self.save_btn.setIcon(self.style().standardIcon(getattr(self.style(), 'SP_DialogSaveButton')))
        self.save_btn.clicked.connect(self.save_decoded_image)
        self.save_btn.setEnabled(False)
        button_layout.addWidget(self.save_btn)
        
        preview_layout.addLayout(button_layout)
        b64_to_img_layout.addWidget(preview_group, stretch=2)
        
        # Add to control layout
        control_layout.addWidget(b64_to_img_group, stretch=1)
    
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
    
    def download_base64(self):
        if not hasattr(self, 'current_image') or not self.current_image:
            QMessageBox.warning(self, "Error", "No image loaded")
            return
            
        format_type = self.format_combo.currentText()
        formatted_output = self.get_formatted_output(format_type)
        
        if formatted_output is None:
            QMessageBox.warning(self, "Error", "No data to download")
            return
        
        # Determine file extension and filter
        if format_type.startswith("TXT"):
            ext = "txt"
            file_filter = "Text Files (*.txt)"
        elif format_type == "JSON":
            ext = "json"
            file_filter = "JSON Files (*.json)"
        else:  # HTML
            ext = "html"
            file_filter = "HTML Files (*.html)"
        
        # Suggest filename based on original image
        base_name = os.path.splitext(os.path.basename(self.current_image))[0]
        suggested_name = f"{base_name}_base64.{ext}"
        
        # Get save path
        path, _ = QFileDialog.getSaveFileName(
            self, 
            'Save Base64 Output',
            suggested_name,
            file_filter
        )
        
        if path:
            try:
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(formatted_output)
                QMessageBox.information(self, "Success", f"File saved successfully to {path}")
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Could not save file: {str(e)}")
    
    def decode_base64(self):
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
            
            # Convert to QPixmap
            data = img.tobytes('raw', 'RGBA')
            qimg = QImage(data, img.size[0], img.size[1], QImage.Format_RGBA8888)
            pixmap = QPixmap.fromImage(qimg)
            
            self.decoded_preview.setPixmap(pixmap)
            self.current_decoded_image = img
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Could not decode Base64: {str(e)}")
    
    def save_decoded_image(self):
        if not hasattr(self, 'current_decoded_image') or not self.current_decoded_image:
            QMessageBox.warning(self, "Error", "No decoded image to save")
            return
        
        path, _ = QFileDialog.getSaveFileName(self, 'Save Image', '',
                                            'PNG (*.png);;JPEG (*.jpg *.jpeg);;BMP (*.bmp);;WEBP (*.webp)')
        if path:
            try:
                self.current_decoded_image.save(path)
                QMessageBox.information(self, "Saved", f"Image saved to {path}")
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Could not save image: {str(e)}")
