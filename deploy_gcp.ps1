# ========================================================
#   x402-cleanweb-agent Google Cloud Run PowerShell Script
# ========================================================

Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "  x402-cleanweb-agent Cloud Run Deployment" -ForegroundColor Cyan
Write-Host "========================================================" -ForegroundColor Cyan

# 1. Check gcloud CLI
if (-not (Get-Command gcloud -ErrorAction SilentlyContinue)) {
    Write-Host "[ERROR] gcloud CLI is not installed or not in PATH." -ForegroundColor Red
    exit 1
}

# 2. Get current GCP Project
$currentProject = (gcloud config get-value project 2>$null).Trim()
if ([string]::IsNullOrEmpty($currentProject)) {
    $currentProject = Read-Host "Enter GCP Project ID"
    gcloud config set project $currentProject
}

Write-Host "Project ID: $currentProject" -ForegroundColor Green
Write-Host "Region: asia-northeast3 (Seoul)" -ForegroundColor Green

# Load .env if present
if (Test-Path .env) {
    Get-Content .env | ForEach-Object {
        $l = $_.Trim()
        if ($l -and -not $l.StartsWith('#') -and $l.Contains('=')) {
            $kv = $l.Split('=', 2)
            $k = $kv[0].Trim()
            $v = $kv[1].Trim()
            if (-not [string]::IsNullOrEmpty($k)) {
                [Environment]::SetEnvironmentVariable($k, $v, "Process")
            }
        }
    }
}

# 3. Enable APIs

Write-Host "`n[1/2] Enabling required GCP APIs (run, cloudbuild, artifactregistry)..." -ForegroundColor Yellow
gcloud services enable run.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com --quiet

# 4. Deploy to Cloud Run
Write-Host "`n[2/2] Deploying container to Cloud Run..." -ForegroundColor Yellow
gcloud run deploy x402-cleanweb-agent `
    --source . `
    --region asia-northeast3 `
    --platform managed `
    --allow-unauthenticated `
    --memory 512Mi `
    --cpu 1 `
    --min-instances 0 `
    --max-instances 10 `
    --set-env-vars="SERVER_WALLET_ADDRESS=0x255F9991233f86B29dB847c8d5b8CB9915e80dCf,PAYMENT_AMOUNT_USDC=0.01,POLYGON_RPC_URL=https://polygon-bor-rpc.publicnode.com,GEMINI_API_KEY=$($env:GEMINI_API_KEY),GEMINI_MODEL=gemini-3.6-flash" `
    --quiet



if ($LASTEXITCODE -eq 0) {
    Write-Host "`n========================================================" -ForegroundColor Green
    Write-Host "  [SUCCESS] Cloud Run deployment successful!" -ForegroundColor Green
    Write-Host "========================================================" -ForegroundColor Green
    $serviceUrl = (gcloud run services describe x402-cleanweb-agent --region asia-northeast3 --format="value(status.url)").Trim()
    Write-Host "Service URL: $serviceUrl" -ForegroundColor Cyan
    Write-Host "Health Check: $serviceUrl/health" -ForegroundColor Cyan
} else {
    Write-Host "`n[ERROR] Deployment failed. Check the logs above." -ForegroundColor Red
}
