@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo =========================================================================
echo   CleanWeb Non-Invasive ElizaOS Brain Continuous Learning 24/7 Daemon
echo =========================================================================
python scripts\run_cleanweb_brain_learning.py --daemon --interval 900
pause

