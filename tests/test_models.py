from blackbox.models import (
    Annotation,
    ChatCompletion,
    ChatMessage,
    Choice,
    CompletionTokensDetails,
    CreditInfo,
    FunctionDescription,
    ImageContentPart,
    ImageData,
    ImageGenerationResponse,
    ModelPricing,
    ReasoningConfig,
    ResponseMessage,
    SessionInfo,
    TextContentPart,
    Tool,
    ToolCall,
    ToolCallFunction,
    ToolChoice,
    ToolChoiceFunction,
    Usage,
    UrlCitation,
    VideoGenerationResponse,
    MODEL_PRICING,
)


class TestChatMessage:
    def test_simple_message(self):
        m = ChatMessage(role="user", content="hello")
        assert m.role == "user"
        assert m.content == "hello"

    def test_with_tool_calls(self):
        tc = ToolCall(id="call_1", function=ToolCallFunction(name="get_weather", arguments='{"loc":"NYC"}'))
        m = ChatMessage(role="assistant", content=None, tool_calls=[tc])
        assert m.role == "assistant"
        assert m.content is None
        assert len(m.tool_calls) == 1
        assert m.tool_calls[0].function.name == "get_weather"

    def test_with_content_parts(self):
        parts = [TextContentPart(text="desc"), ImageContentPart(image_url="https://img.url")]
        m = ChatMessage(role="user", content=parts)
        assert len(m.content) == 2
        assert m.content[0].text == "desc"
        assert m.content[1].image_url == "https://img.url"


class TestChatCompletion:
    def test_empty(self):
        c = ChatCompletion()
        assert c.id == ""
        assert c.content == ""

    def test_with_content(self):
        msg = ResponseMessage(content="Hello world")
        choice = Choice(message=msg)
        c = ChatCompletion(id="test-1", choices=[choice])
        assert c.content == "Hello world"

    def test_with_usage(self):
        usage = Usage(prompt_tokens=10, completion_tokens=20, total_tokens=30, cost=0.0015)
        c = ChatCompletion(id="test-2", usage=usage)
        assert c.usage.prompt_tokens == 10
        assert c.usage.cost == 0.0015

    def test_with_usage_details(self):
        details = CompletionTokensDetails(reasoning_tokens=100)
        usage = Usage(prompt_tokens=5, completion_tokens=150, total_tokens=155, completion_tokens_details=details)
        c = ChatCompletion(id="test-3", usage=usage)
        assert c.usage.completion_tokens_details.reasoning_tokens == 100


class TestAnnotations:
    def test_url_citation(self):
        cit = UrlCitation(url="https://example.com", title="Example")
        ann = Annotation(url_citation=cit)
        assert ann.type == "url_citation"
        assert ann.url_citation.url == "https://example.com"
        assert ann.url_citation.title == "Example"


class TestToolCalling:
    def test_tool_definition(self):
        t = Tool(
            type="function",
            function=FunctionDescription(
                name="search",
                description="Search tool",
                parameters={"type": "object", "properties": {"q": {"type": "string"}}},
            ),
        )
        assert t.type == "function"
        assert t.function.name == "search"

    def test_tool_choice(self):
        tc = ToolChoice(type="function", function=ToolChoiceFunction(name="search"))
        assert tc.function.name == "search"

    def test_tool_call_response(self):
        func = ToolCallFunction(name="get_temp", arguments='{"city":"Paris"}')
        tc = ToolCall(id="call_xyz", function=func)
        assert tc.function.arguments == '{"city":"Paris"}'


class TestReasoning:
    def test_reasoning_config(self):
        r = ReasoningConfig(effort="high", max_tokens=2000)
        assert r.effort == "high"
        assert r.max_tokens == 2000

    def test_reasoning_minimal(self):
        r = ReasoningConfig(effort="minimal")
        assert r.effort == "minimal"

    def test_reasoning_enabled(self):
        r = ReasoningConfig(enabled=True)
        assert r.enabled is True


class TestImageGeneration:
    def test_image_response(self):
        items = [ImageData(url="https://img.url", revised_prompt="a cat")]
        r = ImageGenerationResponse(created=12345, data=items)
        assert r.url == "https://img.url"
        assert r.data[0].revised_prompt == "a cat"

    def test_image_response_empty(self):
        r = ImageGenerationResponse()
        assert r.url == ""


class TestVideoGeneration:
    def test_video_response(self):
        r = VideoGenerationResponse(url="https://vid.url", model="veo-2", prompt="drone")
        assert r.url == "https://vid.url"
        assert r.model == "veo-2"


class TestCreditInfo:
    def test_credits(self):
        c = CreditInfo(total=1000, used=300, remaining=700)
        assert c.total == 1000
        assert c.used == 300
        assert c.remaining == 700


class TestSessionInfo:
    def test_session(self):
        s = SessionInfo(user_id="u1", email="a@b.com", name="Alice")
        assert s.email == "a@b.com"
        assert s.name == "Alice"


class TestModelPricing:
    def test_pricing_constant(self):
        assert "anthropic/claude-sonnet-4.5" in MODEL_PRICING
        p = MODEL_PRICING["anthropic/claude-sonnet-4.5"]
        assert isinstance(p, ModelPricing)
        assert p.input_cost_per_1k == 3.0
        assert p.output_cost_per_1k == 15.0

    def test_pricing_count(self):
        assert len(MODEL_PRICING) >= 20


class TestContentParts:
    def test_text_content_part(self):
        p = TextContentPart(text="hello")
        assert p.type == "text"
        assert p.text == "hello"

    def test_image_content_part(self):
        p = ImageContentPart(image_url="https://example.com/img.png")
        assert p.type == "image_url"
        assert p.image_url == "https://example.com/img.png"
