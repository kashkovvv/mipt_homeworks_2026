from __future__ import annotations

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


ENV_TO_KEY = {
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
    yaml_data = _read_yaml(path)
    env_data = _read_env(env)

    if not yaml_data and not env_data:
        raise ConfigError(
            'не найдены настройки. Создайте config.yaml или задайте переменные окружения.'
        )

    raw = {**yaml_data, **env_data}
    api_key = _required_str(raw, 'api_key')
    api_host = _api_host(_required_str(raw, 'api_host'))
    model = _optional_str(raw, 'model') or 'gemma3:270m'

    return AppConfig(
        api_key=api_key,
        api_host=api_host,
        model=model,
        limit_messages=_optional_positive_int(raw, 'limit_message'),
        limit_chars=_optional_positive_int(raw, 'limit_chars'),
        temperature=_temperature(raw.get('temperature', 0.2)),
        system_prompt=_optional_str(raw, 'system_prompt'),
        stream=_bool(raw.get('stream', True)),
        request_timeout=_positive_float(raw.get('request_timeout', 120), 'request_timeout'),
    )


def _read_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    if not path.is_file():
        raise ConfigError(f'{path} существует, но это не файл.')

    try:
        loaded = yaml.safe_load(path.read_text(encoding='utf-8')) or {}
    except OSError as error:
        raise ConfigError(f'не удалось прочитать {path}: {error}') from error
    except yaml.YAMLError as error:
        raise ConfigError(f'в {path} некорректный YAML: {error}') from error

    if not isinstance(loaded, dict):
        raise ConfigError('config.yaml должен содержать словарь с настройками.')
    return {str(key): value for key, value in loaded.items()}


def _read_env(environ: Mapping[str, str]) -> dict[str, str]:
    result: dict[str, str] = {}
    for env_key, config_key in ENV_TO_KEY.items():
        value = environ.get(env_key)
        if value is not None and value.strip():
            result[config_key] = value
    return result


def _required_str(raw: Mapping[str, Any], key: str) -> str:
    value = _optional_str(raw, key)
    if value is None:
        raise ConfigError(f'обязательный параметр {key} не задан.')
    return value


def _optional_str(raw: Mapping[str, Any], key: str) -> str | None:
    value = raw.get(key)
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _api_host(value: str) -> str:
    parsed = urlparse(value)
    if parsed.scheme not in {'http', 'https'} or not parsed.netloc:
        raise ConfigError('api_host должен быть URL вида http://host/v1/.')
    return value.rstrip('/') + '/'


def _optional_positive_int(raw: Mapping[str, Any], key: str) -> int | None:
    value = raw.get(key)
    if value is None:
        return None
    if isinstance(value, str) and not value.strip():
        return None
    try:
        parsed = int(value)
    except (TypeError, ValueError) as error:
        raise ConfigError(f'{key} должен быть целым числом.') from error
    if parsed <= 0:
        raise ConfigError(f'{key} должен быть положительным.')
    return parsed


def _temperature(value: Any) -> float:
    parsed = _positive_float(value, 'temperature', allow_zero=True)
    if parsed > 1:
        raise ConfigError('temperature должен быть от 0 до 1.')
    return parsed


def _positive_float(value: Any, name: str, *, allow_zero: bool = False) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError) as error:
        raise ConfigError(f'{name} должен быть числом.') from error

    if allow_zero:
        if parsed < 0:
            raise ConfigError(f'{name} должен быть не меньше 0.')
    elif parsed <= 0:
        raise ConfigError(f'{name} должен быть положительным.')
    return parsed


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    text = str(value).strip().lower()
    if text in {'1', 'true', 'yes', 'y', 'on'}:
        return True
    if text in {'0', 'false', 'no', 'n', 'off'}:
        return False
    raise ConfigError('stream должен быть булевым значением.')
