# 🌐 CleanWeb Studio — Clean Web & Document Extraction Web App

> **Turn any cluttered webpage, YouTube video, or PDF paper into clean, readable text with a single click.**  
> *No expensive monthly subscriptions. Try it instantly on the interactive Web UI.*

[![Live Web App](https://img.shields.io/badge/Live%20Web%20App-Try%20Free%20UI-00f2fe?style=for-the-badge&logo=googlechrome&logoColor=black)](https://x402-cleanweb-agent-7qxtp3324q-du.a.run.app)
[![PyPI Package](https://img.shields.io/pypi/v/x402-cleanweb-agent.svg?color=blue&label=PyPI%20Package)](https://pypi.org/project/x402-cleanweb-agent/)
[![Glama.ai](https://img.shields.io/badge/Glama.ai-Listed-00ffcc?style=for-the-badge&logo=anthropic&logoColor=black)](https://glama.ai/mcp/servers/nohosa001-pixel/x402-cleanweb-agent)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## ✨ Experience the Live Interactive Web UI

No setup required. Access our modern Web App directly from your browser:

### 🔗 **[👉 Launch Live Web App (Free Instant Test)](https://x402-cleanweb-agent-7qxtp3324q-du.a.run.app)**

```
┌────────────────────────────────────────────────────────────────────────┐
│  ✨ CleanWeb Studio                                  [⚡ Free Test]     │
├────────────────────────────────────────────────────────────────────────┤
│  [ 🌐 Clean Web ]  [ 🎬 YouTube ]  [ 📑 PDF & Papers ]  [ 📝 Text ]    │
├────────────────────────────────────────────────────────────────────────┤
│  Target URL: https://example.com/long-article                          │
│                                                                        │
│  [  ⚡ Extract Clean Content  ]   [ 📋 Copy to AI (ChatGPT / Claude) ]  │
│                                                                        │
│  ✓ 100% Ads & Noise Removed   ✓ Ready-to-Read Markdown   ✓ Instant    │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 🎯 What You Get (User Services)

Tired of messy ads, popups, and expensive $49/month SaaS subscriptions just to read or summarize articles?  
**CleanWeb Studio** solves your daily reading and research hassles:

1. 🌐 **Clutter-Free Web Reader**: Strips banners, ads, and sidebars from any website. Returns 100% pure, readable text ready for note-taking.
2. 🎬 **YouTube Script & Timestamp Extractor**: Paste any YouTube link to get the entire spoken transcript organized with clean timestamps in seconds.
3. 📑 **PDF & Paper Formatter**: Converts dense PDF documents and research papers into clean, structured text that is easy to read.
4. 📝 **AI-Ready Text Extractor**: Prepares clean text formatted perfectly to copy-paste directly into ChatGPT, Claude, or Notion.
5. 💎 **Pay-As-You-Go (No Monthly Lock-in)**: No forced monthly subscriptions. Pay only a few cents ($0.005 ~ $0.05) per document when you actually use it.
6. ⚡ **Zero-Login Free Preview**: Click the `[⚡ Free Instant Test]` button in the Web UI to test any feature immediately without creating an account.

---

## 🖥️ Interactive Web UI Features

| Feature Tab | What it Does | Best Used For |
| :--- | :--- | :--- |
| **🌐 Clean Web** | Removes all ads, banners & clutter from articles | Researching news, blogs, and documentation |
| **🎬 YouTube Transcript** | Extracts full video scripts with timestamp links | Quick video summaries, lecture notes, podcasts |
| **📑 PDF & Papers** | Formats complex PDF research into clean text | Reading arXiv papers, financial reports, whitepapers |
| **📝 Pure Text** | Extracts lightweight text with zero markup | Copy-pasting into AI chat tools (ChatGPT, Claude) |
| **📦 Batch Process** | Cleans multiple links at once | Bulk research and multi-article reading |

---

## 💻 Developer & AI Assistant Setup (Optional)

You can also run CleanWeb directly inside your favorite AI workspace:

### 1. Claude Desktop & Cursor (1-Second Setup)
Add this to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "cleanweb-studio": {
      "command": "uvx",
      "args": ["x402-cleanweb-agent"]
    }
  }
}
```

### 2. Python Package
```bash
pip install x402-cleanweb-agent
```

```python
from agent_tools import X402AgentToolkit

toolkit = X402AgentToolkit()

# Clean any webpage in 1 line
clean_article = toolkit.clean_web("https://example.com/article")
print(clean_article)
```

---

## 🌐 Quick Links

- 🖥️ **Live Web UI App**: [https://x402-cleanweb-agent-7qxtp3324q-du.a.run.app](https://x402-cleanweb-agent-7qxtp3324q-du.a.run.app)
- 📦 **PyPI Package**: [https://pypi.org/project/x402-cleanweb-agent/](https://pypi.org/project/x402-cleanweb-agent/)
- 🦙 **Glama.ai Listing**: [https://glama.ai/mcp/servers/nohosa001-pixel/x402-cleanweb-agent](https://glama.ai/mcp/servers/nohosa001-pixel/x402-cleanweb-agent)
- 📂 **GitHub Repository**: [https://github.com/nohosa001-pixel/x402-cleanweb-agent](https://github.com/nohosa001-pixel/x402-cleanweb-agent)

---

## 📄 License

Distributed under the **MIT License**.
