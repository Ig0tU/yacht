#!/bin/bash
set -e

echo "⛵ Starting Yacht On-Ramper..."

# 1. Setup Yacht Cloud
echo "☁️ Setting up Yacht Cloud..."
cd yacht-cloud
python3 -m venv .venv
.venv/bin/pip install -e .
cp .env.example .env
mkdir -p data
echo "✅ Yacht Cloud setup complete."
cd ..

# 2. Setup Yacht Mobile
echo "📱 Setting up Yacht Mobile CLI..."
cd yacht-mobile
python3 -m venv .venv
.venv/bin/pip install -e .
echo "✅ Yacht Mobile setup complete."
cd ..

# 3. Configure Yacht Android
echo "🤖 Configuring Yacht Android..."
# Point API_BASE_URL to localhost (assuming local dev server)
# In production, this would be the actual domain.
# Using 10.0.2.2 for Android emulator to talk to localhost.
sed -i 's|buildConfigField("String", "API_BASE_URL", "\\"https://your-api-host.example.com/\\"")|buildConfigField("String", "API_BASE_URL", "\\"http://10.0.2.2:3000/\\"")|' yacht-android/app/build.gradle.kts

# Initialize keystore.properties from example
if [ ! -f yacht-android/keystore.properties ]; then
    cp yacht-android/keystore.properties.example yacht-android/keystore.properties
fi
echo "✅ Yacht Android configuration complete."

# 4. Launch Cloud Backend in background
echo "🚀 Launching Yacht Cloud Backend on port 3000..."
kill $(lsof -t -i :3000) 2>/dev/null || true
cd yacht-cloud && .venv/bin/python -m uvicorn yacht_cloud.main:app --host 0.0.0.0 --port 3000 > /tmp/yacht_cloud.log 2>&1 &
echo "✅ Yacht Cloud Backend launched. Logs at /tmp/yacht_cloud.log"
cd ..

echo "⛵ Yacht is ready for action!"
echo "- Cloud API: http://localhost:3000/docs"
echo "- Mobile CLI: Use yacht-mobile/.venv/bin/yacht"
echo "- Android: Build via yacht-android/gradlew"
