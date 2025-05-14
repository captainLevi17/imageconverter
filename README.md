# Image Master

A Python desktop application for image manipulation with PyQt5.

## Features

### Image Resizer Tool
- Batch process multiple images
- Preset sizes (Small, Medium, HD)
- Custom width/height input
- Maintain aspect ratio option
- Enlarge smaller images option
- Visual preview with scaling information
- Clear output location indicators

### Base64 Converter Tool
- Convert images to Base64 encoded strings
- Convert Base64 encoded strings to images
- Support for various image formats (e.g. JPEG, PNG, GIF)

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

See `requirements.txt` for complete list.
