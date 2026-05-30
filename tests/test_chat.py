import httpx
import pytest
from blackbox.chat import Chat
from blackbox.models import (
    ChatMessage,
    FunctionDescription,
    ReasoningConfig,
    Tool,
    ToolCall,
    ToolCallFunction,
    ToolChoice,
    ToolChoiceFunction,
)


def _make_chat(api_key: str = "sk-test") -> Chat:
    return Chat(httpx.Client(), api_key)


class TestMessageSerialization:
    def test_simple_message(self):
        chat = _make_chat()
        result = chat._serialize_messages([ChatMessage(role="user", content="hello")])
        assert result == [{"role": "user", "content": "hello"}]

    def test_with_name(self):
        chat = _make_chat()
        result = chat._serialize_messages([ChatMessage(role="user", content="hi", name="Alice")])
        assert result[0]["name"] == "Alice"

    def test_with_tool_calls(self):
        chat = _make_chat()
        tc = ToolCall(id="call_1", function=ToolCallFunction(name="get_weather", arguments='{"loc":"NYC"}'))
        m = ChatMessage(role="assistant", content=None, tool_calls=[tc])
        result = chat._serialize_messages([m])
        assert result[0]["tool_calls"][0]["id"] == "call_1"
        assert result[0]["tool_calls"][0]["function"]["arguments"] == '{"loc":"NYC"}'

    def test_with_tool_call_id(self):
        chat = _make_chat()
        m = ChatMessage(role="tool", content='{"temp":72}', tool_call_id="call_1")
        result = chat._serialize_messages([m])
        assert result[0]["tool_call_id"] == "call_1"
        assert result[0]["content"] == '{"temp":72}'


class TestBuildBody:
    def test_minimal(self):
        chat = _make_chat()
        body = chat._build_body(messages=[ChatMessage(role="user", content="hi")])
        assert body["messages"] == [{"role": "user", "content": "hi"}]
        assert "stream" not in body

    def test_all_params(self):
        chat = _make_chat()
        body = chat._build_body(
            messages=[ChatMessage(role="user", content="hi")],
            model="gpt-4",
            stream=True,
            max_tokens=100,
            temperature=0.5,
            top_p=0.9,
            top_k=40,
            seed=42,
            stop=["stop"],
            frequency_penalty=0.1,
            presence_penalty=0.2,
            repetition_penalty=1.1,
            min_p=0.05,
            top_a=0.5,
            top_logprobs=5,
            logit_bias={100: -1.0},
            response_format={"type": "json_object"},
            route="fallback",
            user="user-123",
            structured_outputs=True,
            verbosity="high",
        )
        assert body["model"] == "gpt-4"
        assert body["stream"] is True
        assert body["max_tokens"] == 100
        assert body["temperature"] == 0.5
        assert body["top_p"] == 0.9
        assert body["top_k"] == 40
        assert body["seed"] == 42
        assert body["stop"] == ["stop"]
        assert body["frequency_penalty"] == 0.1
        assert body["presence_penalty"] == 0.2
        assert body["repetition_penalty"] == 1.1
        assert body["min_p"] == 0.05
        assert body["top_a"] == 0.5
        assert body["top_logprobs"] == 5
        assert body["logit_bias"] == {100: -1.0}
        assert body["response_format"] == {"type": "json_object"}
        assert body["route"] == "fallback"
        assert body["user"] == "user-123"
        assert body["structured_outputs"] is True
        assert body["verbosity"] == "high"

    def test_tools_in_body(self):
        chat = _make_chat()
        tools = [
            Tool(
                type="function",
                function=FunctionDescription(
                    name="search",
                    description="Search tool",
                    parameters={"type": "object", "properties": {"q": {"type": "string"}}},
                ),
            )
        ]
        body = chat._build_body(messages=[ChatMessage(role="user", content="hi")], tools=tools)
        assert body["tools"][0]["function"]["name"] == "search"

    def test_tool_choice_string(self):
        chat = _make_chat()
        body = chat._build_body(messages=[ChatMessage(role="user", content="hi")], tool_choice="auto")
        assert body["tool_choice"] == "auto"

    def test_tool_choice_object(self):
        chat = _make_chat()
        tc = ToolChoice(type="function", function=ToolChoiceFunction(name="search"))
        body = chat._build_body(messages=[ChatMessage(role="user", content="hi")], tool_choice=tc)
        assert body["tool_choice"]["function"]["name"] == "search"

    def test_reasoning_config(self):
        chat = _make_chat()
        r = ReasoningConfig(effort="high", max_tokens=2000, exclude=True)
        body = chat._build_body(messages=[ChatMessage(role="user", content="hi")], reasoning=r)
        assert body["reasoning"]["effort"] == "high"
        assert body["reasoning"]["max_tokens"] == 2000
        assert body["reasoning"]["exclude"] is True

    def test_reasoning_dict(self):
        chat = _make_chat()
        body = chat._build_body(messages=[ChatMessage(role="user", content="hi")], reasoning={"effort": "low"})
        assert body["reasoning"]["effort"] == "low"

    def test_prompt_field(self):
        chat = _make_chat()
        body = chat._build_body(prompt="say hello")
        assert body["prompt"] == "say hello"

    def test_provider_preferences(self):
        chat = _make_chat()
        from blackbox.models import ProviderPreferences
        p = ProviderPreferences(order=["openai"], allow_fallbacks=False)
        body = chat._build_body(messages=[ChatMessage(role="user", content="hi")], provider=p)
        assert body["provider"]["order"] == ["openai"]
        assert body["provider"]["allow_fallbacks"] is False

    def test_prediction(self):
        chat = _make_chat()
        body = chat._build_body(messages=[ChatMessage(role="user", content="hi")], prediction={"type": "content", "content": "expected output"})
        assert body["prediction"]["type"] == "content"


SAMPLE_RESPONSE = {
    "id": "gen-123",
    "created": 1700000000,
    "model": "gpt-4",
    "object": "chat.completion",
    "choices": [
        {
            "index": 0,
            "finish_reason": "stop",
            "message": {
                "role": "assistant",
                "content": "Hello back",
            },
        }
    ],
    "usage": {
        "prompt_tokens": 10,
        "completion_tokens": 20,
        "total_tokens": 30,
        "cost": 0.0005,
    },
}

STREAM_CHUNKS = [
    'data: {"id":"x","object":"chat.completion.chunk","choices":[{"index":0,"delta":{"content":"Hello"}}]}',
    'data: {"id":"x","object":"chat.completion.chunk","choices":[{"index":0,"delta":{"content":" world"}}]}',
    "data: [DONE]",
]


class TestParseResponse:
    def test_basic_parse(self):
        chat = _make_chat()
        result = chat._parse_response(SAMPLE_RESPONSE)
        assert result.id == "gen-123"
        assert result.content == "Hello back"
        assert result.usage.prompt_tokens == 10
        assert result.usage.cost == 0.0005

    def test_with_tool_calls_in_response(self):
        data = {
            "id": "gen-456",
            "created": 1700000001,
            "model": "gpt-4",
            "choices": [
                {
                    "index": 0,
                    "finish_reason": "tool_calls",
                    "message": {
                        "role": "assistant",
                        "content": None,
                        "tool_calls": [
                            {
                                "id": "call_abc",
                                "type": "function",
                                "function": {"name": "get_weather", "arguments": '{"loc":"Paris"}'},
                            }
                        ],
                    },
                }
            ],
        }
        chat = _make_chat()
        result = chat._parse_response(data)
        tc = result.choices[0].message.tool_calls[0]
        assert tc.id == "call_abc"
        assert tc.function.name == "get_weather"
        assert tc.function.arguments == '{"loc":"Paris"}'

    def test_with_annotations(self):
        data = {
            "id": "gen-789",
            "created": 1700000002,
            "model": "blackbox-search",
            "choices": [
                {
                    "index": 0,
                    "finish_reason": "stop",
                    "message": {
                        "role": "assistant",
                        "content": "Some answer",
                        "annotations": [
                            {
                                "type": "url_citation",
                                "url_citation": {
                                    "url": "https://example.com",
                                    "title": "Example",
                                    "content": "snippet",
                                },
                            }
                        ],
                    },
                }
            ],
        }
        chat = _make_chat()
        result = chat._parse_response(data)
        ann = result.choices[0].message.annotations[0]
        assert ann.type == "url_citation"
        assert ann.url_citation.url == "https://example.com"
        assert ann.url_citation.title == "Example"

    def test_with_delta(self):
        data = {
            "id": "gen-stream",
            "object": "chat.completion.chunk",
            "choices": [{"index": 0, "finish_reason": None, "delta": {"content": "Hello", "role": "assistant"}}],
        }
        chat = _make_chat()
        result = chat._parse_response(data)
        assert result.choices[0].delta.content == "Hello"
        assert result.choices[0].message is None

    def test_with_error(self):
        data = {
            "id": "gen-err",
            "choices": [
                {
                    "index": 0,
                    "finish_reason": "error",
                    "message": {"role": "assistant", "content": None},
                    "error": {"code": 402, "message": "Insufficient credits"},
                }
            ],
        }
        chat = _make_chat()
        result = chat._parse_response(data)
        assert result.choices[0].error.code == 402
        assert result.choices[0].error.message == "Insufficient credits"

    def test_response_with_provider(self):
        data = {**SAMPLE_RESPONSE, "provider": "OpenAI"}
        chat = _make_chat()
        result = chat._parse_response(data)
        assert result.provider == "OpenAI"

    def test_with_reasoning_tokens(self):
        data = {
            **SAMPLE_RESPONSE,
            "usage": {
                "prompt_tokens": 10,
                "completion_tokens": 200,
                "total_tokens": 210,
                "completion_tokens_details": {"reasoning_tokens": 150},
            },
        }
        chat = _make_chat()
        result = chat._parse_response(data)
        assert result.usage.completion_tokens_details.reasoning_tokens == 150
