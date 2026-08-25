"""Toy data and scripted model conversations. PROVIDED IN FULL.

A real deployment sends a prompt to a real model and gets back whatever it gets back. That's
impossible to test against, so here the model is a script: a list of the exact replies it will
give, in order. Every run of a scenario behaves identically, which is what makes the tests
meaningful and lets you develop with no API key.

Each scenario below exists to exercise a specific path through your code. Once your loop works,
you can drive any of them from the running server — see the README.
"""

from __future__ import annotations

from typing import Union

from app.model_client import FatalError, ThrottleError

# The toy world the tools operate on.
CONTACTS = [
    {"id": "c_1", "name": "Acme Corp", "email": "billing@acme.test", "stage": "renewal"},
    {"id": "c_2", "name": "Globex", "email": "ops@globex.test", "stage": "active"},
    {"id": "c_3", "name": "Initech", "email": "it@initech.test", "stage": "churn-risk"},
]


SCENARIOS: dict[str, list[Union[str, Exception]]] = {
    # Finishes immediately without touching a tool. The simplest possible path through the loop —
    # get this one working first.
    "default": [
        '{"intent": "final", "thought": "nothing to do", "answer": "No action needed."}',
    ],
    # Read, then one write, then finish. The normal happy path.
    "send_followup": [
        '{"intent": "tool_use", "thought": "find Acme", "tool": "search_contacts",'
        ' "args": {"query": "acme"}}',
        '{"intent": "tool_use", "thought": "send the follow-up", "tool": "send_message",'
        ' "args": {"contact_id": "c_1", "body": "Following up on your renewal."}}',
        '{"intent": "final", "thought": "done", "answer": "Sent the renewal follow-up to Acme."}',
    ],
    # A write of the other kind, so you can see update_contact go through the same gate.
    "update_stage": [
        '{"intent": "tool_use", "thought": "find Initech", "tool": "search_contacts",'
        ' "args": {"query": "initech"}}',
        '{"intent": "tool_use", "thought": "mark renewed", "tool": "update_contact",'
        ' "args": {"contact_id": "c_3", "fields": {"stage": "renewed"}}}',
        '{"intent": "final", "thought": "done", "answer": "Updated Initech stage to renewed."}',
    ],
    # THREE writes. With the default budget of 2, the third one has to stop and ask for approval.
    # Run this under `autonomous` to see the budget bite, and under `supervised` to see the very
    # first write stop.
    "three_writes": [
        '{"intent": "tool_use", "thought": "message Acme", "tool": "send_message",'
        ' "args": {"contact_id": "c_1", "body": "one"}}',
        '{"intent": "tool_use", "thought": "message Globex", "tool": "send_message",'
        ' "args": {"contact_id": "c_2", "body": "two"}}',
        '{"intent": "tool_use", "thought": "message Initech", "tool": "send_message",'
        ' "args": {"contact_id": "c_3", "body": "three"}}',
        '{"intent": "final", "thought": "done", "answer": "Sent what I was allowed to send."}',
    ],
    # The model asks for a tool that doesn't exist, is told so, and recovers. Models really do
    # invent plausible-sounding tools. Your loop must not crash here.
    "unknown_tool": [
        '{"intent": "tool_use", "thought": "I will call the archive tool", "tool": "archive_contact",'
        ' "args": {"contact_id": "c_1"}}',
        '{"intent": "final", "thought": "that tool does not exist, giving up gracefully",'
        ' "answer": "I could not archive the contact — no such tool."}',
    ],
    # The tool exists but fails, because that contact id isn't real. Also recoverable.
    "tool_error": [
        '{"intent": "tool_use", "thought": "fetch a contact", "tool": "get_contact",'
        ' "args": {"contact_id": "c_999"}}',
        '{"intent": "final", "thought": "no such contact", "answer": "That contact does not exist."}',
    ],
    # The model replies with prose instead of JSON, then gets it right on the re-prompt.
    "bad_json_then_good": [
        "Sure! I think we should probably send them a message.",
        '{"intent": "final", "thought": "recovered", "answer": "Recovered after a bad reply."}',
    ],
    # The model never produces valid JSON. The run should fail cleanly, not hang or explode.
    "always_bad_json": [
        "not json",
        "still not json",
        "nope",
    ],
    # The provider rate-limits twice, then works. Exercises your retry logic.
    "flaky_provider": [
        ThrottleError("429 Too Many Requests"),
        ThrottleError("429 Too Many Requests"),
        '{"intent": "final", "thought": "got through", "answer": "Succeeded after retries."}',
    ],
    # A permanent failure. Should NOT be retried, and the run should fail.
    "bad_credentials": [
        FatalError("401 invalid api key"),
    ],
    # The model never says it's finished. `max_steps` is what saves you.
    "never_finishes": [
        '{"intent": "tool_use", "thought": "looking", "tool": "search_contacts", "args": {}}'
    ]
    * 50,
}


def script_for(scenario: str) -> list[Union[str, Exception]]:
    """Return a fresh copy of a scenario's script (fresh, so runs don't share a cursor)."""
    return list(SCENARIOS.get(scenario, SCENARIOS["default"]))
