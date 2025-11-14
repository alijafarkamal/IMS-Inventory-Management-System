#!/bin/bash
# Build script for Linux executable using PyInstaller

set -e

echo "Building Linux executable for Inventory Management System..."

# Get the project root directory
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -q --upgrade pip
pip install -q -r requirements.txt
pip install -q pyinstaller

# Create dist directory
mkdir -p dist

# Build with PyInstaller
echo "Building executable..."
pyinstaller \
    --name="inventory_app" \
    --onefile \
    --windowed \
    --add-data="inventory_app/src/inventory_app:inventory_app" \
    --hidden-import="ttkbootstrap" \
    --hidden-import="sqlalchemy.dialects.sqlite" \
    --hidden-import="pandas" \
    --hidden-import="openpyxl" \
    --hidden-import="passlib" \
    --hidden-import="cryptography" \
    --hidden-import="apscheduler" \
    --hidden-import="loguru" \
    --collect-all="ttkbootstrap" \
    --collect-all="sqlalchemy" \
    --clean \
    inventory_app/src/inventory_app/main.py

# Check if build was successful
if [ -f "dist/inventory_app" ]; then
    echo "Build successful! Executable created at: dist/inventory_app"
    echo "You can run it with: ./dist/inventory_app"
    
    # Make executable
    chmod +x dist/inventory_app
    
    # Show file size
    ls -lh dist/inventory_app
else
    echo "Build failed! Check the output above for errors."
    exit 1
fi

echo "Build process completed!"

