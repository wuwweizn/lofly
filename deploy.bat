@echo off
chcp 65001 >nul
echo ========================================
echo LOF基金套利工具 - Windows一键部署脚本
echo ========================================
echo.

:: 检查管理员权限
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo [警告] 建议以管理员身份运行此脚本以获得完整功能
    echo.
)

:: 检查Python是否安装
echo [1/6] 检查Python环境...
python --version >nul 2>&1
if %errorLevel% neq 0 (
    echo [错误] 未检测到Python环境！
    echo 请先安装Python 3.7或更高版本
    echo 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo [成功] 检测到Python版本: %PYTHON_VERSION%
echo.

:: 检查pip是否可用
echo [2/6] 检查pip...
python -m pip --version >nul 2>&1
if %errorLevel% neq 0 (
    echo [错误] pip不可用，请重新安装Python并确保勾选"Add Python to PATH"
    pause
    exit /b 1
)
echo [成功] pip可用
echo.

:: 升级pip
echo [3/6] 升级pip到最新版本...
python -m pip install --upgrade pip -q
echo [完成] pip已升级
echo.

:: 安装依赖
echo [4/6] 安装项目依赖...
python -m pip install -r requirements.txt
if %errorLevel% neq 0 (
    echo [错误] 依赖安装失败！
    pause
    exit /b 1
)
echo [完成] 依赖安装完成
echo.

:: 创建必要的目录
echo [5/6] 创建必要的目录和文件...
if not exist "logs" mkdir logs
if not exist "data" mkdir data
echo [完成] 目录创建完成
echo.

:: 创建启动脚本
echo [6/6] 创建启动脚本...
(
echo @echo off
echo chcp 65001 ^>nul
echo title LOF基金套利工具
echo echo ========================================
echo echo LOF基金套利工具 - 正在启动...
echo echo ========================================
echo echo.
echo echo 服务地址: http://localhost:8505
echo echo 按 Ctrl+C 停止服务
echo echo.
echo python app.py
echo pause
) > start_service.bat

:: 创建后台启动脚本
(
echo @echo off
echo chcp 65001 ^>nul
echo title LOF基金套利工具 - 后台运行
echo echo 正在后台启动服务...
echo start /min python app.py
echo echo 服务已在后台启动
echo echo 访问地址: http://localhost:8505
echo timeout /t 3 /nobreak ^>nul
) > start_service_background.bat

:: 创建停止脚本
(
echo @echo off
echo chcp 65001 ^>nul
echo echo 正在停止LOF基金套利工具服务...
echo taskkill /F /IM python.exe /FI "WINDOWTITLE eq LOF基金套利工具*" ^>nul 2^>^&1
echo taskkill /F /IM python.exe /FI "COMMANDLINE eq *app.py*" ^>nul 2^>^&1
echo echo 服务已停止
echo timeout /t 2 /nobreak ^>nul
) > stop_service.bat

:: 创建Windows服务安装脚本（可选）
(
echo @echo off
echo chcp 65001 ^>nul
echo echo ========================================
echo echo 安装Windows服务（需要管理员权限）
echo echo ========================================
echo echo.
echo echo 此功能需要安装NSSM（Non-Sucking Service Manager）
echo echo 下载地址: https://nssm.cc/download
echo echo.
echo echo 或者使用以下命令手动安装服务:
echo echo sc create LOFArbitrageService binPath= "python %CD%\app.py" start= auto
echo echo.
echo pause
) > install_service.bat

echo [完成] 启动脚本创建完成
echo.

:: 显示部署信息
echo ========================================
echo 部署完成！
echo ========================================
echo.
echo 项目目录: %CD%
echo Python版本: %PYTHON_VERSION%
echo.
echo 可用命令:
echo   - start_service.bat             启动服务（前台）
echo   - start_service_background.bat  启动服务（后台）
echo   - stop_service.bat              停止服务
echo.
echo 访问地址: http://localhost:8505
echo.
echo 默认管理员账号:
echo   用户名: admin
echo   密码: admin123
echo.
echo ========================================
pause
