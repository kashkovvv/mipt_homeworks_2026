from types import SimpleNamespace
from typing import Any

import pytest

from ai_client import ModelError, OpenAIChatClient
from context_mgr import Message


class FakeCompletions:
    def __init__(self, result: Any = None, error: BaseException | None = None) -> None:
        self.result, self.error = result, error
        self.calls: list[dict[str, Any]] = []

    def create(self, **kwargs: Any) -> Any:
        self.calls.append(kwargs)
        if self.error:
            raise self.error
        return self.result


def make_client(completions: FakeCompletions) -> OpenAIChatClient:
    return OpenAIChatClient(SimpleNamespace(chat=SimpleNamespace(completions=completions)), 'model')


def test_complete_once() -> None:
    result = SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content='answer'))])
    completions = FakeCompletions(result)

    answer = make_client(completions).complete(
        [Message('user', 'hi')],
        temperature=0.3,
        stream=False,
    )

    assert answer == 'answer'
    assert completions.calls[0]['messages'] == [{'role': 'user', 'content': 'hi'}]
    assert completions.calls[0]['stream'] is False


def test_stream_and_errors() -> None:
    chunks = [
        SimpleNamespace(choices=[SimpleNamespace(delta=SimpleNamespace(content='he'))]),
        SimpleNamespace(choices=[SimpleNamespace(delta=SimpleNamespace(content='llo'))]),
    ]
    printed: list[str] = []

    answer = make_client(FakeCompletions(chunks)).complete(
        [Message('user', 'hi')], temperature=0.3, stream=True, writer=printed.append
    )

    assert answer == 'hello'
    assert printed == ['he', 'llo']
    with pytest.raises(ModelError):
        make_client(FakeCompletions(error=RuntimeError('bad'))).complete(
            [Message('user', 'hi')], temperature=0.3, stream=False
        )
