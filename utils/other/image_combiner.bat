@echo off
echo.
echo ===============================================
echo Image Vertical Combiner
echo ===============================================
echo.

python --version > nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed
    echo Please install Python from https://www.python.org/downloads/
    pause
    exit /b 1
)

if "%~1"=="" (
    echo Usage:
    echo Drag and drop multiple image files onto this bat file
    echo.
    echo Supported formats: JPG, PNG, BMP, GIF, TIFF, WebP
    echo.
    pause
    exit /b 1
)

set SCRIPT_DIR=%~dp0
set PYTHON_SCRIPT=%SCRIPT_DIR%combine_images.py

if not exist "%PYTHON_SCRIPT%" (
    echo Error: combine_images.py not found
    echo Please place combine_images.py in the same folder as this bat file
    pause
    exit /b 1
)

echo Processing...
echo.

python "%PYTHON_SCRIPT%" %*

if errorlevel 1 (
    echo.
    echo Error occurred during processing
) else (
    echo.
    echo Processing completed successfully
)

echo.
pause