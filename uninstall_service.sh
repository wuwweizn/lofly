#!/bin/bash
# 卸载systemd服务（需要root权限）

if [ "$EUID" -ne 0 ]; then 
   echo "[错误] 需要root权限！"
   echo "请使用: sudo ./uninstall_service.sh"
   exit 1
fi

echo "========================================"
echo "LOF基金套利工具 - systemd服务卸载"
echo "========================================"
echo ""

# 检查服务是否存在
if [ ! -f "/etc/systemd/system/lof-arbitrage.service" ]; then
    echo "[信息] 服务不存在，无需卸载"
    exit 0
fi

echo "[信息] 正在卸载systemd服务..."
echo ""

# 停止服务
echo "[1/3] 停止服务..."
systemctl stop lof-arbitrage.service 2>/dev/null || true
if systemctl is-active --quiet lof-arbitrage.service 2>/dev/null; then
    echo "[等待] 等待服务停止..."
    sleep 3
fi
echo ""

# 禁用服务
echo "[2/3] 禁用服务..."
systemctl disable lof-arbitrage.service 2>/dev/null || true
echo "[完成] 服务已禁用"
echo ""

# 删除服务文件
echo "[3/3] 删除服务文件..."
rm -f /etc/systemd/system/lof-arbitrage.service
systemctl daemon-reload
echo "[完成] 服务文件已删除"
echo ""

echo "========================================"
echo "服务卸载完成！"
echo "========================================"
echo ""
