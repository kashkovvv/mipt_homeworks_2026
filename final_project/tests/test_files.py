from pathlib import Path

import pytest

from file_mgr import AttachmentError, expand_file_mentions, read_text_file


def test_expand_file(tmp_path: Path) -> None:
    path = tmp_path / 'a.txt'
    path.write_text('text', encoding='utf-8')

    assert expand_file_mentions('read @::a.txt::', base_dir=tmp_path) == 'read \ntext\n'


def test_file_errors(tmp_path: Path) -> None:
    with pytest.raises(AttachmentError):
        read_text_file('missing.txt', base_dir=tmp_path)
    with pytest.raises(AttachmentError):
        expand_file_mentions('@::broken', base_dir=tmp_path)


def test_size_limit(tmp_path: Path) -> None:
    path = tmp_path / 'big.txt'
    path.write_bytes(b'abcdef')

    with pytest.raises(AttachmentError):
        read_text_file('big.txt', base_dir=tmp_path, max_size=5)
