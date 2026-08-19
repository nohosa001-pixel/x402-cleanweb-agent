@echo off
chcp 65001 > nul
echo ========================================================
echo  🚀 Polygon x402 Micro-Payment Server 가동 중...
echo ========================================================
echo.
echo [1] 서버 주소: http://localhost:8000
echo [2] Swagger API 문서: http://localhost:8000/docs
echo.
echo 서버를 종료하려면 Ctrl + C 를 누르세요.
echo.

.\.venv\Scripts\python.exe -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
pause
