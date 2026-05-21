from __future__ import annotations

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
        return self._trim([*self.messages, Message('user', content)])

    def commit_exchange(self, sent_messages: Sequence[Message], answer: str) -> None:
        self.messages = self._trim([*sent_messages, Message('assistant', answer)])

    def trim_messages(
        self,
        messages: Sequence[Message],
        *,
        keep_first: bool = False,
    ) -> list[Message]:
        return self._trim(messages, keep_first=keep_first)

    def _trim(self, messages: Sequence[Message], *, keep_first: bool = False) -> list[Message]:
        result = list(messages)
        first = result[0] if keep_first and result else None
        tail = result[1:] if first is not None else result

        if self.limit_messages is not None:
            tail_limit = self.limit_messages - 1 if first is not None else self.limit_messages
            if first is not None and tail:
                tail_limit = max(tail_limit, 1)
            while len(tail) > max(tail_limit, 0):
                tail.pop(0)

        if self.limit_chars is None:
            return _join(first, tail)

        while len(tail) > 1 and _chars_count(_join(first, tail)) > self.limit_chars:
            tail.pop(0)

        result = _join(first, tail)
        if result and _chars_count(result) > self.limit_chars:
            result = _trim_last_messages(result, self.limit_chars)

        return result


def _chars_count(messages: Sequence[Message]) -> int:
    return sum(len(message.content) for message in messages)


def _join(first: Message | None, tail: Sequence[Message]) -> list[Message]:
    if first is None:
        return list(tail)
    return [first, *tail]


def _trim_last_messages(messages: list[Message], limit_chars: int) -> list[Message]:
    if len(messages) == 1:
        message = messages[0]
        return [Message(message.role, message.content[-limit_chars:])]

    first = messages[0]
    last = messages[-1]
    first_budget = min(len(first.content), limit_chars - 1)
    last_budget = limit_chars - first_budget
    return [
        Message(first.role, first.content[-first_budget:] if first_budget else ''),
        Message(last.role, last.content[-last_budget:] if last_budget else ''),
    ]
