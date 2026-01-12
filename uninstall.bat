@echo off
chcp 65001 >nul
echo ========================================
echo LOF基金套利工具 - 卸载脚本
echo ========================================
echo.

set /p CONFIRM="确定要卸载吗？这将删除所有数据文件（用户数据、套利记录、通知等）(Y/N): "
if /i not "%CONFIRM%"=="Y" (
    echo 取消卸载
    pause
    exit /b 0
)

echo.
echo [1/3] 停止运行中的服务...
taskkill /F /IM python.exe /FI "WINDOWTITLE eq LOF基金套利工具*" >nul 2>&1
taskkill /F /IM python.exe /FI "COMMANDLINE eq *app.py*" >nul 2>&1
timeout /t 2 /nobreak >nul
echo [完成] 服务已停止
echo.

echo [2/3] 删除数据文件...
if exist "users.json" del /q "users.json"
if exist "arbitrage_records.json" del /q "arbitrage_records.json"
if exist "notifications.json" del /q "notifications.json"
if exist "user_config.json" del /q "user_config.json"
if exist "logs" rmdir /s /q "logs"
if exist "data" rmdir /s /q "data"
echo [完成] 数据文件已删除
echo.

echo [3/3] 删除启动脚本...
if exist "start_service.bat" del /q "start_service.bat"
if exist "start_service_background.bat" del /q "start_service_background.bat"
if exist "stop_service.bat" del /q "stop_service.bat"
if exist "install_service.bat" del /q "install_service.bat"
echo [完成] 启动脚本已删除
echo.

echo ========================================
echo 卸载完成！
echo ========================================
echo.
echo 注意: Python依赖包和项目源代码文件未删除
echo 如需完全卸载，请手动删除项目目录
echo.
pause
