import json
from unittest.mock import MagicMock, PropertyMock, patch

import httpx
import pytest

from blackbox.chat import Chat
from blackbox.files import chat_with_file, read_file
from blackbox.login import login
from blackbox.models import ChatMessage, FileContentPart, TextContentPart
from blackbox.webchat import WebChat, WebChatResponse


def _mock_transport(handler):
    return httpx.MockTransport(handler)


def _mock_curl_response(status=200, text="", json_data=None, headers=None):
    resp = MagicMock()
    resp.status_code = status
    resp.text = text
    if json_data is not None:
        resp.json.return_value = json_data
    else:
        resp.json.return_value = {}
    if status >= 400:
        resp.raise_for_status.side_effect = Exception(f"HTTP {status}")
    else:
        resp.raise_for_status = MagicMock()
    return resp


# ─── Chat Integration ───

CHAT_RESPONSE = {
    "id": "chat-123",
    "created": 1717000000,
    "model": "blackbox",
    "object": "chat.completion",
    "choices": [
        {
            "finish_reason": "stop",
            "index": 0,
            "message": {
                "role": "assistant",
                "content": "Hello! How can I help you?",
            },
        }
    ],
    "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
}


class TestChatIntegration:
    def test_chat_with_file_content_part(self):
        def handler(request: httpx.Request) -> httpx.Response:
            body = json.loads(request.read())
            msg = body["messages"][0]
            content = msg["content"]
            assert len(content) == 2
            assert content[0]["type"] == "file"
            assert content[0]["file"]["filename"] == "test.txt"
            assert content[0]["file"]["file_data"].startswith("data:text/plain;base64,")
            assert content[1]["type"] == "text"
            assert content[1]["text"] == "What is this?"
            return httpx.Response(200, json=CHAT_RESPONSE)

        transport = _mock_transport(handler)
        client = httpx.Client(transport=transport)
        chat = Chat(client, "sk-test")

        messages = [
            ChatMessage(
                role="user",
                content=[
                    FileContentPart(filename="test.txt", file_data="data:text/plain;base64,aGVsbG8="),
                    TextContentPart(text="What is this?"),
                ],
            )
        ]
        result = chat.complete(messages=messages)
        assert result.content == "Hello! How can I help you?"
        assert result.id == "chat-123"
        assert result.usage.total_tokens == 15

    def test_chat_with_file_mixed_content(self):
        messages_sent = []

        def handler(request: httpx.Request) -> httpx.Response:
            body = json.loads(request.read())
            messages_sent.append(body["messages"])
            return httpx.Response(200, json=CHAT_RESPONSE)

        transport = _mock_transport(handler)
        client = httpx.Client(transport=transport)
        chat = Chat(client, "sk-test")

        chat.complete(
            messages=[
                ChatMessage(role="user", content="plain text"),
                ChatMessage(
                    role="user",
                    content=[
                        FileContentPart(filename="doc.pdf", file_data="data:application/pdf;base64,AAA="),
                        TextContentPart(text="Summarize"),
                    ],
                ),
            ]
        )
        assert len(messages_sent[0]) == 2
        assert messages_sent[0][0]["content"] == "plain text"
        assert messages_sent[0][1]["content"][0]["type"] == "file"


# ─── File Utility Integration ───

class TestFileUtils:
    def test_read_file_not_found(self):
        with pytest.raises(FileNotFoundError):
            read_file("nonexistent_file_xyz.txt")

    def test_read_file_with_tmp(self, tmp_path):
        f = tmp_path / "hello.txt"
        f.write_text("Hello World")
        data_uri, name, mime = read_file(str(f))
        assert name == "hello.txt"
        assert mime == "text/plain"
        assert data_uri.startswith("data:text/plain;base64,")

    def test_chat_with_file_integration(self, tmp_path):
        f = tmp_path / "test.txt"
        f.write_text("Hello World")

        def handler(request: httpx.Request) -> httpx.Response:
            body = json.loads(request.read())
            msg = body["messages"][0]
            content = msg["content"]
            assert content[0]["type"] == "file"
            assert content[0]["file"]["filename"] == "test.txt"
            assert content[0]["file"]["file_data"].startswith("data:text/plain;base64,")
            return httpx.Response(200, json=CHAT_RESPONSE)

        transport = _mock_transport(handler)
        client = httpx.Client(transport=transport)
        chat = Chat(client, "sk-test")

        result = chat_with_file(chat, str(f), "What's this?")
        assert result.content == "Hello! How can I help you?"


# ─── Login Integration ───

LOGIN_PAGE_HTML = """
<html>
<head><link rel="stylesheet" href="/_next/static/css/styles.css"></head>
<body>
<script src="/_next/static/chunks/624-testhash.js"></script>
<script src="/_next/static/chunks/7158-otherhash.js"></script>
</body>
</html>
"""

JS_CHUNK_CONTENT = """(0,i.$)("d1b45d9d8987f0640a6033e9041366d5ff847db6"),some_code();"""
RSC_RESPONSE = '1:{"type":"success","resultCode":"USER_LOGGED_IN"}\n7:null'
SESSION_RESPONSE = json.dumps({"user": {"email": "test@test.com", "id": "user-123"}, "expires": "2026-01-01"})


class TestLoginIntegration:
    def test_login_flow(self):
        from blackbox.login import _find_action_hash, _get_user_info, LOGIN_ACTION_HASH

        session = MagicMock()

        def get_side_effect(url, **kwargs):
            url_str = str(url)
            if "static/chunks" in url_str:
                return _mock_curl_response(200, text=JS_CHUNK_CONTENT)
            if "/login" in url_str:
                return _mock_curl_response(200, text=LOGIN_PAGE_HTML)
            if "api/auth/session" in url_str:
                return _mock_curl_response(200, json_data=json.loads(SESSION_RESPONSE))
            return _mock_curl_response(404)

        session.get.side_effect = get_side_effect

        action_hash = _find_action_hash(session)
        assert action_hash == LOGIN_ACTION_HASH

        user_info = _get_user_info(session)
        assert user_info["email"] == "test@test.com"
        assert user_info["id"] == "user-123"

    def test_login_function(self):
        session = MagicMock()

        def get_side_effect(url, **kwargs):
            url_str = str(url)
            if "static/chunks" in url_str:
                return _mock_curl_response(200, text=JS_CHUNK_CONTENT)
            if "/login" in url_str:
                return _mock_curl_response(200, text=LOGIN_PAGE_HTML)
            if "api/auth/session" in url_str:
                return _mock_curl_response(200, json_data=json.loads(SESSION_RESPONSE))
            return _mock_curl_response(404)

        def post_side_effect(url, **kwargs):
            assert "d1b45d9d8987f0640a6033e9041366d5ff847db6" in str(kwargs.get("headers", {}).get("next-action", ""))
            return _mock_curl_response(200, text=RSC_RESPONSE)

        session.get.side_effect = get_side_effect
        session.post.side_effect = post_side_effect

        mock_cookies = MagicMock()
        mock_cookies.get_dict.return_value = {"next-auth.session-token": "test-session-token"}
        type(session).cookies = PropertyMock(return_value=mock_cookies)

        with patch("blackbox.login.Session", return_value=session):
            result = login(email="test@test.com", password="secret")

        assert result["session_token"] == "test-session-token"
        assert result["user_email"] == "test@test.com"
        assert result["user_id"] == "user-123"


# ─── WebChat Integration ───

SSE_RESPONSE = """data: {"id":"msg-1","model":"claude","text":"Hello","content":"Hello"}

data: {"id":"msg-2","model":"claude","text":" world","content":" world"}

data: [DONE]
"""


class TestWebChatIntegration:
    def test_webchat_sse_parsing(self):
        session = MagicMock()
        resp = _mock_curl_response(200, text=SSE_RESPONSE)
        session.post.return_value = resp

        wc = WebChat(session=session, validated="test-uuid")
        result = wc.chat("hello")
        assert result.content == "Hello world"
        assert result.id == "msg-2"
        assert result.model == "claude"

    def test_webchat_search_mode(self):
        session = MagicMock()
        session.post.return_value = _mock_curl_response(200, text=SSE_RESPONSE)

        wc = WebChat(session=session, validated="test-uuid")
        wc.search("test query")

        call_body = session.post.call_args[1]["json"]
        assert call_body["webSearchModeOption"]["webMode"] is True
        assert call_body["deepSearchMode"] is False

    def test_webchat_code_mode(self):
        session = MagicMock()
        session.post.return_value = _mock_curl_response(200, text=SSE_RESPONSE)

        wc = WebChat(session=session, validated="test-uuid")
        wc.generate_code("write a function", language="python")

        call_body = session.post.call_args[1]["json"]
        assert call_body["codeModelMode"] is True
        assert call_body["userSelectedAgent"] == "CodeGenAgent"
