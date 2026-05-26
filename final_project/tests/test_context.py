from context_mgr import ChatHistory, Message


def test_message_limit() -> None:
    history = ChatHistory(limit_messages=2)
    history.messages = [Message('user', '1'), Message('assistant', '2')]

    assert history.with_user_message('3') == [Message('assistant', '2'), Message('user', '3')]


def test_char_limit() -> None:
    assert ChatHistory(limit_chars=5).with_user_message('0123456789') == [
        Message('user', '56789')
    ]


def test_keep_system_and_user() -> None:
    messages = [Message('system', 'long-system'), Message('user', 'hello')]

    assert ChatHistory(limit_chars=5).trim(messages, keep_first=True) == [
        Message('system', 'long-system'),
        Message('user', 'hello'),
    ]
