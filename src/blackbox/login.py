import re
import uuid
from typing import Optional

from curl_cffi.requests import Session

LOGIN_ACTION_HASH = "d1b45d9d8987f0640a6033e9041366d5ff847db6"


class LoginError(Exception):
    pass


def login(
    email: str,
    password: str,
    existing_session: Optional[Session] = None,
) -> dict:
    session = existing_session or Session(impersonate="chrome142")

    resp = session.get(
        "https://app.blackbox.ai/login",
        headers={
            "accept": "text/html,application/xhtml+xml",
        },
    )
    resp.raise_for_status()

    action_hash = _find_action_hash(session)

    boundary = "----WebKitFormBoundary" + uuid.uuid4().hex[:16]
    body = (
        f'--{boundary}\r\n'
        f'Content-Disposition: form-data; name="1_email"\r\n\r\n'
        f'{email}\r\n'
        f'--{boundary}\r\n'
        f'Content-Disposition: form-data; name="1_password"\r\n\r\n'
        f'{password}\r\n'
        f'--{boundary}\r\n'
        f'Content-Disposition: form-data; name="0"\r\n\r\n'
        f'["$undefined","$K1"]\r\n'
        f'--{boundary}--\r\n'
    ).encode()

    login_resp = session.post(
        "https://app.blackbox.ai/login",
        data=body,
        headers={
            "accept": "text/x-component",
            "content-type": f"multipart/form-data; boundary={boundary}",
            "next-action": action_hash,
            "next-router-state-tree": (
                '["",{"children":["login",{"children":["__PAGE__",{}]}]},null,null,true]'
            ),
            "next-url": "/login",
            "origin": "https://app.blackbox.ai",
            "referer": "https://app.blackbox.ai/login",
        },
    )

    if login_resp.status_code != 200:
        raise LoginError(f"Login failed: HTTP {login_resp.status_code}")

    session_cookies = {k: v for k, v in session.cookies.get_dict().items()}
    session_token = session_cookies.get("next-auth.session-token")
    if not session_token:
        raise LoginError("No session token in response")

    cookie_hdr = "; ".join(f"{k}={v}" for k, v in session_cookies.items())

    user_info = _get_user_info(session)

    return {
        "session": session,
        "cookie_header": cookie_hdr,
        "session_token": session_token,
        "cookies": session_cookies,
        "user_email": user_info.get("email"),
        "user_id": user_info.get("id"),
    }


def _find_action_hash(session: Session) -> str:
    resp = session.get(
        "https://app.blackbox.ai/login",
        headers={
            "accept": "text/html,application/xhtml+xml",
        },
    )

    js_urls = re.findall(r'src="([^"]*\.js[^"]*)"', resp.text)
    for url in js_urls:
        if not url.startswith("http"):
            url = "https://app.blackbox.ai" + url
        try:
            js_resp = session.get(
                url,
                headers={
                    "accept": "*/*",
                },
            )
            if LOGIN_ACTION_HASH in js_resp.text:
                return LOGIN_ACTION_HASH
        except Exception:
            continue

    return LOGIN_ACTION_HASH


def _get_user_info(session: Session) -> dict:
    resp = session.get(
        "https://app.blackbox.ai/api/auth/session",
        headers={"accept": "application/json"},
    )
    if resp.status_code == 200:
        data = resp.json()
        user = data.get("user", {}) if data else {}
        return {"email": user.get("email"), "id": user.get("id")}
    return {}
