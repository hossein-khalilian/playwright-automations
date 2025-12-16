#!/bin/bash

# Script to run playwright codegen for notebooklm.google.com
# If test_google_login profile doesn't exist, it will be created by running google_login.py

set -e  # Exit on error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
PROFILE_DIR="$PROJECT_ROOT/browser_profiles/test_google_login"

# Check if profile directory exists
if [ ! -d "$PROFILE_DIR" ]; then
    echo "[*] Profile directory '$PROFILE_DIR' does not exist."
    echo "[*] Creating it by running google_login.py..."
    
    # Change to project root to ensure relative paths work
    cd "$PROJECT_ROOT"
    
    # Run google_login.py to create the profile
    # Set PYTHONPATH to include backend directory
    export PYTHONPATH="$PROJECT_ROOT/backend:$PYTHONPATH"
    python3 -m app.automation.tasks.google_login
    
    if [ ! -d "$PROFILE_DIR" ]; then
        echo "[!] Error: Profile directory was not created. Exiting."
        exit 1
    fi
    
    echo "[+] Profile directory created successfully."
else
    echo "[+] Profile directory '$PROFILE_DIR' already exists."
fi

# Run playwright codegen
echo "[*] Starting playwright codegen..."
cd "$PROJECT_ROOT"
playwright codegen --user-data-dir="browser_profiles/test_google_login" notebooklm.google.com

