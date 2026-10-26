# blackbox-unofficial-api

> Unofficial Python API client and CLI for **Blackbox AI** (`blackbox.ai`).

---

## Installation

```bash
pip install blackbox-unofficial-api
```

---

## Quick Start

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

## License

MIT &copy; [etrnkz](https://github.com/etrnkz/black-box-unoffcial-api)
