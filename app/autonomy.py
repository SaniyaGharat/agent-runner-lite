"""Governed autonomy: how much the agent is allowed to do on its own.

This is the smallest file in the project and one of the most important. An agent that can send
messages and update records needs a policy sitting between "the model asked for this" and "it
happened". That policy is one pure function.

TASK 1: evaluate_gate.
"""

from __future__ import annotations

from app.config import SETTINGS
from app.models import AutonomyLevel, GateDecision, ToolKind


def evaluate_gate(
    level: AutonomyLevel,
    tool_kind: ToolKind,
    writes_so_far: int,
    max_auto_writes: int = SETTINGS.max_auto_writes,
) -> GateDecision:
    """TASK 1 — decide how one tool call is allowed to proceed.

    The policy — three governance stages, which in the real product a run graduates through as it
    earns trust:

      read tools
          Always allowed, at every level. Looking something up can't break anything.

      shadow — "show me what you would do"
          Write tools are ALLOWED BUT SIMULATED (allow=True, simulate=True). The agent behaves
          exactly as it would in production and we record what it tried to do, but nothing
          actually changes. This is how a new agent gets evaluated against real tasks with zero
          risk: run it in shadow, then check the effects it *would* have produced.

      supervised — "ask me first"
          Every write stops and waits for a human (allow=False, requires_approval=True).

      autonomous — "go ahead, within limits"
          Writes are auto-approved while `writes_so_far < max_auto_writes`. Once the budget is
          used up, further writes need approval (allow=False, requires_approval=True). The budget
          is the safety rail: an autonomous agent stuck in a loop can send two messages, not two
          thousand.
    """
    if tool_kind == "read":
        return GateDecision(
            allow=True,
            simulate=False,
            requires_approval=False,
            reason="Read tools are always allowed."
        )

    if level == "shadow":
        return GateDecision(
            allow=True,
            simulate=True,
            requires_approval=False,
            reason="Shadow mode: writes are allowed but simulated."
        )

    if level == "supervised":
        return GateDecision(
            allow=False,
            simulate=False,
            requires_approval=True,
            reason="Supervised mode: writes require human approval."
        )

    if level == "autonomous":
        if writes_so_far < max_auto_writes:
            return GateDecision(
                allow=True,
                simulate=False,
                requires_approval=False,
                reason=f"Autonomous mode: write allowed within budget ({writes_so_far}/{max_auto_writes})."
            )
        else:
            return GateDecision(
                allow=False,
                simulate=False,
                requires_approval=True,
                reason=f"Autonomous mode: write budget exhausted ({writes_so_far}/{max_auto_writes})."
            )

    # Fallback for safety, though AutonomyLevel is a Literal
    return GateDecision(allow=False, requires_approval=True, reason="Unknown autonomy level.")
