#!/bin/bash

# Define the virtual environment path
VENV_PATH="$HOME/kalandor/venv"

# Define the path within the AppImage temporary directory
APP_DIR="${APPDIR}"  # APPDIR is set by AppImage at runtime to the mounted directory

# Check if the virtual environment exists, if not create it
if [ ! -d "$VENV_PATH" ]; then
    echo "Creating virtual environment..."
    python3 -m venv "$VENV_PATH"
fi

# Activate the virtual environment
source "$VENV_PATH/bin/activate"

# Install requirements (make sure requirements.txt is included in the AppImage and is accessible at this path)
pip install -r "${APP_DIR}/requirements.txt"

# Run the Python application
python "${APP_DIR}/usr/bin/main.py"
