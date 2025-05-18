import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QTabWidget, QSizePolicy,
                            QWidget, QVBoxLayout, QLabel, QPushButton, QFrame)
from PyQt5.QtGui import QIcon, QFont, QPalette, QColor
from PyQt5.QtCore import Qt, QSize

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
        self.setMinimumSize(800, 600)  # Increased minimum size for better layout
        
        # Apply modern style
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f7fa;
            }
            QTabWidget::pane {
                border: 1px solid #d1d9e6;
                border-radius: 8px;
                margin: 8px;
                background: white;
            }
            QTabBar::tab {
                background: #f0f4f8;
                color: #4a5568;
                padding: 10px 20px;
                margin: 2px 1px 0 1px;
                border: 1px solid #d1d9e6;
                border-bottom: none;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                font-weight: 500;
            }
            QTabBar::tab:selected {
                background: white;
                color: #3182ce;
                border-bottom: 2px solid #3182ce;
                margin-bottom: -1px;
            }
            QTabBar::tab:!selected {
                margin-top: 4px;
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
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #2c5282;
            }
            QPushButton:pressed {
                background-color: #2b6cb0;
            }
            QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox {
                padding: 6px 12px;
                border: 1px solid #d1d9e6;
                border-radius: 6px;
                min-height: 36px;
            }
            QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus {
                border: 1px solid #3182ce;
                outline: none;
            }
        """)
        
        # Set application font
        font = QFont("Segoe UI", 9)  # Modern system font
        QApplication.setFont(font)
        
        # Create main widget and layout
        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(16)
        
        # Create header
        header = QLabel("Image Master")
        header_font = QFont()
        header_font.setPointSize(20)
        header_font.setWeight(QFont.Bold)
        header.setFont(header_font)
        header.setStyleSheet("color: #2d3748; margin-bottom: 8px;")
        
        # Create tabs
        self.tabs = QTabWidget()
        self.tabs.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.tabs.setDocumentMode(True)
        
        # Add tools
        self.resizer_tool = ResizerTool()
        self.base64_tool = Base64Tool()
        
        self.tabs.addTab(self.resizer_tool, QIcon(), "Resizer")
        self.tabs.addTab(self.base64_tool, QIcon(), "Base64")
        
        # Add placeholder tabs for other tools
        self.add_placeholder_tab("Dashboard", "Home Dashboard")
        self.add_placeholder_tab("HEIC", "HEIC to JPG")
        self.add_placeholder_tab("Compressor", "Image Compressor")
        self.add_placeholder_tab("Cropper", "Image Cropper")
        self.add_placeholder_tab("WebP", "WebP Converter")
        self.add_placeholder_tab("BG Remover", "Background Remover")
        
        # Add widgets to main layout
        main_layout.addWidget(header)
        main_layout.addWidget(self.tabs)
        
        # Set main widget
        self.setCentralWidget(main_widget)
    
    def add_placeholder_tab(self, tab_name, tool_name):
        """Add placeholder tabs for tools not yet implemented"""
        tab = QWidget()
        tab.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Create a frame for the coming soon message
        frame = QFrame()
        frame.setFrameShape(QFrame.StyledPanel)
        frame.setStyleSheet("""
            QFrame {
                background-color: #f8fafc;
                border: 2px dashed #e2e8f0;
                border-radius: 12px;
            }
        """)
        
        frame_layout = QVBoxLayout(frame)
        frame_layout.setContentsMargins(20, 40, 20, 40)
        
        # Add icon (using text as icon for now)
        icon_label = QLabel("🚧")
        icon_label.setStyleSheet("font-size: 36px;")
        icon_label.setAlignment(Qt.AlignCenter)
        
        # Add title
        title_label = QLabel(tool_name)
        title_label.setStyleSheet("""
            font-size: 18px;
            font-weight: 600;
            color: #2d3748;
            margin-top: 16px;
        """)
        title_label.setAlignment(Qt.AlignCenter)
        
        # Add subtitle
        subtitle_label = QLabel("Coming Soon")
        subtitle_label.setStyleSheet("""
            font-size: 14px;
            color: #718096;
            margin-top: 8px;
        """)
        subtitle_label.setAlignment(Qt.AlignCenter)
        
        frame_layout.addWidget(icon_label)
        frame_layout.addWidget(title_label)
        frame_layout.addWidget(subtitle_label)
        frame_layout.addStretch()
        
        layout.addWidget(frame)
        self.tabs.addTab(tab, tab_name)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ImageMasterApp()
    window.show()
    sys.exit(app.exec_())
