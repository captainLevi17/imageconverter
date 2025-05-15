import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QTabWidget, QSizePolicy
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton
from PyQt5.QtCore import Qt

# Import the actual tools
from resizer_tool import ResizerTool
from base64_tool import Base64Tool

class ImageToolTab(QWidget):
    def __init__(self, tool_name):
        super().__init__()
        self.tool_name = tool_name
        layout = QVBoxLayout()
        self.label = QLabel(f"{tool_name} Tool - Under Construction")
        self.label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.label, stretch=1)
        self.setLayout(layout)

class ImageMasterApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Image Master")
        self.setMinimumSize(600, 400)  # Set minimum window size
        
        # Create tabs
        self.tabs = QTabWidget()
        self.tabs.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setCentralWidget(self.tabs)
        
        # Add tools
        self.resizer_tool = ResizerTool()
        self.base64_tool = Base64Tool()
        
        self.tabs.addTab(self.resizer_tool, "Resizer")  
        self.tabs.addTab(self.base64_tool, "Base64 Converter")
        
        # Add placeholder tabs for other tools
        self.add_placeholder_tab("Dashboard", "Home Dashboard")
        self.add_placeholder_tab("HEIC Converter", "HEIC to JPG")
        self.add_placeholder_tab("Compressor", "Image Compressor")
        self.add_placeholder_tab("Cropper", "Image Cropper")
        self.add_placeholder_tab("WebP", "WebP Converter")
        self.add_placeholder_tab("BG Remover", "Background Remover")
    
    def add_placeholder_tab(self, tab_name, tool_name):
        """Add placeholder tabs for tools not yet implemented"""
        tab = QWidget()
        tab.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout = QVBoxLayout()
        label = QLabel(f"{tool_name} - Coming Soon")
        label.setAlignment(Qt.AlignCenter)
        label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addWidget(label, stretch=1)
        tab.setLayout(layout)
        self.tabs.addTab(tab, tab_name)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ImageMasterApp()
    window.show()
    sys.exit(app.exec_())
