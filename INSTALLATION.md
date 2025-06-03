# Installation Instructions for Windows

## Prerequisites

1. **NSIS (Nullsoft Scriptable Install System)** - Required for creating the installer
   - Download and install from: https://nsis.sourceforge.io/Download
   - Make sure to add NSIS to your system PATH during installation

2. **Python 3.8 or higher**
   - Download and install from: https://www.python.org/downloads/
   - During installation, make sure to check "Add Python to PATH"

## Building the Installer

1. Open a command prompt in the project directory

2. Install the required Python packages:
   ```
   pip install -r requirements.txt
   pip install pyinstaller nsis
   ```

3. Run the build script:
   ```
   python build_windows.py
   ```

4. The installer will be created at: `dist/ImageMaster-Installer.exe`

## Creating a Distribution Package

1. After building the installer, you'll find the following files:
   - `dist/ImageMaster-Installer.exe` - The main installer
   - `dist/ImageMaster/` - The application files (for advanced users)

2. To distribute the application, you only need to share the `ImageMaster-Installer.exe` file.

## Installation

1. Run `ImageMaster-Installer.exe`
2. Follow the on-screen instructions
3. The application will be installed in `C:\Program Files\ImageMaster` by default
4. Shortcuts will be created in the Start Menu and on the Desktop

## Uninstallation

1. Go to Control Panel > Programs > Uninstall a program
2. Find "ImageMaster" in the list
3. Click Uninstall

## Troubleshooting

### Missing DLL Errors
If you encounter missing DLL errors, you may need to install the Visual C++ Redistributable:
- Download and install from: https://aka.ms/vs/17/release/vc_redist.x64.exe

### HEIC Support
For HEIC image support on Windows, you'll need to install the HEIF Image Extensions:
1. Open Microsoft Store
2. Search for "HEIF Image Extensions"
3. Install the app from Microsoft Corporation

### Other Issues
If you encounter any other issues, please check the following:
1. Make sure all dependencies are installed
2. Check the Windows Event Viewer for detailed error messages
3. Open an issue on the project's GitHub repository with details about the problem
