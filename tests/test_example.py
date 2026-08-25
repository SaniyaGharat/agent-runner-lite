"""Example tests over the PROVIDED pieces, so `pytest` is green on a fresh checkout.

They also show the three shapes you'll want. Keep them or delete them — writing your own is
part of the exercise (TASK 6).
"""

from __future__ import annotations

import pytest

from app.models import AgentIntent
from app.seed import CONTACTS
from app.tools import ToolError, Workspace


# Shape 1: a plain unit test. Arrange, act, assert.
def test_intent_parses_valid_json():
    intent = AgentIntent.model_validate_json('{"intent":"final","answer":"hi"}')
    assert intent.intent == "final"
    assert intent.answer == "hi"


# Shape 2: asserting that something correctly REFUSES. Easy to forget, often where the bugs are.
def test_intent_rejects_tool_use_without_a_tool():
    with pytest.raises(Exception):
        AgentIntent.model_validate_json('{"intent":"tool_use","thought":"hmm"}')


# Shape 3: a table-driven test. One case per row, and pytest reports each row separately, so a
# failure tells you exactly which input broke. Ideal for TASK 1's decision table.
@pytest.mark.parametrize(
    "query,expected_id",
    [
        ("acme", "c_1"),
        ("globex", "c_2"),
        ("initech", "c_3"),
    ],
)
def test_search_finds_contacts(query, expected_id):
    ws = Workspace(CONTACTS)
    found = ws.search_contacts(query=query)
    assert [c["id"] for c in found] == [expected_id]


def test_read_tool_raises_for_a_missing_contact():
    ws = Workspace(CONTACTS)
    with pytest.raises(ToolError):
        ws.get_contact(contact_id="c_nope")
