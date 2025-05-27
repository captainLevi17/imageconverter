import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QTabWidget, QSizePolicy,
                            QWidget, QVBoxLayout, QLabel, QPushButton, QFrame)
from PyQt5.QtGui import QIcon, QFont, QPalette, QColor
from PyQt5.QtCore import Qt, QSize

# Import theme
from theme import apply_theme

# Create QApplication first
app = QApplication.instance()
if app is None:
    app = QApplication(sys.argv)

# Apply the theme
apply_theme(app)

# Import the actual tools
from resizer_tool import ResizerTool
from base64_tool import Base64Tool
from compressor_tool import CompressorTool
from webp_tool import WebPConverterTool

# Import remover tool
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
        REMOVER_TOOL_AVAILABLE = True
        print("Background Remover tool is available")
    else:
        REMOVER_TOOL_AVAILABLE = False
        print("Note: Background Remover tool is not available. Check console for details.")
        
except ImportError as e:
    REMBG_ERROR = str(e)
    print(f"Error importing remover tool: {e}")
    import traceback
    traceback.print_exc()
    REMOVER_TOOL_AVAILABLE = False
    
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
        
        # Create tabs
        self.tabs = QTabWidget()
        self.tabs.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.tabs.setDocumentMode(True)
        
        # Add tools to tabs
        self.tabs.addTab(ResizerTool(), "Resizer")
        self.tabs.addTab(CompressorTool(), "Compressor")
        self.tabs.addTab(WebPConverterTool(), "WebP Converter")
        self.tabs.addTab(Base64Tool(), "Base64")
        
        # Add HEIC converter if supported
        if HEIC_SUPPORT:
            try:
                self.tabs.addTab(HEICConverterTool(), "HEIC to JPG")
            except Exception as e:
                print(f"Error initializing HEIC tool: {e}")
        
        # Add Background Remover tab if available
        if REMOVER_TOOL_AVAILABLE:
            try:
                self.tabs.addTab(RemoverTool(), "BG Remover")
            except Exception as e:
                print(f"Error initializing Background Remover: {e}")
                import traceback
                traceback.print_exc()
                self.add_placeholder_tab("BG Remover", "Background Remover (Error - Check Console)")
        else:
            error_msg = """Background Remover (Not Available)
            
            The Background Remover tool requires additional packages to be installed.
            
            Please run these commands in your terminal:
            pip uninstall -y onnxruntime onnxruntime-gpu
            pip install onnxruntime==1.15.1
            pip install rembg==2.0.50
            
            If you still see this message after installation,
            please check the console for detailed error messages.
            """
            self.add_placeholder_tab("BG Remover", error_msg)



        # Add placeholder tabs for other tools
        self.add_placeholder_tab("Dashboard", "Home Dashboard")
        self.add_placeholder_tab("Cropper", "Image Cropper")
        
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
    # The QApplication is already created at the top level
    window = ImageMasterApp()
    window.show()
    sys.exit(app.exec_())
