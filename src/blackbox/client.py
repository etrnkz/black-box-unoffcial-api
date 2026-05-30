from typing import Any, Optional

import httpx

from .agents import Agents
from .auth import Auth
from .chat import Chat
from .code import CodeGen
from .credits import Credits
from .image import ImageGen
from .models import (
    AgentConfig,
    AgentExecution,
    AgentInfo,
    AgentTaskConfig,
    ChatCompletion,
    ChatMessage,
    CodeGenerationResponse,
    CreditInfo,
    ImageGenerationResponse,
    ModelInfo,
    ModelPricing,
    MultiAgentTask,
    ProviderPreferences,
    ReasoningConfig,
    SessionInfo,
    Tool,
    ToolChoice,
    VideoGenerationResponse,
)


class BlackBoxClient:
    def __init__(
        self,
        api_key: Optional[str] = None,
        session_token: Optional[str] = None,
        timeout: float = 30.0,
        proxy: Optional[str] = None,
    ):
        self.api_key = api_key

        cookies: dict[str, str] = {}
        if session_token:
            cookies["__Secure-next-auth.session-token"] = session_token

        transport = None
        if proxy:
            transport = httpx.HTTPTransport(proxy=proxy)

        self._http = httpx.Client(
            cookies=cookies,
            timeout=timeout,
            transport=transport,
            headers={
                "user-agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/144.0.0.0 Safari/537.36"
                ),
                "accept": "*/*",
                "accept-language": "en-US,en;q=0.9",
            },
            follow_redirects=True,
        )

        self.auth = Auth(self._http)
        self.chat = Chat(self._http, api_key)
        self.code = CodeGen(self._http, api_key)
        self.image = ImageGen(self._http, api_key)
        self.credits = Credits(self._http)
        self.agents = Agents(self._http, api_key)

    def login(self, token: str, email: str) -> dict[str, Any]:
        return self.auth.login_with_token(token, email)

    def send_verification(self, email: str) -> dict[str, Any]:
        return self.auth.send_verification(email)

    def verify_email(self, email: str, code: str) -> dict[str, Any]:
        return self.auth.verify_email(email, code)

    def get_session(self) -> SessionInfo:
        data = self.auth.get_session()
        user = data.get("user", {})
        return SessionInfo(
            user_id=user.get("id"),
            email=user.get("email"),
            name=user.get("name"),
            expires=data.get("expires"),
            raw=data,
        )

    def get_credits(self) -> CreditInfo:
        return self.credits.get()

    def get_models(self) -> list[ModelInfo]:
        resp = self._http.get(
            "https://api.blackbox.ai/v1/models",
            headers={"authorization": f"Bearer {self.api_key}"} if self.api_key else {},
        )
        resp.raise_for_status()
        data = resp.json()
        return [
            ModelInfo(
                id=m.get("id", ""),
                name=m.get("id", ""),
                provider=m.get("provider"),
                pricing=ModelPricing(
                    input_cost_per_1k=m.get("pricing", {}).get("input", 0),
                    output_cost_per_1k=m.get("pricing", {}).get("output", 0),
                    context_length=m.get("context_length", 0),
                ) if m.get("pricing") else None,
                raw=m,
            )
            for m in data.get("data", [])
        ]

    # --- Chat Completions ---

    def chat_complete(
        self,
        messages: list[ChatMessage],
        model: Optional[str] = None,
        stream: bool = False,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        top_k: Optional[int] = None,
        seed: Optional[int] = None,
        stop: Optional[str | list[str]] = None,
        frequency_penalty: Optional[float] = None,
        presence_penalty: Optional[float] = None,
        repetition_penalty: Optional[float] = None,
        tools: Optional[list[Tool]] = None,
        tool_choice: Optional[ToolChoice | str] = None,
        reasoning: Optional[ReasoningConfig | dict[str, Any]] = None,
        provider: Optional[ProviderPreferences | dict[str, Any]] = None,
        response_format: Optional[dict[str, str]] = None,
        user: Optional[str] = None,
        **kwargs: Any,
    ) -> ChatCompletion:
        return self.chat.complete(
            messages=messages,
            model=model,
            stream=stream,
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
            top_k=top_k,
            seed=seed,
            stop=stop,
            frequency_penalty=frequency_penalty,
            presence_penalty=presence_penalty,
            repetition_penalty=repetition_penalty,
            tools=tools,
            tool_choice=tool_choice,
            reasoning=reasoning,
            provider=provider,
            response_format=response_format,
            user=user,
            **kwargs,
        )

    def chat_complete_stream(
        self,
        messages: list[ChatMessage],
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        **kwargs: Any,
    ):
        yield from self.chat.complete_stream(
            messages=messages,
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
            **kwargs,
        )

    # --- Web Search ---

    def search(
        self,
        query: str,
        system_prompt: Optional[str] = None,
        stream: bool = False,
    ) -> ChatCompletion:
        return self.chat.search(
            query=query,
            system_prompt=system_prompt,
            stream=stream,
        )

    # --- Image Generation ---

    def generate_image(
        self,
        prompt: str,
        model: Optional[str] = None,
        n: int = 1,
        size: Optional[str] = None,
        quality: Optional[str] = None,
        style: Optional[str] = None,
        response_format: Optional[str] = None,
    ) -> ImageGenerationResponse:
        return self.image.generate(
            prompt=prompt,
            model=model,
            n=n,
            size=size,
            quality=quality,
            style=style,
            response_format=response_format,
        )

    def generate_image_chat(
        self,
        prompt: str,
        model: str = "flux-pro",
        system_prompt: Optional[str] = None,
    ) -> ChatCompletion:
        return self.chat.generate_image(
            prompt=prompt,
            model=model,
            system_prompt=system_prompt,
        )

    # --- Video Generation ---

    def generate_video(
        self,
        prompt: str,
        model: str = "veo-2",
    ) -> VideoGenerationResponse:
        result = self.chat.generate_video(prompt=prompt, model=model)
        url = result.content if result.content else ""
        return VideoGenerationResponse(
            url=url,
            model=model,
            prompt=prompt,
        )

    # --- Code Generation ---

    def generate_code(
        self,
        prompt: str,
        language: Optional[str] = None,
        context: Optional[str] = None,
    ) -> CodeGenerationResponse:
        return self.code.generate(
            prompt=prompt,
            language=language,
            context=context,
        )

    # --- Single Agent API ---

    def create_agent(self, config: AgentConfig) -> AgentInfo:
        return self.agents.create(config)

    def list_agents(self) -> list[AgentInfo]:
        return self.agents.list()

    def get_agent(self, agent_id: str) -> AgentInfo:
        return self.agents.get(agent_id)

    def delete_agent(self, agent_id: str) -> dict[str, Any]:
        return self.agents.delete(agent_id)

    def execute_agent(self, agent_id: str, prompt: str) -> AgentExecution:
        return self.agents.execute(agent_id, prompt)

    def run_agent(
        self,
        prompt: str,
        model: Optional[str] = None,
        system_prompt: Optional[str] = None,
    ) -> AgentExecution:
        return self.agents.run(prompt, model=model, system_prompt=system_prompt)

    # --- Multi-Agent Task API ---

    def create_multi_agent_task(
        self,
        prompt: str,
        agents: list[AgentTaskConfig],
        repo_url: Optional[str] = None,
        selected_branch: Optional[str] = None,
    ) -> MultiAgentTask:
        return self.agents.create_task(
            prompt=prompt,
            agents=agents,
            repo_url=repo_url,
            selected_branch=selected_branch,
        )

    def get_multi_agent_task(self, task_id: str) -> MultiAgentTask:
        return self.agents.get_task(task_id)

    def close(self):
        self._http.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
