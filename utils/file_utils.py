"""
File utilities for Image Master application.

This module contains common file operations used across the application.
"""

import os
import shutil
from pathlib import Path
from typing import List, Optional, Tuple, Union, Set

# Supported image file extensions
SUPPORTED_IMAGE_EXTENSIONS = {
    '.jpg', '.jpeg', '.png', '.webp', '.bmp', '.gif', '.tiff', '.heic', '.heif'
}

def get_supported_extensions() -> Set[str]:
    """Get a set of supported image file extensions.
    
    Returns:
        Set[str]: Set of supported file extensions (including leading dot).
    """
    return SUPPORTED_IMAGE_EXTENSIONS


def is_supported_image(filename: str) -> bool:
    """Check if a file has a supported image extension.
    
    Args:
        filename: Name or path of the file to check.
        
    Returns:
        bool: True if the file has a supported image extension, False otherwise.
    """
    ext = os.path.splitext(filename)[1].lower()
    return ext in SUPPORTED_IMAGE_EXTENSIONS


def validate_directory(path: str) -> Tuple[bool, str]:
    """Check if a directory exists and is writable.
    
    Args:
        path: Path to the directory to validate.
        
    Returns:
        Tuple[bool, str]: (is_valid, message) where is_valid is True if the directory 
        is valid, and message contains an error message if not.
    """
    try:
        path = os.path.abspath(path)
        if not os.path.exists(path):
            return False, f"Directory does not exist: {path}"
        if not os.path.isdir(path):
            return False, f"Path is not a directory: {path}"
        if not os.access(path, os.W_OK):
            return False, f"No write permission for directory: {path}"
        return True, ""
    except Exception as e:
        return False, f"Error validating directory: {str(e)}"


def create_directory(path: str) -> Tuple[bool, str]:
    """Create a directory if it doesn't exist.
    
    Args:
        path: Path to the directory to create.
        
    Returns:
        Tuple[bool, str]: (success, message) where success is True if the directory 
        was created or already exists, and message contains an error message if not.
    """
    try:
        path = os.path.abspath(path)
        os.makedirs(path, exist_ok=True)
        return True, ""
    except Exception as e:
        return False, f"Failed to create directory: {str(e)}"


def get_unique_filename(directory: str, filename: str) -> str:
    """Generate a unique filename in the specified directory.
    
    If a file with the same name exists, appends a number to make it unique.
    
    Args:
        directory: Directory where the file will be saved.
        filename: Desired filename.
        
    Returns:
        str: A unique filename in the specified directory.
    """
    base, ext = os.path.splitext(filename)
    counter = 1
    new_filename = filename
    
    while os.path.exists(os.path.join(directory, new_filename)):
        new_filename = f"{base}_{counter}{ext}"
        counter += 1
    
    return new_filename


def get_files_in_directory(
    directory: str, 
    recursive: bool = False,
    extensions: Optional[Set[str]] = None
) -> List[str]:
    """Get a list of files in a directory, optionally filtered by extension.
    
    Args:
        directory: Directory to search in.
        recursive: If True, search recursively in subdirectories.
        extensions: Set of file extensions to include (including leading dot).
                  If None, all files are included.
                  
    Returns:
        List[str]: List of file paths matching the criteria.
    """
    if not os.path.isdir(directory):
        return []
    
    files = []
    
    if recursive:
        for root, _, filenames in os.walk(directory):
            for filename in filenames:
                if extensions is None or any(filename.lower().endswith(ext) for ext in extensions):
                    files.append(os.path.join(root, filename))
    else:
        for filename in os.listdir(directory):
            full_path = os.path.join(directory, filename)
            if os.path.isfile(full_path) and (extensions is None or any(filename.lower().endswith(ext) for ext in extensions)):
                files.append(full_path)
    
    return files


def safe_remove_file(filepath: str) -> bool:
    """Safely remove a file if it exists.
    
    Args:
        filepath: Path to the file to remove.
        
    Returns:
        bool: True if the file was removed or didn't exist, False otherwise.
    """
    try:
        if os.path.exists(filepath):
            os.remove(filepath)
        return True
    except Exception as e:
        print(f"Error removing file {filepath}: {e}")
        return False


def copy_file(src: str, dst: str, overwrite: bool = False) -> bool:
    """Copy a file from source to destination.
    
    Args:
        src: Source file path.
        dst: Destination file path.
        overwrite: If True, overwrite destination if it exists.
        
    Returns:
        bool: True if the file was copied successfully, False otherwise.
    """
    try:
        if not os.path.exists(src):
            print(f"Source file does not exist: {src}")
            return False
            
        if os.path.exists(dst) and not overwrite:
            print(f"Destination file already exists (use overwrite=True to replace): {dst}")
            return False
            
        # Create destination directory if it doesn't exist
        os.makedirs(os.path.dirname(os.path.abspath(dst)), exist_ok=True)
        
        shutil.copy2(src, dst)
        return True
    except Exception as e:
        print(f"Error copying file from {src} to {dst}: {e}")
        return False


def get_file_size(filepath: str, human_readable: bool = False) -> Union[int, str]:
    """Get the size of a file.
    
    Args:
        filepath: Path to the file.
        human_readable: If True, return size in human-readable format.
        
    Returns:
        Union[int, str]: File size in bytes or human-readable string.
    """
    try:
        size = os.path.getsize(filepath)
        
        if not human_readable:
            return size
            
        # Convert to human-readable format
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.2f} {unit}"
            size /= 1024.0
        return f"{size:.2f} TB"
        
    except Exception as e:
        print(f"Error getting file size for {filepath}: {e}")
        return 0 if not human_readable else "0 B"
