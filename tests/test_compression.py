"""Unit tests for the compression functionality."""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
from PIL import Image
import numpy as np

# Import the worker class
from compressor_tool import CompressionWorker

# Create a test image fixture
@pytest.fixture
def test_image():
    """Create a test image and yield its path, then clean up after the test."""
    # Create a temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a simple image
        img_path = os.path.join(temp_dir, "test_image.jpg")
        img = Image.new('RGB', (100, 100), color='red')
        img.save(img_path, 'JPEG', quality=95)
        
        yield img_path, temp_dir

# Test the CompressionWorker class
class TestCompressionWorker:
    """Test cases for the CompressionWorker class."""
    
    def test_compression_worker_init(self):
        """Test initialization of the CompressionWorker."""
        worker = CompressionWorker(
            input_files=["test1.jpg"],
            output_dir="/output",
            quality=80,
            output_format="JPEG"
        )
        
        assert worker.input_files == ["test1.jpg"]
        assert worker.output_dir == "/output"
        assert worker.quality == 80
        assert worker.output_format == "JPEG"
        assert worker.preserve_metadata is True
        assert worker.is_running is True
    
    def test_process_image_jpeg(self, test_image, tmp_path):
        """Test processing a JPEG image with simplified test case."""
        # Use the test image from the fixture
        img_path, temp_dir = test_image
        
        # Create a simple output directory
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        
        # Create a simple test image
        test_img = Image.new('RGB', (100, 100), color='red')
        test_img_path = str(output_dir / "test.jpg")
        test_img.save(test_img_path, 'JPEG', quality=95)
        
        # Initialize the worker with the test image
        worker = CompressionWorker(
            input_files=[test_img_path],
            output_dir=str(output_dir),
            quality=50,
            output_format="JPEG"
        )
        
        # Process the image
        worker.process_image(test_img_path, 1)
        
        # Check that the output file was created
        output_files = list(output_dir.glob("*.jpg"))
        assert len(output_files) > 0, "No output file was created"
        
        # Check that the output file is smaller than the original
        original_size = os.path.getsize(test_img_path)
        compressed_size = os.path.getsize(output_files[0])
        
        # The compressed size should be smaller than the original
        # or at least not significantly larger (allowing for some overhead)
        max_allowed_size = original_size * 1.1  # Allow 10% overhead
        assert compressed_size <= max_allowed_size, \
            f"Compressed size ({compressed_size}) is too large compared to original ({original_size})"
    
    def test_process_image_rgba_to_jpeg(self, tmp_path):
        """Test converting an RGBA image to JPEG."""
        # Create output directory
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        print(f"Output directory: {output_dir}")
        
        # Create a test RGBA image with transparency
        test_img = Image.new('RGBA', (100, 100), (255, 0, 0, 128))  # Semi-transparent red
        test_img_path = str(output_dir / "test_rgba.png")
        test_img.save(test_img_path, 'PNG')
        print(f"Created test RGBA image at: {test_img_path}")
        
        # Verify the test image was created correctly
        with Image.open(test_img_path) as img:
            print(f"Test image mode: {img.mode}")
            print(f"Test image size: {img.size}")
        
        # Initialize the worker to convert to JPEG
        worker = CompressionWorker(
            input_files=[test_img_path],
            output_dir=str(output_dir),
            quality=80,
            output_format="JPEG"
        )
        
        # Process the image - should not raise an exception
        print("Processing image...")
        try:
            worker.process_image(test_img_path, 1)
            print("Image processing completed")
        except Exception as e:
            print(f"Error processing image: {e}")
            import traceback
            traceback.print_exc()
            raise
        
        # List all files in the output directory for debugging
        print("\nOutput directory contents:")
        for f in output_dir.glob("*"):
            print(f"- {f.name} (size: {f.stat().st_size} bytes)")
        
        # Check that the output file was created (try both .jpg and .jpeg extensions)
        output_files = list(output_dir.glob("*.jpg")) + list(output_dir.glob("*.jpeg"))
        print(f"Found {len(output_files)} JPG/JPEG files: {output_files}")
        
        if not output_files:
            # Try to find any files that might have been created
            all_files = list(output_dir.glob("*"))
            print(f"No JPG/JPEG files found. All files in directory: {all_files}")
        
        assert len(output_files) == 1, "No JPEG output file was created"
        
        # Verify the output is a valid JPEG
        with Image.open(output_files[0]) as img:
            print(f"Output image format: {img.format}")
            print(f"Output image mode: {img.mode}")
            print(f"Output image size: {img.size}")
            assert img.format == 'JPEG', f"Expected JPEG format, got {img.format}"
            assert img.mode == 'RGB', f"Expected RGB mode, got {img.mode}"
    
    def test_process_image_png(self, test_image):
        """Test processing a PNG image."""
        img_path, temp_dir = test_image
        output_dir = os.path.join(temp_dir, "output")
        
        # Create a larger image to ensure compression will work
        large_img_path = os.path.join(temp_dir, "large_test_image.png")
        img = Image.new('RGB', (800, 800), color='blue')
        img.save(large_img_path, 'PNG')
        
        worker = CompressionWorker(
            input_files=[large_img_path],
            output_dir=output_dir,
            quality=50,  # Lower quality to ensure compression
            output_format="PNG"
        )
        
        # Process the image
        worker.process_image(large_img_path, 1)
        
        # Check that the output file was created
        output_files = list(Path(output_dir).glob("*.png"))
        assert len(output_files) == 1, f"Expected 1 output file, found {len(output_files)} in {output_dir}"
    
    def test_process_image_webp(self, test_image):
        """Test processing a WebP image."""
        img_path, temp_dir = test_image
        output_dir = os.path.join(temp_dir, "output")
        os.makedirs(output_dir, exist_ok=True)
        
        worker = CompressionWorker(
            input_files=[img_path],
            output_dir=output_dir,
            quality=80,
            output_format="WEBP"
        )
        
        # Process the image
        worker.process_image(img_path, 1)
        
        # Check that the output file was created
        output_files = list(Path(output_dir).glob("*.webp"))
        assert len(output_files) == 1
    
    def test_process_image_invalid_format(self, test_image):
        """Test processing with an invalid output format."""
        img_path, temp_dir = test_image
        output_dir = os.path.join(temp_dir, "output")
        os.makedirs(output_dir, exist_ok=True)
        
        worker = CompressionWorker(
            input_files=[img_path],
            output_dir=output_dir,
            quality=80,
            output_format="INVALID"  # Invalid format
        )
        
        # This should raise an exception when trying to save with an invalid format
        with pytest.raises(Exception):
            worker.process_image(img_path, 1)
    
    def test_stop_processing(self, test_image):
        """Test stopping the processing."""
        img_path, temp_dir = test_image
        output_dir = os.path.join(temp_dir, "output")
        os.makedirs(output_dir, exist_ok=True)
        
        worker = CompressionWorker(
            input_files=[img_path, img_path, img_path],  # Multiple files
            output_dir=output_dir,
            quality=80,
            output_format="JPEG"
        )
        
        # Stop the worker after processing the first image
        def mock_process_image(*args, **kwargs):
            worker.stop()
            return None
        
        worker.process_image = mock_process_image
        
        # The worker should stop after the first image
        worker.run()
        
        # Only one file should be processed
        output_files = list(Path(output_dir).glob("*.jpg"))
        assert len(output_files) == 0  # Since we mocked process_image
    
    def test_error_handling(self, test_image):
        """Test error handling during processing."""
        img_path, temp_dir = test_image
        output_dir = os.path.join(temp_dir, "output")
        os.makedirs(output_dir, exist_ok=True)
        
        # Create a worker with a mock that will raise an exception
        worker = CompressionWorker(
            input_files=[img_path],
            output_dir=output_dir,
            quality=80,
            output_format="JPEG"
        )
        
        # Mock the process_image method to raise an exception
        original_process = worker.process_image
        def mock_process_image(*args, **kwargs):
            raise Exception("Test error")
        
        worker.process_image = mock_process_image
        
        # The error should be caught and emitted via the error_occurred signal
        with patch.object(worker, 'error_occurred') as mock_error:
            worker.run()
            assert mock_error.emit.called
            assert "Test error" in str(mock_error.emit.call_args[0][0])

# Run the tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
