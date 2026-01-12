@echo off
chcp 65001 >nul
echo ========================================
echo 安装Windows服务（需要管理员权限）
echo ========================================
echo.
echo 此功能需要安装NSSM（Non-Sucking Service Manager）
echo.
echo 或者使用以下命令手动安装服务:
echo sc create LOFArbitrageService binPath= "python C:\lof1\app.py" start= auto
echo.
pause
