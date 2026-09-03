from __future__ import annotations

import pytest

from app.models import ExpectedEffect, Effect, Task, Run, AutonomyLevel
from app.verifier import verify

def test_verify_perfect_match():
    # Case 1: every expected effect happened, nothing else
    task = Task(
        id="t1", goal="do it", scenario="s1", autonomy="autonomous",
        expected_effects=[
            ExpectedEffect(tool="send_message", match={"contact_id": "c_1"}),
            ExpectedEffect(tool="update_record", match={"record_id": "r_1"}),
        ],
        reviewer_approves=True
    )
    run = Run(
        id="r1", task_id="t1", autonomy="autonomous",
        effects=[
            Effect(tool="send_message", args={"contact_id": "c_1", "body": "hi"}),
            Effect(tool="update_record", args={"record_id": "r_1", "value": "ok"}),
        ]
    )
    verdict = verify(task, run)
    assert verdict.passed is True
    assert len(verdict.matched) == 2
    assert len(verdict.missing) == 0
    assert len(verdict.unexpected) == 0

def test_verify_missing_effect():
    # Case 2: an expected effect never happened
    task = Task(
        id="t2", goal="do it", scenario="s1", autonomy="autonomous",
        expected_effects=[
            ExpectedEffect(tool="send_message", match={"contact_id": "c_1"}),
            ExpectedEffect(tool="send_message", match={"contact_id": "c_2"}),
        ],
        reviewer_approves=True
    )
    run = Run(
        id="r2", task_id="t2", autonomy="autonomous",
        effects=[
            Effect(tool="send_message", args={"contact_id": "c_1", "body": "hi"}),
        ]
    )
    verdict = verify(task, run)
    assert verdict.passed is False
    assert len(verdict.matched) == 1
    assert len(verdict.missing) == 1
    assert verdict.missing[0].match == {"contact_id": "c_2"}

def test_verify_unexpected_effect():
    # Case 3: the agent did something nobody asked for
    task = Task(
        id="t3", goal="do it", scenario="s1", autonomy="autonomous",
        expected_effects=[
            ExpectedEffect(tool="send_message", match={"contact_id": "c_1"}),
        ],
        reviewer_approves=True
    )
    run = Run(
        id="r3", task_id="t3", autonomy="autonomous",
        effects=[
            Effect(tool="send_message", args={"contact_id": "c_1", "body": "hi"}),
            Effect(tool="send_message", args={"contact_id": "c_bad", "body": "bye"}),
        ]
    )
    verdict = verify(task, run)
    assert verdict.passed is False
    assert len(verdict.unexpected) == 1
    assert verdict.unexpected[0].tool == "send_message"
    assert verdict.unexpected[0].args["contact_id"] == "c_bad"

def test_verify_simulated_effects():
    # Case 4: simulated effects treated identically to real ones
    task = Task(
        id="t4", goal="do it", scenario="s1", autonomy="shadow",
        expected_effects=[
            ExpectedEffect(tool="send_message", match={"contact_id": "c_1"}),
        ],
        reviewer_approves=True
    )
    run = Run(
        id="r4", task_id="t4", autonomy="shadow",
        effects=[
            Effect(tool="send_message", args={"contact_id": "c_1", "body": "hi"}, simulated=True),
        ]
    )
    verdict = verify(task, run)
    assert verdict.passed is True
    assert len(verdict.matched) == 1

def test_verify_one_to_one_matching():
    # Case 5: two identical ExpectedEffects but only one matching real Effect
    # Rule 2: Each actual effect can only be used once.
    task = Task(
        id="t5", goal="do it", scenario="s1", autonomy="autonomous",
        expected_effects=[
            ExpectedEffect(tool="send_message", match={"contact_id": "c_1"}),
            ExpectedEffect(tool="send_message", match={"contact_id": "c_1"}),
        ],
        reviewer_approves=True
    )
    run = Run(
        id="r5", task_id="t5", autonomy="autonomous",
        effects=[
            Effect(tool="send_message", args={"contact_id": "c_1", "body": "hi"}),
        ]
    )
    verdict = verify(task, run)
    assert verdict.passed is False
    assert len(verdict.matched) == 1
    assert len(verdict.missing) == 1
