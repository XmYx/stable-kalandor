#!/bin/bash

# Step 1: Install Wine
echo "Checking if Wine is installed..."
if ! command -v wine &> /dev/null
then
    echo "Wine could not be found, installing..."
    sudo apt-get update
    sudo apt-get install -y wine
else
    echo "Wine is already installed."
fi

# Define the Wine Python and PyInstaller paths
WINEPREFIX="$HOME/.wine"  # This is the default, change if you use a different Wine prefix
PYTHON_INSTALLER="python-3.10.4-amd64.exe"  # Change to the latest Python 3.10 installer
PYINSTALLER_PATH="C:/Python310/Scripts/pyinstaller.exe"
PYTHON_PATH="C:/Python310/python.exe"

# Step 2: Setup Wine environment
export WINEPREFIX
winetricks vcrun2015
winecfg
# Step 4: Install PyInstaller using the installed Python
echo "Installing PyInstaller..."
wine python -m pip install pyinstaller

# Define application and build directories
APP_DIR="app"  # Your app source directory, change as necessary
BUILD_DIR="build"  # Where to put the build files, change as necessary

# Step 5: Build the executable with PyInstaller
echo "Building the Windows executable with PyInstaller..."
wine python -m pip install -r "$APP_DIR/requirements.txt"
wine pyinstaller --onefile --noconfirm --log-level=ERROR --add-data "$APP_DIR/llm.py;." "$APP_DIR/main.py" --distpath "$BUILD_DIR"
echo "Build process completed. Check the $BUILD_DIR directory for the output."