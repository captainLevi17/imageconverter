# Image Master Specification

## Project Summary
Image Master is a desktop application built with Python designed for image manipulation. It supports:
- Image format conversion
- Resizing
- Compression
- Cropping
- Encoding
- Background removal

## Technology Stack
- Python 3.10+
- GUI Framework: PyQt5
- Image Processing Libraries:
  - Pillow (basic operations)
  - OpenCV (cropping, background removal)
  - rembg (AI background removal)
  - piexif (EXIF data handling)
  - pillow-heif (HEIC/HEIF support)

## Application Modules
1. **Home Dashboard**
2. **HEIC to JPG/PNG Converter**
3. **Image Resizer**
4. **Image Compressor**
   - Batch processing of multiple images
   - Real-time preview of compression results
   - Adjustable quality settings (1-100%)
   - Support for multiple output formats (JPEG, PNG, WebP)
   - Thumbnail gallery for easy selection
   - File size comparison between original and compressed
   - Preserve metadata option
   - Custom output directory selection
5. **Image Cropper"
6. **Image to Base64 Converter**
   - Convert between images and Base64 strings
   - Copy as HTML snippet with one click
   - Multiple output formats (TXT, JSON, HTML)
   - Support for all major image formats
7. **WebP Converter**
   - Convert between WebP and other formats (JPG, PNG)
   - Thumbnail gallery for easy image selection
   - Real-time preview of selected images
   - Adjustable quality settings (1-100%)
   - Lossless compression option
   - Preserve metadata option
   - Custom output directory selection
   - Batch processing support
   - Image information display (dimensions, file size, format)
8. **Image Background Remover**

## Supported File Types
Input: JPG, PNG, BMP, TIFF, WebP, HEIC/HEIF
Output: JPG, PNG, WebP, Base64

## Batch Processing
All major functions support batch operations with progress tracking and real-time feedback

## Full Specification
[Original detailed spec would be maintained here]
