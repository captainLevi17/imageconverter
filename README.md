# Image Master

A Python desktop application for image manipulation with PyQt5.

## Features

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

## Dependencies
- Python 3.10+
- PyQt5
- Pillow
- pillow-heif (for HEIC support)

See `requirements.txt` for complete list.
