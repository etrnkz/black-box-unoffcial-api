<p align="center">
  <img src="media/banner.svg" alt="BlackBox Unofficial API">
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-%3E%3D3.10-3776AB?logo=python&logoColor=white" alt="Python 3.10+">
  <img src="https://img.shields.io/badge/license-MIT-blue" alt="MIT">
  <img src="https://img.shields.io/badge/dependencies-2-lightgrey" alt="2 deps">
  <img src="https://img.shields.io/badge/tests-88--passed-success" alt="88 tests">
  <img src="https://img.shields.io/badge/status-active-success" alt="Active">
</p>

<p align="center">
  <a href="#quick-start">Quick Start</a> •
  <a href="#at-a-glance">At a Glance</a> •
  <a href="#docs">Docs</a> •
  <a href="#cli">CLI</a>
</p>

---

<p align="center">
  <strong>Unofficial Python client for blackbox.ai</strong>
  <br>
  API key unlocks chat, search, images, video, agents — cookies for web auth.
  <br>
  Full OpenAI-compatible chat completions with 30+ documented parameters.
</p>

---

## Quick Start

```bash
pip install httpx curl-cffi
pip install -e .
```

```python
from blackbox import BlackBoxClient, ChatMessage

client = BlackBoxClient(api_key="sk-...")
result = client.chat_complete(
    messages=[ChatMessage(role="user", content="Hello!")],
    model="anthropic/claude-sonnet-4.5",
)
print(result.content)
```

## At a Glance

| Area | Methods | Auth |
|------|---------|------|
| Chat | `chat_complete`, `chat_complete_stream` | API key |
| Search | `search` (with source citations) | API key |
| Image | `generate_image`, `generate_image_chat` | API key |
| Video | `generate_video` (Veo-2, Ray-2, etc.) | API key |
| Code | `generate_code` | API key |
| Tools | function calling, tool_choice, reasoning | API key |
| Files | `chat_with_file`, `read_file`, `FileContentPart` | API key |
| Agents | `create_agent`, `list_agents`, `execute_agent` | API key |
| Multi-Agent | `create_multi_agent_task` (parallel) | API key |
| Web Chat | `web_chat`, `web_search`, `web_generate_*` | cookie |
| Login | `login` (NextAuth flow) | email/password |
| Account | `get_session`, `get_credits`, `get_models` | API key / cookie |

## Examples

```python
# Search with sources
result = client.search("latest AI news")
print(result.content)

# Image generation
img = client.generate_image("a cat in space", model="flux-pro")
print(img.data[0].url)

# Tool calling with reasoning
from blackbox import Tool, ReasoningConfig

tools = [Tool(type="function", function={
    "name": "get_weather",
    "description": "Get weather for a city",
    "parameters": {
        "type": "object",
        "properties": {"location": {"type": "string"}},
        "required": ["location"],
    },
})]
result = client.chat_complete(
    messages=[ChatMessage(role="user", content="Weather in Paris?")],
    model="google/gemini-2.0-flash-001",
    tools=tools,
    reasoning=ReasoningConfig(effort="medium"),
)

# File chat with local file
result = client.chat_with_file("document.pdf", "Summarize this")
print(result.content)

# Multi-agent task
from blackbox import AgentTaskConfig
task = client.create_multi_agent_task(
    prompt="Add README in Spanish",
    agents=[
        AgentTaskConfig(agent="claude", model="anthropic/claude-sonnet-4.5"),
        AgentTaskConfig(agent="blackbox", model="blackbox-pro"),
    ],
)
```

## Web Auth

```python
from blackbox import WebChat

# Login with email/password
wc = WebChat.login(email="user@example.com", password="...")
result = wc.chat("Hello from web")
print(result.content)

# Or with BlackBoxClient
client = BlackBoxClient(session_token="...", validated="a38f5889-...")
session = client.get_session()
credits = client.get_credits()
```

## CLI

```bash
# API key commands
python -m blackbox --api-key "sk-..." chat "Hello" --model anthropic/claude-sonnet-4.5
python -m blackbox --api-key "sk-..." search "latest AI news"
python -m blackbox --api-key "sk-..." image "a cat" --model flux-pro
python -m blackbox --api-key "sk-..." video "drone shot" --model veo-2
python -m blackbox --api-key "sk-..." code "quicksort in python"

# Web chat
python -m blackbox webchat "Hello"
python -m blackbox websearch "AI news"
python -m blackbox login --email user@example.com
```

## Docs

| | |
|---|---|
| <img src="media/icon.svg" width="18" align="center"> [Chat Completions](src/blackbox/chat.py) | Full OpenAI-compatible API with all 30+ parameters, streaming, tool calling |
| <img src="media/icon.svg" width="18" align="center"> [Web Auth](src/blackbox/login.py) | NextAuth.js login flow — action hash discovery, RSC parsing, session extraction |
| <img src="media/icon.svg" width="18" align="center"> [Web Chat](src/blackbox/webchat.py) | Browser-session chat at `app.blackbox.ai/api/chat` with SSE streaming |
| <img src="media/icon.svg" width="18" align="center"> [File Upload](src/blackbox/files.py) | Base64 file encoding, MIME detection, chat-with-file utility |
| <img src="media/icon.svg" width="18" align="center"> [Agent API](src/blackbox/agents.py) | Single-agent CRUD + multi-agent task orchestration |
| <img src="media/icon.svg" width="18" align="center"> [Models & Pricing](src/blackbox/models.py) | All data classes, constants, 24-entry MODEL_PRICING |

## Project

```
src/blackbox/
├── __init__.py    # Public API exports
├── __main__.py    # python -m blackbox
├── cli.py         # CLI entry point
├── client.py      # BlackBoxClient — unified interface
├── login.py       # NextAuth login (curl_cffi)
├── webchat.py     # app.blackbox.ai/api/chat (curl_cffi)
├── chat.py        # API chat completions (httpx)
├── files.py       # File upload utilities
├── auth.py        # Web authentication helpers
├── image.py       # Image generation
├── code.py        # Code generation
├── credits.py     # Credit balance
├── agents.py      # Single + Multi-agent APIs
└── models.py      # Data classes + pricing constants
```

## License

MIT &copy; [black-box-unoffcial-api](https://github.com/anomalyco/black-box-unoffcial-api)
