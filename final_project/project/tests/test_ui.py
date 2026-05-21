from __future__ import annotations

from collections.abc import Sequence
from io import StringIO
from pathlib import Path

import pytest

import ui as app_module
from ai_client import ModelError, StreamWriter
from config import AppConfig
from context_mgr import Message
from ui import ConsoleApp, ConsoleExit


class FakeClient:
    def __init__(
        self,
        answers: list[str] | None = None,
        *,
        error: BaseException | None = None,
    ) -> None:
        self.answers = answers or ['ok']
        self.error = error
        self.calls: list[list[Message]] = []

    def complete(
        self,
        messages: Sequence[Message],
        *,
        temperature: float,
        stream: bool,
        writer: StreamWriter | None = None,
    ) -> str:
        _ = temperature
        self.calls.append(list(messages))
        if self.error is not None:
            raise self.error
        answer = self.answers.pop(0) if self.answers else 'ok'
        if stream and writer is not None:
            for part in answer.split():
                writer(part)
                writer(' ')
            return answer + ' '
        return answer


def make_config(*, stream: bool = False, system_prompt: str | None = None) -> AppConfig:
    return AppConfig(
        api_key='key',
        api_host='http://localhost:11434/v1/',
        model='model',
        limit_messages=10,
        limit_chars=500,
        temperature=0.2,
        system_prompt=system_prompt,
        stream=stream,
        request_timeout=10,
    )


def test_handle_message_sends_history_and_stores_answer() -> None:
    output = StringIO()
    client = FakeClient(['answer'])
    app = ConsoleApp(config=make_config(), client=client, stdout=output)

    app._handle_message('hello')

    assert [[message.content for message in call] for call in client.calls] == [['hello']]
    assert 'answer' in output.getvalue()
    assert [message.content for message in app._history.messages] == ['hello', 'answer']


def test_system_prompt_is_sent_but_not_saved_in_history() -> None:
    output = StringIO()
    client = FakeClient(['answer'])
    app = ConsoleApp(
        config=make_config(system_prompt='Отвечай по делу.'),
        client=client,
        stdout=output,
    )

    app._handle_message('hello')

    assert client.calls[0][0] == Message('system', 'Отвечай по делу.')
    assert app._history.messages[0] == Message('user', 'hello')


def test_streaming_writes_answer_once() -> None:
    output = StringIO()
    client = FakeClient(['one two'])
    app = ConsoleApp(config=make_config(stream=True), client=client, stdout=output)

    app._handle_message('hello')

    assert output.getvalue() == 'one two \n'
    assert app._history.messages[-1] == Message('assistant', 'one two ')


def test_model_error_keeps_history_clean() -> None:
    output = StringIO()
    client = FakeClient(error=ModelError('server is down'))
    app = ConsoleApp(config=make_config(), client=client, stdout=output)

    app._handle_message('hello')

    assert 'Ошибка модели' in output.getvalue()
    assert app._history.messages == []


def test_keyboard_interrupt_keeps_history_clean() -> None:
    output = StringIO()
    client = FakeClient(error=KeyboardInterrupt())
    app = ConsoleApp(config=make_config(), client=client, stdout=output)

    app._handle_message('hello')

    assert 'Запрос прерван' in output.getvalue()
    assert app._history.messages == []


def test_file_chunk_auto_does_not_use_chat_history(tmp_path: Path) -> None:
    source = tmp_path / 'book.txt'
    source.write_text('first\n\nsecond', encoding='utf-8')
    answers = ['summary 1', 'summary 2']
    client = FakeClient(answers)
    user_inputs = iter([str(source), 'summary please'])
    output = StringIO()
    app = ConsoleApp(
        config=make_config(),
        client=client,
        stdout=output,
        input_func=lambda _prompt: next(user_inputs),
    )

    app._run_file_chunk('/file_chunk -y')

    assert len(client.calls) == 2
    assert client.calls[0] == [Message('user', 'summary please\n\nfirst')]
    assert client.calls[1] == [Message('user', 'summary please\n\nsecond')]
    assert app._history.messages == []
    assert 'Обработка файла завершена' in output.getvalue()


def test_reset_command_clears_history_and_screen(monkeypatch: pytest.MonkeyPatch) -> None:
    output = StringIO()
    client = FakeClient()
    app = ConsoleApp(config=make_config(), client=client, stdout=output)
    app._history.messages = [Message('user', 'old')]
    clear_calls: list[str] = []
    monkeypatch.setattr(app_module, 'clear_screen', lambda: clear_calls.append('clear'))

    handled = app._handle_command('/reset')

    assert handled is True
    assert app._history.messages == []
    assert clear_calls == ['clear']
    assert 'История очищена' in output.getvalue()


def test_quit_command_raises_console_exit() -> None:
    app = ConsoleApp(config=make_config(), client=FakeClient(), stdout=StringIO())

    with pytest.raises(ConsoleExit):
        app._handle_command('  \\q  ')
