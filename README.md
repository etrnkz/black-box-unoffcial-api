# BlackBox Unofficial API

Unofficial Python client for [blackbox.ai](https://www.blackbox.ai).

Reflects the official API docs at [docs.blackbox.ai](https://docs.blackbox.ai).

## Features

- **Chat Completions** — full OpenAI-compatible API with all documented parameters
- **Web Search** — via `blackbox-search` model with source citations
- **Image Generation** — via `/v1/images/generations` or chat completions (flux-pro, ideogram-v3, etc.)
- **Video Generation** — via chat completions (veo-2, veo-3, ray-2, etc.)
- **Code Generation** — routed through chat completions with system prompt
- **Streaming** — real-time response chunks
- **Tool/Function Calling** — with reasoning and interleaved thinking
- **Web Authentication** — NextAuth.js login flow (csrf, token, verify)
- **Credit Balance** — check remaining credits
- **Single Agents** — CRUD and execution at `api.blackbox.ai/v1/agents/*`
- **Multi-Agent Tasks** — parallel agent execution at `cloud.blackbox.ai/api/tasks`
- **Model List** — available models with pricing data

## Install

```bash
pip install httpx
pip install -e .
```

## Library Usage

```python
from blackbox import BlackBoxClient, ChatMessage, Tool, ReasoningConfig

# API key auth (for chat/search/image/video/code/models)
client = BlackBoxClient(api_key="sk-...")

# --- Chat Completions (all documented params) ---
result = client.chat_complete(
    messages=[ChatMessage(role="user", content="Hello!")],
    model="anthropic/claude-sonnet-4.5",
    temperature=0.7,
    max_tokens=256,
    reasoning=ReasoningConfig(effort="medium"),
)
print(result.content)
print(f"Tokens: {result.usage.prompt_tokens}p / {result.usage.completion_tokens}c")

# --- Web Search ---
result = client.search("latest AI news")
print(result.content)
if result.choices[0].message.annotations:
    for ann in result.choices[0].message.annotations:
        print(f"  Source: {ann.url_citation.title} -> {ann.url_citation.url}")

# --- Image Generation ---
img = client.generate_image("a cat in space", model="flux-pro")
print(img.data[0].url)

# --- Video Generation ---
video = client.generate_video("drone over mountains", model="veo-2")
print(video.url)

# --- Tool Calling ---
tools = [
    Tool(type="function", function={
        "name": "get_weather",
        "description": "Get weather for a city",
        "parameters": {
            "type": "object",
            "properties": {
                "location": {"type": "string"}
            },
            "required": ["location"]
        }
    })
]
result = client.chat_complete(
    messages=[ChatMessage(role="user", content="What's the weather in Paris?")],
    model="google/gemini-2.0-flash-001",
    tools=tools,
)
if result.choices[0].message.tool_calls:
    print(f"Tool call: {result.choices[0].message.tool_calls[0].function.name}")

# --- Multi-Agent Task ---
from blackbox import AgentTaskConfig
task = client.create_multi_agent_task(
    prompt="Add README in Spanish",
    agents=[
        AgentTaskConfig(agent="claude", model="blackboxai/anthropic/claude-sonnet-4.5"),
        AgentTaskConfig(agent="blackbox", model="blackboxai/blackbox-pro"),
    ],
    repo_url="https://github.com/user/repo.git",
)

# --- Web auth ---
client = BlackBoxClient(session_token="...")
session = client.get_session()
print(session.email)
credits = client.get_credits()
print(f"Remaining: {credits.remaining}")
```

## CLI

```bash
# API key commands
python -m blackbox --api-key "sk-..." models
python -m blackbox --api-key "sk-..." chat "Hello!" --model anthropic/claude-sonnet-4.5
python -m blackbox --api-key "sk-..." search "latest AI news"
python -m blackbox --api-key "sk-..." image "a cat" --model flux-pro
python -m blackbox --api-key "sk-..." video "drone shot" --model veo-2
python -m blackbox --api-key "sk-..." code "quicksort in python"

# Web auth commands
python -m blackbox auth csrf
python -m blackbox auth login --token TOKEN --email user@example.com
python -m blackbox auth session
python -m blackbox credits

# Multi-agent task
python -m blackbox --api-key "bb_..." agent task \
  --prompt "Add README" \
  --agents "claude:blackboxai/anthropic/claude-sonnet-4.5,blackbox:blackboxai/blackbox-pro"
```

## API Endpoints

| Endpoint | Method | Domain |
|---|---|---|
| `/chat/completions` | POST | api.blackbox.ai |
| `/v1/chat/completions` | POST | api.blackbox.ai |
| `/v1/models` | GET | api.blackbox.ai |
| `/v1/images/generations` | POST | api.blackbox.ai |
| `/v1/agents/*` | CRUD | api.blackbox.ai |
| `/api/tasks` | POST/GET | cloud.blackbox.ai |
| `/api/auth/session` | GET | app.blackbox.ai |
| `/api/auth/send-verification` | POST | app.blackbox.ai |
| `/api/auth/verify-email` | POST | app.blackbox.ai |
| `/api/auth/csrf` | GET | builder.blackbox.ai |
| `/api/auth/callback/auto-login-token` | POST | builder.blackbox.ai |
| `/api/credits/get` | GET | builder.blackbox.ai |

## Project Structure

```
src/blackbox/
├── __init__.py   # Public API exports
├── __main__.py   # python -m blackbox
├── cli.py        # CLI entry point
├── client.py     # BlackBoxClient
├── auth.py       # Web authentication
├── chat.py       # Chat completions (full OpenAI-compat)
├── code.py       # Code generation via chat
├── image.py      # Image generation (OpenAI-compat)
├── credits.py    # Credit balance
├── agents.py     # Single + Multi-agent APIs
└── models.py     # All data classes + pricing constants
```

## Official Docs Reference

Implementation based on [docs.blackbox.ai](https://docs.blackbox.ai):
- [Introduction](https://docs.blackbox.ai/api-reference/introduction)
- [Authentication](https://docs.blackbox.ai/api-reference/authentication)
- [Requests](https://docs.blackbox.ai/api-reference/requests)
- [Responses](https://docs.blackbox.ai/api-reference/responses)
- [Parameters](https://docs.blackbox.ai/api-reference/parameters)
- [Tool Calling](https://docs.blackbox.ai/api-reference/tool-calling)
- [Web Search](https://docs.blackbox.ai/api-reference/web-search)
- [Multi-Agent Task](https://docs.blackbox.ai/api-reference/multi-agent-task)
- [Models & Pricing](https://docs.blackbox.ai/api-reference/models/chat-models)
- [Errors](https://docs.blackbox.ai/api-reference/errors)
