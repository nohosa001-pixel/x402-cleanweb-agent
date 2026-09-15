@echo off
chcp 65001 >nul
title PyPI Build & Publish - x402-cleanweb-agent v2.5.3

echo =========================================================
echo  📦 PyPI Package Build & Publish Tool (v2.5.3)
echo =========================================================
echo.

set PY_BIN=python
if exist .venv\Scripts\python.exe set PY_BIN=.venv\Scripts\python.exe

echo [1/3] Cleaning old build artifacts in dist/...
if exist dist rmdir /s /q dist
if exist build rmdir /s /q build
if exist x402_cleanweb_agent.egg-info rmdir /s /q x402_cleanweb_agent.egg-info

echo.
echo [2/3] Building Wheel & Source Distribution...
%PY_BIN% -m build

if %errorlevel% neq 0 (
    echo [ERROR] Build failed!
    pause
    exit /b 1
)

echo.
echo [3/3] Checking distribution files with twine...
%PY_BIN% -m twine check dist/*

echo.
echo =========================================================
echo  ✅ Build completed successfully!
echo  Distribution files in /dist:
dir /b dist
echo =========================================================
echo.
set /p UPLOAD_CONFIRM="Do you want to upload to PyPI now? (y/N): "

if /i "%UPLOAD_CONFIRM%"=="y" (
    echo.
    echo Uploading to PyPI via Twine...
    set PYTHONIOENCODING=utf-8
    %PY_BIN% -m twine upload --disable-progress-bar dist/*
) else (
    echo.
    echo [SKIPPED] Upload cancelled. You can upload later with:
    echo   %PY_BIN% -m twine upload dist/*
)

echo.
pause
