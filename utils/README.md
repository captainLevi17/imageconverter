# Image Master - Utilities Documentation

This directory contains shared utilities and components used across the Image Master application. The utilities are organized into logical modules for better maintainability and code reuse.

## Table of Contents

1. [UI Components (`ui_components.py`)](#ui-components)
2. [Image Utilities (`image_utils.py`)](#image-utilities)
3. [File Utilities (`file_utils.py`)](#file-utilities)
4. [Preview Management (`preview.py`)](#preview-management)
5. [Initialization (`__init__.py`)](#initialization)

## UI Components (`ui_components.py`)

Reusable UI components that provide consistent look and behavior across the application.

### Key Components:

- **ThumbnailLabel**: A QLabel subclass for displaying image thumbnails with consistent styling.
  - Handles image scaling while maintaining aspect ratio
  - Provides hover and selection states
  - Used in gallery views and previews

- **ImagePreviewGallery**: A scrollable grid layout for displaying image thumbnails.
  - Handles dynamic thumbnail arrangement
  - Supports selection and navigation
  - Used in tools that need to display multiple images

- **FileControls**: Standard controls for file operations.
  - Browse/Open file dialogs
  - Clear selection
  - File count display
  - Used in tools that require file selection

## Image Utilities (`image_utils.py`)

Core image processing functions and helpers.

### Key Functions:

- **Image Loading/Saving**
  - `load_image(path)`: Safely loads an image from disk
  - `save_image(image, output_path, format, quality)`: Saves an image with proper error handling

- **Image Manipulation**
  - `resize_image(image, width, height, keep_aspect_ratio=True)`: Resizes images with optional aspect ratio preservation
  - `create_thumbnail(image_path, size, output_path)`: Creates thumbnails from images
  - `convert_image_format(image, format, **kwargs)`: Converts between image formats

- **Batch Processing**
  - `batch_process_images(image_paths, process_func, output_dir, **kwargs)`: Processes multiple images with a given function

## File Utilities (`file_utils.py`)

File system operations and path handling.

### Key Functions:

- **File Operations**
  - `validate_directory(path)`: Checks if a directory exists and is writable
  - `create_directory(path)`: Creates a directory if it doesn't exist
  - `get_unique_filename(path)`: Generates a non-conflicting filename
  - `get_file_size(path)`: Gets human-readable file size
  - `safe_remove_file(path)`: Safely removes a file with error handling
  - `copy_file(src, dst)`: Copies files with error handling

- **File Type Handling**
  - `get_supported_extensions()`: Returns list of supported image extensions
  - `is_supported_image(path)`: Checks if a file is a supported image type

## Preview Management (`preview.py`)

Image preview and thumbnail management.

### Key Components:

- **PreviewManager**: Manages image previews and thumbnails
  - Handles thumbnail generation and caching
  - Provides consistent preview sizes
  - Used for efficient image preview generation

- **ImageViewer**: Interactive image viewing widget
  - Supports zooming and panning
  - Maintains aspect ratio
  - Used in preview panels

## Initialization (`__init__.py`)

Package initialization that exposes the public API of the utils package.

### Usage Example:

```python
# Import utilities
from utils import (
    # UI Components
    ThumbnailLabel,
    ImagePreviewGallery,
    FileControls,
    
    # Image Utilities
    load_image,
    save_image,
    resize_image,
    
    # File Utilities
    validate_directory,
    create_directory,
    
    # Preview Management
    PreviewManager
)
```

## Best Practices

1. **Use the provided utilities** instead of reimplementing common functionality
2. **Keep UI components consistent** by using the provided UI components
3. **Handle errors appropriately** - most utility functions include error handling
4. **Use the PreviewManager** for all thumbnail and preview generation
5. **Follow the file utils** for all file system operations to ensure consistency
