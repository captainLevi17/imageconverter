"""
Tests for GUI components.
"""
import os
import pytest
from pathlib import Path
from PyQt5.QtWidgets import QApplication, QTabWidget, QPushButton, QLabel, QFileDialog
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtTest import QTest

# Import the application and tools
from main import ImageMasterApp
from resizer_tool import ResizerTool
from compressor_tool import CompressorTool
from webp_tool import WebPConverterTool
from base64_tool import Base64Tool
from remover_tool import RemoverTool

# Test data directory
TEST_DATA_DIR = Path(__file__).parent / 'test_data'

@pytest.fixture
def app(qapp):
    """Fixture to provide the application instance."""
    return ImageMasterApp()

class TestMainWindow:
    """Test cases for the main application window."""
    
    def test_window_initialization(self, app):
        """Test that the main window initializes correctly."""
        # Check window title
        assert app.windowTitle() == "Image Master"
        
        # Check window size policy
        assert app.minimumWidth() == 800
        assert app.minimumHeight() == 600
        
        # Check if tabs are created
        tabs = app.findChild(QTabWidget)
        assert tabs is not None
        
        # Check if all expected tabs are present
        tab_names = [tabs.tabText(i) for i in range(tabs.count())]
        expected_tabs = ["Resizer", "Compressor", "WebP Converter", "Base64"]
        for tab in expected_tabs:
            assert tab in tab_names
            
        # Check if background remover tab is present if available
        if hasattr(app, 'tabs'):
            bg_remover_tab = next((i for i in range(app.tabs.count()) 
                                 if app.tabs.tabText(i) == "BG Remover"), None)
            if bg_remover_tab is not None:
                assert app.tabs.tabText(bg_remover_tab) == "BG Remover"

class TestResizerTab:
    """Test cases for the Resizer tab."""
    
    def test_resizer_ui_elements(self, qapp):
        """Test that all UI elements are properly initialized."""
        resizer = ResizerTool()
        
        # Check if main widgets exist
        assert hasattr(resizer, 'width_input')
        assert hasattr(resizer, 'height_input')
        assert hasattr(resizer, 'maintain_aspect_ratio')
        assert hasattr(resizer, 'browse_button')
        assert hasattr(resizer, 'process_button')
        
        # Check default values
        assert resizer.width_input.value() == 800
        assert resizer.height_input.value() == 600
        assert resizer.maintain_aspect_ratio.isChecked() is True

class TestBackgroundRemoverTab:
    """Test cases for the Background Remover tab."""
    
    def test_remover_ui_elements(self, qapp):
        """Test that all UI elements are properly initialized."""
        if not hasattr(sys, 'frozen') and not hasattr(sys, '_MEIPASS'):
            # Only run this test if we're not in a frozen environment (like PyInstaller)
            remover = RemoverTool()
            
            # Check if main widgets exist
            assert hasattr(remover, 'browse_button')
            assert hasattr(remover, 'clear_button')
            assert hasattr(remover, 'process_button')
            assert hasattr(remover, 'bg_transparent')
            assert hasattr(remover, 'bg_white')
            assert hasattr(remover, 'bg_black')
            assert hasattr(remover, 'bg_custom')
            assert hasattr(remover, 'select_color_btn')
            
            # Check default values
            assert remover.bg_white.isChecked() is True
            assert remover.select_color_btn.isEnabled() is False

class TestImageProcessing:
    """Test cases for image processing functionality."""
    
    def test_resize_image(self, tmp_path):
        """Test image resizing functionality."""
        # Create a test image
        from PIL import Image
        img_path = TEST_DATA_DIR / 'test_image.jpg'
        output_path = tmp_path / 'resized.jpg'
        
        # Create a 100x100 test image
        img = Image.new('RGB', (100, 100), color='red')
        img.save(img_path)
        
        # Test resizing
        resizer = ResizerTool()
        resizer.width_input.setValue(50)
        resizer.height_input.setValue(50)
        
        # Simulate file selection
        resizer.image_paths = [str(img_path)]
        resizer.output_dir = str(tmp_path)
        
        # Process the image
        resizer.process_images()
        
        # Check if output file exists
        assert output_path.exists()
        
        # Check output dimensions
        with Image.open(output_path) as img:
            assert img.size == (50, 50)

    def test_remove_background(self, tmp_path, monkeypatch):
        """Test background removal functionality with mocking."""
        if not hasattr(sys, 'frozen') and not hasattr(sys, '_MEIPASS'):
            # Skip this test if we're in a frozen environment
            # or if rembg is not available
            if not hasattr(sys.modules.get('remover_tool'), 'REMBG_AVAILABLE'):
                pytest.skip("rembg not available")
                
            # Create a test image
            from PIL import Image
            img_path = TEST_DATA_DIR / 'test_image.png'
            output_path = tmp_path / 'no_bg.png'
            
            # Create a test image with alpha channel
            img = Image.new('RGBA', (100, 100), (255, 0, 0, 255))  # Red square
            img.save(img_path, 'PNG')
            
            # Mock the remove_background_pil function
            def mock_remove_bg(img, model_name='u2net'):
                # Return a transparent version of the image
                img = img.convert('RGBA')
                data = img.getdata()
                new_data = []
                for item in data:
                    # Make red pixels transparent
                    if item[0] > 200 and item[1] < 50 and item[2] < 50:
                        new_data.append((0, 0, 0, 0))  # Transparent
                    else:
                        new_data.append(item)
                img.putdata(new_data)
                return img
            
            # Apply the mock
            monkeypatch.setattr('remover_tool.remove_background_pil', mock_remove_bg)
            
            # Set up the remover tool
            remover = RemoverTool()
            remover.image_paths = [str(img_path)]
            remover.output_dir = str(tmp_path)
            remover.bg_transparent.setChecked(True)
            
            # Process the image
            remover.process_images()
            
            # Check if output file exists
            assert output_path.exists()
            
            # Check if the output has transparency
            with Image.open(output_path) as img:
                assert img.mode == 'RGBA'
                # Check if there are transparent pixels
                has_transparency = any(pixel[3] < 255 for pixel in img.getdata())
                assert has_transparency, "Output image should have transparency"
