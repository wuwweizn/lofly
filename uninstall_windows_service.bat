@echo off
chcp 65001 >nul
echo ========================================
echo LOF基金套利工具 - Windows服务卸载
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

:: 检查服务是否存在
sc query LOFArbitrageService >nul 2>&1
if %errorLevel% neq 0 (
    echo [信息] 服务不存在，无需卸载
    pause
    exit /b 0
)

echo [信息] 正在卸载Windows服务...
echo.

:: 停止服务
echo [1/2] 停止服务...
sc stop LOFArbitrageService
if %errorLevel% equ 0 (
    echo [等待] 等待服务停止...
    timeout /t 3 /nobreak >nul
) else (
    echo [信息] 服务未运行或已停止
)
echo.

:: 删除服务
echo [2/2] 删除服务...
sc delete LOFArbitrageService
if %errorLevel% neq 0 (
    echo [错误] 服务删除失败！
    pause
    exit /b 1
)

echo [成功] 服务已删除
echo.

echo ========================================
echo 服务卸载完成！
echo ========================================
echo.
pause
