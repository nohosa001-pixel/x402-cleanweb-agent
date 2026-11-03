# LangChain x402 CleanWeb Integration

Official LangChain tool integration for **x402 CleanWeb Studio** (`x402-cleanweb-agent`).

Enables autonomous LangChain agents, conversational bots, and RAG pipelines to scrape and ingest web content at scale without drowning LLM context windows in boilerplate HTML, navigation scripts, tracking pixels, and ads.

---

## ⚡ Key Features

- **87% Token Compression**: Strips boilerplate, ads, cookie modals, and navigation markup before index embedding.
- **Indirect Prompt Injection Defense**: Neutralizes hidden CSS text, zero-width steganography, and malicious query-parameter exfiltration links.
- **Multimodal Alt-Text Preservation**: Extracts descriptive image `alt` tags (`![alt](url)`) for visual LLMs while neutralizing 1x1 tracking pixels.
- **SPA Hydration Extraction**: Zero-overhead pre-rendered state parsing for Next.js (`__NEXT_DATA__`), Nuxt.js (`__NUXT_DATA__`), and Schema.org JSON-LD.
- **x402 Autonomous Micropayments**: Native machine-to-machine USDC micropayments over Base, Polygon, Arbitrum, and Solana with a zero-auth 5-call trial tier.
- **LangChain Standard Compliance**: Implements both sync `_run` and async `_arun` via `langchain_core.tools.BaseTool` with Pydantic v2 `args_schema`.

---

## 📦 Installation

```bash
pip install langchain-x402-cleanweb
```

---

## 🚀 Quickstart

### 1. Direct Tool Invocation

```python
from langchain_x402_cleanweb import X402CleanWebTool

# Initialize tool (uses official Cloud Run gateway by default)
tool = X402CleanWebTool()

# Scrape and clean web page
clean_markdown = tool.run("https://en.wikipedia.org/wiki/Web_scraping")
print(clean_markdown)
```

### 2. Autonomous LangChain Agent Integration

```python
from langchain.agents import initialize_agent, AgentType
from langchain_openai import ChatOpenAI
from langchain_x402_cleanweb import X402CleanWebTool

llm = ChatOpenAI(model="gpt-4o", temperature=0)
tools = [X402CleanWebTool()]

agent = initialize_agent(
    tools=tools,
    llm=llm,
    agent=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True
)

response = agent.run("Summarize the latest engineering news on https://news.ycombinator.com")
print(response)
```

### 3. Asynchronous Execution

```python
import asyncio
from langchain_x402_cleanweb import X402CleanWebTool

async def main():
    tool = X402CleanWebTool()
    content = await tool.arun("https://docs.python.org/3/whatsnew/3.13.html")
    print(content[:500])

asyncio.run(main())
```

---

## ⚙️ Configuration & Authentication

The tool works out of the box with **5 free trial requests** per session nonce.

For production high-throughput autonomous agents, set the environment variable:

```bash
export AGENT_VAULT_KEY="your_funded_vault_session_key"
```

Or pass it programmatically:

```python
tool = X402CleanWebTool(
    vault_key="your_vault_key",
    gateway_url="https://x402-cleanweb-agent-7qxtp3324q-du.a.run.app"
)
```

---

## 🛡️ License

MIT License. Developed by the x402 Autonomous Agent Ecosystem.
