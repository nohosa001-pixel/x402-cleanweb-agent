@echo off
chcp 65001 > nul
echo ========================================================
echo  🚀 CleanWeb Studio Server 가동 중...
echo ========================================================
echo.
echo [1] 웹 대시보드 (Web UI): http://localhost:8080/dashboard
echo [2] Swagger API 문서     : http://localhost:8080/docs
echo [3] 실시간 헬스 체크     : http://localhost:8080/health
echo.
echo 서버를 종료하려면 Ctrl + C 를 누르세요.
echo.

if exist .venv\Scripts\python.exe (
    .venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload
) else (
    python -m uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload
)
pause
