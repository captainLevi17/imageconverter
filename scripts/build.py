#!/usr/bin/env python3
"""
Build script for creating standalone executables using PyInstaller.
"""
import os
import shutil
import subprocess
import sys
from pathlib import Path

def build_executable():
    """Build the standalone executable using PyInstaller."""
    # Ensure we're in the project root
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)
    
    # Clean up previous builds
    build_dir = project_root / "build"
    dist_dir = project_root / "dist"
    spec_file = project_root / "image-master.spec"
    
    for path in [build_dir, dist_dir]:
        if path.exists():
            shutil.rmtree(path)
    if spec_file.exists():
        spec_file.unlink()
    
    # Determine the correct PyInstaller command based on the platform
    if sys.platform == 'win32':
        pyinstaller_cmd = 'pyinstaller'
    else:
        pyinstaller_cmd = 'python -m PyInstaller'
    
    # Build the executable
    cmd = (
        f"{pyinstaller_cmd} --noconfirm --onefile --windowed "
        "--name image-master "
        "--icon=assets/icon.ico "
        "--add-data=assets;assets "
        "--add-data=README.md;. "
        "--add-data=CHANGELOG.md;. "
        "--hidden-import=PIL "
        "--hidden-import=PIL._tkinter_finder "
        "--hidden-import=PyQt5.QtCore "
        "--hidden-import=PyQt5.QtGui "
        "--hidden-import=PyQt5.QtWidgets "
        "main.py"
    )
    
    print("Building executable...")
    result = subprocess.run(cmd, shell=True, check=False)
    
    if result.returncode == 0:
        print("\nBuild completed successfully!")
        print(f"Executable location: {dist_dir / 'image-master'}")
    else:
        print("\nBuild failed!")
        sys.exit(1)

if __name__ == "__main__":
    build_executable()
