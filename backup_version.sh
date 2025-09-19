#!/bin/bash
# backup_version.sh - 创建当前版本备份

echo "========================================"
echo "MMP版本备份 - $(date)"
echo "========================================"

# 设置备份目录
BACKUP_DIR="../mmp_backups"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_PATH="${BACKUP_DIR}/mmp_v1.2.0_${TIMESTAMP}"

# 创建备份目录
mkdir -p "$BACKUP_PATH"

echo "📁 创建备份目录: $BACKUP_PATH"

# 复制核心文件
echo "📋 复制核心应用文件..."
cp -r app/ "$BACKUP_PATH/"
cp -r templates/ "$BACKUP_PATH/"
cp -r static/ "$BACKUP_PATH/" 2>/dev/null || echo "static目录不存在，跳过"

echo "📄 复制配置和启动文件..."
cp run_app.py "$BACKUP_PATH/"
cp config.py "$BACKUP_PATH/"
cp enhanced_config.py "$BACKUP_PATH/"
cp requirements.txt "$BACKUP_PATH/"
cp *.sh "$BACKUP_PATH/" 2>/dev/null || echo "没有.sh文件"

echo "📚 复制文档文件..."
cp *.md "$BACKUP_PATH/"

echo "🗃️ 复制会话数据..."
cp -r session_data/ "$BACKUP_PATH/" 2>/dev/null || echo "session_data目录不存在，跳过"

# 创建备份信息文件
cat > "$BACKUP_PATH/BACKUP_INFO.txt" << EOF
MMP系统备份信息
================

备份时间: $(date)
版本号: v1.2.0
Python版本: $(python3.8 --version 2>/dev/null || echo "Python 3.8")
备份路径: $BACKUP_PATH

主要更新:
- 修复端口配置问题 (5005 → 5001)
- 新增PRD产品需求文档
- 创建版本快照文档
- 服务启动成功验证

核心文件:
- run_app.py (已修正端口)
- app/web_app.py (Flask主应用)
- MMP_PRD_2025.md (新增)
- VERSION_SNAPSHOT_20250919.md (新增)

状态: 稳定运行 ✅
EOF

# 显示备份完成信息
echo ""
echo "✅ 备份完成!"
echo "📂 备份位置: $BACKUP_PATH"
echo "📊 备份大小: $(du -sh "$BACKUP_PATH" | cut -f1)"
echo ""
echo "恢复命令:"
echo "  cp -r \"$BACKUP_PATH\"/* ."
echo ""

# 列出备份内容
echo "📋 备份内容:"
ls -la "$BACKUP_PATH"