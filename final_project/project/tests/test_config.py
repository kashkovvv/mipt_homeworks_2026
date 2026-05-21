from __future__ import annotations

from pathlib import Path

import pytest

from config import ConfigError, load_config


def test_loads_yaml_config(tmp_path: Path) -> None:
    config_path = tmp_path / 'config.yaml'
    config_path.write_text(
        '\n'.join(
            [
                'api_key: yaml-key',
                'api_host: http://localhost:11434/v1',
                'model: qwen',
                'limit_message: 4',
                'limit_chars: 200',
                'temperature: 0.4',
                'system_prompt: Говори кратко.',
                'stream: false',
            ]
        ),
        encoding='utf-8',
    )

    config = load_config(config_path, environ={})

    assert config.api_key == 'yaml-key'
    assert config.api_host == 'http://localhost:11434/v1/'
    assert config.model == 'qwen'
    assert config.limit_messages == 4
    assert config.limit_chars == 200
    assert config.temperature == 0.4
    assert config.system_prompt == 'Говори кратко.'
    assert config.stream is False


def test_env_overrides_yaml(tmp_path: Path) -> None:
    config_path = tmp_path / 'config.yaml'
    config_path.write_text(
        'api_key: yaml-key\napi_host: http://yaml/v1\nlimit_chars: 100\n',
        encoding='utf-8',
    )

    config = load_config(
        config_path,
        environ={'API_KEY': 'env-key', 'API_HOST': 'http://env/v1', 'LIMIT_CHARS': '300'},
    )

    assert config.api_key == 'env-key'
    assert config.api_host == 'http://env/v1/'
    assert config.limit_chars == 300


def test_missing_config_is_error(tmp_path: Path) -> None:
    with pytest.raises(ConfigError, match='не найдены настройки'):
        load_config(tmp_path / 'config.yaml', environ={})


@pytest.mark.parametrize(
    ('field', 'value', 'message'),
    [
        ('api_host', 'localhost:11434/v1', 'URL'),
        ('limit_message', '0', 'положительным'),
        ('limit_chars', 'abc', 'целым числом'),
        ('temperature', '1.5', 'от 0 до 1'),
        ('stream', 'maybe', 'булевым'),
    ],
)
def test_invalid_values_are_rejected(
    tmp_path: Path,
    field: str,
    value: str,
    message: str,
) -> None:
    config_path = tmp_path / 'config.yaml'
    config_path.write_text(
        f'api_key: key\napi_host: http://host/v1\n{field}: {value}\n',
        encoding='utf-8',
    )

    with pytest.raises(ConfigError, match=message):
        load_config(config_path, environ={})
