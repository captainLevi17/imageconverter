import os
import sys
import subprocess
import shutil

def clean():
    """Clean up previous builds."""
    for dir_name in ['build', 'dist', 'ImageMaster']:
        if os.path.exists(dir_name):
            print(f"Removing {dir_name}...")
            shutil.rmtree(dir_name, ignore_errors=True)

def build():
    """Build the executable using PyInstaller."""
    print("Building executable with PyInstaller...")
    
    # Ensure the assets directory exists
    os.makedirs('assets', exist_ok=True)
    
    # Simple PyInstaller command
    cmd = [
        sys.executable, '-m', 'PyInstaller',
        '--name=ImageMaster',
        '--windowed',
        '--onefile',
        '--add-data=assets;assets',
        '--add-data=tools;tools',
        '--add-data=utils;utils',
        'main.py'
    ]
    
    print("Running command:", ' '.join(cmd))
    subprocess.check_call(cmd)

def main():
    print("=== Starting ImageMaster Build ===")
    clean()
    build()
    print("\nBuild completed!")
    print("Executable is in the 'dist' directory.")

if __name__ == "__main__":
    main()
