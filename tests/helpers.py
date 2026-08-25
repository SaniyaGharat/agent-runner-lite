"""Test helpers. PROVIDED IN FULL — `make_run` will save you a lot of typing.

Read this before you write your first test for the agent loop.
"""

from __future__ import annotations

from typing import Union

from app.agent import AgentDeps
from app.config import SETTINGS, Settings
from app.model_client import MockModelClient
from app.models import AutonomyLevel, ExpectedEffect, Run, Task
from app.seed import CONTACTS
from app.store import Store
from app.tools import Workspace, build_registry


def make_run(
    script: list[Union[str, Exception]],
    *,
    autonomy: AutonomyLevel = "autonomous",
    expected: list[ExpectedEffect] | None = None,
    goal: str = "do the thing",
    reviewer_approves: bool = True,
    settings: Settings = SETTINGS,
) -> tuple[Run, AgentDeps]:
    """Build an isolated Run and its AgentDeps, backed by a fresh Store and Workspace.

    Everything is per-call, so tests can't contaminate each other and there's nothing to reset.

        from app.seed import SCENARIOS
        from tests.helpers import make_run

        def test_shadow_does_not_really_send():
            run, deps = make_run(SCENARIOS["send_followup"], autonomy="shadow")
            run_agent(run, deps)
            assert run.status == "completed"
            assert run.effects[0].simulated is True
            assert deps.workspace.messages == []   # nothing actually happened

    Pass `settings=` to change behaviour for one test — e.g. a tighter write budget:

        from dataclasses import replace
        run, deps = make_run(script, settings=replace(SETTINGS, max_auto_writes=1))

    `script` is the list of replies the mock model will give, in order. `app/seed.py` has ready-made
    ones in `SCENARIOS`, or write your own inline — a string is returned to the agent, an Exception
    instance is raised by the model.
    """
    store = Store()
    task = Task(
        id="t_test",
        goal=goal,
        scenario="test",
        autonomy=autonomy,
        expected_effects=expected or [],
        reviewer_approves=reviewer_approves,
    )
    store.add_task(task)

    run = Run(id="r_test", task_id=task.id, autonomy=autonomy)
    store.add_run(run)

    ws = Workspace(CONTACTS)
    deps = AgentDeps(
        model=MockModelClient(script),
        workspace=ws,
        registry=build_registry(ws),
        store=store,
        settings=settings,
    )
    return run, deps
