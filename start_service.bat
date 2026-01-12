@echo off
chcp 65001 >nul
title LOF基金套利工具
echo ========================================
echo LOF基金套利工具 - 正在启动...
echo ========================================
echo.
echo 服务地址: http://localhost:8505
echo 按 Ctrl+C 停止服务
echo.
python app.py
pause
