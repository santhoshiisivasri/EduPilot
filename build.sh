#!/usr/bin/env bash
# ============================================================
# EduPilot – Render Build Script
# Runs during each deploy on Render
# ============================================================

set -o errexit  # Exit on error

echo "=== EduPilot Build Script ==="

# 1. Upgrade pip
pip install --upgrade pip

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run database migrations (if using Flask-Migrate)
# Uncomment below when you have migrations set up:
# python -m flask db upgrade

echo "=== Build Complete ==="
