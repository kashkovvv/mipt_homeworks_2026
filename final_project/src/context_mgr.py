from dataclasses import dataclass, field
from typing import Literal, Sequence, TypedDict

Role = Literal['system', 'user', 'assistant']


class OpenAIMessage(TypedDict):
    role: Role
    content: str


@dataclass(frozen=True)
class Message:
    role: Role
    content: str

    def as_openai(self) -> OpenAIMessage:
        return {'role': self.role, 'content': self.content}


@dataclass
class ChatHistory:
    limit_messages: int | None = None
    limit_chars: int | None = None
    messages: list[Message] = field(default_factory=list)

    def clear(self) -> None:
        self.messages.clear()

    def with_user_message(self, content: str) -> list[Message]:
        return self.trim([*self.messages, Message('user', content)])

    def commit(self, sent: Sequence[Message], answer: str) -> None:
        self.messages = self.trim([*sent, Message('assistant', answer)])

    def trim(self, messages: Sequence[Message], *, keep_first: bool = False) -> list[Message]:
        fixed = [messages[0]] if keep_first and messages else []
        tail = list(messages[1:] if fixed else messages)

        if self.limit_messages is not None:
            count = max(self.limit_messages - len(fixed), 1 if fixed and tail else 0)
            tail = tail[-count:]

        if self.limit_chars is not None:
            while len(tail) > 1 and _size(tail) > self.limit_chars:
                tail.pop(0)
            if tail and _size(tail) > self.limit_chars:
                last = tail[-1]
                tail[-1] = Message(last.role, last.content[-self.limit_chars :])
        return [*fixed, *tail]


def _size(messages: Sequence[Message]) -> int:
    return sum(len(message.content) for message in messages)
