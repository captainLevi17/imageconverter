# Changelog

## [Unreleased]
### Added
- Added Background Remover Tool with AI-powered background removal
- Implemented custom color selection for background replacement
- Added transparent background support (PNG)
- Added batch processing capability for background removal
- Implemented preview functionality for background removal
- Added comprehensive test suite for core functionality
- Added test coverage reporting
- Implemented CI-ready test configuration
- Added aspect ratio presets (e.g., 1:1, 16:9, 4:3, Free) to the Image Cropper tool
- Added image transformation controls (rotate, flip) to the Image Cropper
- Implemented output format and quality settings for the Image Cropper

### Changed
- **Codebase Optimization (2025-05-28)**:
  - Created shared utility modules in `utils/` package:
    - `ui_components.py`: Reusable UI components (ThumbnailLabel, ImagePreviewGallery, FileControls)
    - `image_utils.py`: Common image processing functions (loading, saving, resizing, format conversion)
    - `file_utils.py`: File system operations and validation
    - `preview.py`: Image preview and thumbnail management
  - Updated `__init__.py` to properly expose all public APIs
  - Improved code organization and reduced duplication
  - Added comprehensive docstrings and type hints
  - Standardized error handling across utility functions

### Fixed
- Fixed HEIC converter tab visibility when pillow-heif is installed
- Improved error handling in image processing tools
- Fixed memory management in batch processing
- Resolved image cropper accuracy issues by refining coordinate calculations and using `round()` for precision
- Fixed duplicate UI elements in the Image Cropper output settings
- Improved layout and organization of the Image Cropper interface
- Fixed issues with output directory selection and file naming

## [0.5.0] - 2025-05-26
### Added
- Added new Image Compressor Tool with preview functionality
- Implemented thumbnail gallery for image selection in all tools
- Added real-time preview to WebP Converter tool
- Support for JPEG, PNG, and WebP output formats
- Added quality adjustment slider (1-100%)
- Included file size comparison in preview
- Added preserve metadata option
- Implemented custom output directory selection
- Added image format and dimension information display
- Click-to-preview functionality in gallery view

## [0.4.0] - 2025-05-20
### Added
- Added "Copy HTML Snippet" button to Base64 tool for quick HTML image tag generation
- Added comprehensive preset categories to Image Resizer:
  - Common presets (800x600, 1280x720, 1920x1080, 2K, 4K)
  - Social Media presets (Instagram, Facebook, Twitter, LinkedIn)
  - Device-specific presets (iPhone, iPad, MacBook, 4K/8K monitors)
- Organized presets into collapsible group boxes for better usability

### Fixed
- Fixed QApplication import issue in HEIC converter
- Resolved duplicate method definitions in HEIC tool
- Improved error handling for HEIC image loading
- Fixed thumbnail generation and preview functionality
- Addressed UI responsiveness during conversion

### Changed
- Optimized HEIC image conversion process
- Improved error messages and user feedback
- Enhanced thumbnail grid layout

### Added
- HEIC to JPG/PNG conversion
- Thumbnail preview gallery
- Output quality settings (60-100%)
  - Maximum (100%)
  - High (90%)
  - Good (80%)
  - Medium (70%)
  - Low (60%)
- Output format selection (JPEG/PNG)
- Custom output directory selection
- Progress tracking during conversion

## [0.3.0] - 2025-05-19
### Fixed
- Resolved layout issues in Resizer tool
- Fixed Base64 tool button initialization
- Addressed QLayout warning messages
- Improved error handling in image processing
- Removed temporary development files

### Changed
- Cleaned up and optimized code structure
- Improved UI consistency across tools
- Enhanced error messages and user feedback
### Added
- Base64 output download options:
  - Added format selection (TXT, JSON, HTML)
  - Download button to save Base64 output in selected format
  - JSON output includes metadata (filename, timestamp, mime type)
  - HTML output generates an image tag with embedded Base64
  - Copy to clipboard respects selected format
- Output format selection in Resizer tool
  - Added dropdown menu for JPEG, PNG, and WebP formats
  - Automatic format conversion during image saving
  - Proper handling of format-specific settings (quality, color modes)
- Complete Base64 Converter tool implementation
  - Image to Base64 encoding
  - Base64 to image decoding
  - Clipboard copy functionality
  - Image preview capabilities
- Enhanced documentation (README.md)
- Responsive UI design for all tool interfaces

### Changed
- Improved window resizing behavior
- Fixed QSizePolicy import locations
- Resolved layout parenting warnings

### Fixed
- Aspect ratio calculations in Resizer tool
- Clipboard functionality in Base64 tool
- Various UI improvements
- Proper widget expansion/shrinking at different window sizes
- Maintained layout structure during resizing
- Minimum size constraints for all components

## [0.2.0] - Resizer Tool
- Batch image resizing
- Preset sizes (Small, Medium, HD)
- Aspect ratio preservation
- Visual scaling indicators
- Output location tracking

## [0.1.0] - Initial Setup
- Project structure
- Basic PyQt5 application framework
- Tabbed interface foundation
