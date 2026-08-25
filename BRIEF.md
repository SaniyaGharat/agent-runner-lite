# Agent Runner Lite — Product Engineer Intern (Agent Systems) Take-Home

**Level:** Internship / early career · **Time budget:** ~4–6 focused hours (you have **3 calendar days**)
**Stack:** **Python 3.11+**, **FastAPI**, **pytest**. Synchronous — no `asyncio`. No frontend.

A **starter scaffold** is provided. It imports, runs, and passes its example tests on a fresh
checkout — you won't spend your evening fighting setup. The parts you build are marked
`TODO(candidate)`, and each one has a worked example of the same idea nearby. See `README.md` for
how to run it.

There are no API keys, no network calls and no costs. The language model is a **script** — a list of
replies it will give, in order — so every run behaves identically and you can develop offline.

If you finish in three hours, good. If you run out of time, also fine: submit what works and say in
the README what you'd have done next. **Four tasks done carefully beats six done in a panic.**

---

## 1. What you're building

A small **governed agent runner**: a backend service that drives an AI agent through a
**tool-use loop** to get a job done, under **governance rules** that decide what the agent is
allowed to do on its own, and which then **verifies** that the agent actually did what was asked —
and nothing more.

An agent, stripped of the hype, is a loop:

```
ask the model what to do  →  do it  →  tell the model what happened  →  repeat
```

…until the model says it's finished. The interesting engineering isn't the loop itself, it's
everything wrapped around it:

- **Governance.** The agent can send messages and edit records. Which of those is it trusted to do
  unsupervised? A run is in one of three stages — `shadow` (simulate everything, change nothing),
  `supervised` (ask a human before every write), `autonomous` (go ahead, up to a budget).
- **Verification.** "The agent said it was done" is not evidence. We compare the side effects the
  task *expected* against the effects that *actually happened*, and that diff is the verdict.
- **Resilience.** Model providers rate-limit you. Calls get repeated. Sending the same message
  twice is a real problem with real consequences.

The domain the agent works in — a handful of CRM-ish contacts — is deliberately trivial. Nobody is
assessing your contact management. The machinery around the agent is the point.

---

## 2. Why this exercise

The team builds agents as a product: loops that call models and tools, running under governed
autonomy with a human in the loop, shipped with verification as a first-class deliverable. This is
that, shrunk to something you can finish in an afternoon. Every task maps to something the team
does for real.

It's also, deliberately, a lot of reading. Roughly 70% of this scaffold is provided and commented,
and working out how someone else's code fits together before adding to it is most of what the first
few months of the job looks like.

---

## 3. What's provided vs. what you build

Every file says at the top which it is.

**Provided — read it, use it, don't rebuild it:**

- FastAPI app and three of the four routes (`app/api.py`, `app/main.py`).
- The whole data contract (`app/models.py`) — read this first, it's the map.
- `ModelClient` protocol and the scripted `MockModelClient` (`app/model_client.py`).
- The `Store` (`app/store.py`), the toy data and eleven ready-made model scripts (`app/seed.py`).
- All the read tools plus `update_contact` as a worked write tool (`app/tools.py`).
- The agent-loop helpers — `_decide`, `_emit`, `_ask_reviewer`, `_execute`, `_observation` — which
  do the fiddly parts of TASK 3 for you.
- `tests/helpers.py::make_run`, which builds an isolated run in one line, and a `client` fixture
  for end-to-end tests.

**You build — six tasks:**

| # | Task | Where | Rough time |
|---|---|---|---|
| 1 | The governance policy | `app/autonomy.py` → `evaluate_gate` | 45 min |
| 2 | Behaviour-equivalence check | `app/verifier.py` → `verify` | 1 hr |
| 3 | The agent loop | `app/agent.py` → `run_agent` | 1.5 hr |
| 4 | Resilience: retry, and an idempotent write | `app/model_client.py`, `app/tools.py` | 45 min |
| 5 | The start-run endpoint | `app/api.py` → `start_run` | 30 min |
| 6 | Tests | `tests/` | 1 hr |

**Do them in that order.** Tasks 1, 2 and 4 are small, self-contained functions that task 3 then
calls — a loop is much easier to debug when the pieces it uses are already tested. Task 5 makes it
all runnable from a browser.

Task 6 isn't really last. Tasks 1 and 2 are pure functions with no setup, which makes them the best
place you'll ever get to practise writing the test first. Do that — details below.

---

## 4. The tasks

The full detail, including hints and the exact rules, is in the `TODO(candidate)` docstring in each
file. This is the summary so you can see the shape of the whole thing.

### Task 1 — The governance policy (`app/autonomy.py`)

One pure function: given the autonomy level, whether the tool reads or writes, and how many writes
have happened already, decide whether this call runs, gets simulated, or has to stop and ask a
human. Reads always pass. `shadow` simulates writes. `supervised` asks every time. `autonomous`
allows writes up to a budget, then asks.

No I/O, four arguments, one returned object — so you can test every branch of it in a few lines.

### Task 2 — Behaviour-equivalence check (`app/verifier.py`)

Diff `task.expected_effects` against `run.effects` and return a pass/fail `Verdict`. Two rules are
easy to get wrong, and both are called out in the docstring: each actual effect may only satisfy
one expectation, and an effect nobody asked for is a **failure**, not a curiosity. An agent that
did its job and also messaged three other people has not passed.

This must behave identically for simulated effects. That identical treatment is exactly what makes
a shadow stage useful: you get a correctness proof with zero real-world impact.

### Task 3 — The agent loop (`app/agent.py`)

The centrepiece. A loop bounded by `max_steps`. Each turn: get a decision from the model → either
finish, or call a tool through the gate → feed the result back as an observation.

The docstring gives you the whole thing as annotated pseudocode, step by step. The theme to hold
onto: **a tool that doesn't exist, a tool that errors, and a reviewer who says no are all normal.**
They become observations and the model gets another turn. Only two things end a run — the model
saying it's finished, or something genuinely unrecoverable. A loop that dies the first time a model
invents a tool name is useless, and real models invent tool names constantly.

### Task 4 — Resilience (`app/model_client.py`, `app/tools.py`)

Two small functions, one idea each.

**(a) `complete_with_retry`.** Some failures are worth retrying and some aren't. Retry
`ThrottleError` (rate limited — try again in a moment) with exponential backoff; raise `FatalError`
(bad API key — it will fail identically forever) immediately. Telling transient from permanent is
the skill.

**(b) `send_message`.** Make it safe to call twice. If an update runs twice you end up in the same
place; if a *send* runs twice the customer gets two emails. The caller passes an idempotency key,
the tool remembers which keys it has handled, and a repeat returns the original result without
sending again.

### Task 5 — The start-run endpoint (`app/api.py`)

Look up the task (404 if it's not there), build the run and its dependencies, call `run_agent`,
return the finished run. Small, and it's what lets you drive your own agent from the interactive
docs at `/docs` instead of only from pytest.

### Task 6 — Tests (`tests/`)

**Tests are a first-class deliverable here, not a box to tick.** The team writes tests before code
and the JD says so; this is where we find out whether that's a habit you're building.

Aim for eight to twelve tests that would genuinely catch a bug. A good spread:

- **the gate** — a table-driven test (`@pytest.mark.parametrize`) over the decision table,
  including the budget boundary;
- **the verifier** — one test per outcome: pass, missing, unexpected;
- **the loop** — completes with no tools; completes with one write and passes verification;
  recovers from an unknown tool; a `shadow` run records a simulated effect and leaves the workspace
  untouched; `never_finishes` ends `failed` instead of hanging;
- **retry** — throttled-twice-then-succeeds (assert `model.calls == 3`), and fatal-not-retried
  (assert `model.calls == 1`);
- **idempotency** — same key twice, then assert `len(ws.messages) == 1`.

Two habits worth picking up now, because they're what separates a test that catches bugs from one
that just goes green:

- **Assert on the world, not the return value.** For idempotency, checking what `send_message`
  returned proves nothing — the bug you're guarding against is the second message *existing*, so
  assert on `ws.messages`. Same for shadow mode: `deps.workspace.messages == []` is the assertion
  that proves nothing really happened.
- **Assert on what should NOT have happened.** `model.calls == 1` after a `FatalError` is what
  proves you didn't retry it. A test that only checks "it raised" passes even if you retried three
  times first.

**Please write the Task 1 and Task 2 tests before those functions.** Run them, watch them fail,
then make them pass. Mention in your README that you did — we look for it in the commit history too.

---

## 5. Out of scope — please don't spend time here

A real model provider or API key. A real database. `asyncio`, background workers, queues, Celery,
Temporal. Streaming or SSE. Auth. Docker or Kubernetes. A frontend. Retries anywhere except the
model call. Any agent framework — LangChain, LlamaIndex, Bedrock AgentCore or similar — because
they hide the loop, the gating and the retries, and implementing those *is* the exercise.

Everything you need is already installed. Adding a dependency is a signal you've misread the task.

---

## 6. What we're looking for

In rough order of weight:

- **Does it work?** Can we start a run and watch the whole thing end to end — loop, gate,
  verdict — with a sensible answer at all three autonomy levels.
- **Does it survive bad news?** Unknown tool, failing tool, rejected approval, a run that never
  finishes, a fatal provider error. None of these should crash the run or hang it.
- **Correct policy and verdict.** The gate's budget boundary is exact. The verifier catches missing
  *and* unexpected effects, and doesn't let one effect satisfy two expectations.
- **Tests that mean something.** Eight small tests that could each fail for a real reason beat
  thirty that can't.
- **Readable Python.** Type hints where they help, small functions, clear names, no dead code or
  leftover `print`s. Would the next person understand this?
- **An audit trail.** After a run, `run.steps` should read like a transcript of what happened and
  why each write was permitted. Governed autonomy is worthless if you can't show your work.
- **Your README.** What you did, what you found hard, what you'd do next. We read it closely.

We are **not** looking for: every edge case, exhaustive tests, clever abstractions, or performance
work. Clean and working beats broad and half-finished.

### If you have time left over

Optional, and only once the six tasks are solid. Note anything you attempt in the README.

- A per-tool override on the gate, so `send_message` can require approval even under `autonomous`.
- A summary line on the `Verdict` naming which specific expectation went missing.
- Structured logging of each step with the run id as a correlation id.
- A test that drives the whole thing over HTTP with the `client` fixture (see `tests/conftest.py`).

---

## 7. Submitting

Send us a **git repository** — a link, or a zip that includes the `.git` folder. We read the commit
history, so please commit as you go rather than in one giant "final" commit. A handful of small
commits with honest messages tells us more about you than a perfect diff does. The scaffold arrives
as a git repo with one commit already, so you can just start committing on top.

It must run with `pip install -r requirements.txt && pytest` on **Python 3.11+** with no extra setup.

Update `README.md` with:

1. **What's working** — which of the six tasks you finished, and anything half-done or knowingly broken.
2. **Design decisions** — how you structured the loop, how you decided what ends a run versus what
   becomes an observation, your idempotency key handling, anything the brief left ambiguous and what
   you assumed.
3. **Your testing approach** — what you chose to test and what you deliberately didn't, and whether
   you wrote the Task 1 and 2 tests first.
4. **What was hardest**, and how you worked it out. We read this closely and it counts. *"I hadn't
   used `@pytest.mark.parametrize` before, so I read the pytest docs and rewrote my four
   near-identical gate tests as one table"* is a genuinely good answer.
5. **What you'd do next** with another day.

### Ground rules — please read this bit

**AI tools are allowed.** Claude, Copilot, ChatGPT — we use them daily and we're not going to
pretend otherwise. The team's whole thesis is that agents handle the repetitive 60–70% so engineers
can own the judgment. But there's a condition, and we mean it:

> **You own every line you submit.** In the follow-up interview we'll open your code, ask why a
> particular piece works the way it does, and ask you to change something live.

Code you can't explain is worse than code you didn't write, because it wastes both our time. If you
use AI to learn something, make sure you actually learned it. If you use it to generate something,
read it until you'd be comfortable defending it. Pasting in something you don't understand is the
one thing that will definitely end the process here.

Worth knowing: this exercise is unusually easy to get a *plausible-looking* wrong answer for. The
gate's budget boundary, the verifier's "one effect can only match one expectation" rule, and
not-retrying a fatal error are all places where generated code tends to look right and be subtly
wrong. Your tests are what catch that — which is rather the point of asking for them.

Other rules:

- Don't add dependencies. Everything you need is installed.
- If a requirement is ambiguous, make a reasonable call, **write it in the README**, and move on.
  Don't get stuck. Deciding under uncertainty and documenting it is the job.
- Stuck on setup rather than on the actual work? Email us. Being blocked for two hours on something
  we could have unblocked in two minutes is not a test of anything.

---

*Questions about the brief? Email [HIRING CONTACT].*

Good luck — we're looking forward to reading it.
