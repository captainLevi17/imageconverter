# Changelog

## [Unreleased] - 2025-05-18
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
