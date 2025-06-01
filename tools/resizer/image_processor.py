"""
Image processing functionality for the Resizer tool.
"""
import os
from pathlib import Path
from typing import Optional, Tuple, Dict, Any
from PIL import Image
from utils.file_utils import get_unique_filename

def calculate_dimensions(
    img: Image.Image,
    target_width: int,
    target_height: int,
    maintain_aspect: bool,
    allow_enlarge: bool
) -> Tuple[int, int]:
    """Calculate the new dimensions for resizing.
    
    Args:
        img: Input image
        target_width: Target width in pixels
        target_height: Target height in pixels
        maintain_aspect: Whether to maintain aspect ratio
        allow_enlarge: Whether to allow enlarging the image
        
    Returns:
        Tuple of (new_width, new_height)
    """
    orig_width, orig_height = img.size
    
    if not allow_enlarge:
        target_width = min(target_width, orig_width)
        target_height = min(target_height, orig_height)
    
    if not maintain_aspect:
        return target_width, target_height
        
    # Calculate dimensions to maintain aspect ratio
    ratio = min(target_width/orig_width, target_height/orig_height)
    new_width = int(orig_width * ratio)
    new_height = int(orig_height * ratio)
    
    return new_width, new_height

def process_single_image(
    input_path: str,
    output_dir: str,
    width: int,
    height: int,
    output_format: str,
    maintain_aspect: bool = True,
    allow_enlarge: bool = False,
    quality: int = 95
) -> Optional[str]:
    """Process and save a single image with the given settings.
    
    Args:
        input_path: Path to the input image
        output_dir: Directory to save the processed image
        width: Target width in pixels
        height: Target height in pixels
        output_format: Output format (JPEG, PNG, etc.)
        maintain_aspect: Whether to maintain aspect ratio
        allow_enlarge: Whether to allow enlarging the image
        quality: Quality setting for output (1-100)
        
    Returns:
        Path to the saved image, or None if processing failed
    """
    try:
        with Image.open(input_path) as img:
            # Calculate new dimensions
            new_width, new_height = calculate_dimensions(
                img, width, height, maintain_aspect, allow_enlarge
            )
            
            # Resize the image
            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # Prepare output path
            output_dir = Path(output_dir).resolve()
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate output filename
            input_path = Path(input_path)
            output_ext = output_format.lower()
            output_filename = f"{input_path.stem}_resized.{output_ext}"
            unique_filename = get_unique_filename(str(output_dir), output_filename)
            output_path = output_dir / unique_filename
            
            # Prepare save options
            save_options: Dict[str, Any] = {}
            if output_format == 'JPEG':
                save_options['quality'] = quality
                # Convert RGBA to RGB for JPEG
                if img.mode == 'RGBA':
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    background.paste(img, mask=img.split()[3])
                    img = background
            
            # Save the image
            img.save(output_path, format=output_format, **save_options)
            return str(output_path)
            
    except Exception as e:
        print(f"Error processing {input_path}: {str(e)}")
        import traceback
        traceback.print_exc()
        return None
