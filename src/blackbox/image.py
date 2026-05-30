from typing import Any, Optional

import httpx

from .models import ImageData, ImageGenerationResponse


class ImageGen:
    BASE_URL = "https://api.blackbox.ai"

    def __init__(self, client: httpx.Client, api_key: Optional[str] = None):
        self._client = client
        self._api_key = api_key

    def _headers(self) -> dict[str, str]:
        h = {"content-type": "application/json"}
        if self._api_key:
            h["authorization"] = f"Bearer {self._api_key}"
        return h

    def generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        n: int = 1,
        size: Optional[str] = None,
        quality: Optional[str] = None,
        style: Optional[str] = None,
        response_format: Optional[str] = None,
    ) -> ImageGenerationResponse:
        body: dict[str, Any] = {"prompt": prompt, "n": n}
        if model:
            body["model"] = model
        if size:
            body["size"] = size
        if quality:
            body["quality"] = quality
        if style:
            body["style"] = style
        if response_format:
            body["response_format"] = response_format

        resp = self._client.post(
            f"{self.BASE_URL}/v1/images/generations",
            headers=self._headers(),
            json=body,
        )
        resp.raise_for_status()
        data = resp.json()

        raw_items = data.get("data", [])
        items = [
            ImageData(
                url=item.get("url", ""),
                revised_prompt=item.get("revised_prompt"),
                b64_json=item.get("b64_json"),
            )
            for item in raw_items
        ]

        return ImageGenerationResponse(
            created=data.get("created", 0),
            data=items,
        )
