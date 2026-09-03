Read app/models.py fully first — it's the data contract. Then read the TASK 1 docstring in
app/autonomy.py end to end (don't skip the "suggested tests" section), and look at the
table-driven parametrize example in tests/test_example.py for the style already used in this repo.

Work in two steps. Stop after step 1 and show me your output — do not do step 2 until I say go.

STEP 1: Create tests/test_autonomy.py and write tests for evaluate_gate BEFORE implementing it.
Use @pytest.mark.parametrize, table-driven, and cover every branch in the docstring:
  - a read tool at each of the three autonomy levels → allow=True, simulate=False, requires_approval=False
  - shadow + write → allow=True, simulate=True
  - supervised + write → allow=False, requires_approval=True
  - autonomous + write, writes_so_far=0, max_auto_writes=2 → allowed
  - autonomous + write, writes_so_far=1, max_auto_writes=2 → still allowed
  - autonomous + write, writes_so_far=2, max_auto_writes=2 → allow=False, requires_approval=True
    (the exact boundary — this is the case that's easiest to get off-by-one)
Run `pytest tests/test_autonomy.py -v` and confirm every test fails with NotImplementedError.
Paste the test file and the failure output back to me. Do not touch app/autonomy.py yet.

STEP 2 (only once I reply "go"): implement evaluate_gate in app/autonomy.py so the tests in
step 1 pass, following the policy described in the docstring exactly (reads always pass; shadow
allows+simulates writes; supervised always asks; autonomous allows writes while
writes_so_far < max_auto_writes, then asks). Give `reason` a short human-readable string per
branch. Do not edit tests/test_autonomy.py to make it pass — if a test looks wrong to you, tell
me instead of changing it. Run the full test suite to confirm nothing else broke.

Commit step 1 and step 2 as two separate commits with clear messages.