#!/bin/bash
# Build LeadTime App with PyInstaller
# Usage: bash build.sh

set -e

cd "$(dirname "$0")"

echo "=== Installing PyInstaller ==="
source venv/bin/activate
pip install pyinstaller

echo "=== Cleaning old build ==="
rm -rf build dist __pycache__
find . -name "*.pyc" -delete

echo "=== Running PyInstaller ==="
pyinstaller leadtime.spec --noconfirm --clean

echo ""
echo "=== Build Complete ==="
echo "Output: dist/LeadTimeApp/"
echo ""

if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    echo "Windows build: dist/LeadTimeApp.exe"
else
    echo "Linux/macOS build: run dist/LeadTimeApp/LeadTimeApp"
fi
