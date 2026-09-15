# 📌 CleanWeb Studio - 다음 단계 작업 메모 (Next Steps)

작성일: 2026-09-14

---

## 🎯 내일 진행할 수 있는 주요 작업 목록

### 1. ☁️ GCP Cloud Run 클라우드 정식 배포 (외부 서비스 공개)
* **목적**: 로컬 PC가 꺼져도 전 세계 누구나 24시간 접속 가능한 퍼블릭 HTTPS 도메인 확보
* **스크립트**: [`deploy_gcp.ps1`](../deploy_gcp.ps1) 실행
* **확인 사항**: 환경변수(`.env`), GCP 프로젝트 ID, 아티팩트 레지스트리 및 Cloud Run 배포 상태 점검

### 2. 📦 PyPI 패키지 최신 버전 릴리즈 (`x402-cleanweb-agent`)
* **목적**: 외부 개발자 및 LangChain/CrewAI 에이전트들이 `pip install x402-cleanweb-agent`로 바로 쓸 수 있도록 배포
* **스크립트**: [`build_and_publish_pypi.bat`](../build_and_publish_pypi.bat) 실행
* **버전**: v2.5.3 최신 사양 반영

### 3. ⛓️ Base & Arbitrum 컨트랙트 추가 등록 (선택 사항)
* **목적**: Polygon 외에 BaseScan, Arbiscan에서도 공식 초록색 `Verified 🟢` 마크 획득
* **가이드**: [`contracts/verification/VERIFICATION_GUIDE.md`](verification/VERIFICATION_GUIDE.md)의 직접 검증 링크 및 Constructor HEX 활용

---

## 💡 현재 정상 가동 중인 로컬 서비스 상태
* **웹 스튜디오 대시보드**: `http://localhost:8080/dashboard` (사람 & 에이전트 공용 영문 UI)
* **API 문서**: `http://localhost:8080/docs`
* **서버 구동 파일**: [`run_server.bat`](../run_server.bat)
* **Polygon Mainnet 컨트랙트**: 3종 모두 Polygonscan 등록 및 라이브 연동 테스트 100% 완료
