import sys
import os
from pathlib import Path
from typing import Optional, List, Dict, Any

from PyQt5.QtWidgets import (QApplication, QMainWindow, QTabWidget, QSizePolicy,
                            QWidget, QVBoxLayout, QLabel, QPushButton, QFrame,
                            QMessageBox, QStatusBar, QFileDialog, QStyle)
from PyQt5.QtGui import QIcon, QFont, QPalette, QColor, QPixmap
from PyQt5.QtCore import Qt, QSize, pyqtSignal, pyqtSlot

# Import theme
from theme import apply_theme

# Create QApplication first
app = QApplication.instance() or QApplication(sys.argv)

# Apply the theme
apply_theme(app)

# Import the tools
try:
    from resizer_tool import ResizerTool
    from base64_tool import Base64Tool
    from compressor_tool import CompressorTool
    from webp_tool import WebPConverterTool
    from cropper_tool import CropperTool
    TOOLS_IMPORTED = True
except ImportError as e:
    print(f"Failed to import tools: {e}")
    TOOLS_IMPORTED = False

# Import remover tool if available
REMBG_AVAILABLE = False
REMBG_ERROR = ""
RemoverTool = None

try:
    # First try to import onnxruntime directly to check if it's working
    import onnxruntime as ort
    print(f"ONNX Runtime version: {getattr(ort, '__version__', 'unknown')}")
    
    # Now try to import remover_tool
    from remover_tool import RemoverTool, REMBG_AVAILABLE
    
    if REMBG_AVAILABLE:
        print("Background Remover tool is available")
    else:
        print("Note: Background Remover tool is not available. Check console for details.")
        
except ImportError as e:
    REMBG_ERROR = str(e)
    print(f"Error importing remover tool: {e}")
    import traceback
    traceback.print_exc()
    
    if "No module named 'onnxruntime'" in REMBG_ERROR:
        REMBG_ERROR = "onnxruntime is not installed. Please install it with: pip install onnxruntime"
    elif "No module named 'rembg'" in REMBG_ERROR:
        REMBG_ERROR = "rembg is not installed. Please install it with: pip install rembg"

# Initialize HEIC support flag
HEIC_SUPPORT = False

# Import HEIC tool only after QApplication is created
try:
    import pillow_heif
    pillow_heif.register_heif_opener()
    from heic_tool import HEICConverterTool
    HEIC_SUPPORT = True
except ImportError:
    print("Warning: HEIC support is not available. Install pillow-heif for HEIC support.")
    HEIC_SUPPORT = False

class ImageToolTab(QWidget):
    """Container widget for image tools."""
    
    def __init__(self, tool_name: str, tool_widget: Optional[QWidget] = None):
        """Initialize the ImageToolTab.
        
        Args:
            tool_name: Name of the tool
            tool_widget: The widget to display (if None, shows "Under Construction")
        """
        super().__init__()
        self.tool_name = tool_name
        
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        
        if tool_widget:
            layout.addWidget(tool_widget)
        else:
            # Fallback for tools that haven't been implemented yet
            label = QLabel(f"{tool_name} Tool - Under Construction")
            label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            label.setAlignment(Qt.AlignCenter)
            layout.addWidget(label)
            
        self.setLayout(layout)

class ImageMasterApp(QMainWindow):
    """Main application window for Image Master."""
    
    def __init__(self):
        """Initialize the application window."""
        super().__init__()
        self.setWindowTitle("Image Master")
        self.setMinimumSize(1024, 768)  # Increased minimum size for better layout
        
        # Set application icon if available
        self.setWindowIcon(self._load_app_icon())
        
        # Create main widget and layout
        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(16)
        
        # Add header with ID for specific styling
        header = QLabel("Image Master")
        header.setObjectName("titleLabel")
        header.setStyleSheet("""
            QLabel#titleLabel {
                color: #2937f0;
                font-size: 24px;
                font-weight: bold;
                margin-bottom: 16px;
            }
        """)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        self.tab_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        # Add tabs for each tool
        if TOOLS_IMPORTED:
            self.tab_widget.addTab(ResizerTool(), "Resizer")
            self.tab_widget.addTab(CompressorTool(), "Compressor")
            self.tab_widget.addTab(WebPConverterTool(), "WebP Converter")
            
            # Add HEIC converter tab if supported
            if HEIC_SUPPORT:
                self.tab_widget.addTab(HEICConverterTool(), "HEIC Converter")
            
            # Add Base64 tool
            self.tab_widget.addTab(Base64Tool(), "Base64")
            
            # Add Background Remover tab if available
            if REMBG_AVAILABLE and RemoverTool is not None:
                self.tab_widget.addTab(RemoverTool(), "Background Remover")
            
            # Add Cropper tool
            self.tab_widget.addTab(CropperTool(), "Cropper")
        else:
            # Add error message if tools couldn't be imported
            error_widget = QWidget()
            error_layout = QVBoxLayout(error_widget)
            error_label = QLabel("Error: Could not import required tools. Please check the console for details.")
            error_label.setWordWrap(True)
            error_label.setAlignment(Qt.AlignCenter)
            error_layout.addWidget(error_label)
            self.tab_widget.addTab(error_widget, "Error")
        
        # Add more tools as they are implemented
        # self.tab_widget.addTab(ImageToolTab("Watermark"), "Watermark")
        # self.tab_widget.addTab(ImageToolTab("Effects"), "Effects")
        # self.tab_widget.addTab(ImageToolTab("Convert"), "Convert")
        
        main_layout.addWidget(header)
        main_layout.addWidget(self.tab_widget)
        
        # Set the main widget
        self.setCentralWidget(main_widget)
        
        # Initialize status bar
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.statusBar.showMessage("Ready")
        
        # Apply styles
        self.apply_styles()
    
    def _load_app_icon(self) -> QIcon:
        """Load the application icon if available.
        
        Returns:
            QIcon: The application icon, or a default icon if not found.
        """
        # Look for icon in common locations
        icon_paths = [
            "icons/app_icon.png",
            "resources/app_icon.png",
            "assets/icon.png",
            "app_icon.png",
            "assets/icons/app_icon.png",
            "resources/icons/app_icon.png",
            "resources/images/icon.png",
            "images/icon.png",
            "icon.png"
        ]
        
        # Also check in the same directory as the script
        script_dir = os.path.dirname(os.path.abspath(__file__))
        for path in icon_paths:
            full_path = os.path.join(script_dir, path)
            if os.path.exists(full_path):
                return QIcon(full_path)
        
        # If no icon found, return a default icon
        return QApplication.style().standardIcon(QStyle.SP_ComputerIcon)
    
    def apply_styles(self) -> None:
        """Apply custom styles to the application."""
        # Set style for the entire application
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f5f5;
            }
            QTabWidget::pane {
                border: 1px solid #ccc;
                background: white;
                border-radius: 4px;
                margin-top: 4px;
            }
            QTabBar::tab {
                background: #e0e0e0;
                border: 1px solid #ccc;
                border-bottom: none;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                padding: 8px 16px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background: white;
                border-bottom: 1px solid white;
                margin-bottom: -1px;
            }
            QTabBar::tab:!selected {
                margin-top: 2px;
            }
            QGroupBox {
                border: 1px solid #ddd;
                border-radius: 4px;
                margin-top: 1em;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
            QPushButton {
                background-color: #4a90e2;
                color: white;
                border: none;
                padding: 6px 12px;
                border-radius: 4px;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #3a7bc8;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
            QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {
                padding: 4px;
                border: 1px solid #ccc;
                border-radius: 3px;
                min-height: 24px;
            }
            QLabel[status="error"] {
                color: #d32f2f;
                font-weight: bold;
            }
            QLabel[status="success"] {
                color: #388e3c;
                font-weight: bold;
            }
        """)
    
    def show_status_message(self, message: str, timeout: int = 5000) -> None:
        """Show a status message in the status bar.
        
        Args:
            message: The message to display
            timeout: How long to show the message in milliseconds
        """
        self.statusBar.showMessage(message, timeout)
    
    def show_error_message(self, title: str, message: str) -> None:
        """Show an error message dialog.
        
        Args:
            title: Dialog title
            message: Error message to display
        """
        QMessageBox.critical(self, title, message)
    
    def closeEvent(self, event) -> None:
        """Handle application close event."""
        # Add any cleanup code here
        event.accept()

def main():
    """Main entry point for the application."""
    # Create and show the main window
    window = ImageMasterApp()
    window.show()
    
    # Start the event loop
    return app.exec_()

if __name__ == "__main__":
    sys.exit(main())
