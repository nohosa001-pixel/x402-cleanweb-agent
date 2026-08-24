# 🚀 GCP (Google Cloud Platform) 완벽 운영 및 배포 가이드

`x402-cleanweb-agent` 마이크로 에이전트 서비스를 **Google Cloud Platform (GCP)** 의 최신 서버리스 컨테이너 플랫폼인 **Cloud Run**에 배포하고 실무 운영/모니터링하기 위한 종합 가이드입니다.

---

## 🌟 왜 Google Cloud Run인가요?

1. **완전 관리형 서버리스**: 트래픽이 없을 때는 인스턴스가 0개로 축소(Scale to Zero)되어 **비용이 0원**입니다.
2. **넉넉한 무료 티어**: 매월 2백만 회의 요청, 360,000GB-초 메모리, 180,000vCPU-초가 무료로 제공됩니다.
3. **자동 HTTPS & 커스텀 도메인**: 기본 `https://...run.app` 주소가 즉시 발급되며 무료 SSL 인증서가 제공됩니다.
4. **서울 리전(`asia-northeast3`) 지원**: 초저지연(0.4초 미만) 한국 서버 운영이 가능합니다.

---

## 📁 구성된 GCP 인프라 설정 파일들

| 파일명 | 역할 및 내용 |
|---|---|
| [`Dockerfile`](file:///Dockerfile) | Python 3.11 기반 경량 컨테이너 이미지 정의 (기본 포트 8080) |
| [`.gcloudignore`](file:///.gcloudignore) | 빌드 시 불필요한 파일(`.venv`, `.git` 등)을 제외하여 빠른 빌드 지원 |
| [`cloudbuild.yaml`](file:///cloudbuild.yaml) | Cloud Build CI/CD 자동화 빌드 & 배포 파이프라인 |
| [`deploy_gcp.bat`](file:///deploy_gcp.bat) | Windows 1-클릭 자동 배포 배치 파일 |
| [`deploy_gcp.ps1`](file:///deploy_gcp.ps1) | PowerShell 자동 배포 스크립트 |

---

## ⚡ 방법 1: 원클릭 자동 배포 (가장 빠름)

프로젝트 폴더에서 아래 스크립트 중 하나를 실행하면 자동으로 빌드와 배포가 완료됩니다.

### Windows CMD
```cmd
deploy_gcp.bat
```

### Windows PowerShell
```powershell
.\deploy_gcp.ps1
```

---

## 🛠️ 방법 2: gcloud CLI 직접 명령어 배포

### 1. GCP 계정 로그인 및 프로젝트 설정
```bash
# GCP 로그인
gcloud auth login

# 배포할 프로젝트 설정 (예: my-nohosa-87175)
gcloud config set project my-nohosa-87175
```

### 2. 필수 API 활성화 (최초 1회만 필요)
```bash
gcloud services enable run.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com
```

### 3. Cloud Run 배포 실행 (소스코드 직접 빌드 & 배포)
```bash
gcloud run deploy x402-cleanweb-agent \
    --source . \
    --region asia-northeast3 \
    --platform managed \
    --allow-unauthenticated \
    --memory 512Mi \
    --cpu 1 \
    --min-instances 0 \
    --max-instances 10 \
    --set-env-vars SERVER_WALLET_ADDRESS=0x255F9991233f86B29dB847c8d5b8CB9915e80dCf,PAYMENT_AMOUNT_USDC=0.01,POLYGON_RPC_URL=https://polygon-bor-rpc.publicnode.com
```

---

## 🔐 환경 변수(Environment Variables) 설정

운영 환경에 맞춰 환경 변수를 변경할 때는 아래와 같이 지정하거나 GCP 콘솔(Cloud Run -> 서비스 수정)에서 변경할 수 있습니다.

| 환경 변수명 | 기본값 / 권장값 | 설명 |
|---|---|---|
| `SERVER_WALLET_ADDRESS` | `0x255F9991233f86B29dB847c8d5b8CB9915e80dCf` | 결제(USDC)를 수신할 폴리곤 지갑 주소 |
| `PAYMENT_AMOUNT_USDC` | `0.01` | 기본 웹 클린 결제 요구 금액 (USDC) |
| `POLYGON_RPC_URL` | `https://polygon-bor-rpc.publicnode.com` | 폴리곤 메인넷 RPC 노드 주소 |
| `USDC_CONTRACT_ADDRESS` | `0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359` | 폴리곤 네이티브 USDC 토큰 컨트랙트 |

**환경 변수 업데이트 명령어:**
```bash
gcloud run services update x402-cleanweb-agent \
    --region asia-northeast3 \
    --update-env-vars PAYMENT_AMOUNT_USDC=0.02
```

---

## 🔍 배포 후 상태 확인 및 테스트

배포된 서비스 엔드포인트:
- **Canonical Short URL**: `https://x402-cleanweb-agent-7qxtp3324q-du.a.run.app`
- **Region URL**: `https://x402-cleanweb-agent-212942243360.asia-northeast3.run.app`

### 1. 헬스 체크
```bash
curl https://x402-cleanweb-agent-7qxtp3324q-du.a.run.app/health
```
**응답:**
```json
{"status":"healthy","version":"1.2.1","chain_id":137,"network":"Polygon Mainnet","pypi":"https://pypi.org/project/x402-cleanweb-agent/"}
```

### 2. 결제 요구(402) 응답 테스트
```bash
curl -i "https://x402-cleanweb-agent-7qxtp3324q-du.a.run.app/api/v1/clean-web?url=https://example.com"
```
**응답:** `HTTP/1.1 402 Payment Required` 및 폴리곤 지갑 결제 안내 헤더/바디 반환

### 3. LLM Machine Guide (`/llms.txt`) 확인
```bash
curl https://x402-cleanweb-agent-7qxtp3324q-du.a.run.app/llms.txt
```

---

## 📊 실시간 로그 스트리밍 & 모니터링 (운영 팁)

에이전트들의 실시간 결제 검증 내역, URL 스크래핑 성공/실패 로그를 터미널에서 실시간으로 확인할 수 있습니다.

### 실시간 로그 스트리밍 (Tail Logs)
```bash
gcloud run services logs tail x402-cleanweb-agent --region asia-northeast3
```

### 최근 에러 로그만 필터링 조회
```bash
gcloud beta run services logs read x402-cleanweb-agent --region asia-northeast3 --limit=50
```

---

## ⚡ 콜드 스타트 vs 제로 비용 최적화 전략

| 설정 옵션 | 명령어 옵션 | 장점 | 비용 |
|---|---|---|---|
| **기본 (비용 0원 최적화)** | `--min-instances 0` | 요청 없을 때 비용 0원 | 첫 요청 시 약 1~2초 콜드스타트 |
| **초저지연 무지연 응답** | `--min-instances 1` | 24시간 항상 인스턴스 상주, 0ms 콜드스타트 | 월 무료 티어 소진 후 소액 발생 가능 |

**최소 인스턴스 1개로 상시 대기 전환:**
```bash
gcloud run services update x402-cleanweb-agent --region asia-northeast3 --min-instances 1
```

---

## 🌐 커스텀 도메인 연결 (선택 사항)

자체 보유 도메인(예: `agent.yourdomain.com`)을 연결하려면:
1. GCP 콘솔 접속 ➡️ **Cloud Run** ➡️ **맞춤 도메인 관리 (Custom Domains)**
2. **도메인 매핑 추가** 클릭 ➡️ 서비스(`x402-cleanweb-agent`) 및 도메인 선택
3. 안내되는 DNS CNAME 레코드를 도메인 관리자(Cloudflare, 가비아, 후이즈 등)에 등록
4. 무료 Let's Encrypt SSL 인증서가 15~30분 내 자동 발급 및 적용됩니다.

---

## ⛓️ 온체인 수신 지갑 모니터링

서버로 수신되는 모든 마이크로 결제(USDC)는 폴리곤 익스플로러에서 실시간으로 확인할 수 있습니다:
- **수신 지갑 Polygonscan**: [0x255F9991233f86B29dB847c8d5b8CB9915e80dCf](https://polygonscan.com/address/0x255F9991233f86B29dB847c8d5b8CB9915e80dCf)
- **USDC Token Tracker**: [0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359](https://polygonscan.com/token/0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359?a=0x255F9991233f86B29dB847c8d5b8CB9915e80dCf)
