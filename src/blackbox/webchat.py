import json
import uuid
from dataclasses import dataclass, field
from typing import Any, Optional

import httpx


@dataclass
class WebChatResponse:
    content: str = ""
    id: str = ""
    model: str = ""
    sources: list[dict[str, str]] = field(default_factory=list)
    raw: Any = None


class WebChat:
    APP_URL = "https://app.blackbox.ai"

    def __init__(
        self,
        cookie_header: Optional[str] = None,
        validated: Optional[str] = None,
        user_email: Optional[str] = None,
        user_id: Optional[str] = None,
    ):
        self._client = httpx.Client(
            timeout=120.0,
            headers={
                "user-agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/148.0.0.0 Safari/537.36"
                ),
            },
            follow_redirects=True,
        )
        self._cookie_header = cookie_header
        self._validated = validated or str(uuid.uuid4())
        self._user_email = user_email
        self._user_id = user_id

    def _build_body(
        self,
        message: str,
        *,
        agent: str = "VscodeAgent",
        model: Optional[str] = None,
        code: bool = False,
        search: bool = False,
        deep_search: bool = False,
        reasoning: bool = False,
        image: bool = False,
        beast: bool = False,
        designer: bool = False,
        interpreter: bool = False,
        max_tokens: int = 1024,
    ) -> dict[str, Any]:
        msg_id = str(uuid.uuid4())[:20]
        chat_id = str(uuid.uuid4())[:7]

        web_search_mode = {"autoMode": False, "webMode": False, "offlineMode": True}
        if search:
            web_search_mode = {"autoMode": False, "webMode": True, "offlineMode": False}
        elif deep_search:
            web_search_mode = {"autoMode": True, "webMode": False, "offlineMode": False}

        return {
            "messages": [{"id": msg_id, "role": "user", "content": message}],
            "id": chat_id,
            "previewToken": None,
            "userId": None,
            "codeModelMode": code,
            "trendingAgentMode": {},
            "isMicMode": False,
            "maxTokens": max_tokens,
            "playgroundTopP": None,
            "playgroundTemperature": None,
            "isChromeExt": False,
            "githubToken": "",
            "clickedAnswer2": False,
            "clickedAnswer3": False,
            "clickedForceWebSearch": search,
            "visitFromDelta": False,
            "isMemoryEnabled": False,
            "mobileClient": False,
            "userSelectedModel": model,
            "userSelectedAgent": agent,
            "validated": self._validated,
            "imageGenerationMode": image,
            "imageGenMode": "autoMode" if image else "autoMode",
            "webSearchModePrompt": search,
            "deepSearchMode": deep_search,
            "promptSelection": "",
            "domains": None,
            "vscodeClient": False,
            "codeInterpreterMode": interpreter,
            "customProfile": {
                "name": "", "occupation": "", "traits": [],
                "additionalInfo": "", "enableNewChats": False,
            },
            "webSearchModeOption": web_search_mode,
            "session": (
                {
                    "user": {"email": self._user_email, "id": self._user_id},
                    "expires": "2026-06-29T13:17:02.109Z",
                    "isNewUser": False,
                }
                if self._user_email
                else None
            ),
            "isPremium": False,
            "teamAccount": self._user_email or "",
            "subscriptionCache": (
                {
                    "status": "FREE",
                    "customerId": None,
                    "expiryTimestamp": None,
                    "lastChecked": 1780147021751,
                    "isTrialSubscription": False,
                    "hasPaymentVerificationFailure": False,
                    "verificationFailureTimestamp": None,
                    "requiresAuthentication": False,
                    "isTeam": False,
                    "numSeats": 1,
                    "provider": "stripe",
                    "previouslySubscribed": False,
                    "activeInsuffientCredits": False,
                }
                if self._user_email
                else None
            ),
            "beastMode": beast,
            "reasoningMode": reasoning,
            "designerMode": designer,
            "workspaceId": "",
            "asyncMode": False,
            "isTaskPersistent": False,
            "selectedElement": None,
        }

    def _chat_headers(self) -> dict[str, str]:
        headers = {
            "accept": "*/*",
            "accept-language": "en-US,en;q=0.9",
            "cache-control": "no-cache",
            "content-type": "application/json",
            "origin": self.APP_URL,
            "pragma": "no-cache",
            "priority": "u=1, i",
            "referer": f"{self.APP_URL}/chat",
            "sec-ch-ua": '"Chromium";v="148", "Google Chrome";v="148", "Not/A)Brand";v="99"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
        }
        if self._cookie_header:
            headers["cookie"] = self._cookie_header
        return headers

    def _parse_sse(self, text: str) -> WebChatResponse:
        result = WebChatResponse()
        content_parts: list[str] = []
        for line in text.splitlines():
            line = line.strip()
            if line.startswith("data: "):
                payload = line[6:]
                if payload == "[DONE]":
                    continue
                try:
                    data = json.loads(payload)
                    result.raw = data
                    if isinstance(data, dict):
                        content_parts.append(data.get("text", data.get("content", "")))
                        if data.get("id"):
                            result.id = data["id"]
                        if data.get("model"):
                            result.model = data["model"]
                        annotations = data.get("annotations", data.get("sources"))
                        if annotations and isinstance(annotations, list):
                            for ann in annotations:
                                source = {
                                    "url": (ann.get("url_citation") or ann).get("url", ""),
                                    "title": (ann.get("url_citation") or ann).get("title", ""),
                                }
                                if source["url"]:
                                    result.sources.append(source)
                except json.JSONDecodeError:
                    content_parts.append(payload)
            else:
                content_parts.append(line)
        result.content = "".join(content_parts)
        return result

    def chat(
        self,
        message: str,
        *,
        agent: str = "VscodeAgent",
        model: Optional[str] = None,
        code: bool = False,
        search: bool = False,
        deep_search: bool = False,
        reasoning: bool = False,
        image: bool = False,
        beast: bool = False,
        designer: bool = False,
        interpreter: bool = False,
        max_tokens: int = 1024,
    ) -> WebChatResponse:
        body = self._build_body(
            message=message,
            agent=agent,
            model=model,
            code=code,
            search=search,
            deep_search=deep_search,
            reasoning=reasoning,
            image=image,
            beast=beast,
            designer=designer,
            interpreter=interpreter,
            max_tokens=max_tokens,
        )
        resp = self._client.post(
            f"{self.APP_URL}/api/chat",
            json=body,
            headers=self._chat_headers(),
        )
        resp.raise_for_status()
        return self._parse_sse(resp.text)

    def chat_stream(
        self,
        message: str,
        *,
        agent: str = "VscodeAgent",
        model: Optional[str] = None,
        code: bool = False,
        search: bool = False,
        deep_search: bool = False,
        reasoning: bool = False,
        image: bool = False,
        beast: bool = False,
        designer: bool = False,
        interpreter: bool = False,
        max_tokens: int = 1024,
    ):
        body = self._build_body(
            message=message,
            agent=agent,
            model=model,
            code=code,
            search=search,
            deep_search=deep_search,
            reasoning=reasoning,
            image=image,
            beast=beast,
            designer=designer,
            interpreter=interpreter,
            max_tokens=max_tokens,
        )
        with self._client.stream(
            "POST",
            f"{self.APP_URL}/api/chat",
            headers=self._chat_headers(),
            json=body,
        ) as resp:
            resp.raise_for_status()
            for line in resp.iter_lines():
                line = line.strip()
                if not line:
                    continue
                if line.startswith("data: "):
                    payload = line[6:]
                    if payload.strip() == "[DONE]":
                        break
                    yield payload
                else:
                    yield line

    def search(
        self,
        query: str,
        deep: bool = False,
        max_tokens: int = 1024,
    ) -> WebChatResponse:
        return self.chat(query, search=not deep, deep_search=deep, max_tokens=max_tokens)

    def search_stream(
        self,
        query: str,
        deep: bool = False,
        max_tokens: int = 1024,
    ):
        yield from self.chat_stream(query, search=not deep, deep_search=deep, max_tokens=max_tokens)

    def generate_code(
        self,
        prompt: str,
        language: Optional[str] = None,
        max_tokens: int = 2048,
    ) -> WebChatResponse:
        msg = f"Write {language} code: {prompt}" if language else prompt
        return self.chat(msg, code=True, agent="CodeGenAgent", max_tokens=max_tokens)

    def generate_image(
        self,
        prompt: str,
        model: Optional[str] = None,
    ) -> WebChatResponse:
        return self.chat(prompt, image=True, model=model, agent="ImageGenAgent")

    def generate_video(
        self,
        prompt: str,
        model: Optional[str] = None,
    ) -> WebChatResponse:
        return self.chat(prompt, model=model, agent="VideoGenAgent")

    def close(self):
        self._client.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
