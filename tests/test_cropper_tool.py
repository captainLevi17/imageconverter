"""
Tests for the Cropper Tool functionality.
"""
import os
import sys
import pytest
from pathlib import Path
from PyQt5.QtWidgets import QApplication, QPushButton, QLabel, QFileDialog, QWidget
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtTest import QTest

# Import the CropperTool
from cropper_tool import CropperTool, CropperThumbnailItem, CropArea

# Test data directory
TEST_DATA_DIR = Path(__file__).parent / 'test_data'

# Create a QApplication instance for testing
@pytest.fixture(scope="session")
def qapp():
    """Create a QApplication instance for testing."""
    app = QApplication.instance() or QApplication(sys.argv)
    yield app

class TestCropperTool:
    """Test cases for the Cropper Tool."""
    
    @pytest.fixture
    def cropper_tool(self, qapp):
        """Fixture to provide a CropperTool instance for testing."""
        return CropperTool()
    
    def test_initialization(self, cropper_tool):
        """Test that the CropperTool initializes correctly."""
        # Check if main widgets are initialized
        assert hasattr(cropper_tool, 'thumbnail_scroll_area')
        assert hasattr(cropper_tool, 'crop_area')
        assert hasattr(cropper_tool, 'add_images_button')
        assert hasattr(cropper_tool, 'clear_button')
        assert hasattr(cropper_tool, 'crop_button')
        
        # Check default values
        assert len(cropper_tool.thumbnail_items) == 0
        assert cropper_tool.current_selected_thumbnail_item is None
        assert cropper_tool.output_dir is not None
    
    def test_add_images(self, cropper_tool, monkeypatch, tmp_path):
        """Test adding images to the cropper."""
        # Create a test image
        from PIL import Image
        test_image = tmp_path / "test_image.jpg"
        img = Image.new('RGB', (100, 100), color='red')
        img.save(test_image)
        
        # Mock the file dialog to return the test image
        monkeypatch.setattr(QFileDialog, 'getOpenFileNames', 
                           lambda *args, **kwargs: ([str(test_image)], None))
        
        # Click the add images button
        QTest.mouseClick(cropper_tool.add_images_button, Qt.LeftButton)
        
        # Check if the image was added
        assert len(cropper_tool.thumbnail_items) == 1
        assert cropper_tool.current_selected_thumbnail_item is not None
        
        # Check if the image is loaded in the crop area
        assert cropper_tool.current_pil_image is not None
    
    def test_clear_images(self, cropper_tool, monkeypatch):
        """Test clearing all images from the cropper."""
        # First add an image
        test_image = str(TEST_DATA_DIR / 'test_image.jpg')
        monkeypatch.setattr(QFileDialog, 'getOpenFileNames', 
                           lambda *args, **kwargs: ([test_image], None))
        QTest.mouseClick(cropper_tool.add_images_button, Qt.LeftButton)
        
        # Now clear the images
        QTest.mouseClick(cropper_tool.clear_button, Qt.LeftButton)
        
        # Check if images were cleared
        assert len(cropper_tool.thumbnail_items) == 0
        assert cropper_tool.current_selected_thumbnail_item is None
        assert cropper_tool.crop_area.pixmap() is None
    
    def test_aspect_ratio_selection(self, cropper_tool):
        """Test changing aspect ratio presets."""
        # Get the aspect ratio buttons
        buttons = cropper_tool.aspect_buttons.buttons()
        
        # Test each aspect ratio button
        for i, btn in enumerate(buttons):
            # Skip the custom aspect ratio button (last one)
            if i == len(buttons) - 1:
                continue
                
            # Click the button
            QTest.mouseClick(btn, Qt.LeftButton)
            
            # Check if the crop area's aspect ratio was updated
            if btn.text() == "Free Form":
                assert cropper_tool.crop_area.aspect_ratio == 0
            else:
                # Extract the aspect ratio from the button's text
                ratio_text = btn.text().split(" ")[0]  # Get the first part (e.g., "1:1" or "16:9")
                w, h = map(int, ratio_text.split(":"))
                expected_ratio = w / h
                actual_ratio = cropper_tool.crop_area.aspect_ratio
                
                # For 1:1 aspect ratio, check if it's close to 1.0
                if w == h:
                    assert abs(actual_ratio - 1.0) < 1e-6
                else:
                    # For other aspect ratios, check if they match the expected ratio
                    expected = expected_ratio
                    actual = actual_ratio
                    # Check if either the ratio or its reciprocal matches
                    assert (abs(actual - expected) < 1e-6 or 
                           abs(1/actual - 1/expected) < 1e-6)
    
    def test_output_directory_selection(self, cropper_tool, monkeypatch, tmp_path):
        """Test selecting an output directory."""
        # Mock the file dialog to return a temporary directory
        test_dir = str(tmp_path / 'output')
        monkeypatch.setattr(QFileDialog, 'getExistingDirectory', 
                           lambda *args, **kwargs: test_dir)
        
        # Click the output directory button
        QTest.mouseClick(cropper_tool.output_dir_button, Qt.LeftButton)
        
        # Check if the output directory was updated
        assert cropper_tool.output_dir == test_dir
        assert test_dir in cropper_tool.output_dir_label.text()

class TestCropperThumbnailItem:
    """Test cases for the CropperThumbnailItem class."""
    
    def test_thumbnail_creation(self, qapp):
        """Test creating a thumbnail item."""
        test_image = str(TEST_DATA_DIR / 'test_image.jpg')
        parent = QWidget()
        thumbnail = CropperThumbnailItem(test_image, 0, parent)
        
        # Check if the thumbnail was created with the correct properties
        assert thumbnail.image_path == test_image
        assert thumbnail.index == 0
        assert hasattr(thumbnail, 'image_label')
        assert hasattr(thumbnail, 'name_label')
        
        # Check initial state
        assert not thumbnail.is_selected
        assert thumbnail.property("selected") == False
    
    def test_thumbnail_selection(self, qapp):
        """Test selecting a thumbnail."""
        test_image = str(TEST_DATA_DIR / 'test_image.jpg')
        parent = QWidget()
        thumbnail = CropperThumbnailItem(test_image, 0, parent)
        
        # Select the thumbnail
        thumbnail.set_selected(True)
        assert thumbnail.is_selected
        assert thumbnail.property("selected") == True
        
        # Deselect the thumbnail
        thumbnail.set_selected(False)
        assert not thumbnail.is_selected
        assert thumbnail.property("selected") == False

if __name__ == "__main__":
    pytest.main(["-v", __file__])
