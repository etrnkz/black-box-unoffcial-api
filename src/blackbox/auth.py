from typing import Optional

import httpx


class Auth:
    BUILDER_URL = "https://builder.blackbox.ai"
    APP_URL = "https://app.blackbox.ai"

    def __init__(self, client: httpx.Client):
        self._client = client
        self._csrf_token: Optional[str] = None
        self._session_token: Optional[str] = None

    @property
    def csrf_token(self) -> Optional[str]:
        return self._csrf_token

    @property
    def session_token(self) -> Optional[str]:
        return self._session_token

    def get_csrf(self) -> str:
        resp = self._client.get(f"{self.BUILDER_URL}/api/auth/csrf")
        resp.raise_for_status()
        data = resp.json()
        self._csrf_token = data.get("csrfToken", "")
        return self._csrf_token

    def login_with_token(self, token: str, email: str, redirect: bool = False) -> dict:
        self.get_csrf()
        data = {
            "token": token,
            "email": email,
            "redirect": "true" if redirect else "false",
            "csrfToken": self._csrf_token,
            "callbackUrl": f"{self.BUILDER_URL}/",
        }
        resp = self._client.post(
            f"{self.BUILDER_URL}/api/auth/callback/auto-login-token",
            data=data,
        )
        resp.raise_for_status()
        return resp.json()

    def get_session(self) -> dict:
        resp = self._client.get(f"{self.APP_URL}/api/auth/session")
        resp.raise_for_status()
        data = resp.json()
        if data and data.get("sessionToken"):
            self._session_token = data["sessionToken"]
        return data or {}

    def send_verification(self, email: str) -> dict:
        resp = self._client.post(
            f"{self.APP_URL}/api/auth/send-verification",
            json={"email": email},
        )
        resp.raise_for_status()
        return resp.json()

    def verify_email(self, email: str, code: str, use_builder: bool = False) -> dict:
        base = self.BUILDER_URL if use_builder else self.APP_URL
        resp = self._client.post(
            f"{base}/api/auth/verify-email",
            json={"email": email, "code": code},
        )
        resp.raise_for_status()
        return resp.json()

    def is_authenticated(self) -> bool:
        if not self._session_token:
            try:
                session = self.get_session()
                return bool(session.get("user"))
            except Exception:
                return False
        return True
