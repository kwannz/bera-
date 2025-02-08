import pytest
from src.chat_interface.services.context_service import ContextManager


@pytest.mark.asyncio
async def test_context_manager_init(context_manager: ContextManager):
    assert context_manager.max_context_rounds == 5


@pytest.mark.asyncio
async def test_get_context_empty(context_manager: ContextManager):
    context = await context_manager.get_context("test_session")
    assert context == []


@pytest.mark.asyncio
async def test_add_and_get_message(context_manager: ContextManager):
    session_id = "test_session"
    test_message = {"role": "user", "content": "test message"}

    await context_manager.add_message(session_id, test_message)
    context = await context_manager.get_context(session_id)

    assert len(context) == 1
    assert context[0] == test_message


@pytest.mark.asyncio
async def test_context_limit(context_manager: ContextManager):
    session_id = "test_session"
    max_messages = context_manager.max_context_rounds * 2

    # Add more messages than the limit
    for i in range(max_messages + 5):
        await context_manager.add_message(
            session_id,
            {"role": "user", "content": f"message {i}"}
        )

    context = await context_manager.get_context(session_id)
    # Should have first message + last 2 rounds (4 messages)
    assert len(context) == 5
    # First message should be the first user message
    assert context[0]["content"] == "message 0"
    # Last 4 messages should be from the last 2 rounds
    assert context[-4]["content"] == "message 11"
    assert context[-3]["content"] == "message 12"
    assert context[-2]["content"] == "message 13"
    assert context[-1]["content"] == "message 14"
