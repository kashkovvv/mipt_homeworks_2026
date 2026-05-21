from __future__ import annotations

import os
import sys
from collections.abc import Callable
from pathlib import Path
from typing import TextIO

from ai_client import ChatClient, ModelError
from commands import ChunkCommandError, ChunkOptions, make_chunks, parse_chunk_command
from config import AppConfig
from context_mgr import ChatHistory, Message
from file_mgr import AttachmentError, expand_file_mentions, read_text_file

InputFunc = Callable[[str], str]


class ConsoleExit(Exception):
    pass


class ConsoleApp:
    def __init__(
        self,
        *,
        config: AppConfig,
        client: ChatClient,
        stdout: TextIO | None = None,
        input_func: InputFunc | None = None,
    ) -> None:
        self._config = config
        self._client = client
        self._stdout = stdout or sys.stdout
        self._input = input_func or input
        self._history = ChatHistory(
            limit_messages=config.limit_messages,
            limit_chars=config.limit_chars,
        )

    def run(self) -> None:
        self._line('GigaVibeMiptCode запущен. \\q — выход, /reset — новый чат.')
        while True:
            raw = self._input('>>> ')
            try:
                if self._handle_command(raw):
                    continue
                self._handle_message(raw)
            except ConsoleExit:
                self._line('До встречи.')
                return

    def _handle_command(self, raw: str) -> bool:
        command = raw.strip()
        if not command:
            return True
        if command == '\\q':
            raise ConsoleExit
        if command == '/reset':
            self._history.clear()
            clear_screen()
            self._line('История очищена.')
            return True
        if command.startswith(('/file_chunk', '/filechunk')):
            self._run_file_chunk(command)
            return True
        return False

    def _handle_message(self, raw: str) -> None:
        try:
            user_text = expand_file_mentions(raw, base_dir=Path.cwd())
        except AttachmentError as error:
            self._line(f'Не удалось подставить файл: {error}')
            return

        sent_messages = self._history.with_user_message(user_text)
        request_messages = self._messages_with_system(sent_messages)
        answer = self._ask_model(request_messages)
        if answer is None:
            return

        self._history.commit_exchange(_without_system(request_messages), answer)
        if not self._config.stream:
            self._line(answer)

    def _run_file_chunk(self, command: str) -> None:
        try:
            options = parse_chunk_command(command)
        except ChunkCommandError as error:
            self._line(f'Ошибка команды: {error}')
            return

        self._line('Введите путь до файла')
        file_name = self._read_command_input()
        try:
            text = read_text_file(file_name, base_dir=Path.cwd(), max_size=None)
        except AttachmentError as error:
            self._line(f'Не удалось прочитать файл: {error}')
            return

        self._line('Принято. Что нужно сделать для каждого фрагмента (User Prompt)?')
        prompt = self._read_command_input()
        if not prompt.strip():
            self._line('Промпт пустой, режим отменен.')
            return

        chunks = make_chunks(text, options)
        if not chunks:
            self._line('В файле нет текста для обработки.')
            return

        self._line(f'Принято. Начинаю обработку: всего фрагментов {len(chunks)}.')
        for index, chunk in enumerate(chunks, start=1):
            if not options.auto and index > 1:
                self._wait_next_chunk()
            if not self._process_chunk(prompt, chunk, options, index=index, total=len(chunks)):
                return

        self._line('Обработка файла завершена.')

    def _process_chunk(
        self,
        prompt: str,
        chunk: str,
        options: ChunkOptions,
        *,
        index: int,
        total: int,
    ) -> bool:
        if options.auto:
            self._line(f'--- Фрагмент {index}/{total} ---')

        message = Message('user', f'{prompt.strip()}\n\n{chunk}')
        answer = self._ask_model([message])
        if answer is None:
            return False
        if not self._config.stream:
            self._line(answer)
        return True

    def _wait_next_chunk(self) -> None:
        while True:
            self._line('Нажмите Enter для следующего фрагмента или введите \\q для выхода.')
            answer = self._read_command_input(allow_empty=True)
            if answer == '':
                return
            self._line('Для продолжения нужна пустая строка.')

    def _ask_model(self, messages: list[Message]) -> str | None:
        try:
            answer = self._client.complete(
                messages,
                temperature=self._config.temperature,
                stream=self._config.stream,
                writer=self._write if self._config.stream else None,
            )
            if self._config.stream:
                self._line('')
            return answer
        except KeyboardInterrupt:
            self._line('\nЗапрос прерван. Можно ввести новое сообщение.')
            return None
        except ModelError as error:
            self._line(f'Ошибка модели: {error}')
            return None

    def _messages_with_system(self, messages: list[Message]) -> list[Message]:
        if self._config.system_prompt is None:
            return messages
        payload = [Message('system', self._config.system_prompt), *messages]
        return self._history.trim_messages(payload, keep_first=True)

    def _read_command_input(self, *, allow_empty: bool = False) -> str:
        value = self._input('>>> ')
        if value.strip() == '\\q':
            raise ConsoleExit
        if allow_empty:
            return value
        return value.strip()

    def _write(self, text: str) -> None:
        self._stdout.write(text)
        self._stdout.flush()

    def _line(self, text: str) -> None:
        self._stdout.write(text + '\n')
        self._stdout.flush()


def clear_screen() -> None:
    command = 'cls' if os.name == 'nt' else 'clear'
    os.system(command)


def _without_system(messages: list[Message]) -> list[Message]:
    return [message for message in messages if message.role != 'system']
