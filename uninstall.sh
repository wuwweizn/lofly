#!/bin/bash
# LOF基金套利工具 - 卸载脚本

set -e

echo "========================================"
echo "LOF基金套利工具 - 卸载脚本"
echo "========================================"
echo ""

read -p "确定要卸载吗？这将删除所有数据文件（用户数据、套利记录、通知等）(y/N): " CONFIRM
if [ "$CONFIRM" != "y" ] && [ "$CONFIRM" != "Y" ]; then
    echo "取消卸载"
    exit 0
fi

PROJECT_DIR=$(cd "$(dirname "$0")" && pwd)

echo ""
echo "[1/3] 停止运行中的服务..."

# 停止systemd服务（如果已安装）
if systemctl is-active --quiet lof-arbitrage.service 2>/dev/null; then
    echo "停止systemd服务..."
    sudo systemctl stop lof-arbitrage.service 2>/dev/null || true
fi

# 停止后台服务
if [ -f "$PROJECT_DIR/stop_service.sh" ]; then
    bash "$PROJECT_DIR/stop_service.sh" 2>/dev/null || true
fi

sleep 2
echo "[完成] 服务已停止"
echo ""

echo "[2/3] 删除数据文件..."
rm -f "$PROJECT_DIR/users.json"
rm -f "$PROJECT_DIR/arbitrage_records.json"
rm -f "$PROJECT_DIR/notifications.json"
rm -f "$PROJECT_DIR/user_config.json"
rm -rf "$PROJECT_DIR/logs"
rm -rf "$PROJECT_DIR/data"
rm -f "$PROJECT_DIR/service.pid"
echo "[完成] 数据文件已删除"
echo ""

echo "[3/3] 删除启动脚本..."
rm -f "$PROJECT_DIR/start_service.sh"
rm -f "$PROJECT_DIR/start_service_background.sh"
rm -f "$PROJECT_DIR/stop_service.sh"
rm -f "$PROJECT_DIR/install_service.sh"
rm -f "$PROJECT_DIR/uninstall_service.sh"
echo "[完成] 启动脚本已删除"
echo ""

echo "========================================"
echo "卸载完成！"
echo "========================================"
echo ""
echo "注意: Python依赖包和项目源代码文件未删除"
echo "如需完全卸载，请手动删除项目目录"
echo ""
echo "如果已安装systemd服务，请运行: sudo ./uninstall_service.sh"
echo ""
