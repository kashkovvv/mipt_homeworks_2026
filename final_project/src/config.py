import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping
from urllib.parse import urlparse

import yaml


class ConfigError(Exception):
    pass


@dataclass(frozen=True)
class AppConfig:
    api_key: str
    api_host: str
    model: str
    limit_messages: int | None
    limit_chars: int | None
    temperature: float
    system_prompt: str | None
    stream: bool
    request_timeout: float


ENV_KEYS = {
    'API_KEY': 'api_key',
    'API_HOST': 'api_host',
    'MODEL': 'model',
    'LIMIT_MESSAGE': 'limit_message',
    'LIMIT_MESSAGES': 'limit_message',
    'LIMIT_CHARS': 'limit_chars',
    'TEMPERATURE': 'temperature',
    'STREAM': 'stream',
    'REQUEST_TIMEOUT': 'request_timeout',
}


def load_config(
    path: Path = Path('config.yaml'),
    environ: Mapping[str, str] | None = None,
) -> AppConfig:
    env = os.environ if environ is None else environ
    raw = _yaml(path)
    raw.update({name: env[key] for key, name in ENV_KEYS.items() if env.get(key, '').strip()})
    if not raw:
        raise ConfigError('не найдены настройки: нужен config.yaml или переменные окружения.')

    temperature = _float(raw.get('temperature', 0.2), 'temperature', zero=True)
    if temperature > 1:
        raise ConfigError('temperature должен быть от 0 до 1.')

    return AppConfig(
        _required(raw, 'api_key'),
        _host(_required(raw, 'api_host')),
        _text(raw.get('model')) or 'gemma3:270m',
        _positive_int(raw.get('limit_message'), 'limit_message'),
        _positive_int(raw.get('limit_chars'), 'limit_chars'),
        temperature,
        _text(raw.get('system_prompt')),
        _bool(raw.get('stream', True)),
        _float(raw.get('request_timeout', 120), 'request_timeout', zero=False),
    )


def _yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        data = yaml.safe_load(path.read_text(encoding='utf-8')) or {}
    except OSError as error:
        raise ConfigError(f'не удалось прочитать {path}: {error}') from error
    except yaml.YAMLError as error:
        raise ConfigError(f'ошибка в YAML: {error}') from error
    if not isinstance(data, dict):
        raise ConfigError('config.yaml должен содержать словарь.')
    return {str(key): value for key, value in data.items()}


def _text(value: Any) -> str | None:
    text = '' if value is None else str(value).strip()
    return text or None


def _required(raw: Mapping[str, Any], key: str) -> str:
    value = _text(raw.get(key))
    if value is None:
        raise ConfigError(f'не задан параметр {key}.')
    return value


def _host(value: str) -> str:
    parsed = urlparse(value)
    if parsed.scheme not in {'http', 'https'} or not parsed.netloc:
        raise ConfigError('api_host должен быть URL вида http://host/v1/.')
    return value.rstrip('/') + '/'


def _positive_int(value: Any, name: str) -> int | None:
    if value is None or str(value).strip() == '':
        return None
    try:
        number = int(value)
    except (TypeError, ValueError) as error:
        raise ConfigError(f'{name} должен быть целым числом.') from error
    if number <= 0:
        raise ConfigError(f'{name} должен быть положительным.')
    return number


def _float(value: Any, name: str, *, zero: bool) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError) as error:
        raise ConfigError(f'{name} должен быть числом.') from error
    if number < 0 or (number == 0 and not zero):
        raise ConfigError(f'{name} должен быть положительным.')
    return number


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    text = str(value).strip().lower()
    if text in {'1', 'true', 'yes', 'y', 'on'}:
        return True
    if text in {'0', 'false', 'no', 'n', 'off'}:
        return False
    raise ConfigError('stream должен быть булевым значением.')
