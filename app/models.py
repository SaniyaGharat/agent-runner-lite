"""The data contract for the whole service.

PROVIDED IN FULL — nothing here needs changing. Read it once, top to bottom, before you start
anything else. Every task you have to do is described in terms of these types, and most of the
questions you'll have ("what shape do I return?") are answered here.

These are Pydantic models. Two things they buy us:
  - FastAPI turns them into request/response validation and the interactive docs at /docs for free;
  - `Model.model_validate_json(text)` parses JSON and raises if it doesn't fit the shape, which is
    how we validate what the language model hands back.
"""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import BaseModel, Field, model_validator

# The three governed-autonomy stages. How much the agent is trusted to do on its own.
AutonomyLevel = Literal["shadow", "supervised", "autonomous"]

# Tools are split into two kinds. Reads are harmless; writes change the world, so they're
# what the governance rules actually care about.
ToolKind = Literal["read", "write"]

IntentType = Literal["tool_use", "final"]
RunStatus = Literal["pending", "running", "completed", "failed"]
StepType = Literal["tool_call", "tool_result", "gate", "final", "error"]


class AgentIntent(BaseModel):
    """What the model must produce on every turn.

    The model replies with JSON text; we parse it into this class. If it doesn't fit — a missing
    field, a tool_use with no tool named — validation raises and the agent re-prompts rather than
    carrying on with nonsense. This is what "structured output" means in practice: you don't trust
    the model's prose, you make it fill in a form.
    """

    intent: IntentType
    thought: str = ""
    tool: Optional[str] = None
    args: dict[str, Any] = Field(default_factory=dict)
    answer: Optional[str] = None

    @model_validator(mode="after")
    def _check_shape(self) -> "AgentIntent":
        if self.intent == "tool_use" and not self.tool:
            raise ValueError("a tool_use intent must name a 'tool'")
        if self.intent == "final" and self.answer is None:
            raise ValueError("a final intent must include an 'answer'")
        return self


class ExpectedEffect(BaseModel):
    """A side effect the task says SHOULD happen. The verifier checks these against reality.

    `match` is a subset of the tool's arguments that must line up. So
        ExpectedEffect(tool="send_message", match={"contact_id": "c_1"})
    means "a send_message must have happened, addressed to c_1" — and doesn't care what the
    message body was.
    """

    tool: str
    match: dict[str, Any] = Field(default_factory=dict)


class Effect(BaseModel):
    """A side effect that actually happened during a run.

    `simulated=True` means shadow mode: the agent decided to do it and we recorded the intent,
    but nothing was really changed. Recording simulated effects is the whole point of a shadow
    stage — you get to check what the agent WOULD have done, for free.
    """

    tool: str
    args: dict[str, Any]
    simulated: bool = False


class TaskSpec(BaseModel):
    """What a caller submits to create a task."""

    goal: str
    # Picks which scripted model conversation to use (see app/seed.py). A real deployment would
    # send a prompt to a real model; scripting it keeps the server and the tests deterministic.
    scenario: str = "default"
    autonomy: AutonomyLevel = "autonomous"
    expected_effects: list[ExpectedEffect] = Field(default_factory=list)
    # Stands in for the human reviewer under `supervised`. In the real product a person clicks
    # approve or reject; here the answer is decided up front so runs and tests stay predictable.
    reviewer_approves: bool = True


class Task(TaskSpec):
    id: str


class Step(BaseModel):
    """One observable thing that happened, in order. The run's audit trail.

    Governed autonomy is only worth anything if you can show afterwards what the agent did and
    why it was allowed to, so every decision gets a Step.
    """

    index: int
    type: StepType
    message: str = ""
    tool: Optional[str] = None
    args: dict[str, Any] = Field(default_factory=dict)
    result: Optional[Any] = None
    ok: bool = True


class Verdict(BaseModel):
    """The behaviour-equivalence result: did the run do what the task expected, and nothing else?"""

    passed: bool
    matched: list[ExpectedEffect] = Field(default_factory=list)
    missing: list[ExpectedEffect] = Field(default_factory=list)
    unexpected: list[Effect] = Field(default_factory=list)
    mode: AutonomyLevel = "autonomous"
    detail: str = ""


class Run(BaseModel):
    """One execution of a task, plus everything that happened during it."""

    id: str
    task_id: str
    autonomy: AutonomyLevel
    status: RunStatus = "pending"
    steps: list[Step] = Field(default_factory=list)
    effects: list[Effect] = Field(default_factory=list)
    verdict: Optional[Verdict] = None
    error: Optional[str] = None


class GateDecision(BaseModel):
    """What the governance policy decided about one tool call.

    Exactly one of these three outcomes should apply:
      allow=True,  simulate=False  → run it for real
      allow=True,  simulate=True   → pretend to run it (shadow mode)
      allow=False, requires_approval=True → stop and ask a human first
    """

    allow: bool
    simulate: bool = False
    requires_approval: bool = False
    reason: str = ""
