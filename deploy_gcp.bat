@echo off
chcp 65001 > nul
echo ========================================================
echo   x402-cleanweb-agent Google Cloud Run 배포 스크립트
echo ========================================================
echo.

:: 1. gcloud 설치 확인
where gcloud >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] gcloud CLI가 설치되어 있지 않습니다.
    echo Google Cloud SDK를 설치 후 다시 실행해주세요.
    pause
    exit /b 1
)

:: 2. 현재 설정된 프로젝트 확인
for /f "tokens=*" %%i in ('gcloud config get-value project 2^>nul') do set GCP_PROJECT=%%i

if "%GCP_PROJECT%"=="" (
    echo [WARNING] 기본 GCP 프로젝트가 설정되어 있지 않습니다.
    set /p GCP_PROJECT="배포할 GCP Project ID를 입력하세요: "
    gcloud config set project %GCP_PROJECT%
)

echo [INFO] 대상 프로젝트: %GCP_PROJECT%
echo [INFO] 배포 리전: asia-northeast3 (서울)
echo.

:: 3. 필수 API 활성화 (최초 1회 필요)
echo [1/3] 필수 GCP API 활성화 확인 중 (Cloud Run, Cloud Build)...
call gcloud services enable run.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com --quiet

:: 4. Cloud Run 소스 기반 배포 실행
echo [2/3] Cloud Run으로 소스코드를 업로드하여 빌드 및 배포를 진행합니다...
call gcloud run deploy x402-cleanweb-agent ^
    --source . ^
    --region asia-northeast3 ^
    --platform managed ^
    --allow-unauthenticated ^
    --memory 512Mi ^
    --cpu 1 ^
    --min-instances 0 ^
    --max-instances 10 ^
    --set-env-vars="SERVER_WALLET_ADDRESS=0x255F9991233f86B29dB847c8d5b8CB9915e80dCf,PAYMENT_AMOUNT_USDC=0.01,POLYGON_RPC_URL=https://polygon-bor-rpc.publicnode.com"

if %errorlevel% equ 0 (
    echo.
    echo ========================================================
    echo   [SUCCESS] GCP Cloud Run 배포가 성공적으로 완료되었습니다!
    echo ========================================================
    echo.
    gcloud run services describe x402-cleanweb-agent --region asia-northeast3 --format="value(status.url)"
) else (
    echo.
    echo [ERROR] 배포 도중 오류가 발생했습니다. 위 로그를 확인해주세요.
)

echo.
pause
