# Image Master

A Python desktop application for image manipulation with PyQt5.

## Features

### Image Compressor Tool
- Batch process multiple images
- Preview before and after compression
- Adjustable quality settings (1-100%)
- Support for multiple output formats (JPEG, PNG, WebP)
- Thumbnail gallery for easy selection
- Visual comparison of original and compressed sizes
- Custom output directory selection
- Preserve image metadata option

### Image Resizer Tool
- Batch process multiple images
- **Preset Sizes**:
  - **Common**: 800x600, 1280x720, 1920x1080, 2K (2560x1440), 4K (3840x2160)
  - **Social Media**: 
    - Instagram Post (1080x1080), Story (1080x1920)
    - Facebook Post (1200x630)
    - Twitter Header (1500x500)
    - LinkedIn Post (1200x627)
  - **Devices**:
    - iPhone 15 (1179x2556)
    - iPad Pro (2048x2732)
    - MacBook Pro 16" (3072x1920)
    - 4K/8K Monitors
- Custom width/height input
- Maintain aspect ratio option
- Enlarge smaller images option
- Visual preview with scaling information
- Clear output location indicators

### HEIC Converter Tool
- Convert HEIC/HEIF images to JPG or PNG
- Batch process multiple HEIC files
- Thumbnail preview gallery
- Adjustable output quality (60-100%)
- Choose output format (JPEG/PNG)
- Custom output directory selection
- Progress tracking during conversion

### Base64 Converter Tool
- Convert images to Base64 encoded strings
- Convert Base64 encoded strings to images
- Support for various image formats (e.g. JPEG, PNG, GIF, HEIC)
- Copy as HTML snippet with one click
- Multiple output formats: Plain Text, JSON, HTML

### Background Remover Tool
- Remove backgrounds from images with AI-powered processing
- Multiple background options:
  - Transparent (PNG)
  - Solid color (white, black, or custom)
- Batch process multiple images
- Preview before processing
- Supports various image formats
- Custom output directory selection

### Image Cropper Tool
- Interactively select an area of an image to crop
- Preview the selected crop area
- Choose from predefined aspect ratios (e.g., 1:1, 16:9, 4:3, Free) or crop freely.
- Save the cropped image in various formats (JPEG, PNG, WebP)
- Adjustable quality for JPEG/WebP output
- Custom output directory selection

## Installation

1. Clone this repository
2. Install requirements:
```bash
pip install -r requirements.txt
```

## Usage

Run the application:
```bash
python main.py
```

### Resizer Tool Guide
1. Click "Browse Images" to select images
2. Choose resize method:
   - Select preset size
   - Enter custom dimensions
3. Toggle options:
   - Maintain Aspect Ratio
   - Enlarge Smaller Images
4. Select output folder (optional)
5. Click "Resize Images"

Output files will have "_resized" suffix and be saved in:
- Specified output folder, or
- Same folder as originals if no output folder selected

### HEIC Converter Guide
1. Click "Add HEIC Images" to select HEIC/HEIF files
2. View thumbnails in the gallery
3. Click any thumbnail to see a larger preview
4. Select output format (JPEG/PNG)
5. Choose quality setting (60-100%)
6. (Optional) Click "Select Output Directory" to choose save location
7. Click "Convert to JPG/PNG"

Output files will be saved in:
- Specified output folder, or
- Same folder as originals if no output folder selected

### Base64 Converter Guide
1. Click "Browse Image" to select an image
2. Choose conversion method:
   - Image to Base64
   - Base64 to Image
3. Enter output file name (optional)
4. Click "Convert"

Output files will be saved in:
- Specified output folder, or
- Same folder as originals if no output folder selected

### Image Cropper Tool Guide
1. Click "Browse Images" to load an image into the cropper.
2. (Optional) Select a predefined aspect ratio from the available presets (e.g., 1:1, 16:9, 4:3) or leave as 'Free' for custom selection.
3. Click and drag on the image to draw a selection rectangle. If an aspect ratio is set, the selection will maintain it.
4. Adjust the selection by dragging the rectangle or its resize handles.
5. Select the desired output format (JPEG, PNG, WebP).
6. Adjust quality for JPEG/WebP if needed using the slider.
7. (Optional) Click "Select Output Directory" to choose a custom save location.
8. Click "Crop and Save Image".

Output files will have a "_cropped" suffix and be saved in:
- The specified output folder, or
- The same folder as the original image if no output folder is selected.

## Dependencies
- Python 3.10+
- PyQt5
- Pillow
- pillow-heif (for HEIC support)

See `requirements.txt` for complete list.
