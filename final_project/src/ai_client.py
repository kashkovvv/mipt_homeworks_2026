from collections.abc import Callable, Sequence
from typing import Any

from config import AppConfig
from context_mgr import Message

StreamWriter = Callable[[str], None]
ChatClient = Any


class ModelError(Exception):
    pass


class OpenAIChatClient:
    def __init__(self, client: Any, model: str) -> None:
        self._client = client
        self._model = model

    @classmethod
    def from_config(cls, config: AppConfig) -> 'OpenAIChatClient':
        try:
            import httpx
            from openai import OpenAI
        except ImportError as error:
            raise RuntimeError('установите зависимости из requirements.txt') from error

        try:
            http_client = httpx.Client(timeout=config.request_timeout, trust_env=False)
            client = OpenAI(
                api_key=config.api_key,
                base_url=config.api_host,
                http_client=http_client,
            )
        except Exception as error:
            raise RuntimeError(str(error) or error.__class__.__name__) from error
        return cls(client, config.model)

    def complete(
        self,
        messages: Sequence[Message],
        *,
        temperature: float,
        stream: bool,
        writer: StreamWriter | None = None,
    ) -> str:
        payload = [message.as_openai() for message in messages]
        try:
            response = self._client.chat.completions.create(
                model=self._model,
                messages=payload,
                temperature=temperature,
                stream=stream,
            )
            if not stream:
                return response.choices[0].message.content or ''
            return _collect_stream(response, writer)
        except KeyboardInterrupt:
            raise
        except Exception as error:
            raise ModelError(str(error) or error.__class__.__name__) from error


def _collect_stream(chunks: Any, writer: StreamWriter | None) -> str:
    parts: list[str] = []
    for chunk in chunks:
        text = chunk.choices[0].delta.content
        if not text:
            continue
        parts.append(text)
        if writer is not None:
            writer(text)
    return ''.join(parts)
