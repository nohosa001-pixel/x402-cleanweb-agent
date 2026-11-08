@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo ========================================================
echo   A-GRID 24/7 Daily Traffic & Revenue Digest Dispatcher
echo ========================================================
python scripts\daily_traffic_digest.py
pause
