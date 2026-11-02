# LlamaIndex Integration: x402 CleanWeb Data Reader

Official LlamaIndex `BaseReader` integration for **CleanWeb Studio** (`x402-cleanweb-agent`).

## 🌟 Key Features
- **87% Token Compression**: Drops ads, navigation, and boilerplate before loading into LlamaIndex indices.
- **Indirect Prompt Injection Defense**: Strips zero-width steganography, invisible CSS containers, and covert parameter tracking.
- **Built-in Document Metadata**: Automatically attaches `source`, `title`, `content_hash` (SHA-256 fingerprint), and `token_reduction_percent`.
- **Zero-Trust Autonomous Micropayments**: Native x402 USDC micropayment handling on Solana, Base, Polygon, and Arbitrum.

## 🚀 Quickstart Example

```python
from integrations.llamaindex.x402_cleanweb_reader import X402CleanWebReader
from llama_index.core import VectorStoreIndex

# 1. Initialize reader with optional Vault Key
reader = X402CleanWebReader(vault_key="your_vault_session_key")

# 2. Ingest clean web documents
documents = reader.load_data(
    urls=["https://news.ycombinator.com/", "https://en.wikipedia.org/wiki/Artificial_intelligence"],
    preserve_alt_text=True,
    dynamic_render=False
)

# 3. Build Vector Index directly
index = VectorStoreIndex.from_documents(documents)
query_engine = index.as_query_engine()
response = query_engine.query("What are the key discussions today?")
print(response)
```

