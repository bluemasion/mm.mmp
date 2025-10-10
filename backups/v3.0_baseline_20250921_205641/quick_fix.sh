#!/bin/bash
# One-click fix for MMP template and routing issues
# MMP问题一键修复脚本

TARGET_PATH="${1:-/dt1/mmp/mmp}"

echo "🔧 MMP Quick Fix Script"
echo "======================="
echo "Target: $TARGET_PATH"

# Stop service
echo "⏹️  Stopping MMP service..."
pkill -f "python.*run_app.py" 2>/dev/null || true
sleep 2

# Navigate to target
cd "$TARGET_PATH" || exit 1

# Fix 1: Create error.html template
echo "📄 Creating error.html template..."
cat > templates/error.html << 'EOF'
{% extends "base.html" %}
{% block title %}Error - MMP System{% endblock %}
{% block content %}
<div class="container mt-5">
    <div class="row justify-content-center">
        <div class="col-md-8">
            <div class="card border-danger">
                <div class="card-header bg-danger text-white">
                    <h4><i class="fas fa-exclamation-triangle"></i> Error {{ error_code or '500' }}</h4>
                </div>
                <div class="card-body text-center">
                    <h3>{{ error_message or 'An error occurred' }}</h3>
                    <div class="mt-4">
                        <a href="{{ url_for('index') }}" class="btn btn-primary">
                            <i class="fas fa-home"></i> Home
                        </a>
                        <button onclick="history.back()" class="btn btn-secondary">
                            <i class="fas fa-arrow-left"></i> Back
                        </button>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>
{% endblock %}
EOF

# Fix 2: Update web_app.py - Flask template path
echo "🛠️  Fixing Flask template path..."
sed -i.bak 's|app = Flask(__name__)|project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))\napp = Flask(__name__, template_folder=os.path.join(project_root, "templates"))|' app/web_app.py

# Fix 3: Add redirect routes
echo "🔀 Adding redirect routes..."
cat >> app/web_app.py << 'EOF'

# Additional redirect routes
@app.route('/categorize')
def categorize_redirect():
    return redirect(url_for('category_selection'))

@app.route('/category') 
def category_redirect():
    return redirect(url_for('category_selection'))
EOF

# Fix 4: Ensure imports
echo "📥 Checking imports..."
if ! grep -q "from flask import.*redirect" app/web_app.py; then
    sed -i '1s|from flask import|from flask import redirect, |' app/web_app.py
fi

# Start service
echo "▶️  Starting MMP service..."
nohup python3 run_app.py > app.log 2>&1 &
sleep 3

# Check status
if pgrep -f "python.*run_app.py" > /dev/null; then
    echo "✅ MMP service started successfully!"
    echo "🌐 Access: http://$(hostname -I | awk '{print $1}'):5000"
    echo "📊 Check status: curl http://localhost:5000/api/status"
else
    echo "❌ Failed to start MMP service"
    echo "📝 Check logs: tail -f $TARGET_PATH/app.log"
fi

echo "🏁 Fix completed!"
