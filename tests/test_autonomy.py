from __future__ import annotations

import pytest

from app.autonomy import evaluate_gate
from app.models import GateDecision

@pytest.mark.parametrize(
    "level, tool_kind, writes_so_far, max_auto_writes, expected",
    [
        # Read tools: Always allowed, not simulated, no approval needed at any level
        ("shadow", "read", 0, 2, GateDecision(allow=True, simulate=False, requires_approval=False)),
        ("supervised", "read", 0, 2, GateDecision(allow=True, simulate=False, requires_approval=False)),
        ("autonomous", "read", 0, 2, GateDecision(allow=True, simulate=False, requires_approval=False)),

        # Shadow + write: Allowed but simulated
        ("shadow", "write", 0, 2, GateDecision(allow=True, simulate=True, requires_approval=False)),

        # Supervised + write: Always requires approval
        ("supervised", "write", 0, 2, GateDecision(allow=False, simulate=False, requires_approval=True)),

        # Autonomous + write: Allowed while writes_so_far < max_auto_writes
        ("autonomous", "write", 0, 2, GateDecision(allow=True, simulate=False, requires_approval=False)),
        ("autonomous", "write", 1, 2, GateDecision(allow=True, simulate=False, requires_approval=False)),

        # Autonomous + write: Requires approval once budget is exhausted (writes_so_far == max_auto_writes)
        ("autonomous", "write", 2, 2, GateDecision(allow=False, simulate=False, requires_approval=True)),
    ],
)
def test_evaluate_gate(level, tool_kind, writes_so_far, max_auto_writes, expected):
    # We ignore 'reason' in the comparison because it's a human-readable string that might vary
    decision = evaluate_gate(level, tool_kind, writes_so_far, max_auto_writes)

    assert decision.allow == expected.allow
    assert decision.simulate == expected.simulate
    assert decision.requires_approval == expected.requires_approval
