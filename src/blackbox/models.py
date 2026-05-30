from dataclasses import dataclass, field
from typing import Any, Optional


# --- Content Parts ---

@dataclass
class ImageContentPart:
    type: str = "image_url"
    image_url: str = ""
    detail: Optional[str] = None


@dataclass
class TextContentPart:
    type: str = "text"
    text: str = ""


ContentPart = TextContentPart | ImageContentPart


# --- Messages ---

@dataclass
class ToolCallFunction:
    name: str
    arguments: str


@dataclass
class ToolCall:
    id: str
    type: str = "function"
    function: Optional[ToolCallFunction] = None


@dataclass
class ChatMessage:
    role: str
    content: str | list[ContentPart] | None = None
    name: Optional[str] = None
    tool_calls: Optional[list[ToolCall]] = None
    tool_call_id: Optional[str] = None


# --- Tool Calling ---

@dataclass
class FunctionDescription:
    name: str
    description: Optional[str] = None
    parameters: Optional[dict[str, Any]] = None


@dataclass
class Tool:
    type: str = "function"
    function: Optional[FunctionDescription] = None


@dataclass
class ToolChoiceFunction:
    name: str


@dataclass
class ToolChoice:
    type: str = "function"
    function: Optional[ToolChoiceFunction] = None


# --- Reasoning ---

@dataclass
class ReasoningConfig:
    effort: Optional[str] = None
    max_tokens: Optional[int] = None
    exclude: Optional[bool] = None
    enabled: Optional[bool] = None


# --- Provider Preferences ---

@dataclass
class ProviderPreferences:
    order: Optional[list[str]] = None
    allow_fallbacks: Optional[bool] = None
    require: Optional[str] = None
    skip: Optional[str] = None


# --- Response Types ---

@dataclass
class UrlCitation:
    url: str
    title: Optional[str] = None
    content: Optional[str] = None
    start_index: Optional[int] = None
    end_index: Optional[int] = None


@dataclass
class Annotation:
    type: str = "url_citation"
    url_citation: Optional[UrlCitation] = None


@dataclass
class CompletionTokensDetails:
    accepted_prediction_tokens: Optional[int] = None
    audio_tokens: Optional[int] = None
    reasoning_tokens: Optional[int] = None
    rejected_prediction_tokens: Optional[int] = None
    image_tokens: Optional[int] = None


@dataclass
class PromptTokensDetails:
    audio_tokens: Optional[int] = None
    cached_tokens: Optional[int] = None


@dataclass
class CostDetails:
    upstream_inference_cost: Optional[float] = None
    upstream_inference_prompt_cost: Optional[float] = None
    upstream_inference_completions_cost: Optional[float] = None


@dataclass
class Usage:
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    completion_tokens_details: Optional[CompletionTokensDetails] = None
    prompt_tokens_details: Optional[PromptTokensDetails] = None
    cost: Optional[float] = None
    is_byok: Optional[bool] = None
    cost_details: Optional[CostDetails] = None


@dataclass
class ErrorResponse:
    code: int = 0
    message: str = ""
    metadata: Optional[dict[str, Any]] = None


@dataclass
class ResponseMessage:
    content: str | None = None
    role: str = "assistant"
    tool_calls: Optional[list[ToolCall]] = None
    annotations: Optional[list[Annotation]] = None
    reasoning_details: Optional[Any] = None


@dataclass
class Choice:
    finish_reason: Optional[str] = None
    native_finish_reason: Optional[str] = None
    index: int = 0
    message: Optional[ResponseMessage] = None
    delta: Optional[ResponseMessage] = None
    text: Optional[str] = None
    error: Optional[ErrorResponse] = None


@dataclass
class ChatCompletion:
    id: str = ""
    created: int = 0
    model: str = ""
    object: str = "chat.completion"
    choices: list[Choice] = field(default_factory=list)
    system_fingerprint: Optional[str] = None
    usage: Optional[Usage] = None
    provider: Optional[str] = None

    @property
    def content(self) -> str:
        if self.choices:
            msg = self.choices[0].message
            if msg and msg.content:
                return msg.content
        return ""


# --- Image Generation ---

@dataclass
class ImageData:
    url: str = ""
    revised_prompt: Optional[str] = None
    b64_json: Optional[str] = None


@dataclass
class ImageGenerationResponse:
    created: int = 0
    data: list[ImageData] = field(default_factory=list)

    @property
    def url(self) -> str:
        if self.data:
            return self.data[0].url
        return ""


# --- Code Generation ---

@dataclass
class CodeGenerationResponse:
    code: str = ""
    language: str = ""
    explanation: Optional[str] = None


# --- Video Generation ---

@dataclass
class VideoGenerationResponse:
    url: str = ""
    model: str = ""
    prompt: str = ""


# --- Web Search ---

@dataclass
class SearchResult:
    content: str = ""
    annotations: list[Annotation] = field(default_factory=list)
    url: Optional[str] = None


# --- Credits ---

@dataclass
class CreditInfo:
    total: int = 0
    used: int = 0
    remaining: int = 0


# --- Session ---

@dataclass
class SessionInfo:
    user_id: Optional[str] = None
    email: Optional[str] = None
    name: Optional[str] = None
    expires: Optional[str] = None
    raw: dict[str, Any] = field(default_factory=dict)


# --- Models ---

@dataclass
class ModelPricing:
    input_cost_per_1k: float = 0.0
    output_cost_per_1k: float = 0.0
    context_length: int = 0


@dataclass
class ModelInfo:
    id: str
    name: str = ""
    provider: Optional[str] = None
    pricing: Optional[ModelPricing] = None
    raw: dict[str, Any] = field(default_factory=dict)


# --- Agents ---

@dataclass
class AgentConfig:
    name: str
    description: Optional[str] = None
    model: Optional[str] = None
    system_prompt: Optional[str] = None
    tools: Optional[list[dict[str, Any]]] = None


@dataclass
class AgentInfo:
    id: str
    name: str
    description: Optional[str] = None
    model: Optional[str] = None
    status: Optional[str] = None
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentExecution:
    id: str = ""
    agent_id: str = ""
    status: str = "pending"
    input: str = ""
    output: Optional[str] = None
    error: Optional[str] = None
    commits: Optional[list[dict[str, Any]]] = None
    files_changed: Optional[int] = None


# --- Multi-Agent Task ---

@dataclass
class AgentTaskConfig:
    agent: str
    model: str


@dataclass
class MultiAgentTask:
    id: str = ""
    prompt: str = ""
    repo_url: Optional[str] = None
    selected_branch: Optional[str] = None
    status: str = "pending"
    agent_executions: Optional[list[AgentExecution]] = None
    selected_agents: list[AgentTaskConfig] = field(default_factory=list)
    task_url: Optional[str] = None
    raw: dict[str, Any] = field(default_factory=dict)


# --- Constants: Official Model Pricing ---

MODEL_PRICING: dict[str, ModelPricing] = {
    "anthropic/claude-opus-4.7": ModelPricing(5.00, 25.00, 1000000),
    "anthropic/claude-opus-4.6": ModelPricing(5.00, 25.00, 1000000),
    "anthropic/claude-sonnet-4.6": ModelPricing(3.00, 15.00, 1000000),
    "anthropic/claude-sonnet-4.5": ModelPricing(3.00, 15.00, 200000),
    "anthropic/claude-opus-4.5": ModelPricing(5.00, 25.00, 200000),
    "openai/gpt-5.5": ModelPricing(5.00, 20.00, 1050000),
    "openai/gpt-5.4": ModelPricing(2.50, 15.00, 1050000),
    "openai/gpt-5.4-pro": ModelPricing(30.00, 180.00, 1050000),
    "openai/gpt-5.4-mini": ModelPricing(0.75, 4.50, 400000),
    "openai/gpt-5.4-nano": ModelPricing(0.20, 1.25, 400000),
    "openai/gpt-5.3-codex": ModelPricing(1.75, 14.00, 400000),
    "openai/gpt-5.2-codex": ModelPricing(1.75, 14.00, 400000),
    "google/gemini-2.5-flash": ModelPricing(0.30, 2.50, 1048576),
    "google/gemini-2.5-pro": ModelPricing(1.25, 10.00, 1048576),
    "deepseek/deepseek-chat": ModelPricing(0.38, 0.89, 163840),
    "deepseek/deepseek-r1": ModelPricing(0.45, 2.15, 128000),
    "blackbox-search": ModelPricing(0.20, 0.50, 1048576),
    "meta-llama/llama-4-maverick": ModelPricing(0.15, 0.60, 1048576),
    "meta-llama/llama-4-scout": ModelPricing(0.08, 0.30, 1048576),
    "minimax/minimax-m2.7": ModelPricing(0.30, 1.20, 204800),
    "minimax/minimax-m2.5": ModelPricing(0.15, 1.15, 204800),
    "cohere/command-a": ModelPricing(2.50, 10.00, 256000),
    "mistralai/mistral-large": ModelPricing(2.00, 6.00, 128000),
    "qwen/qwq-32b": ModelPricing(0.07, 0.15, 131072),
}
