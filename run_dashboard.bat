@echo off
chcp 65001 >nul
title x402 AI Agent Suite - Real-Time Dashboard
echo ===================================================
echo  Starting x402 Real-Time Monitoring Dashboard...
echo ===================================================

if exist .venv\Scripts\python.exe (
    .venv\Scripts\python.exe monitor_dashboard.py %*
) else (
    python monitor_dashboard.py %*
)
pause
