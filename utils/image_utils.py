"""
Image utilities for Image Master application.

This module contains common image processing functions used across the application.
"""

import os
from PIL import Image, ImageOps
from typing import Optional, Tuple, Union, List


def load_image(image_path: str) -> Optional[Image.Image]:
    """Load an image from the given path.
    
    Args:
        image_path: Path to the image file.
        
    Returns:
        PIL.Image.Image: The loaded image or None if loading fails.
    """
    try:
        return Image.open(image_path)
    except Exception as e:
        print(f"Error loading image {image_path}: {e}")
        return None


def save_image(
    image: Image.Image, 
    output_path: str, 
    format: str = 'JPEG', 
    quality: int = 90
) -> bool:
    """Save an image to the specified path.
    
    Args:
        image: PIL Image to save.
        output_path: Path where to save the image.
        format: Output format (JPEG, PNG, etc.).
        quality: Quality for JPEG (1-100).
        
    Returns:
        bool: True if save was successful, False otherwise.
    """
    try:
        # Create output directory if it doesn't exist
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        
        # Save with optimized settings
        kwargs = {}
        if format.upper() == 'JPEG':
            kwargs['quality'] = quality
            kwargs['optimize'] = True
            kwargs['progressive'] = True
        
        image.save(output_path, format=format, **kwargs)
        return True
    except Exception as e:
        print(f"Error saving image to {output_path}: {e}")
        return False


def resize_image(
    image: Image.Image, 
    width: Optional[int] = None, 
    height: Optional[int] = None,
    keep_aspect_ratio: bool = True
) -> Image.Image:
    """Resize an image while optionally maintaining aspect ratio.
    
    Args:
        image: Input image.
        width: Target width in pixels. If None, calculated from height.
        height: Target height in pixels. If None, calculated from width.
        keep_aspect_ratio: Whether to maintain the aspect ratio.
        
    Returns:
        PIL.Image.Image: Resized image.
    """
    if width is None and height is None:
        return image
        
    original_width, original_height = image.size
    
    if keep_aspect_ratio:
        if width is not None and height is not None:
            # Use the smaller ratio to ensure the image fits within both dimensions
            width_ratio = width / original_width
            height_ratio = height / original_height
            ratio = min(width_ratio, height_ratio)
            new_width = int(original_width * ratio)
            new_height = int(original_height * ratio)
        elif width is not None:
            # Calculate height to maintain aspect ratio
            ratio = width / original_width
            new_width = width
            new_height = int(original_height * ratio)
        else:  # height is not None
            # Calculate width to maintain aspect ratio
            ratio = height / original_height
            new_width = int(original_width * ratio)
            new_height = height
    else:
        new_width = width if width is not None else original_width
        new_height = height if height is not None else original_height
    
    # Use LANCZOS for high-quality downsampling
    return image.resize((new_width, new_height), Image.Resampling.LANCZOS)


def create_thumbnail(
    image_path: str, 
    size: Tuple[int, int] = (200, 200),
    output_path: Optional[str] = None
) -> Optional[str]:
    """Create a thumbnail of the specified size.
    
    Args:
        image_path: Path to the source image.
        size: Target size as (width, height).
        output_path: Path to save the thumbnail. If None, saves in memory.
        
    Returns:
        Optional[str]: Path to the saved thumbnail or None if failed.
    """
    try:
        with Image.open(image_path) as img:
            # Create thumbnail (modifies in place)
            img.thumbnail(size, Image.Resampling.LANCZOS)
            
            if output_path is None:
                # Generate a temporary path if none provided
                base, ext = os.path.splitext(image_path)
                output_path = f"{base}_thumb{ext}"
            
            # Save the thumbnail
            img.save(output_path)
            return output_path
    except Exception as e:
        print(f"Error creating thumbnail for {image_path}: {e}")
        return None


def get_image_info(image_path: str) -> dict:
    """Get basic information about an image.
    
    Args:
        image_path: Path to the image file.
        
    Returns:
        dict: Dictionary containing image information.
    """
    try:
        with Image.open(image_path) as img:
            return {
                'path': image_path,
                'format': img.format,
                'size': img.size,  # (width, height)
                'mode': img.mode,
                'size_bytes': os.path.getsize(image_path)
            }
    except Exception as e:
        print(f"Error getting info for {image_path}: {e}")
        return {}


def convert_image_format(
    image: Image.Image, 
    format: str = 'JPEG',
    **kwargs
) -> Image.Image:
    """Convert an image to a different format.
    
    Args:
        image: Input image.
        format: Target format (JPEG, PNG, etc.).
        **kwargs: Additional format-specific parameters.
        
    Returns:
        PIL.Image.Image: Converted image.
    """
    if image.mode in ('RGBA', 'LA') and format.upper() == 'JPEG':
        # Convert to RGB for JPEG output
        background = Image.new('RGB', image.size, (255, 255, 255))
        background.paste(image, mask=image.split()[-1])
        return background
    return image


def batch_process_images(
    image_paths: List[str], 
    process_func: callable,
    output_dir: Optional[str] = None,
    **kwargs
) -> List[str]:
    """Process multiple images with the given function.
    
    Args:
        image_paths: List of input image paths.
        process_func: Function that processes a single image.
        output_dir: Directory to save processed images. If None, uses input directory.
        **kwargs: Additional arguments to pass to process_func.
        
    Returns:
        List[str]: Paths to the processed images.
    """
    results = []
    
    for img_path in image_paths:
        try:
            img = load_image(img_path)
            if img is None:
                continue
                
            # Process the image
            processed = process_func(img, **kwargs)
            
            # Determine output path
            if output_dir is None:
                output_dir = os.path.dirname(img_path)
            
            filename = os.path.basename(img_path)
            base, ext = os.path.splitext(filename)
            output_format = kwargs.get('format', 'JPEG')
            output_ext = f".{output_format.lower()}" if output_format else ext
            output_path = os.path.join(output_dir, f"{base}_processed{output_ext}")
            
            # Save the processed image
            if save_image(processed, output_path, format=output_format, 
                         quality=kwargs.get('quality', 90)):
                results.append(output_path)
                
        except Exception as e:
            print(f"Error processing {img_path}: {e}")
    
    return results
