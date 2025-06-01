"""
Worker thread for compressing images in the background.
"""
import os
from typing import List, Optional

from PyQt5.QtCore import QThread, pyqtSignal, pyqtSlot
from PIL import Image, ImageFile

# Configure PIL to be more tolerant of image files
ImageFile.LOAD_TRUNCATED_IMAGES = True

class CompressWorker(QThread):
    """Worker thread for compressing images in the background."""
    
    # Signals
    progress_updated = pyqtSignal(int)  # Current progress (1-based index)
    finished = pyqtSignal()  # Emitted when all images are processed
    error_occurred = pyqtSignal(str)  # Emitted when an error occurs
    
    def __init__(self, image_paths: List[str], output_dir: str, quality: int, 
                 output_format: str, preserve_metadata: bool = True):
        """Initialize the worker.
        
        Args:
            image_paths: List of input image paths
            output_dir: Directory to save compressed images
            quality: Compression quality (1-100)
            output_format: Output format ('jpeg', 'png', 'webp')
            preserve_metadata: Whether to preserve image metadata
        """
        super().__init__()
        self.image_paths = image_paths
        self.output_dir = output_dir
        self.quality = quality
        self.output_format = output_format.lower()
        self.preserve_metadata = preserve_metadata
        self._is_running = True
    
    def run(self):
        """Process all images in a separate thread."""
        try:
            for i, image_path in enumerate(self.image_paths, 1):
                if not self._is_running:
                    break
                
                try:
                    self._process_single_image(image_path)
                    self.progress_updated.emit(i)
                except Exception as e:
                    self.error_occurred.emit(
                        f"Error processing {os.path.basename(image_path)}: {str(e)}"
                    )
            
            if self._is_running:
                self.finished.emit()
                
        except Exception as e:
            self.error_occurred.emit(f"Unexpected error: {str(e)}")
    
    def _process_single_image(self, input_path: str) -> None:
        """Process a single image with the current settings.
        
        Args:
            input_path: Path to the input image
            
        Raises:
            Exception: If processing fails
        """
        try:
            # Generate output filename
            filename = os.path.basename(input_path)
            name, _ = os.path.splitext(filename)
            output_path = os.path.join(
                self.output_dir,
                f"{name}_compressed.{self.output_format}"
            )
            
            # Open and process the image
            with Image.open(input_path) as img:
                # Convert to RGB if necessary (for JPEG)
                if self.output_format == 'jpeg' and img.mode in ('RGBA', 'P'):
                    img = img.convert('RGB')
                
                # Prepare save options
                save_kwargs = {
                    'quality': self.quality,
                    'optimize': True
                }
                
                # Format-specific options
                if self.output_format == 'jpeg':
                    save_kwargs['progressive'] = True
                elif self.output_format == 'webp':
                    save_kwargs['method'] = 6  # Best quality/speed tradeoff
                
                # Handle metadata if needed
                if self.preserve_metadata and 'exif' in img.info:
                    save_kwargs['exif'] = img.info['exif']
                
                # Save the image
                img.save(output_path, **save_kwargs)
                
        except Exception as e:
            raise Exception(f"Failed to process {filename}: {str(e)}")
    
    def stop(self):
        """Stop the worker thread."""
        self._is_running = False
