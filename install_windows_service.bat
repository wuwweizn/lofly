@echo off
chcp 65001 >nul
echo ========================================
echo LOF基金套利工具 - Windows服务安装
echo ========================================
echo.

:: 检查管理员权限
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo [错误] 需要管理员权限！
    echo 请右键点击此脚本，选择"以管理员身份运行"
    pause
    exit /b 1
)

echo [信息] 正在安装Windows服务...
echo.

:: 获取当前目录的完整路径
set "SERVICE_DIR=%~dp0"
set "SERVICE_DIR=%SERVICE_DIR:~0,-1%"

:: 获取Python路径
for /f "delims=" %%i in ('where python') do set PYTHON_PATH=%%i

if not defined PYTHON_PATH (
    echo [错误] 未找到Python路径！
    pause
    exit /b 1
)

echo Python路径: %PYTHON_PATH%
echo 服务目录: %SERVICE_DIR%
echo 应用文件: %SERVICE_DIR%\app.py
echo.

:: 检查服务是否已存在
sc query LOFArbitrageService >nul 2>&1
if %errorLevel% equ 0 (
    echo [信息] 服务已存在，正在删除旧服务...
    sc stop LOFArbitrageService >nul 2>&1
    timeout /t 2 /nobreak >nul
    sc delete LOFArbitrageService
    if %errorLevel% neq 0 (
        echo [警告] 删除旧服务失败，请手动删除
    )
    echo.
)

:: 创建服务
echo [1/2] 创建Windows服务...
sc create LOFArbitrageService ^
    binPath= "\"%PYTHON_PATH%\" \"%SERVICE_DIR%\app.py\"" ^
    DisplayName= "LOF基金套利工具" ^
    start= auto ^
    obj= "NT AUTHORITY\LocalService"

if %errorLevel% neq 0 (
    echo [错误] 服务创建失败！
    echo.
    echo 提示: 如果失败，可以尝试使用NSSM工具安装服务
    echo 下载地址: https://nssm.cc/download
    pause
    exit /b 1
)

echo [成功] 服务创建成功
echo.

:: 设置服务描述
echo [2/2] 设置服务描述...
sc description LOFArbitrageService "LOF基金套利工具 - 监控和计算LOF基金套利机会的Web服务"
echo [完成] 服务描述已设置
echo.

echo ========================================
echo 服务安装完成！
echo ========================================
echo.
echo 服务名称: LOFArbitrageService
echo 显示名称: LOF基金套利工具
echo.
echo 可用命令:
echo   - 启动服务: net start LOFArbitrageService
echo   - 停止服务: net stop LOFArbitrageService
echo   - 查看状态: sc query LOFArbitrageService
echo.
echo 服务将在系统启动时自动运行
echo 访问地址: http://localhost:8505
echo.
echo ========================================
pause
