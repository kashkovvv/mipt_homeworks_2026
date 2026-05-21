from io import StringIO
from pathlib import Path
from typing import Any

import pytest

from ai_client import ModelError
from config import AppConfig
from context_mgr import Message
from file_mgr import MAX_ATTACHMENT_SIZE
from main import ConsoleApp, ConsoleExit


class FakeClient:
    def __init__(self, answer: str = 'ok', error: BaseException | None = None) -> None:
        self.answer, self.error = answer, error
        self.calls: list[list[Message]] = []

    def complete(self, messages: Any, **kwargs: Any) -> str:
        self.calls.append(list(messages))
        if self.error:
            raise self.error
        writer = kwargs.get('writer')
        if writer:
            writer(self.answer)
        return self.answer


def cfg(stream: bool = False, prompt: str | None = None) -> AppConfig:
    return AppConfig('key', 'http://host/v1/', 'model', 10, 500, 0.2, prompt, stream, 10)


def test_console_message_flow() -> None:
    out, client = StringIO(), FakeClient('answer')
    app = ConsoleApp(cfg(prompt='sys'), client, stdout=out)
    app._message('hi')
    assert client.calls[0][0] == Message('system', 'sys')
    assert app.history.messages[-1] == Message('assistant', 'answer')
    assert 'answer' in out.getvalue()

    out = StringIO()
    ConsoleApp(cfg(stream=True), FakeClient('x'), stdout=out)._message('hi')
    assert out.getvalue() == 'x\n'


def test_console_errors_and_commands(monkeypatch: pytest.MonkeyPatch) -> None:
    app = ConsoleApp(cfg(), FakeClient(error=ModelError('bad')), stdout=StringIO())
    app._message('hi')
    assert app.history.messages == []

    app = ConsoleApp(cfg(), FakeClient(), stdout=StringIO())
    app.history.messages = [Message('user', 'old')]
    monkeypatch.setattr('main.clear_screen', lambda: None)
    assert app._command('/reset') is True
    assert app.history.messages == []
    with pytest.raises(ConsoleExit):
        app._command('\\q')


def test_filechunk_checks_file_size(tmp_path: Path) -> None:
    path = tmp_path / 'big.txt'
    path.write_bytes(b'x' * (MAX_ATTACHMENT_SIZE + 1))
    out, client = StringIO(), FakeClient()
    values = iter([str(path), 'summarize'])

    app = ConsoleApp(cfg(), client, stdout=out, input_func=lambda _: next(values))
    app._filechunk('/filechunk')

    assert client.calls == []
    assert 'больше 5 МБ' in out.getvalue()
