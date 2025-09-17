#!/bin/bash
# Quick fix for Flask endpoint name issue
# 修复Flask端点名称问题

TARGET_PATH="${1:-/dt1/mmp/mmp}"

echo "🔧 Fixing Flask endpoint names..."
echo "Target: $TARGET_PATH"

# Stop service
echo "⏹️  Stopping MMP service..."
pkill -f "python.*run_app.py" 2>/dev/null || true
sleep 2

# Navigate to target
cd "$TARGET_PATH" || exit 1

# Fix the endpoint name in redirect routes
echo "🔀 Fixing redirect endpoint names..."
sed -i.bak "s/url_for('category_selection')/url_for('category_selection_page')/g" app/web_app.py

# Verify the fix
if grep -q "url_for('category_selection_page')" app/web_app.py; then
    echo "✅ Endpoint names fixed successfully"
else
    echo "❌ Failed to fix endpoint names"
    exit 1
fi

# Start service
echo "▶️  Starting MMP service..."
nohup python3 run_app.py > app.log 2>&1 &
sleep 3

# Check status
if pgrep -f "python.*run_app.py" > /dev/null; then
    echo "✅ MMP service started successfully!"
    echo "🌐 Test redirect: curl -I http://localhost:5000/categorize"
else
    echo "❌ Failed to start MMP service"
    echo "📝 Check logs: tail -f $TARGET_PATH/app.log"
fi

echo "🏁 Endpoint fix completed!"
