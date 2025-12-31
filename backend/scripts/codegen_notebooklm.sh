#!/bin/bash

# Script to run playwright codegen for notebooklm.google.com
# If test_google_login profile doesn't exist, it will be created by running google_login.py

set -e  # Exit on error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
PROJECT_ROOT="$(cd "$BACKEND_DIR/.." && pwd)"
PROFILE_DIR="$BACKEND_DIR/browser_profiles/test_google_login"

# Ensure the browser_profiles directory exists
mkdir -p "$BACKEND_DIR/browser_profiles"

# Check if profile directory exists and has content
if [ ! -d "$PROFILE_DIR" ] || [ -z "$(ls -A "$PROFILE_DIR" 2>/dev/null)" ]; then
    echo "[*] Profile directory '$PROFILE_DIR' doesn't exist or is empty."
    echo "[*] Creating it by running google_login.py..."
    
    # Change to project root to ensure relative paths work
    cd "$PROJECT_ROOT"
    
    # Run google_login.py to create the profile and login to Gmail
    # Set PYTHONPATH to include backend directory
    export PYTHONPATH="$BACKEND_DIR:$PYTHONPATH"
    python3 -m app.automation.tasks.google_login
    
    if [ ! -d "$PROFILE_DIR" ] || [ -z "$(ls -A "$PROFILE_DIR" 2>/dev/null)" ]; then
        echo "[!] Error: Profile directory was not created. Exiting."
        exit 1
    fi
    
    echo "[+] Profile directory created and Gmail login completed successfully."
else
    echo "[+] Profile directory '$PROFILE_DIR' already exists."
fi

# Run playwright codegen
echo "[*] Starting playwright codegen..."
echo "[*] Using profile directory: $PROFILE_DIR"
echo "[*] Note: Standard codegen CLI cannot use initialize_page_sync's stealth mode."
echo "[*] For full stealth mode, use: python3 backend/scripts/codegen_notebooklm_stealth.py"
echo ""
cd "$PROJECT_ROOT"
playwright codegen \
  --user-data-dir="$PROFILE_DIR" \
  --browser=chromium \
  notebooklm.google.com

