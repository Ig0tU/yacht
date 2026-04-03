#!/bin/bash
set -e

# Configuration
PROJECT_ROOT=$(pwd)
ANDROID_DIR="$PROJECT_ROOT/yacht-android"
MOBILE_DIR="$PROJECT_ROOT/yacht-mobile"
APK_PATH="$ANDROID_DIR/app/build/outputs/apk/debug/app-debug.apk"

echo "=== Yacht Automation: Computer (Build & Webapp) ==="

# 1. Update Android Version
echo "[1/4] Incrementing Android version..."
VERSION_FILE="$ANDROID_DIR/app/build.gradle.kts"
CURRENT_VERSION=$(grep "versionCode =" "$VERSION_FILE" | awk '{print $3}')
NEW_VERSION=$((CURRENT_VERSION + 1))
sed -i "s/versionCode = $CURRENT_VERSION/versionCode = $NEW_VERSION/" "$VERSION_FILE"
echo "      New version code: $NEW_VERSION"

# 2. Build APK
echo "[2/4] Building Android debug APK..."
cd "$ANDROID_DIR"
gradle assembleDebug > /dev/null
echo "      APK generated at: $APK_PATH"

# 3. Setup Python environment if needed
echo "[3/4] Ensuring yacht-mobile is ready..."
cd "$MOBILE_DIR"
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
fi
source .venv/bin/activate
pip install -e . > /dev/null

# 4. Launch Web Interface
echo "[4/4] Launching Yacht Web Interface..."
yacht serve --port 8000 &
SERVER_PID=$!

echo ""
echo "===================================================="
echo "Yacht is ready!"
echo "APK Download: $APK_PATH"
echo "Web Interface: http://localhost:8000"
echo "===================================================="
echo "Press Ctrl+C to stop the web server."

# Keep script running to maintain the background server
wait $SERVER_PID
