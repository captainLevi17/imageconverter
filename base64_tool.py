import base64
import os
import json
from io import BytesIO
from datetime import datetime

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QFileDialog, QScrollArea, QMessageBox, QApplication,
    QSizePolicy, QComboBox
)
from PyQt5.QtCore import Qt, QFileInfo
from PyQt5.QtGui import QPixmap, QImage
from PIL import Image


class Base64Tool(QWidget):
    def __init__(self):
        super().__init__()
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.current_image = None
        self.init_ui()
    
    def init_ui(self):
        # Main layout
        layout = QVBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Image to Base64 section
        img_to_b64_layout = QVBoxLayout()
        img_to_b64_layout.setSpacing(5)
        img_to_b64_layout.addWidget(QLabel("<b>Image to Base64</b>"))
        
        # Image selection
        img_select_layout = QHBoxLayout()
        self.img_path_label = QLabel("No image selected")
        self.img_path_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        browse_btn = QPushButton("Browse Image")
        browse_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        browse_btn.clicked.connect(self.browse_image)
        img_select_layout.addWidget(self.img_path_label)
        img_select_layout.addWidget(browse_btn)
        img_to_b64_layout.addLayout(img_select_layout)
        
        # Image preview
        self.img_preview = QLabel()
        self.img_preview.setAlignment(Qt.AlignCenter)
        self.img_preview.setMinimumSize(300, 200)
        self.img_preview.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        img_to_b64_layout.addWidget(self.img_preview, stretch=1)
        
        # Base64 output
        self.b64_output = QTextEdit()
        self.b64_output.setPlaceholderText("Base64 encoded string will appear here")
        self.b64_output.setReadOnly(True)
        self.b64_output.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        img_to_b64_layout.addWidget(self.b64_output, stretch=2)
        
        # Format selection and buttons
        button_layout = QHBoxLayout()
        
        # Format selection
        self.format_combo = QComboBox()
        self.format_combo.addItems(["TXT (Plain Text)", "JSON", "HTML"])
        button_layout.addWidget(self.format_combo)
        
        # Copy button
        copy_btn = QPushButton("Copy to Clipboard")
        copy_btn.clicked.connect(self.copy_to_clipboard)
        button_layout.addWidget(copy_btn)
        
        # Download button
        download_btn = QPushButton("Download")
        download_btn.clicked.connect(self.download_base64)
        button_layout.addWidget(download_btn)
        
        img_to_b64_layout.addLayout(button_layout)
        
        layout.addLayout(img_to_b64_layout, stretch=1)
        
        # Base64 to Image section
        b64_to_img_layout = QVBoxLayout()
        b64_to_img_layout.setSpacing(5)
        b64_to_img_layout.addWidget(QLabel("<b>Base64 to Image</b>"))
        
        # Base64 input
        self.b64_input = QTextEdit()
        self.b64_input.setPlaceholderText("Paste Base64 encoded string here")
        self.b64_input.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        b64_to_img_layout.addWidget(self.b64_input, stretch=2)
        
        # Decode button
        decode_btn = QPushButton("Decode and Preview")
        decode_btn.clicked.connect(self.decode_base64)
        b64_to_img_layout.addWidget(decode_btn)
        
        # Decoded image preview
        self.decoded_preview = QLabel()
        self.decoded_preview.setAlignment(Qt.AlignCenter)
        self.decoded_preview.setMinimumSize(300, 200)
        self.decoded_preview.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        b64_to_img_layout.addWidget(self.decoded_preview, stretch=1)
        
        # Save button
        save_btn = QPushButton("Save Image")
        save_btn.clicked.connect(self.save_decoded_image)
        b64_to_img_layout.addWidget(save_btn)
        
        layout.addLayout(b64_to_img_layout, stretch=1)
        
        # Create main widget and set its layout
        main_widget = QWidget()
        main_widget.setLayout(layout)
        
        # Set up scroll area
        scroll = QScrollArea()
        scroll.setWidget(main_widget)
        scroll.setWidgetResizable(True)
        
        # Set scroll area as the central widget
        main_layout = QVBoxLayout()
        main_layout.addWidget(scroll)
        self.setLayout(main_layout)
    
    def browse_image(self):
        path, _ = QFileDialog.getOpenFileName(self, 'Select Image', '', 
                                            'Image Files (*.png *.jpg *.jpeg *.bmp *.webp)')
        if path:
            self.current_image = path
            self.img_path_label.setText(os.path.basename(path))
            self.display_image_preview(path)
            self.encode_to_base64(path)
    
    def display_image_preview(self, path):
        try:
            img = Image.open(path)
            img.thumbnail((300, 300))
            
            # Convert to QPixmap
            img = img.convert("RGBA")
            data = img.tobytes("raw", "RGBA")
            qimg = QImage(data, img.size[0], img.size[1], QImage.Format_RGBA8888)
            pixmap = QPixmap.fromImage(qimg)
            
            self.img_preview.setPixmap(pixmap)
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Could not load image: {str(e)}")
    
    def encode_to_base64(self, path):
        try:
            with open(path, "rb") as img_file:
                b64_str = base64.b64encode(img_file.read()).decode("utf-8")
            self.b64_output.setPlainText(b64_str)
            # Store the original file path for later use
            self.current_image = path
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Could not encode image: {str(e)}")
    
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
            QMessageBox.warning(self, "Error", "No data to copy")
            return
            
        clipboard = QApplication.clipboard()
        clipboard.setText(formatted_output)
        QMessageBox.information(self, "Copied", "Content copied to clipboard")
    
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
            
            # Convert to QPixmap
            img = img.convert("RGBA")
            data = img.tobytes("raw", "RGBA")
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
