from typing import Any, Optional

import httpx

from .models import (
    Annotation,
    ChatCompletion,
    ChatMessage,
    Choice,
    CompletionTokensDetails,
    CostDetails,
    ErrorResponse,
    PromptTokensDetails,
    ProviderPreferences,
    ReasoningConfig,
    ResponseMessage,
    Tool,
    ToolCall,
    ToolCallFunction,
    ToolChoice,
    Usage,
    UrlCitation,
)


class Chat:
    BASE_URL = "https://api.blackbox.ai"

    def __init__(self, client: httpx.Client, api_key: Optional[str] = None):
        self._client = client
        self._api_key = api_key

    def _headers(self) -> dict[str, str]:
        h = {"content-type": "application/json"}
        if self._api_key:
            h["authorization"] = f"Bearer {self._api_key}"
        return h

    def _serialize_messages(self, messages: list[ChatMessage]) -> list[dict[str, Any]]:
        result = []
        for m in messages:
            d: dict[str, Any] = {"role": m.role}
            if m.content is not None:
                if isinstance(m.content, list):
                    d["content"] = [
                        (
                            {"type": "text", "text": p.text}
                            if hasattr(p, "text")
                            else {
                                "type": "image_url",
                                "image_url": {"url": p.image_url},
                            }
                        )
                        for p in m.content
                    ]
                else:
                    d["content"] = m.content
            if m.name:
                d["name"] = m.name
            if m.tool_calls:
                d["tool_calls"] = [
                    {
                        "id": tc.id,
                        "type": tc.type,
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments,
                        },
                    }
                    for tc in m.tool_calls
                    if tc.function
                ]
            if m.tool_call_id:
                d["tool_call_id"] = m.tool_call_id
            result.append(d)
        return result

    def _parse_choice_message(self, msg: dict[str, Any]) -> ResponseMessage:
        tool_calls = None
        raw_tc = msg.get("tool_calls")
        if raw_tc:
            tool_calls = [
                ToolCall(
                    id=tc.get("id", ""),
                    type=tc.get("type", "function"),
                    function=ToolCallFunction(
                        name=tc.get("function", {}).get("name", ""),
                        arguments=tc.get("function", {}).get("arguments", ""),
                    ),
                )
                for tc in raw_tc
            ]

        annotations = None
        raw_ann = msg.get("annotations")
        if raw_ann:
            annotations = [
                Annotation(
                    type=a.get("type", "url_citation"),
                    url_citation=UrlCitation(**a.get("url_citation", {}))
                    if a.get("url_citation")
                    else None,
                )
                for a in raw_ann
            ]

        return ResponseMessage(
            content=msg.get("content"),
            role=msg.get("role", "assistant"),
            tool_calls=tool_calls,
            annotations=annotations,
            reasoning_details=msg.get("reasoning_details"),
        )

    def _parse_usage(self, u: Optional[dict[str, Any]]) -> Optional[Usage]:
        if not u:
            return None
        details = u.get("completion_tokens_details")
        return Usage(
            prompt_tokens=u.get("prompt_tokens", 0),
            completion_tokens=u.get("completion_tokens", 0),
            total_tokens=u.get("total_tokens", 0),
            completion_tokens_details=CompletionTokensDetails(**details) if details else None,
            prompt_tokens_details=PromptTokensDetails(**u.get("prompt_tokens_details", {})) if u.get("prompt_tokens_details") else None,
            cost=u.get("cost"),
            is_byok=u.get("is_byok"),
            cost_details=CostDetails(**u.get("cost_details", {})) if u.get("cost_details") else None,
        )

    def complete(
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
        min_p: Optional[float] = None,
        top_a: Optional[float] = None,
        top_logprobs: Optional[int] = None,
        logit_bias: Optional[dict[int, float]] = None,
        response_format: Optional[dict[str, str]] = None,
        tools: Optional[list[Tool]] = None,
        tool_choice: Optional[ToolChoice | str] = None,
        parallel_tool_calls: Optional[bool] = None,
        reasoning: Optional[ReasoningConfig | dict[str, Any]] = None,
        provider: Optional[ProviderPreferences | dict[str, Any]] = None,
        route: Optional[str] = None,
        transforms: Optional[list[str]] = None,
        models: Optional[list[str]] = None,
        user: Optional[str] = None,
        structured_outputs: Optional[bool] = None,
        verbosity: Optional[str] = None,
        prediction: Optional[dict[str, str]] = None,
        prompt: Optional[str] = None,
    ) -> ChatCompletion:
        body = self._build_body(
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
            min_p=min_p,
            top_a=top_a,
            top_logprobs=top_logprobs,
            logit_bias=logit_bias,
            response_format=response_format,
            tools=tools,
            tool_choice=tool_choice,
            parallel_tool_calls=parallel_tool_calls,
            reasoning=reasoning,
            provider=provider,
            route=route,
            transforms=transforms,
            models=models,
            user=user,
            structured_outputs=structured_outputs,
            verbosity=verbosity,
            prediction=prediction,
            prompt=prompt,
        )

        resp = self._client.post(
            f"{self.BASE_URL}/chat/completions",
            headers=self._headers(),
            json=body,
        )
        resp.raise_for_status()
        return self._parse_response(resp.json())

    def complete_stream(
        self,
        messages: list[ChatMessage],
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        **kwargs: Any,
    ):
        body = self._build_body(
            messages=messages,
            model=model,
            stream=True,
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
            **{k: v for k, v in kwargs.items() if v is not None},
        )

        with self._client.stream(
            "POST",
            f"{self.BASE_URL}/chat/completions",
            headers=self._headers(),
            json=body,
        ) as resp:
            resp.raise_for_status()
            for line in resp.iter_lines():
                if line.startswith("data: "):
                    payload = line[6:]
                    if payload.strip() == "[DONE]":
                        break
                    yield payload

    def search(
        self,
        query: str,
        system_prompt: Optional[str] = None,
        stream: bool = False,
    ) -> ChatCompletion:
        messages = []
        if system_prompt:
            messages.append(ChatMessage(role="system", content=system_prompt))
        messages.append(ChatMessage(role="user", content=query))
        return self.complete(
            messages=messages,
            model="blackbox-search",
            stream=stream,
        )

    def generate_image(
        self,
        prompt: str,
        model: str = "flux-pro",
        system_prompt: Optional[str] = None,
    ) -> ChatCompletion:
        messages = []
        if system_prompt:
            messages.append(ChatMessage(role="system", content=system_prompt))
        messages.append(ChatMessage(role="user", content=prompt))
        return self.complete(messages=messages, model=model)

    def generate_video(
        self,
        prompt: str,
        model: str = "veo-2",
        system_prompt: Optional[str] = None,
    ) -> ChatCompletion:
        messages = []
        if system_prompt:
            messages.append(ChatMessage(role="system", content=system_prompt))
        messages.append(ChatMessage(role="user", content=prompt))
        return self.complete(messages=messages, model=model)

    def _build_body(
        self,
        messages: Optional[list[ChatMessage]] = None,
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
        min_p: Optional[float] = None,
        top_a: Optional[float] = None,
        top_logprobs: Optional[int] = None,
        logit_bias: Optional[dict[int, float]] = None,
        response_format: Optional[dict[str, str]] = None,
        tools: Optional[list[Tool]] = None,
        tool_choice: Optional[ToolChoice | str] = None,
        parallel_tool_calls: Optional[bool] = None,
        reasoning: Optional[ReasoningConfig | dict[str, Any]] = None,
        provider: Optional[ProviderPreferences | dict[str, Any]] = None,
        route: Optional[str] = None,
        transforms: Optional[list[str]] = None,
        models: Optional[list[str]] = None,
        user: Optional[str] = None,
        structured_outputs: Optional[bool] = None,
        verbosity: Optional[str] = None,
        prediction: Optional[dict[str, str]] = None,
        prompt: Optional[str] = None,
    ) -> dict[str, Any]:
        body: dict[str, Any] = {}

        if messages:
            body["messages"] = self._serialize_messages(messages)
        if prompt:
            body["prompt"] = prompt
        if model:
            body["model"] = model
        if stream:
            body["stream"] = True
        if max_tokens is not None:
            body["max_tokens"] = max_tokens
        if temperature is not None:
            body["temperature"] = temperature
        if top_p is not None:
            body["top_p"] = top_p
        if top_k is not None:
            body["top_k"] = top_k
        if seed is not None:
            body["seed"] = seed
        if stop is not None:
            body["stop"] = stop
        if frequency_penalty is not None:
            body["frequency_penalty"] = frequency_penalty
        if presence_penalty is not None:
            body["presence_penalty"] = presence_penalty
        if repetition_penalty is not None:
            body["repetition_penalty"] = repetition_penalty
        if min_p is not None:
            body["min_p"] = min_p
        if top_a is not None:
            body["top_a"] = top_a
        if top_logprobs is not None:
            body["top_logprobs"] = top_logprobs
        if logit_bias is not None:
            body["logit_bias"] = logit_bias
        if response_format is not None:
            body["response_format"] = response_format
        if tools is not None:
            body["tools"] = []
            for t in tools:
                fn = t.function
                if not fn:
                    continue
                if isinstance(fn, dict):
                    body["tools"].append({
                        "type": t.type,
                        "function": {
                            "name": fn.get("name", ""),
                            "description": fn.get("description"),
                            "parameters": fn.get("parameters", {}),
                        },
                    })
                else:
                    body["tools"].append({
                        "type": t.type,
                        "function": {
                            "name": fn.name,
                            "description": fn.description,
                            "parameters": fn.parameters or {},
                        },
                    })
        if tool_choice is not None:
            if isinstance(tool_choice, str):
                body["tool_choice"] = tool_choice
            else:
                fn = tool_choice.function
                fn_name = fn.name if not isinstance(fn, dict) else fn.get("name", "")
                body["tool_choice"] = {
                    "type": tool_choice.type,
                    "function": {"name": fn_name},
                }
        if parallel_tool_calls is not None:
            body["parallel_tool_calls"] = parallel_tool_calls
        if reasoning is not None:
            if isinstance(reasoning, ReasoningConfig):
                r: dict[str, Any] = {}
                if reasoning.effort:
                    r["effort"] = reasoning.effort
                if reasoning.max_tokens:
                    r["max_tokens"] = reasoning.max_tokens
                if reasoning.exclude is not None:
                    r["exclude"] = reasoning.exclude
                if reasoning.enabled is not None:
                    r["enabled"] = reasoning.enabled
                body["reasoning"] = r
            else:
                body["reasoning"] = reasoning
        if provider is not None:
            if isinstance(provider, ProviderPreferences):
                p: dict[str, Any] = {}
                if provider.order:
                    p["order"] = provider.order
                if provider.allow_fallbacks is not None:
                    p["allow_fallbacks"] = provider.allow_fallbacks
                if provider.require:
                    p["require"] = provider.require
                if provider.skip:
                    p["skip"] = provider.skip
                body["provider"] = p
            else:
                body["provider"] = provider
        if route is not None:
            body["route"] = route
        if transforms is not None:
            body["transforms"] = transforms
        if models is not None:
            body["models"] = models
        if user is not None:
            body["user"] = user
        if structured_outputs is not None:
            body["structured_outputs"] = structured_outputs
        if verbosity is not None:
            body["verbosity"] = verbosity
        if prediction is not None:
            body["prediction"] = prediction

        return body

    def _parse_response(self, data: dict[str, Any]) -> ChatCompletion:
        raw_choices = data.get("choices", [])
        choices = []
        for c in raw_choices:
            msg_data = None
            delta_data = None

            if "message" in c:
                msg_data = self._parse_choice_message(c["message"])
            if "delta" in c:
                delta_data = self._parse_choice_message(c["delta"])

            err = c.get("error")
            error_obj = ErrorResponse(**err) if err else None

            choices.append(
                Choice(
                    finish_reason=c.get("finish_reason"),
                    native_finish_reason=c.get("native_finish_reason"),
                    index=c.get("index", 0),
                    message=msg_data,
                    delta=delta_data,
                    text=c.get("text"),
                    error=error_obj,
                )
            )

        return ChatCompletion(
            id=data.get("id", ""),
            created=data.get("created", 0),
            model=data.get("model", ""),
            object=data.get("object", "chat.completion"),
            choices=choices,
            system_fingerprint=data.get("system_fingerprint"),
            usage=self._parse_usage(data.get("usage")),
            provider=data.get("provider"),
        )
