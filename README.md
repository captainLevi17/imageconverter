# Comprehensive Image Manipulator

A Windows desktop application for various image manipulation tasks, built with Python, Tkinter, and Pillow.

## Features

The application aims to include the following features:
- **HEIC to JPG Conversion**: Convert HEIC/HEIF images to JPG format.
- **Image Resizing**: Resize images to specified dimensions or percentages.
- **Image Compression**: Reduce image file size with adjustable quality.
- **Enhanced Image Cropper**: Interactively crop images with features like fixed aspect ratios, resizing, moving, rotation, flipping, and undo. (Current Focus)
- **Image to Base64 Conversion**: Convert images to Base64 strings.
- **WebP Conversion**: Convert images to and from WebP format.
- **Image Background Removal**: Automatically remove backgrounds from images (will require `rembg`).

## Prerequisites

- Python 3.7+

## Setup

1.  **Project Directory:**
    Ensure you have this [README.md](cci:7://file:///e:/Projects/GitHub/Desktop%20Apps/Image%20Converter%20App/README.md:0:0-0:0) and [image_app.py](cci:7://file:///e:/Projects/GitHub/Desktop%20Apps/Image%20Converter%20App/image_app.py:0:0-0:0) in your project directory: `e:\Projects\GitHub\Desktop Apps\Image Converter App\`

2.  **Create a virtual environment (recommended):**
    Open a terminal or command prompt in your project directory.
    ```bash
    python -m venv venv
    ```
    Activate the virtual environment:
    - Windows: `.\venv\Scripts\activate`
    - macOS/Linux: `source venv/bin/activate`

3.  **Install dependencies:**
    Ensure your [requirements.txt](cci:7://file:///e:/Projects/GitHub/Desktop%20Apps/Image%20Converter%20App/requirements.txt:0:0-0:0) file in your project directory contains:
    ```
    Pillow>=9.0.0
    pillow-heif>=0.7.0
    rembg>=0.5.0 
    ```
    Then run:
    ```bash
    pip install -r requirements.txt
    ```

4.  **Run the application:**
    ```bash
    python image_app.py
    ```

## Project Structure

-   [image_app.py](cci:7://file:///e:/Projects/GitHub/Desktop%20Apps/Image%20Converter%20App/image_app.py:0:0-0:0): Main application script.
-   [requirements.txt](cci:7://file:///e:/Projects/GitHub/Desktop%20Apps/Image%20Converter%20App/requirements.txt:0:0-0:0): Python package dependencies.
-   [README.md](cci:7://file:///e:/Projects/GitHub/Desktop%20Apps/Image%20Converter%20App/README.md:0:0-0:0): This file.

## Development Focus

The current development focus is on implementing and refining the **Enhanced Image Cropper**.

### Enhanced Image Cropper Details

The cropper module provides a comprehensive set of tools for precise image cropping:

- **Image Loading**: Load common image formats (JPG, PNG, etc.) into the cropper.
- **Aspect Ratios**: 
    - **Freeform Selection**: Draw any rectangular crop area.
    - **Fixed Presets**: Choose from common aspect ratios like 1:1 (Square), 4:3, 16:9, and custom ratios.
    - The selection rectangle for fixed aspect ratios is always visible and interactive.
- **Interactive Selection**: 
    - **Drawing**: Click and drag to define a new crop area (in Freeform mode).
    - **Moving**: Click and drag inside an existing selection to move it.
    - **Resizing**: Drag the corners or edges of the selection rectangle to resize it. Aspect ratio is maintained for fixed presets. A minimum selection size is enforced.
- **Image Transformations** (applied to the entire image before cropping):
    - **Rotate**: 90° left or 90° right.
    - **Flip**: Horizontally or vertically.
- **Cropping Operation**:
    - The crop is performed directly on the displayed image (destructive within the cropper session).
    - The cropped area replaces the original image on the canvas.
- **Undo**: Revert the last destructive operation (crop, rotation, or flip).
- **Saving**: Save the finally cropped image to a new file (JPG, PNG, etc.).

## Contributing

Contributions are welcome. Please feel free to fork the project, make improvements, and submit pull requests. For major changes, please open an issue first to discuss what you would like to change.