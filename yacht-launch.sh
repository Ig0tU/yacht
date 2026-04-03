#!/bin/bash

# This script is intended to be run on an Android device (e.g., via Termux)
# It attempts to launch the Yacht application.

PACKAGE_NAME="com.yacht.mobile.debug"
ACTIVITY_NAME=".MainActivity"

echo "=== Yacht Automation: Phone (Launch) ==="

# Check if am (Activity Manager) is available
if command -v am &> /dev/null; then
    echo "Launching Yacht app..."
    am start -n "$PACKAGE_NAME/$ACTIVITY_NAME"
    if [ $? -eq 0 ]; then
        echo "Successfully sent launch intent."
    else
        echo "Failed to launch. Is the app installed?"
    fi
else
    echo "Error: 'am' command not found. Are you running this in a mobile terminal with the necessary permissions?"
    echo "Alternatively, you can open the web interface from your computer script in your mobile browser."
fi
