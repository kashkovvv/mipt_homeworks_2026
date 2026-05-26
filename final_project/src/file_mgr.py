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
    parts: list[str] = []
    pos = 0
    while True:
        start = text.find('@::', pos)
        if start == -1:
            parts.append(text[pos:])
            return ''.join(parts)
        end = text.find('::', start + 3)
        if end == -1:
            raise AttachmentError('у @:: нет закрывающего ::.')
        parts.append(text[pos:start])
        file_name = text[start + 3 : end].strip()
        if not file_name:
            raise AttachmentError('пустой путь к файлу.')
        _append(parts, read_text_file(file_name, base_dir=base_dir, max_size=max_size))
        pos = end + 2


def read_text_file(
    file_name: str,
    *,
    base_dir: Path | None = None,
    max_size: int | None = MAX_ATTACHMENT_SIZE,
) -> str:
    path = Path(file_name).expanduser()
    if base_dir is not None and not path.is_absolute():
        path = base_dir / path
    try:
        stat = path.stat()
        if not path.is_file():
            raise AttachmentError(f'{path} не является файлом.')
        if max_size is not None and stat.st_size > max_size:
            raise AttachmentError(f'{path} больше 5 МБ.')
        return path.read_bytes().decode('utf-8-sig')
    except AttachmentError:
        raise
    except UnicodeDecodeError as error:
        raise AttachmentError(f'{path} не похож на UTF-8 текст.') from error
    except OSError as error:
        raise AttachmentError(f'не удалось прочитать {path}: {error}') from error


def _append(parts: list[str], content: str) -> None:
    if parts and parts[-1] and not parts[-1].endswith('\n'):
        parts.append('\n')
    parts.append(content)
    if content and not content.endswith('\n'):
        parts.append('\n')
