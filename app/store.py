"""Where tasks and runs live. PROVIDED IN FULL.

Two dictionaries. No database, no ORM, no migrations — state lives in the process and disappears
when you restart the server. That's fine for this exercise and it's deliberate: swapping this for
DynamoDB later is a change to one file, because nothing else knows how storage works.
"""

from __future__ import annotations

from typing import Optional

from app.models import Run, Task


class Store:
    def __init__(self) -> None:
        self.tasks: dict[str, Task] = {}
        self.runs: dict[str, Run] = {}

    # --- tasks ---
    def add_task(self, task: Task) -> None:
        self.tasks[task.id] = task

    def get_task(self, task_id: str) -> Optional[Task]:
        return self.tasks.get(task_id)

    # --- runs ---
    def add_run(self, run: Run) -> None:
        self.runs[run.id] = run

    def get_run(self, run_id: str) -> Optional[Run]:
        return self.runs.get(run_id)


# The single instance the FastAPI app uses. Tests build their own Store instead, so they never
# have to worry about state left behind by another test.
store = Store()
