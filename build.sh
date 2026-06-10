#!/bin/bash
# Build LeadTime App dengan PyInstaller
# Usage: bash build.sh [--clean]
#
# --clean  : hapus build/ dan dist/ dulu, fresh build
# (tanpa)  : incremental build (lebih cepat)

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# ── Python venv ──────────────────────────────────────
if [ ! -d "venv" ]; then
    echo "=== Membuat virtual environment ==="
    python3 -m venv venv
fi

source venv/bin/activate

echo "=== Install dependencies ==="
pip install -q -r requirements.txt pyinstaller

# ── Clean ────────────────────────────────────────────
if [ "$1" = "--clean" ]; then
    echo "=== Cleaning old build ==="
    rm -rf build dist
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
fi

# ── Build ────────────────────────────────────────────
echo "=== Running PyInstaller ==="
pyinstaller leadtime.spec --noconfirm

# ── Result ───────────────────────────────────────────
echo ""
echo "========================================"
echo "  BUILD SELESAI"
echo "========================================"

if [ -f "dist/LeadTimeApp" ]; then
    SIZE=$(du -sh dist/LeadTimeApp | cut -f1)
    echo "  Binary : dist/LeadTimeApp ($SIZE)"
    echo "  Run    : ./dist/LeadTimeApp"
elif [ -f "dist/LeadTimeApp.exe" ]; then
    SIZE=$(du -sh dist/LeadTimeApp.exe | cut -f1)
    echo "  Binary : dist/LeadTimeApp.exe ($SIZE)"
fi

if [ -d "dist/LeadTimeApp" ]; then
    echo "  Folder : dist/LeadTimeApp/"
    echo "  Run    : dist/LeadTimeApp/LeadTimeApp"
fi
