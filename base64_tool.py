import base64
import os
from io import BytesIO

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QFileDialog, QScrollArea, QMessageBox, QApplication,
    QSizePolicy
)
from PyQt5.QtCore import Qt
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
        
        # Copy button
        copy_btn = QPushButton("Copy to Clipboard")
        copy_btn.clicked.connect(self.copy_to_clipboard)
        img_to_b64_layout.addWidget(copy_btn)
        
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
        
        # Combine sections
        main_split = QHBoxLayout()
        img_to_b64_group = QWidget()
        img_to_b64_group.setLayout(img_to_b64_layout)
        
        b64_to_img_group = QWidget()
        b64_to_img_group.setLayout(b64_to_img_layout)
        
        main_split.addWidget(img_to_b64_group)
        main_split.addWidget(b64_to_img_group)
        
        layout.addLayout(main_split)
        self.setLayout(layout)
    
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
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Could not encode image: {str(e)}")
    
    def copy_to_clipboard(self):
        clipboard = QApplication.clipboard()
        clipboard.setText(self.b64_output.toPlainText())
        QMessageBox.information(self, "Copied", "Base64 string copied to clipboard")
    
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
