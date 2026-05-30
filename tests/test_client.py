import httpx
import pytest
from blackbox.client import BlackBoxClient
from blackbox.models import (
    AgentTaskConfig,
    ChatMessage,
    FunctionDescription,
    ReasoningConfig,
    Tool,
    ToolChoice,
    ToolChoiceFunction,
)


class TestClientInit:
    def test_default_init(self):
        client = BlackBoxClient(api_key="sk-test")
        assert client.api_key == "sk-test"
        client.close()

    def test_with_cookies(self):
        client = BlackBoxClient(cookie_header="test=cookie")
        assert client._cookie_header == "test=cookie"
        client.close()

    def test_with_proxy(self):
        client = BlackBoxClient(api_key="sk-test", proxy="http://localhost:8080")
        transport = client._http._transport
        proxy_url = transport._pool._proxy_url
        assert proxy_url.host == b"localhost"
        assert proxy_url.port == 8080
        client.close()


HTTP_ERRORS = (httpx.HTTPStatusError, httpx.ConnectError, httpx.RemoteProtocolError, httpx.TimeoutException)


class TestClientMethods:
    def test_chat_complete_signature(self):
        client = BlackBoxClient(api_key="sk-test")
        with pytest.raises(HTTP_ERRORS):
            client.chat_complete(
                messages=[ChatMessage(role="user", content="hi")],
                model="anthropic/claude-sonnet-4.5",
                temperature=0.7,
                max_tokens=256,
                top_p=0.9,
                seed=42,
                frequency_penalty=0.1,
                presence_penalty=0.2,
                repetition_penalty=1.1,
                reasoning=ReasoningConfig(effort="medium"),
                user="user-123",
            )
        client.close()

    def test_chat_with_tools(self):
        client = BlackBoxClient(api_key="sk-test")
        tools = [
            Tool(
                type="function",
                function=FunctionDescription(
                    name="search",
                    description="s",
                    parameters={"type": "object"},
                ),
            )
        ]
        with pytest.raises(HTTP_ERRORS):
            client.chat_complete(
                messages=[ChatMessage(role="user", content="hi")],
                model="gpt-4",
                tools=tools,
            )
        client.close()

    def test_with_tool_choice(self):
        client = BlackBoxClient(api_key="sk-test")
        tools = [
            Tool(
                type="function",
                function=FunctionDescription(name="search", parameters={"type": "object"}),
            )
        ]
        tc = ToolChoice(type="function", function=ToolChoiceFunction(name="search"))
        with pytest.raises(HTTP_ERRORS):
            client.chat_complete(
                messages=[ChatMessage(role="user", content="hi")],
                model="gpt-4",
                tools=tools,
                tool_choice=tc,
            )
        client.close()

    def test_search_signature(self):
        client = BlackBoxClient(api_key="sk-test")
        with pytest.raises(HTTP_ERRORS):
            client.search("test query")
        client.close()

    def test_generate_image_signature(self):
        client = BlackBoxClient(api_key="sk-test")
        with pytest.raises(HTTP_ERRORS):
            client.generate_image("a cat")
        client.close()

    def test_generate_video_signature(self):
        client = BlackBoxClient(api_key="sk-test")
        with pytest.raises(HTTP_ERRORS):
            client.generate_video("drone shot", model="veo-2")
        client.close()

    def test_generate_code_signature(self):
        client = BlackBoxClient(api_key="sk-test")
        with pytest.raises(HTTP_ERRORS):
            client.generate_code("fib in python", language="python")
        client.close()

    def test_multi_agent_task_signature(self):
        client = BlackBoxClient(api_key="sk-test")
        agents = [
            AgentTaskConfig(agent="claude", model="blackboxai/anthropic/claude-sonnet-4.5"),
            AgentTaskConfig(agent="blackbox", model="blackboxai/blackbox-pro"),
        ]
        with pytest.raises(HTTP_ERRORS):
            client.create_multi_agent_task(prompt="Add README", agents=agents)
        client.close()

    def test_get_credits_signature(self):
        client = BlackBoxClient(api_key="sk-test")
        with pytest.raises(HTTP_ERRORS):
            client.get_credits()
        client.close()

    def test_generate_image_chat(self):
        client = BlackBoxClient(api_key="sk-test")
        with pytest.raises(HTTP_ERRORS):
            client.generate_image_chat("a cat", model="flux-pro")
        client.close()
