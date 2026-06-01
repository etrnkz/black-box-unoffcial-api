import base64
import mimetypes
from pathlib import Path
from typing import Optional

from .chat import Chat
from .models import ChatCompletion, ChatMessage, FileContentPart, TextContentPart


def read_file(filepath: str) -> tuple[str, str, str]:
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {filepath}")
    data = path.read_bytes()
    b64 = base64.b64encode(data).decode("utf-8")
    mime, _ = mimetypes.guess_type(str(path))
    mime = mime or "application/octet-stream"
    data_uri = f"data:{mime};base64,{b64}"
    return data_uri, path.name, mime


def chat_with_file(
    chat: Chat,
    filepath: str,
    prompt: str,
    model: Optional[str] = None,
) -> ChatCompletion:
    data_uri, filename, _ = read_file(filepath)
    messages = [
        ChatMessage(
            role="user",
            content=[
                FileContentPart(filename=filename, file_data=data_uri),
                TextContentPart(text=prompt),
            ],
        )
    ]
    return chat.complete(messages=messages, model=model)
