from __future__ import annotations

from pathlib import Path

MAX_ATTACHMENT_SIZE = 5 * 1024 * 1024


class AttachmentError(Exception):
    pass


def expand_file_mentions(
    text: str,
    *,
    base_dir: Path | None = None,
    max_size: int | None = MAX_ATTACHMENT_SIZE,
) -> str:
    result: list[str] = []
    position = 0

    while True:
        start = text.find('@::', position)
        if start == -1:
            result.append(text[position:])
            break

        result.append(text[position:start])
        end = text.find('::', start + 3)
        if end == -1:
            raise AttachmentError('найден @:: без закрывающего ::.')

        file_name = text[start + 3 : end].strip()
        if not file_name:
            raise AttachmentError('путь внутри @::...:: пустой.')

        content = read_text_file(file_name, base_dir=base_dir, max_size=max_size)
        _append_content(result, content)
        position = end + 2

    return ''.join(result)


def read_text_file(
    file_name: str,
    *,
    base_dir: Path | None = None,
    max_size: int | None = MAX_ATTACHMENT_SIZE,
) -> str:
    path = Path(file_name).expanduser()
    if not path.is_absolute() and base_dir is not None:
        path = base_dir / path

    try:
        stat = path.stat()
    except OSError as error:
        raise AttachmentError(f'не удалось открыть {path}: {error}') from error

    if not path.is_file():
        raise AttachmentError(f'{path} не является файлом.')
    if max_size is not None and stat.st_size > max_size:
        raise AttachmentError(f'{path} больше допустимых 5 МБ.')

    try:
        data = path.read_bytes()
    except OSError as error:
        raise AttachmentError(f'не удалось прочитать {path}: {error}') from error

    try:
        return data.decode('utf-8-sig')
    except UnicodeDecodeError as error:
        raise AttachmentError(f'{path} не похож на UTF-8 текст.') from error


def _append_content(result: list[str], content: str) -> None:
    if result and result[-1] and not result[-1].endswith('\n'):
        result.append('\n')
    result.append(content)
    if content and not content.endswith('\n'):
        result.append('\n')
