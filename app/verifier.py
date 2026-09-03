"""Behaviour-equivalence checking: did the agent do what it was supposed to, and nothing else?

An agent that finishes and says "done!" has told you nothing. The model's own summary of its work
is not evidence. So after every run we compare the side effects the task *expected* against the
effects that *actually happened*, and that diff is the verdict.

This is the part that makes shadow mode valuable. Effects recorded in shadow mode are simulated,
but the diff works exactly the same on them — so you can prove an agent would have behaved
correctly before you ever let it touch production.

TASK 2: verify.
"""

from __future__ import annotations

from app.models import Run, Task, Verdict


def verify(task: Task, run: Run) -> Verdict:
    """TASK 2 — diff what was expected against what happened.

    The rules:
      1. An ExpectedEffect is MATCHED by an actual Effect when the `tool` names are equal AND
         every key/value in the expected `match` appears in the actual `args`. It's a SUBSET
         check, not an equality check.
      2. Each actual effect can only be used once.
      3. Any actual effect that no expectation claimed goes in `unexpected`.
      4. passed = there is nothing in `missing` AND nothing in `unexpected`.
      5. Set `mode` to the run's autonomy level, and `detail` to a short summary.
      6. Treat simulated effects exactly like real ones.
    """
    matched = []
    missing = []

    # Track which actual effects have been matched
    spent_indices = set()

    for expected in task.expected_effects:
        found_match = False
        for i, effect in enumerate(run.effects):
            if i in spent_indices:
                continue

            # Rule 1: Tool names must match AND match dict must be a subset of args
            if effect.tool == expected.tool:
                # Subset check: every item in match must be in args
                is_subset = all(
                    effect.args.get(k) == v for k, v in expected.match.items()
                )
                if is_subset:
                    matched.append(expected)
                    spent_indices.add(i)
                    found_match = True
                    break

        if not found_match:
            missing.append(expected)

    # Rule 3: Unclaimed effects are unexpected
    unexpected = [
        effect for i, effect in enumerate(run.effects)
        if i not in spent_indices
    ]

    # Rule 4: passed = no missing AND no unexpected
    passed = (len(missing) == 0 and len(unexpected) == 0)

    # Rule 5: detail and mode
    detail = f"{len(matched)} matched, {len(missing)} missing, {len(unexpected)} unexpected"

    return Verdict(
        passed=passed,
        matched=matched,
        missing=missing,
        unexpected=unexpected,
        mode=run.autonomy,
        detail=detail
    )
