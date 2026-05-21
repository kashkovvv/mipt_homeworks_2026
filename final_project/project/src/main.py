from __future__ import annotations

import sys
from pathlib import Path

from ai_client import OpenAIChatClient
from config import ConfigError, load_config
from ui import ConsoleApp


def main() -> int:
    try:
        config = load_config(Path('config.yaml'))
    except ConfigError as error:
        print(f'Ошибка конфигурации: {error}', file=sys.stderr)
        return 2

    try:
        client = OpenAIChatClient.from_config(config)
    except RuntimeError as error:
        print(f'Не удалось подготовить клиент модели: {error}', file=sys.stderr)
        return 2

    app = ConsoleApp(config=config, client=client)
    app.run()
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
