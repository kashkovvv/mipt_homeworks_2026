from __future__ import annotations

import pytest

from commands import ChunkCommandError, ChunkOptions, make_chunks, parse_chunk_command


def test_parse_default_file_chunk_command() -> None:
    options = parse_chunk_command('/file_chunk')

    assert options == ChunkOptions(mode='paragraph', size=1, auto=False)


def test_parse_paragraph_auto_alias() -> None:
    options = parse_chunk_command('/filechunk paragraph=3 -y')

    assert options == ChunkOptions(mode='paragraph', size=3, auto=True)


def test_parse_len_mode() -> None:
    options = parse_chunk_command('/file_chunk len=150')

    assert options == ChunkOptions(mode='chars', size=150, auto=False)


@pytest.mark.parametrize(
    'command',
    [
        '/file_chunk paragraph=0',
        '/file_chunk len=-1',
        '/file_chunk paragraph=2 len=5',
        '/file_chunk strange=1',
    ],
)
def test_invalid_chunk_commands(command: str) -> None:
    with pytest.raises(ChunkCommandError):
        parse_chunk_command(command)


def test_make_paragraph_chunks() -> None:
    text = 'one\n\ntwo\n\nthree'

    chunks = make_chunks(text, ChunkOptions(mode='paragraph', size=2))

    assert chunks == ['one\n\ntwo', 'three']


def test_make_char_chunks() -> None:
    chunks = make_chunks('abcdef', ChunkOptions(mode='chars', size=2))

    assert chunks == ['ab', 'cd', 'ef']
