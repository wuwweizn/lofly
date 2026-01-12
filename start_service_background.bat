@echo off
chcp 65001 >nul
title LOF基金套利工具 - 后台运行
echo 正在后台启动服务...
start /min python app.py
echo 服务已在后台启动
echo 访问地址: http://localhost:8505
timeout /t 3 /nobreak >nul
