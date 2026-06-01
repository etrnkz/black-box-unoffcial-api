<p align="center">
  <img src="media/banner.svg" alt="BlackBox API — Reverse of Blackbox.ai">
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-%3E%3D3.10-3776AB?logo=python&logoColor=white" alt="Python 3.10+">
  <img src="https://img.shields.io/badge/license-MIT-blue" alt="MIT">
  <img src="https://img.shields.io/badge/status-active-success" alt="Active">
  <img src="https://img.shields.io/badge/PRs-welcome-8A2BE2" alt="PRs Welcome">
</p>

<p align="center">
  <a href="#quick-start">Quick Start</a> •
  <a href="#usage">Usage</a> •
  <a href="#commands">Commands</a> •
  <a href="#auth">Auth</a>
</p>

---

<p align="center">
  <strong>Full reverse of blackbox.ai</strong>
  <br>
  No API key. No tokens. No signup required.
  <br>
  Just paste your browser cookies or login — and you're in.
</p>

---

## Quick Start

```bash
pip install httpx curl-cffi
pip install -e .
```

**Chat — zero setup, just cookies from your browser:**

```bash
python -m blackbox --cookie "session=abc; next-auth.session-token=xyz" chat "What is the capital of France?"
```

```python
from blackbox import WebChat

# Paste cookies from app.blackbox.ai → DevTools → Network tab
wc = WebChat(cookie_header="session=abc; next-auth.session-token=xyz; ...")

result = wc.chat("What is the capital of France?")
print(result.content)
```

**Or login with email/password (gets cookies automatically):**

```python
wc = WebChat.login(email="user@example.com", password="your-password")
result = wc.chat("Explain quantum computing")
```

**That's it. No API key. No token. Just the website.**

## Usage

```python
from blackbox import WebChat

wc = WebChat(cookie_header="...")

# Chat
r = wc.chat("Hello")
r = wc.chat_stream("Write a poem")  # generator
for chunk in r:
    print(chunk, end="")

# Search
r = wc.search("latest Python news")
for s in r.sources:
    print(f"  {s['title']}: {s['url']}")

# Code
r = wc.generate_code("quicksort", language="python")

# Image
r = wc.generate_image("a cat in space")

# Video
r = wc.generate_video("drone over mountains")

# File
r = wc.chat_with_file("document.pdf", "Summarize this")

# Reasoning
r = wc.chat("Solve this math problem", reasoning=True)

# Login
wc = WebChat.login(email="user@example.com", password="...")
r = wc.chat("Hello after login")
```

## Commands

```bash
# All work without any API key — just --cookie or login

python -m blackbox login --email user@example.com   # login, prints cookie header
python -m blackbox --cookie "..." chat "Hello"       # chat
python -m blackbox --cookie "..." search "AI news"   # web search
python -m blackbox --cookie "..." code "quicksort"   # code generation
python -m blackbox --cookie "..." image "a cat"      # image generation
python -m blackbox --cookie "..." video "drone"      # video generation
python -m blackbox --cookie "..." file doc.pdf "Summarize"  # file chat
python -m blackbox --cookie "..." reason "solve x"   # reasoning mode
```

## Auth

| Method | How it works |
|--------|-------------|
| Browser cookies | Open app.blackbox.ai → DevTools → Network → copy `Cookie` header from any request. Pass with `--cookie "..."` or `cookie_header="..."` |
| Email login | `WebChat.login(email, password)` — logs in programmatically, stores cookies in session |
| Validated UUID | Some features need a `validated` UUID. Extract from DevTools once — per-account, not per-session |

## Project

```
src/blackbox/
├── __init__.py    # Exports
├── __main__.py    # python -m blackbox
├── cli.py         # CLI (all web-first, no API key)
├── webchat.py     # Web endpoint — full website reverse
├── login.py       # NextAuth login (curl_cffi)
├── files.py       # File upload utilities
├── models.py      # Data classes
├── chat.py        # API chat (optional, needs API key)
├── client.py      # BlackBoxClient (optional, needs API key)
├── auth.py        # Web auth helpers
├── image.py       # Image gen via API
├── code.py        # Code gen via API
├── credits.py     # Credits via API
└── agents.py      # Agents via API
```

## License

MIT &copy; [etrnkz](https://github.com/etrnkz/black-box-unoffcial-api)
