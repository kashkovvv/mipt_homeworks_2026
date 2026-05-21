from __future__ import annotations

from context_mgr import ChatHistory, Message


def test_message_limit_removes_oldest_messages() -> None:
    history = ChatHistory(limit_messages=3)
    history.messages = [
        Message('user', 'one'),
        Message('assistant', 'two'),
        Message('user', 'three'),
    ]

    messages = history.with_user_message('four')

    assert [message.content for message in messages] == ['two', 'three', 'four']


def test_char_limit_removes_old_messages_until_it_fits() -> None:
    history = ChatHistory(limit_chars=8)
    history.messages = [Message('user', 'abcd'), Message('assistant', 'efgh')]

    messages = history.with_user_message('ij')

    assert [message.content for message in messages] == ['efgh', 'ij']


def test_single_huge_message_is_trimmed_from_left() -> None:
    history = ChatHistory(limit_chars=5)

    messages = history.with_user_message('0123456789')

    assert messages == [Message('user', '56789')]


def test_fixed_first_message_keeps_current_user_message() -> None:
    history = ChatHistory(limit_messages=1, limit_chars=12)
    messages = [
        Message('system', 'system'),
        Message('assistant', 'old'),
        Message('user', '0123456789'),
    ]

    trimmed = history.trim_messages(messages, keep_first=True)

    assert trimmed == [Message('system', 'system'), Message('user', '456789')]


def test_tiny_char_limit_keeps_tail_of_system_and_user() -> None:
    history = ChatHistory(limit_chars=5)
    messages = [Message('system', 'very-long-system'), Message('user', 'hello')]

    trimmed = history.trim_messages(messages, keep_first=True)

    assert trimmed == [Message('system', 'stem'), Message('user', 'o')]


def test_commit_exchange_applies_limits() -> None:
    history = ChatHistory(limit_messages=2)
    sent = [Message('user', 'question')]

    history.commit_exchange(sent, 'answer')

    assert history.messages == [Message('user', 'question'), Message('assistant', 'answer')]


def test_clear_removes_history() -> None:
    history = ChatHistory(messages=[Message('user', 'hello')])

    history.clear()

    assert history.messages == []
