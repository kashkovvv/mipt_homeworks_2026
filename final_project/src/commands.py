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
        raise ChunkCommandError(str(error)) from error
    if not parts or parts[0] not in {'/file_chunk', '/filechunk'}:
        raise ChunkCommandError('ожидалась команда /file_chunk.')

    auto = '-y' in parts[1:]
    paragraph: int | None = None
    length: int | None = None
    for part in parts[1:]:
        if part == '-y':
            continue
        if part.startswith('paragraph='):
            paragraph = _positive(part.split('=', 1)[1], 'paragraph')
        elif part.startswith('len='):
            length = _positive(part.split('=', 1)[1], 'len')
        else:
            raise ChunkCommandError(f'неизвестный аргумент {part!r}.')
    if paragraph is not None and length is not None:
        raise ChunkCommandError('нельзя одновременно задавать paragraph и len.')
    if length is not None:
        return ChunkOptions('chars', length, auto)
    return ChunkOptions('paragraph', paragraph or 1, auto)


def make_chunks(text: str, options: ChunkOptions) -> list[str]:
    if options.mode == 'chars':
        return [text[i : i + options.size] for i in range(0, len(text), options.size)]
    paragraphs = [part.strip() for part in re.split(r'\n+', text) if part.strip()]
    return [
        '\n\n'.join(paragraphs[i : i + options.size])
        for i in range(0, len(paragraphs), options.size)
    ]


def _positive(value: str, name: str) -> int:
    try:
        number = int(value)
    except ValueError as error:
        raise ChunkCommandError(f'{name} должен быть целым числом.') from error
    if number <= 0:
        raise ChunkCommandError(f'{name} должен быть положительным.')
    return number
