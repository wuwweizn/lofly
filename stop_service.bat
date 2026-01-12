@echo off
chcp 65001 >nul
echo 正在停止LOF基金套利工具服务...
taskkill /F /IM python.exe /FI "WINDOWTITLE eq LOF基金套利工具*" >nul 2>&1
taskkill /F /IM python.exe /FI "COMMANDLINE eq *app.py*" >nul 2>&1
echo 服务已停止
timeout /t 2 /nobreak >nul
