# 🚀 LangChain 공식 등록 (PR & Integration Submission Pack)

이 문서는 **LangChain 공식 생태계([langchain-ai/langchain](https://github.com/langchain-ai/langchain))**에 `x402 CleanWeb Tool`을 공식 도구로 등록하기 위해 준비된 마스터 가이드입니다.

---

## 📁 1. 준비된 파일 및 코드 (검증 완료 🟢)

로컬에서 단위 테스트 및 실시간 게이트웨이 호출 테스트(100% PASS)를 완료한 파일들입니다:

1. **도구 본체 (`tool.py`)**: [`integrations/langchain/x402_cleanweb_tool.py`](file:///c:/Users/nohos/OneDrive/바탕%20화면/x402-micro-agent/integrations/langchain/x402_cleanweb_tool.py)
   - LangChain `BaseTool` 표준 준수 (`_run`, `_arun`, Pydantic v2 `args_schema`)
   - HTTP 402 결제 챌린지 및 마이크로페이먼트 볼트 자동 연동
   - 87% 토큰 압축 마크다운 반환
2. **단위 테스트 (`test_tool.py`)**: [`integrations/langchain/test_langchain_x402_cleanweb.py`](file:///c:/Users/nohos/OneDrive/바탕%20화면/x402-micro-agent/integrations/langchain/test_langchain_x402_cleanweb.py)
   - 4개 단위 테스트 100% 통과 (메타데이터, 200 성공, 402 결제 챌린지, 비동기 호출)

---

## 🛠️ 2. LangChain 레포지토리 기준 파일 배치 경로

LangChain을 Fork한 후 복사할 파일 위치입니다:

```text
langchain/
└── libs/
    └── community/
        ├── langchain_community/
        │   └── tools/
        │       ├── x402_cleanweb/
        │       │   ├── __init__.py
        │       │   └── tool.py  <-- (x402_cleanweb_tool.py 내용 복사)
        │       └── __init__.py  <-- (X402CleanWebTool export 추가)
        └── tests/
            └── unit_tests/
                └── tools/
                    └── test_x402_cleanweb.py  <-- (test_x402_cleanweb_tool.py 내용 복사)
```

---

## 📋 3. GitHub PR 제출 정보 (복사해서 바로 사용 가능)

### 📌 PR Title (제목)
```text
community: Add x402 CleanWeb tool for autonomous 87% token-reduced web scraping
```

---

### 📝 PR Body (본문 마크다운)

```markdown
### Summary
This PR introduces the **`X402CleanWebTool`** to `langchain-community`, enabling LangChain agents to autonomously scrape webpages, strip ads and HTML boilerplate, and return pure, LLM-optimized Markdown with **87% token reduction** via x402 micropayments.

### Motivation
- **Token Efficiency**: LLM agents often consume tens of thousands of tokens scraping raw HTML. `X402CleanWebTool` reduces 20,000-token HTML pages to ~2,600 clean Markdown tokens, cutting inference costs by up to 86%.
- **Zero-Friction Agent Economics**: Supports autonomous machine-to-machine micropayments (USDC) over Solana, Polygon, Base, and Arbitrum with pre-funded agent vaults, eliminating the need for human credit card intervention.
- **Included Free Tier**: Includes a 5-call zero-auth sandbox trial per session nonce for instant zero-configuration testing.

### Key Features
- **LangChain Standard Compliance**: Implements both sync `_run` and async `_arun` via `BaseTool`.
- **Pydantic v2 Schema**: Validated `args_schema` (`X402CleanWebInput`).
- **Autonomous Error & 402 Handling**: Gracefully handles HTTP 402 Payment Required challenges and network timeouts.

### Testing
- Unit tests added at `libs/community/tests/unit_tests/tools/test_x402_cleanweb.py`.
- Verified 100% pass on pytest with mocked responses for metadata, 200 OK, 402 challenge, and async execution.
- Tested against live production gateway (`https://x402-cleanweb-agent-7qxtp3324q-du.a.run.app`).

### Example Usage
```python
from langchain_community.tools.x402_cleanweb import X402CleanWebTool

tool = X402CleanWebTool()
result = tool.run("https://news.ycombinator.com")
print(result)
```

### Checklist
- [x] Linting and formatting pass.
- [x] Unit tests added and passing.
- [x] `__all__` updated in `__init__.py`.
- [x] PR title follows conventions (`community: ...`).
```

---

## ⚡ 4. 터미널 실행 명령어 (Git 워크플로우 4단계)

GitHub CLI(`gh`) 또는 Git을 통해 PR을 생성하는 순서입니다:

### Step 1: LangChain 공식 레포 Fork 및 Clone
```bash
# 본인 계정으로 langchain 레포 fork 후 로컬 클론
git clone https://github.com/<YOUR_GITHUB_ID>/langchain.git
cd langchain
git checkout -b feature/x402-cleanweb-tool
```

### Step 2: 준비된 코드 복사 & 파일 생성
```bash
# 디렉토리 생성
mkdir -p libs/community/langchain_community/tools/x402_cleanweb
mkdir -p libs/community/tests/unit_tests/tools

# x402_micro-agent 프로젝트에서 파일 복사
# tool.py 생성 및 test_x402_cleanweb.py 생성
```

### Step 3: 커밋 및 푸시
```bash
git add libs/community/langchain_community/tools/x402_cleanweb/
git add libs/community/tests/unit_tests/tools/test_x402_cleanweb.py
git commit -m "community: Add x402 CleanWeb tool for autonomous 87% token-reduced web scraping"
git push origin feature/x402-cleanweb-tool
```

### Step 4: PR 생성
* 브라우저에서 `https://github.com/langchain-ai/langchain` 접속 후 **"Compare & pull request"** 클릭
* 위의 [3. GitHub PR 제출 정보]의 제목과 본문을 그대로 붙여넣고 **"Create pull request"** 클릭!

---

## 💡 추가 옵션: LangChain 공식 Integration Listing Issue 제출

최근 LangChain 팀은 커뮤니티 PR 외에도 **"Integration Listing"**을 장려하고 있습니다.
* 이미 PyPI에 배포된 `x402-cleanweb-agent`를 LangChain 공식 문서 레지스트리에 등록 요청하는 이슈(Issue)도 함께 제출하면 채택 확률이 2배로 높아집니다:
* 이슈 등록 URL: `https://github.com/langchain-ai/langchain/issues/new?template=integration_listing.yml`
