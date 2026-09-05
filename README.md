# Agent Runner Lite — Intern Take-Home

Thanks for taking the time on this. You'll build a small **governed agent runner**: a service that
drives an AI agent through a tool-use loop, decides what the agent is allowed to do on its own, and
then checks that it actually did what was asked — and nothing more.

The full brief — the six tasks, what we look for, and the ground rules — is in **`BRIEF.md`**.
**Read that first.** This file is just how to run things, plus a map of the code, and it's where you
write up your work when you're done.

## Run it

```bash
python -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -r requirements.txt

pytest -q                                             # the example tests pass on a fresh checkout
uvicorn app.main:app --reload                         # http://127.0.0.1:8000/docs
```

Requires **Python 3.11+**. No API keys, no network, no external services — the language model is a
script (`app/seed.py`), so everything is deterministic and offline.

On a fresh checkout the app imports and `pytest` is green, but the six functions you're implementing
raise `NotImplementedError` (and `POST /runs` returns a 501). That's expected. Search the project for
`TODO(candidate)` to find them — there are six, numbered by task.

Nothing is persisted. Restart the server and your tasks and runs are gone. That's fine, don't work
around it.

## Where things are

```
app/
  models.py          the whole data contract — READ THIS FIRST, it's the map
  config.py          settings, all overridable by env var
  seed.py            toy contacts + 11 scripted model conversations
  store.py           two dicts standing in for a database
  model_client.py    TASK 4a — complete_with_retry     (mock model provided)
  tools.py           TASK 4b — send_message            (read tools + update_contact provided)
  autonomy.py        TASK 1  — evaluate_gate
  verifier.py        TASK 2  — verify
  agent.py           TASK 3  — run_agent               (five helpers provided)
  api.py             TASK 5  — start_run               (three other routes provided)
  main.py            the FastAPI app
tests/
  helpers.py         make_run() — builds an isolated run in one line
  conftest.py        store reset + a `client` fixture for HTTP tests
  test_example.py    four example tests showing the shapes you'll want
```

## A suggested first hour

If you're not sure where to start:

1. `pip install -r requirements.txt && pytest -q`. Green? Good.
2. Read **`app/models.py`** top to bottom. It's commented and it's the whole data model — most of
   the "what shape do I return?" questions are answered there.
3. Read **`app/seed.py`** to see what the mock model does. This is the trick that makes the whole
   thing testable, and it's worth understanding before anything else.
4. Open **`app/autonomy.py`** (Task 1). Write the tests for it first — `test_example.py` has a
   `parametrize` example to copy. Watch them fail, then make them pass.
5. Then `app/verifier.py` (Task 2), same way.

By then you'll have the shape of the codebase and two of the six tasks done.

## Useful to know

- **The scenarios in `app/seed.py` are your test fixtures.** There's one for each path you need to
  handle: `send_followup` (the happy path), `unknown_tool` (a hallucinated tool name),
  `tool_error` (a tool that fails), `three_writes` (the autonomy budget), `never_finishes` (the
  `max_steps` cap), `flaky_provider` (throttled then fine), `bad_credentials` (fatal, don't retry),
  `bad_json_then_good` and `always_bad_json` (malformed model output). Read the comments there.
- **`tests/helpers.py::make_run`** gives you a Run and its dependencies in one line, isolated. Use it
  for every loop test.
- **Everything is synchronous.** Plain `def`, `time.sleep`, no `await` anywhere. If you find
  yourself reaching for `asyncio`, you've gone off the path.
- **Settings are injected, not global.** Your functions take `settings`, so a test can say "budget
  of 1, retry twice" without touching the environment:
  `make_run(script, settings=replace(SETTINGS, max_auto_writes=1))`.
- Once Task 5 is done, `http://127.0.0.1:8000/docs` gives you a UI to create a task and start a run
  without writing any curl. Good for a sanity check that pytest can't give you.

---

# Your write-up

### What's working

All six tasks are complete: the governance gate (`autonomy.py`), the verifier (`verifier.py`),
the agent loop (`agent.py`), retry + idempotency (`model_client.py`, `tools.py`), the start-run
endpoint (`api.py`), and the test suite (32 tests, all passing). Nothing is stubbed or
half-finished — no `TODO(candidate)` markers remain.

### Design decisions

- **The loop treats almost nothing as fatal.** An unknown tool, a failing tool call, and a
  rejected reviewer approval all become an observation fed back to the model, not an exception —
  only `max_steps` being exhausted or an unhandled exception (e.g. a `FatalError` from the model
  client) ends a run early, and even those resolve to `status="failed"` rather than crashing the
  request.
- **The gate always runs before execution, including on the approved path.** When a write requires
  approval and the reviewer approves it, execution falls through to the same `_execute` call used
  for ungated writes, rather than being handled as a separate branch — this keeps there being only
  one code path that actually performs a tool call.
- **Idempotency keys are derived from `run.id` + step count** (`f"{run.id}:{len(run.steps)}"`),
  generated once per logical send in `_execute`, so a retried call reuses the same key rather than
  minting a new one.
- **The verifier does one-to-one matching**, not "does at least one effect match": each real effect
  can only satisfy one expected effect, tracked via a spent-index set, so two identical expectations
  with only one matching effect correctly produce 1 matched + 1 missing rather than 2 matched.
- **Each run gets its own `Workspace` and tool registry** in `start_run`, so concurrent runs can't
  leak state into each other.

### Testing approach

Tests were written before the implementation for all six tasks, following the brief's suggested
TDD flow — write the test, run it, watch it fail with `NotImplementedError`, then implement.
Worth noting on the commit history: for Task 1, Task 3, and Task 5 the test-first and
implementation commits are split cleanly; for Task 2 and Task 4 they ended up in a single combined
commit even though the tests were still written and confirmed failing first. That's a commit
hygiene gap on my part, not a process one.

32 tests total, covering: the gate's full decision table including the exact budget boundary; the
verifier's five outcomes (pass, missing, unexpected, simulated-treated-identically, and the
double-match case); the agent loop across all seven scenario types in `seed.py` (no tools, a
successful autonomous write, the same write under shadow mode, an unknown tool, the budget being
hit, a run that never finishes, and a fatal provider error); retry behavior for both throttled and
fatal errors, asserting on call counts rather than just the outcome; idempotency, asserting on
workspace state rather than return values; and one HTTP-level test through the `/runs` endpoint.

I did not add tests beyond what the brief's suggested list covers — no exhaustive edge-case
sweep, per the brief's note that 8-12 meaningful tests beat 30 that don't catch real bugs.

### What was hardest

Two things, honestly. First, getting my AI coding setup working at all — I lost real time to a
tooling issue where my terminal session wasn't actually executing commands (it was routing
everything through a chat-only panel instead of a real shell), which meant early prompts were
getting misinterpreted instead of acted on. Once I found an actual terminal, it worked as expected. And I also had a network issue in my region so I was a bit slowed down by it.

Second, and more substantively: understanding the codebase before writing anything. The brief
warns this is ~70% reading, and that was accurate — working through `models.py`, the five provided
agent-loop helpers, and how the scripted `MockModelClient` and `seed.py` scenarios tie into the
tests took longer than any single task's implementation.

One specific thing worth calling out from reading the verifier closely: without the `spent_indices`
tracking, `verify()` would double-count a single real effect against two identical expectations —
check the first expected effect, find `run.effects[0]`, mark it matched; check the second identical
expectation, scan again, find the same `run.effects[0]` still unmarked, match it a second time; end
up with everything "matched" and `passed=True` even though the agent only actually did one of the
two things it was supposed to. That's the false positive rule 2 in the docstring exists to prevent.

### What I'd do next

With more time I'd look at the optional extras: a per-tool override on the gate (so
`send_message` could require approval even under `autonomous`), and a summary line on `Verdict`
naming which specific expectation went missing, since that seems like the most useful of the three
suggested extras for actually debugging a failed run. I'd also add structured logging of each step
with the run id as a correlation id, which would help in reading `run.steps` as an audit trail at
a glance rather than reconstructing it from the raw list.

### Time spent

Roughly 6-7 hours.