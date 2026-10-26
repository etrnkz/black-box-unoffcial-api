# blackbox-unofficial-api

> Python client and CLI for **Blackbox AI** (`blackbox.ai`).

---

## Highlights

- **Dual Backend Support**:
  - **Enterprise Gateway**: Full OpenAI-compatible chat completions (`https://enterprise.blackbox.ai/v1`).
  - **Web Session Client**: Browser cookie-based session automation.
- **Streaming & Multi-Model**: Full SSE streaming response parsing across code, chat, reasoning, and image generation modes.
- **Developer CLI**: Terminal commands for chatting, search, code synthesis, and session inspection.

---

## Installation

```bash
pip install -e .
```

Or install dependencies directly:
```bash
pip install httpx curl-cffi
```

---

## Quickstart

### 1. Enterprise Mode (API Key)

```python
from blackbox import BlackBoxClient

client = BlackBoxClient(api_key="your-blackbox-api-key")

# Standard chat completion
completion = client.chat.complete([
    {"role": "user", "content": "Write an async HTTP server in Rust using Tokio and Axum"}
], model="blackboxai/anthropic/claude-sonnet-4.5")

print(completion.choices[0].message.content)
```

### 2. Browser Session Mode (WebChat)

Blackbox web endpoints require session cookies from an active browser session. Copy your cookie string from DevTools (`app.blackbox.ai` -> Network tab -> `Cookie` header):

```python
from blackbox import WebChat

wc = WebChat(cookie_header="sessionId=...; __Secure-authjs.callback-url=...")

# Ask a question
response = wc.chat("Explain Raft consensus in simple terms")
print(response.content)

# Web search with source citations
search_res = wc.search("Latest developments in quantum error correction")
print(search_res.content)
for src in search_res.sources:
    print(f"- {src['title']}: {src['url']}")

# Code generation
code_res = wc.generate_code("A thread-safe circular buffer in C++20")
print(code_res.content)
```

---

## CLI Reference

```bash
# Chat using session cookies
blackbox --cookie "sessionId=..." chat "Write a binary search algorithm in Go"

# Deep web search
blackbox --cookie "sessionId=..." search "What is eBPF and how does it work?" --deep

# Code synthesis
blackbox --cookie "sessionId=..." code "LRU cache implementation" --language python

# Reasoning mode
blackbox --cookie "sessionId=..." reason "Solve this logic riddle"
```

---

## License

MIT License. Reverse-engineered for research and developer interoperability.
