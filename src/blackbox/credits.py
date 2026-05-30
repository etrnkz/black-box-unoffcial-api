import httpx

from .models import CreditInfo


class Credits:
    BUILDER_URL = "https://builder.blackbox.ai"

    def __init__(self, client: httpx.Client):
        self._client = client

    def get(self) -> CreditInfo:
        resp = self._client.get(f"{self.BUILDER_URL}/api/credits/get")
        resp.raise_for_status()
        data = resp.json()
        return CreditInfo(
            total=data.get("total", 0),
            used=data.get("used", 0),
            remaining=data.get("remaining", data.get("total", 0) - data.get("used", 0)),
        )

    def get_via_api(self, api_key: str) -> CreditInfo:
        resp = self._client.get(
            "https://api.blackbox.ai/v1/credits",
            headers={"authorization": f"Bearer {api_key}"},
        )
        resp.raise_for_status()
        data = resp.json()
        return CreditInfo(
            total=data.get("total", 0),
            used=data.get("used", 0),
            remaining=data.get("remaining", data.get("total", 0) - data.get("used", 0)),
        )
