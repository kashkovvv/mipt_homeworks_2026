from __future__ import annotations

import re
import shlex
from dataclasses import dataclass
from typing import Literal

ChunkMode = Literal['paragraph', 'chars']


class ChunkCommandError(Exception):
    pass


@dataclass(frozen=True)
class ChunkOptions:
    mode: ChunkMode = 'paragraph'
    size: int = 1
    auto: bool = False


def parse_chunk_command(command: str) -> ChunkOptions:
    try:
        parts = shlex.split(command)
    except ValueError as error:
        raise ChunkCommandError(f'не удалось разобрать команду: {error}') from error

    if not parts or parts[0] not in {'/file_chunk', '/filechunk'}:
        raise ChunkCommandError('ожидалась команда /file_chunk.')

    auto = False
    paragraph_size: int | None = None
    char_size: int | None = None

    for part in parts[1:]:
        if part == '-y':
            auto = True
        elif part.startswith('paragraph='):
            paragraph_size = _positive_int(part.removeprefix('paragraph='), 'paragraph')
        elif part.startswith('len='):
            char_size = _positive_int(part.removeprefix('len='), 'len')
        else:
            raise ChunkCommandError(f'неизвестный аргумент {part!r}.')

    if paragraph_size is not None and char_size is not None:
        raise ChunkCommandError('нельзя одновременно задавать paragraph и len.')
    if char_size is not None:
        return ChunkOptions(mode='chars', size=char_size, auto=auto)
    return ChunkOptions(mode='paragraph', size=paragraph_size or 1, auto=auto)


def make_chunks(text: str, options: ChunkOptions) -> list[str]:
    if options.mode == 'chars':
        return [
            text[index : index + options.size]
            for index in range(0, len(text), options.size)
            if text[index : index + options.size]
        ]

    paragraphs = [item.strip() for item in re.split(r'\n+', text) if item.strip()]
    chunks: list[str] = []
    for index in range(0, len(paragraphs), options.size):
        chunks.append('\n\n'.join(paragraphs[index : index + options.size]))
    return chunks


def _positive_int(value: str, name: str) -> int:
    try:
        parsed = int(value)
    except ValueError as error:
        raise ChunkCommandError(f'{name} должен быть целым числом.') from error
    if parsed <= 0:
        raise ChunkCommandError(f'{name} должен быть положительным.')
    return parsed
