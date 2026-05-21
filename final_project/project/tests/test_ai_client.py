from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pytest

from ai_client import ModelError, OpenAIChatClient
from context_mgr import Message


@dataclass
class FakeMessage:
    content: str | None


@dataclass
class FakeDelta:
    content: str | None


@dataclass
class FakeAnswerChoice:
    message: FakeMessage


@dataclass
class FakeStreamChoice:
    delta: FakeDelta


@dataclass
class FakeAnswer:
    choices: list[FakeAnswerChoice]


@dataclass
class FakeStreamChunk:
    choices: list[FakeStreamChoice]


class EmptyError(Exception):
    def __str__(self) -> str:
        return ''


class FakeCompletions:
    def __init__(self, result: Any = None, *, error: BaseException | None = None) -> None:
        self.result = result
        self.error = error
        self.calls: list[dict[str, Any]] = []

    def create(self, **kwargs: Any) -> Any:
        self.calls.append(kwargs)
        if self.error is not None:
            raise self.error
        return self.result


@dataclass
class FakeChat:
    completions: FakeCompletions


@dataclass
class FakeOpenAI:
    chat: FakeChat


def make_client(completions: FakeCompletions) -> OpenAIChatClient:
    return OpenAIChatClient(client=FakeOpenAI(chat=FakeChat(completions)), model='test-model')


def test_complete_once_sends_openai_payload() -> None:
    completions = FakeCompletions(FakeAnswer([FakeAnswerChoice(FakeMessage('answer'))]))
    client = make_client(completions)

    answer = client.complete(
        [Message('user', 'hello')],
        temperature=0.4,
        stream=False,
    )

    assert answer == 'answer'
    assert completions.calls == [
        {
            'model': 'test-model',
            'messages': [{'role': 'user', 'content': 'hello'}],
            'temperature': 0.4,
            'stream': False,
        }
    ]


def test_complete_stream_writes_chunks() -> None:
    completions = FakeCompletions(
        [
            FakeStreamChunk([FakeStreamChoice(FakeDelta('hel'))]),
            FakeStreamChunk([FakeStreamChoice(FakeDelta(None))]),
            FakeStreamChunk([FakeStreamChoice(FakeDelta('lo'))]),
        ]
    )
    client = make_client(completions)
    printed: list[str] = []

    answer = client.complete(
        [Message('user', 'hello')],
        temperature=0.1,
        stream=True,
        writer=printed.append,
    )

    assert answer == 'hello'
    assert printed == ['hel', 'lo']
    assert completions.calls[0]['stream'] is True


def test_empty_model_error_keeps_class_name() -> None:
    client = make_client(FakeCompletions(error=EmptyError()))

    with pytest.raises(ModelError, match='EmptyError'):
        client.complete([Message('user', 'hello')], temperature=0.1, stream=False)


def test_keyboard_interrupt_is_not_wrapped() -> None:
    client = make_client(FakeCompletions(error=KeyboardInterrupt()))

    with pytest.raises(KeyboardInterrupt):
        client.complete([Message('user', 'hello')], temperature=0.1, stream=False)
