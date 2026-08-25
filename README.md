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

Please replace this section before submitting. See `BRIEF.md` §7 for what we're after.

### What's working

<!-- Which of the six tasks are done? Anything half-finished or knowingly broken? -->

### Design decisions

<!-- How did you structure the loop? How did you decide what ends a run versus what becomes an
     observation the model sees? How do you handle the idempotency key? Anything the brief left
     ambiguous, and what you assumed. -->

### Testing approach

<!-- What did you test, and what did you deliberately not test? Did you write the Task 1 and 2
     tests before the implementations? -->

### What was hardest

<!-- Be honest here — we read this part closely and it counts. What confused you, and how did you
     work it out? -->

### What I'd do next

<!-- With another day. -->

### Time spent

<!-- Roughly. There's no wrong answer; it helps us calibrate the exercise. -->
