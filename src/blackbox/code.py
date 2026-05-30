from typing import Optional

import httpx

from .models import CodeGenerationResponse


class CodeGen:
    BASE_URL = "https://api.blackbox.ai"

    def __init__(self, client: httpx.Client, api_key: Optional[str] = None):
        self._client = client
        self._api_key = api_key

    def _headers(self) -> dict:
        h = {"content-type": "application/json"}
        if self._api_key:
            h["authorization"] = f"Bearer {self._api_key}"
        return h

    def generate(
        self,
        prompt: str,
        language: Optional[str] = None,
        context: Optional[str] = None,
    ) -> CodeGenerationResponse:
        system = "You are a code generation assistant."
        if language:
            system += f" Generate code in {language}."
        if context:
            system += f" Context: {context}"

        body = {
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
            "model": "blackbox",
        }

        resp = self._client.post(
            f"{self.BASE_URL}/v1/chat/completions",
            headers=self._headers(),
            json=body,
        )
        resp.raise_for_status()
        data = resp.json()

        content = ""
        choices = data.get("choices", [])
        if choices:
            content = choices[0].get("message", {}).get("content", "")

        return CodeGenerationResponse(
            code=content,
            language=language or "",
        )
