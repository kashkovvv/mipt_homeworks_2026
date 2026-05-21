from __future__ import annotations

from pathlib import Path

import pytest

from file_mgr import AttachmentError, expand_file_mentions, read_text_file


def test_expand_single_file_mention(tmp_path: Path) -> None:
    source = tmp_path / 'main.py'
    source.write_text('print(1)\n', encoding='utf-8')

    result = expand_file_mentions('Что тут не так? @::main.py::', base_dir=tmp_path)

    assert result == 'Что тут не так? \nprint(1)\n'


def test_expand_multiple_file_mentions(tmp_path: Path) -> None:
    first = tmp_path / 'a.txt'
    second = tmp_path / 'b.txt'
    first.write_text('alpha', encoding='utf-8')
    second.write_text('beta', encoding='utf-8')

    result = expand_file_mentions('@::a.txt:: + @::b.txt::', base_dir=tmp_path)

    assert 'alpha' in result
    assert 'beta' in result


def test_unclosed_marker_is_error(tmp_path: Path) -> None:
    with pytest.raises(AttachmentError, match='закрывающего'):
        expand_file_mentions('@::broken', base_dir=tmp_path)


def test_missing_file_is_error(tmp_path: Path) -> None:
    with pytest.raises(AttachmentError, match='не удалось открыть'):
        read_text_file('missing.txt', base_dir=tmp_path)


def test_directory_is_error(tmp_path: Path) -> None:
    with pytest.raises(AttachmentError, match='не является файлом'):
        read_text_file(str(tmp_path))


def test_big_file_is_error(tmp_path: Path) -> None:
    source = tmp_path / 'big.txt'
    source.write_bytes(b'abcdef')

    with pytest.raises(AttachmentError, match='больше допустимых'):
        read_text_file('big.txt', base_dir=tmp_path, max_size=5)


def test_invalid_utf8_is_error(tmp_path: Path) -> None:
    source = tmp_path / 'bad.txt'
    source.write_bytes(b'\xff\xff')

    with pytest.raises(AttachmentError, match='UTF-8'):
        read_text_file('bad.txt', base_dir=tmp_path)
