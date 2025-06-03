import os
import sys
import subprocess
import shutil
import logging

def setup_logging():
    """Set up logging to file and console."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('build.log'),
            logging.StreamHandler()
        ]
    )

def clean():
    """Clean up previous builds."""
    for dir_name in ['build', 'dist']:
        if os.path.exists(dir_name):
            logging.info(f"Removing {dir_name} directory...")
            shutil.rmtree(dir_name, ignore_errors=True)

def build():
    """Build the executable using PyInstaller with debug options."""
    logging.info("Starting build process...")
    
    # Ensure the assets directory exists
    os.makedirs('assets', exist_ok=True)
    
    # PyInstaller command with debug options
    cmd = [
        sys.executable, '-m', 'PyInstaller',
        '--name=ImageMaster',
        '--windowed',
        '--onefile',
        '--clean',
        '--debug=all',
        '--log-level=DEBUG',
        '--noconfirm',
        '--add-data=assets;assets',
        '--add-data=tools;tools',
        '--add-data=utils;utils',
        'main.py'
    ]
    
    logging.info("Running PyInstaller with command: %s", ' '.join(cmd))
    
    try:
        subprocess.check_call(cmd)
        logging.info("Build completed successfully!")
    except subprocess.CalledProcessError as e:
        logging.error(f"Build failed with error: {e}")
        sys.exit(1)

def main():
    setup_logging()
    logging.info("=== Starting ImageMaster Debug Build ===")
    clean()
    build()
    logging.info("Build process completed. Check build.log for details.")

if __name__ == "__main__":
    main()
