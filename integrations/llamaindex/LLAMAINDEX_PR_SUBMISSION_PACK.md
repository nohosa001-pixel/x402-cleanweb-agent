# 🦙 LlamaIndex Official Integration Pull Request Pack: `llama-index-readers-x402-cleanweb`

This pack provides the exact, copy-paste ready Pull Request metadata and description to list **`llama-index-readers-x402-cleanweb`** into the official **[`run-llama/llama_index`](https://github.com/run-llama/llama_index)** repository.

---

## 📌 PR Metadata

- **Target Repository**: [`run-llama/llama_index`](https://github.com/run-llama/llama_index)
- **Base Branch**: `main`
- **Head Branch**: `feat/add-x402-cleanweb-reader`
- **PR Title**: `feat(readers): add x402-cleanweb reader integration for high-purity RAG and prompt injection defense`
- **Package on PyPI**: [`llama-index-readers-x402-cleanweb` (v0.1.0)](https://pypi.org/project/llama-index-readers-x402-cleanweb/0.1.0/)
- **Source Code**: [`packages/llama-index-readers-x402-cleanweb`](https://github.com/nohosa001-pixel/x402-cleanweb-agent/tree/main/packages/llama-index-readers-x402-cleanweb)

---

## 📋 Copy-Paste PR Body

```markdown
### Summary
This PR adds the official **`X402CleanWebReader`** integration (`llama-index-readers-x402-cleanweb`) to `llama-index-integrations/readers`.

`X402CleanWebReader` enables autonomous LlamaIndex agents and RAG pipelines to scrape and ingest web documents with **87% token reduction**, **indirect prompt injection defense**, and **multimodal alt-text preservation**.

- **PyPI Package**: `llama-index-readers-x402-cleanweb` (v0.1.0 published & verified)
- **Source Repository**: `nohosa001-pixel/x402-cleanweb-agent`
- **Documentation**: [https://github.com/nohosa001-pixel/x402-cleanweb-agent/tree/main/packages/llama-index-readers-x402-cleanweb#readme](https://github.com/nohosa001-pixel/x402-cleanweb-agent/tree/main/packages/llama-index-readers-x402-cleanweb#readme)

---

### Key Features
1. **87% Token Compression**: Drops web advertisements, boilerplate HTML, navigation scripts, and cookie modals before vector embedding.
2. **Indirect Prompt Injection Defense (OWASP LLM01)**: Neutralizes hidden CSS text (`display:none`, `visibility:hidden`, `font-size:0`), zero-width steganography, and query parameter data-exfiltration beacons.
3. **Multimodal Alt-Text Preservation**: Extracts descriptive image captions and charts (`![alt](url)`) for visual LLMs while neutralizing 1x1 tracking pixels.
4. **Zero-Overhead SPA Hydration**: Ingests pre-rendered state from Next.js (`__NEXT_DATA__`), Nuxt.js (`__NUXT_DATA__`), and Schema.org JSON-LD without spinning up heavy 500MB headless browser instances.
5. **Verifiable Provenance**: Attaches canonical URL, title, reading time, SHA-256 content fingerprints, and token reduction metrics directly into LlamaIndex `Document.metadata`.
6. **x402 Micropayments**: Handles autonomous machine-to-machine HTTP 402 settlement on Base, Polygon, Arbitrum, and Solana with a zero-auth sandbox trial.

---

### Quickstart

```python
from llama_index.readers.x402_cleanweb import X402CleanWebReader
from llama_index.core import VectorStoreIndex

# 1. Initialize reader (works out-of-the-box with free trial tier)
reader = X402CleanWebReader()

# 2. Ingest clean web documents
documents = reader.load_data(
    urls=["https://news.ycombinator.com/", "https://en.wikipedia.org/wiki/Retrieval-augmented_generation"],
    preserve_alt_text=True,
    dynamic_render=False
)

# 3. Build Vector Index directly
index = VectorStoreIndex.from_documents(documents)
query_engine = index.as_query_engine()
response = query_engine.query("Summarize the key discussion points.")
print(response)
```

---

### Test Plan
- [x] Unit test suite implemented and passing with 100% green status (`pytest packages/llama-index-readers-x402-cleanweb/tests/test_reader.py`).
- [x] Verified `load_data` with single URL and list of URLs.
- [x] Verified metadata preservation (`source`, `title`, `content_hash`, `token_reduction_percent`, `spa_framework`, `is_safe`).
- [x] Verified HTTP 402 payment required and network timeout error handling into structured `Document` objects.
- [x] Verified PyPI distribution `llama-index-readers-x402-cleanweb` installs cleanly.
```

---

## 🔗 Direct Link to Submit

- Open Pull Request on run-llama/llama_index:  
  **`https://github.com/run-llama/llama_index/compare`**
