#!/bin/bash
# LOF基金套利工具 - Linux一键部署脚本

set -e

echo "========================================"
echo "LOF基金套利工具 - Linux一键部署脚本"
echo "========================================"
echo ""

# 检查是否为root用户（可选，某些操作需要root）
if [ "$EUID" -eq 0 ]; then 
   echo "[警告] 建议使用普通用户运行此脚本，仅在安装systemd服务时需要root权限"
   echo ""
fi

# 检查Python是否安装
echo "[1/7] 检查Python环境..."
if ! command -v python3 &> /dev/null; then
    echo "[错误] 未检测到Python3环境！"
    echo "请先安装Python 3.11或更高版本"
    echo "Ubuntu/Debian: sudo apt-get install python3.11 python3.11-venv python3-pip"
    echo "CentOS/RHEL: sudo yum install python311 python311-pip"
    exit 1
fi

PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo "[成功] 检测到Python版本: $PYTHON_VERSION"
echo ""

# 检查Python版本是否>=3.7
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)
if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 7 ]); then
    echo "[错误] Python版本需要3.7或更高版本，当前版本: $PYTHON_VERSION"
    exit 1
fi

# 检查pip是否可用
echo "[2/7] 检查pip..."
if ! command -v pip3 &> /dev/null && ! python3 -m pip --version &> /dev/null; then
    echo "[错误] pip不可用，请安装pip"
    echo "Ubuntu/Debian: sudo apt-get install python3-pip"
    echo "CentOS/RHEL: sudo yum install python3-pip"
    exit 1
fi
echo "[成功] pip可用"
echo ""

# 升级pip
echo "[3/7] 升级pip到最新版本..."
python3 -m pip install --upgrade pip -q
echo "[完成] pip已升级"
echo ""

# 获取项目目录
PROJECT_DIR=$(cd "$(dirname "$0")" && pwd)
echo "[信息] 项目目录: $PROJECT_DIR"
echo ""

# 安装依赖
echo "[4/7] 安装项目依赖..."
python3 -m pip install -r "$PROJECT_DIR/requirements.txt"
if [ $? -ne 0 ]; then
    echo "[错误] 依赖安装失败！"
    exit 1
fi
echo "[完成] 依赖安装完成"
echo ""

# 创建必要的目录
echo "[5/7] 创建必要的目录和文件..."
mkdir -p "$PROJECT_DIR/logs"
mkdir -p "$PROJECT_DIR/data"
echo "[完成] 目录创建完成"
echo ""

# 创建启动脚本
echo "[6/7] 创建启动脚本..."
cat > "$PROJECT_DIR/start_service.sh" << 'EOF'
#!/bin/bash
# 启动LOF基金套利工具服务（前台运行）

PROJECT_DIR=$(cd "$(dirname "$0")" && pwd)
cd "$PROJECT_DIR"

echo "========================================"
echo "LOF基金套利工具 - 正在启动..."
echo "========================================"
echo ""
echo "服务地址: http://localhost:8505"
echo "按 Ctrl+C 停止服务"
echo ""

python3 app.py
EOF

chmod +x "$PROJECT_DIR/start_service.sh"

# 创建后台启动脚本（使用nohup）
cat > "$PROJECT_DIR/start_service_background.sh" << 'EOF'
#!/bin/bash
# 启动LOF基金套利工具服务（后台运行）

PROJECT_DIR=$(cd "$(dirname "$0")" && pwd)
cd "$PROJECT_DIR"

echo "正在后台启动服务..."

# 停止已运行的服务
if [ -f "$PROJECT_DIR/service.pid" ]; then
    OLD_PID=$(cat "$PROJECT_DIR/service.pid")
    if ps -p $OLD_PID > /dev/null 2>&1; then
        echo "停止旧服务进程 (PID: $OLD_PID)..."
        kill $OLD_PID 2>/dev/null || true
        sleep 2
    fi
    rm -f "$PROJECT_DIR/service.pid"
fi

# 启动新服务
nohup python3 app.py > "$PROJECT_DIR/logs/service.log" 2>&1 &
NEW_PID=$!
echo $NEW_PID > "$PROJECT_DIR/service.pid"

echo "服务已在后台启动 (PID: $NEW_PID)"
echo "访问地址: http://localhost:8505"
echo "日志文件: $PROJECT_DIR/logs/service.log"
echo ""
echo "查看日志: tail -f $PROJECT_DIR/logs/service.log"
echo "停止服务: $PROJECT_DIR/stop_service.sh"
EOF

chmod +x "$PROJECT_DIR/start_service_background.sh"

# 创建停止脚本
cat > "$PROJECT_DIR/stop_service.sh" << 'EOF'
#!/bin/bash
# 停止LOF基金套利工具服务

PROJECT_DIR=$(cd "$(dirname "$0")" && pwd)

echo "正在停止LOF基金套利工具服务..."

# 通过PID文件停止
if [ -f "$PROJECT_DIR/service.pid" ]; then
    PID=$(cat "$PROJECT_DIR/service.pid")
    if ps -p $PID > /dev/null 2>&1; then
        echo "停止进程 (PID: $PID)..."
        kill $PID 2>/dev/null || true
        sleep 2
        # 如果还在运行，强制杀死
        if ps -p $PID > /dev/null 2>&1; then
            kill -9 $PID 2>/dev/null || true
        fi
    fi
    rm -f "$PROJECT_DIR/service.pid"
fi

# 通过进程名停止（备用方法）
pkill -f "python3.*app.py" 2>/dev/null || true

echo "服务已停止"
EOF

chmod +x "$PROJECT_DIR/stop_service.sh"

# 创建systemd服务安装脚本
cat > "$PROJECT_DIR/install_service.sh" << 'INSTALL_EOF'
#!/bin/bash
# 安装systemd服务（需要root权限）

if [ "$EUID" -ne 0 ]; then 
   echo "[错误] 需要root权限！"
   echo "请使用: sudo ./install_service.sh"
   exit 1
fi

PROJECT_DIR=$(cd "$(dirname "$0")" && pwd)
PYTHON_PATH=$(which python3)
SERVICE_USER=$(who am i | awk '{print $1}')

if [ -z "$SERVICE_USER" ]; then
    SERVICE_USER=$(logname 2>/dev/null || echo "root")
fi

echo "========================================"
echo "LOF基金套利工具 - systemd服务安装"
echo "========================================"
echo ""
echo "Python路径: $PYTHON_PATH"
echo "服务目录: $PROJECT_DIR"
echo "运行用户: $SERVICE_USER"
echo ""

# 创建systemd服务文件
SERVICE_FILE="/etc/systemd/system/lof-arbitrage.service"

echo "[1/3] 创建systemd服务文件..."
cat > "$SERVICE_FILE" << SERVICE_EOF
[Unit]
Description=LOF基金套利工具 - 监控和计算LOF基金套利机会的Web服务
After=network.target

[Service]
Type=simple
User=$SERVICE_USER
WorkingDirectory=$PROJECT_DIR
ExecStart=$PYTHON_PATH $PROJECT_DIR/app.py
Restart=always
RestartSec=10
StandardOutput=append:$PROJECT_DIR/logs/service.log
StandardError=append:$PROJECT_DIR/logs/service.log

[Install]
WantedBy=multi-user.target
SERVICE_EOF

echo "[成功] 服务文件已创建: $SERVICE_FILE"
echo ""

# 重新加载systemd
echo "[2/3] 重新加载systemd配置..."
systemctl daemon-reload
echo "[完成] systemd配置已重新加载"
echo ""

# 启用服务（开机自启）
echo "[3/3] 启用服务（开机自启）..."
systemctl enable lof-arbitrage.service
echo "[完成] 服务已启用"
echo ""

echo "========================================"
echo "服务安装完成！"
echo "========================================"
echo ""
echo "服务名称: lof-arbitrage"
echo ""
echo "可用命令:"
echo "  - 启动服务: sudo systemctl start lof-arbitrage"
echo "  - 停止服务: sudo systemctl stop lof-arbitrage"
echo "  - 查看状态: sudo systemctl status lof-arbitrage"
echo "  - 查看日志: sudo journalctl -u lof-arbitrage -f"
echo "  - 重启服务: sudo systemctl restart lof-arbitrage"
echo ""
echo "服务将在系统启动时自动运行"
echo "访问地址: http://localhost:8505"
echo ""
echo "========================================"
INSTALL_EOF

chmod +x "$PROJECT_DIR/install_service.sh"

echo "[完成] 启动脚本创建完成"
echo ""

# 显示部署信息
echo "========================================"
echo "部署完成！"
echo "========================================"
echo ""
echo "项目目录: $PROJECT_DIR"
echo "Python版本: $PYTHON_VERSION"
echo ""
echo "可用命令:"
echo "  - ./start_service.sh                 启动服务（前台）"
echo "  - ./start_service_background.sh       启动服务（后台，使用nohup）"
echo "  - ./stop_service.sh                  停止服务"
echo "  - sudo ./install_service.sh          安装systemd服务（推荐，开机自启）"
echo ""
echo "访问地址: http://localhost:8505"
echo ""
echo "默认管理员账号:"
echo "  用户名: admin"
echo "  密码: admin123"
echo ""
echo "========================================"
