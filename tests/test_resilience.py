from __future__ import annotations

import pytest
from dataclasses import replace

from app.model_client import MockModelClient, ThrottleError, FatalError, complete_with_retry
from app.tools import Workspace
from app.config import SETTINGS

def test_complete_with_retry_success_after_throttles():
    # a scripted client that raises ThrottleError twice then succeeds
    # result: ultimately succeeds AND model.calls == 3
    responses = [
        ThrottleError("429"),
        ThrottleError("429"),
        '{"intent": "final", "answer": "ok"}'
    ]
    model = MockModelClient(responses)
    messages = [{"role": "user", "content": "hi"}]

    # We use a modified settings to avoid long sleeps in tests
    settings = replace(SETTINGS, model_max_retries=3, model_backoff_base_seconds=0.01)

    result = complete_with_retry(model, messages, settings=settings)

    assert result == '{"intent": "final", "answer": "ok"}'
    assert model.calls == 3

def test_complete_with_retry_fatal_error():
    # a scripted client that raises FatalError immediately
    # result: raises FatalError AND model.calls == 1
    responses = [
        FatalError("bad key"),
        '{"intent": "final", "answer": "ok"}'
    ]
    model = MockModelClient(responses)
    messages = [{"role": "user", "content": "hi"}]

    with pytest.raises(FatalError):
        complete_with_retry(model, messages)

    assert model.calls == 1

def test_send_message_idempotency_same_key():
    # calling it twice with the SAME idempotency key
    # result: len(ws.messages) == 1
    ws = Workspace([{"id": "c_1", "name": "Test", "email": "t@t.com", "stage": "lead"}])

    # First call
    ws.send_message(contact_id="c_1", body="Hello 1", idempotency_key="key_1")
    # Second call with same key
    ws.send_message(contact_id="c_1", body="Hello 2", idempotency_key="key_1")

    assert len(ws.messages) == 1
    assert ws.messages[0]["body"] == "Hello 1"

def test_send_message_idempotency_different_keys():
    # calling it twice with DIFFERENT idempotency keys
    # result: len(ws.messages) == 2
    ws = Workspace([{"id": "c_1", "name": "Test", "email": "t@t.com", "stage": "lead"}])

    ws.send_message(contact_id="c_1", body="Hello 1", idempotency_key="key_1")
    ws.send_message(contact_id="c_1", body="Hello 2", idempotency_key="key_2")

    assert len(ws.messages) == 2
