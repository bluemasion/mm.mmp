#!/bin/bash
# 一键部署到服务器脚本
# 使用方法: bash quick_deploy.sh user@server /path/to/mmp

set -e

# 检查参数
if [[ $# -lt 2 ]]; then
    echo "使用方法: $0 <服务器地址> <部署路径>"
    echo "示例: $0 root@192.168.1.100 /opt/mmp"
    exit 1
fi

SERVER="$1"
DEPLOY_PATH="$2"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

echo "=================================================="
echo "  MMP系统一键部署脚本"
echo "=================================================="
echo "服务器: $SERVER"
echo "路径: $DEPLOY_PATH"
echo "时间: $(date)"
echo "=================================================="

# 1. 本地打包
echo "🔄 正在打包项目文件..."
cd "/Users/mason/Desktop/code /mmp"
tar --exclude='.DS_Store' --exclude='__pycache__' --exclude='*.pyc' \
    --exclude='.git' --exclude='venv' --exclude='*.log' \
    -czf "mmp_update_${TIMESTAMP}.tar.gz" .

echo "✅ 打包完成: mmp_update_${TIMESTAMP}.tar.gz"

# 2. 上传文件
echo "🔄 正在上传文件到服务器..."
scp "mmp_update_${TIMESTAMP}.tar.gz" "$SERVER:/tmp/"
scp deploy_update.sh "$SERVER:/tmp/"

echo "✅ 文件上传完成"

# 3. 远程部署
echo "🔄 正在服务器上执行部署..."
ssh "$SERVER" << EOF
    set -e
    
    # 解压文件
    cd /tmp
    rm -rf mmp_new
    mkdir -p mmp_new
    tar -xzf mmp_update_${TIMESTAMP}.tar.gz -C mmp_new/
    
    # 执行部署
    chmod +x /tmp/deploy_update.sh
    bash /tmp/deploy_update.sh "$DEPLOY_PATH"
    
    # 清理临时文件
    rm -f mmp_update_${TIMESTAMP}.tar.gz
    rm -rf mmp_new
    
    echo "🎉 远程部署完成！"
EOF

# 4. 清理本地临时文件
rm -f "mmp_update_${TIMESTAMP}.tar.gz"

echo "=================================================="
echo "🎉 一键部署完成！"
echo "=================================================="
echo "请检查服务器上的应用是否正常运行："
echo "curl http://$SERVER:5000"
echo
echo "如有问题，可以查看部署日志：" 
echo "ssh $SERVER 'tail -f $DEPLOY_PATH/app.log'"
