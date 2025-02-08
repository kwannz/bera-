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
    assert len(context) == max_messages
    assert context[-1]["content"] == f"message {max_messages + 4}"
