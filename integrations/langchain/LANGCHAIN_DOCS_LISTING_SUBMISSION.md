# 📋 LangChain 공식 문서 디렉토리(Integrations Directory) 등재 신청 팩

LangChain 공식 문서 사이트([docs.langchain.com](https://docs.langchain.com/oss/python/integrations/providers))에 `langchain-x402-cleanweb`을 공식 커뮤니티 도구로 등재하기 위한 작성 가이드입니다.

---

## 🔗 1. 등록 신청 링크 (클릭하여 이동)
👉 **[LangChain Docs Issue 생성 페이지 열기](https://github.com/langchain-ai/docs/issues/new?template=integration-submission.yml)**
*(또는 [https://github.com/langchain-ai/docs/issues/new/choose](https://github.com/langchain-ai/docs/issues/new/choose) 접속 후 `New integration listing request` 선택)*

---

## 📝 2. 입력 항목별 복사-붙여넣기 내용

### 1) Display or Class Name
```text
X402CleanWebTool
```

### 2) Language / Ecosystem
```text
Python
```

### 3) Component Type
```text
tools
```

### 4) Package Name (PyPI)
```text
langchain-x402-cleanweb
```

### 5) Documentation URL
```text
https://github.com/nohosa001-pixel/x402-cleanweb-agent/tree/main/packages/langchain-x402-cleanweb#readme
```

### 6) Source Repository
```text
nohosa001-pixel/x402-cleanweb-agent
```

### 7) Short Provider Description
```text
Autonomous web scraping and cleaning tool for LangChain agents. Achieves 87% token reduction by stripping ads, cookie modals, and DOM boilerplate. Features indirect prompt injection defense, Next.js/Nuxt.js SPA hydration extraction, multimodal image alt-text preservation, and autonomous USDC micropayments over Base, Polygon, Arbitrum, and Solana.
```

### 8) PyPI Verification Link
```text
https://pypi.org/project/langchain-x402-cleanweb/0.1.0/
```

### 9) Checkbox Confirmation
- [x] Package is published and verified on PyPI.

---

## ⚡ 3. 제출 후 자동 처리 절차
1. 폼 제출 시 GitHub Actions 자동화 봇(`integration-run`)이 PyPI 메타데이터를 즉시 검증합니다.
2. 검증 통과 시 `scripts/data/integration_external_docs.yaml`에 `langchain-x402-cleanweb` 항목이 자동으로 등록됩니다.
3. [docs.langchain.com/oss/python/integrations/providers](https://docs.langchain.com/oss/python/integrations/providers) 공식 페이지 목록에 우리 CleanWeb 도구가 실시간 노출됩니다.

