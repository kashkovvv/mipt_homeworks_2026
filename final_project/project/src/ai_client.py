from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Any, Protocol

from config import AppConfig
from context_mgr import Message, OpenAIMessage

StreamWriter = Callable[[str], None]


class ModelError(Exception):
    pass


class ChatClient(Protocol):
    def complete(
        self,
        messages: Sequence[Message],
        *,
        temperature: float,
        stream: bool,
        writer: StreamWriter | None = None,
    ) -> str:
        ...


class OpenAIChatClient:
    def __init__(self, client: Any, model: str) -> None:
        self._client = client
        self._model = model

    @classmethod
    def from_config(cls, config: AppConfig) -> OpenAIChatClient:
        try:
            from openai import OpenAI
            import httpx
        except ImportError as error:
            raise RuntimeError('установите зависимости из requirements.txt') from error

        try:
            http_client = httpx.Client(
                timeout=config.request_timeout,
                trust_env=False,
            )
            client = OpenAI(
                api_key=config.api_key,
                base_url=config.api_host,
                http_client=http_client,
            )
        except Exception as error:
            message = str(error) or error.__class__.__name__
            raise RuntimeError(message) from error
        return cls(client=client, model=config.model)

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
            if stream:
                return self._complete_stream(payload, temperature=temperature, writer=writer)
            return self._complete_once(payload, temperature=temperature)
        except KeyboardInterrupt:
            raise
        except Exception as error:
            message = str(error) or error.__class__.__name__
            raise ModelError(message) from error

    def _complete_once(self, payload: list[OpenAIMessage], *, temperature: float) -> str:
        response = self._client.chat.completions.create(
            model=self._model,
            messages=payload,
            temperature=temperature,
            stream=False,
        )
        answer = response.choices[0].message.content
        return answer or ''

    def _complete_stream(
        self,
        payload: list[OpenAIMessage],
        *,
        temperature: float,
        writer: StreamWriter | None,
    ) -> str:
        chunks = self._client.chat.completions.create(
            model=self._model,
            messages=payload,
            temperature=temperature,
            stream=True,
        )

        parts: list[str] = []
        for chunk in chunks:
            delta = chunk.choices[0].delta.content
            if delta:
                parts.append(delta)
                if writer is not None:
                    writer(delta)
        return ''.join(parts)
