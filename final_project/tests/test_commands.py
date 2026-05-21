import pytest

from commands import ChunkCommandError, ChunkOptions, make_chunks, parse_chunk_command


def test_parse_chunk_command() -> None:
    assert parse_chunk_command('/filechunk paragraph=2 -y') == ChunkOptions(
        'paragraph',
        2,
        True,
    )
    assert parse_chunk_command('/file_chunk len=3') == ChunkOptions('chars', 3, False)


def test_parse_chunk_command_errors() -> None:
    for command in ['/filechunk len=0', '/filechunk len=2 paragraph=2', '/bad']:
        with pytest.raises(ChunkCommandError):
            parse_chunk_command(command)


def test_make_chunks() -> None:
    assert make_chunks('a\n\nb\nc', ChunkOptions('paragraph', 2)) == ['a\n\nb', 'c']
    assert make_chunks('abcdef', ChunkOptions('chars', 2)) == ['ab', 'cd', 'ef']
