@echo off
REM Build script for ImageMaster Windows installer

echo [*] Setting up Python virtual environment...
python -m venv venv
call venv\Scripts\activate.bat

REM Install required packages
echo [*] Installing required packages...
pip install --upgrade pip
pip install -r requirements.txt
pip install pyinstaller nsis

REM Build the executable
echo [*] Building executable...
python build_windows.py

if exist "dist\ImageMaster-Installer.exe" (
    echo [*] Build successful! Installer created at: dist\ImageMaster-Installer.exe
    echo [*] You can now distribute this installer to other Windows machines.
) else (
    echo [ERROR] Build failed. Check the output above for errors.
    pause
    exit /b 1
)

pause
