@echo off
setlocal

rem Define the home directory and paths for the virtual environment and application
set "HOME_DIR=%USERPROFILE%\kalandor"
set "VENV_PATH=%HOME_DIR%\venv"
set "APP_DIR=%HOME_DIR%\app"
set "PYTHON_EXE=%VENV_PATH%\Scripts\python.exe"
set "PIP_EXE=%VENV_PATH%\Scripts\pip.exe"

rem Ensure the application directory exists
if not exist "%APP_DIR%" (
    echo Application directory does not exist. Please check the installation.
    exit /b
)

rem Check if the virtual environment exists, if not, create it
if not exist "%PYTHON_EXE%" (
    echo Creating virtual environment...
    python -m venv "%VENV_PATH%"
)

rem Activate the virtual environment and install requirements
call "%VENV_PATH%\Scripts\activate.bat"
echo Installing requirements...
call "%PIP_EXE%" install -r "%APP_DIR%\requirements.txt"

rem Run the Python application
echo Running application...
call "%PYTHON_EXE%" "%APP_DIR%\main.py"

endlocal