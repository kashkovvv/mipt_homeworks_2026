import os
import sys
from collections.abc import Callable
from pathlib import Path
from typing import TextIO

from ai_client import ChatClient, ModelError, OpenAIChatClient
from commands import ChunkCommandError, make_chunks, parse_chunk_command
from config import AppConfig, ConfigError, load_config
from context_mgr import ChatHistory, Message
from file_mgr import AttachmentError, expand_file_mentions, read_text_file


class ConsoleExit(Exception):
    pass


class ConsoleApp:
    def __init__(
        self,
        config: AppConfig,
        client: ChatClient,
        stdout: TextIO | None = None,
        input_func: Callable[[str], str] | None = None,
    ) -> None:
        self.config = config
        self.client = client
        self.out = stdout or sys.stdout
        self.input = input_func or input
        self.history = ChatHistory(config.limit_messages, config.limit_chars)

    def run(self) -> None:
        self._line('GigaVibeMiptCode запущен. \\q — выход, /reset — новый чат.')
        while True:
            try:
                line = self.input('>>> ')
                if not self._command(line):
                    self._message(line)
            except ConsoleExit:
                self._line('До встречи.')
                return

    def _command(self, line: str) -> bool:
        command = line.strip()
        if not command:
            return True
        if command == '\\q':
            raise ConsoleExit
        if command == '/reset':
            self.history.clear()
            clear_screen()
            self._line('История очищена.')
            return True
        if command.startswith(('/filechunk', '/file_chunk')):
            self._filechunk(command)
            return True
        return False

    def _message(self, line: str) -> None:
        try:
            sent = self.history.with_user_message(expand_file_mentions(line, base_dir=Path.cwd()))
            request = self._with_system(sent)
            answer = self._ask(request)
        except AttachmentError as error:
            self._line(f'Не удалось подставить файл: {error}')
            return
        if answer is None:
            return
        self.history.commit([msg for msg in request if msg.role != 'system'], answer)

    def _filechunk(self, command: str) -> None:
        try:
            options = parse_chunk_command(command)
            self._line('Введите путь до файла')
            text = read_text_file(self._read(), base_dir=Path.cwd())
            self._line('Принято. Что нужно сделать для каждого фрагмента?')
            prompt = self._read()
            if not prompt:
                raise ChunkCommandError('пустой промпт.')
            chunks = make_chunks(text, options)
        except (AttachmentError, ChunkCommandError) as error:
            self._line(f'Ошибка: {error}')
            return
        self._line(f'Принято. Начинаю обработку: всего фрагментов {len(chunks)}.')
        for index, chunk in enumerate(chunks, 1):
            if not options.auto and index > 1:
                self._line('Нажмите Enter для следующего фрагмента или \\q для выхода.')
                while self._read(allow_empty=True) != '':
                    self._line('Для продолжения нужна пустая строка.')
            if options.auto:
                self._line(f'--- Фрагмент {index}/{len(chunks)} ---')
            if self._ask([Message('user', f'{prompt}\n\n{chunk}')]) is None:
                return
        self._line('Обработка файла завершена.')

    def _ask(self, messages: list[Message]) -> str | None:
        try:
            answer = str(
                self.client.complete(
                    messages,
                    temperature=self.config.temperature,
                    stream=self.config.stream,
                    writer=self._write if self.config.stream else None,
                )
            )
        except KeyboardInterrupt:
            self._line('\nЗапрос прерван. Можно ввести новое сообщение.')
            return None
        except ModelError as error:
            self._line(f'Ошибка модели: {error}')
            return None
        self._line('' if self.config.stream else answer)
        return answer

    def _with_system(self, messages: list[Message]) -> list[Message]:
        if self.config.system_prompt is None:
            return messages
        prompt = Message('system', self.config.system_prompt)
        return self.history.trim([prompt, *messages], keep_first=True)

    def _read(self, *, allow_empty: bool = False) -> str:
        value = self.input('>>> ')
        if value.strip() == '\\q':
            raise ConsoleExit
        return value if allow_empty else value.strip()

    def _write(self, text: str) -> None:
        self.out.write(text)
        self.out.flush()

    def _line(self, text: str) -> None:
        self.out.write(text + '\n')
        self.out.flush()


def clear_screen() -> None:
    os.system('cls' if os.name == 'nt' else 'clear')


def main() -> int:
    try:
        config = load_config(Path('config.yaml'))
        client = OpenAIChatClient.from_config(config)
    except ConfigError as error:
        print(f'Ошибка конфигурации: {error}', file=sys.stderr)
        return 2
    except RuntimeError as error:
        print(f'Не удалось подготовить клиент модели: {error}', file=sys.stderr)
        return 2
    ConsoleApp(config, client).run()
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
