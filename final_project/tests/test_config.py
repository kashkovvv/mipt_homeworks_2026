from pathlib import Path

import pytest

from config import ConfigError, load_config


def write_config(tmp_path: Path, text: str) -> Path:
    path = tmp_path / 'config.yaml'
    path.write_text(text, encoding='utf-8')
    return path


def test_load_yaml_and_env_priority(tmp_path: Path) -> None:
    path = write_config(tmp_path, 'api_key: yaml\napi_host: http://yaml/v1\nlimit_message: 3\n')

    config = load_config(path, environ={'API_KEY': 'env', 'API_HOST': 'http://env/v1'})

    assert config.api_key == 'env'
    assert config.api_host == 'http://env/v1/'
    assert config.limit_messages == 3


def test_missing_config() -> None:
    with pytest.raises(ConfigError):
        load_config(Path('missing.yaml'), environ={})


@pytest.mark.parametrize(
    ('extra', 'message'),
    [
        ('api_host: localhost\n', 'URL'),
        ('api_host: http://x/v1\nlimit_chars: 0\n', 'положительным'),
        ('api_host: http://x/v1\ntemperature: 2\n', 'от 0 до 1'),
    ],
)
def test_bad_values(tmp_path: Path, extra: str, message: str) -> None:
    path = write_config(tmp_path, f'api_key: key\n{extra}')
    with pytest.raises(ConfigError, match=message):
        load_config(path, environ={})
