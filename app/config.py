"""Runtime settings. PROVIDED IN FULL.

Every knob is a field with a default, and every default is overridable from an environment
variable. That's deliberate: the same code runs in a test (tiny numbers, fast) and in production
(bigger numbers, patient) without an `if TESTING:` anywhere.

Your functions take `settings` as an argument rather than reaching for the global. That's what
lets a test say "retry twice, sleep for a millisecond" without touching the environment.
"""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    # --- agent loop ---
    # Hard cap on turns. Without this, a model that never says "final" loops forever.
    max_steps: int = 10

    # --- model calls ---
    model_max_retries: int = 3  # how many times to retry a throttled call
    model_backoff_base_seconds: float = 0.01  # tiny so tests are fast; seconds in production

    # --- structured output ---
    parse_max_retries: int = 1  # re-prompts allowed when the model's JSON is malformed

    # --- governance ---
    # Under `autonomous`, this many writes go through unchallenged. After that the run has to
    # stop and ask. A budget like this is what stops an autonomous agent running away.
    max_auto_writes: int = 2

    @classmethod
    def from_env(cls) -> "Settings":
        def _int(name: str, default: int) -> int:
            return int(os.environ.get(name, default))

        def _float(name: str, default: float) -> float:
            return float(os.environ.get(name, default))

        return cls(
            max_steps=_int("AGENT_MAX_STEPS", cls.max_steps),
            model_max_retries=_int("MODEL_MAX_RETRIES", cls.model_max_retries),
            model_backoff_base_seconds=_float(
                "MODEL_BACKOFF_BASE_SECONDS", cls.model_backoff_base_seconds
            ),
            parse_max_retries=_int("PARSE_MAX_RETRIES", cls.parse_max_retries),
            max_auto_writes=_int("MAX_AUTO_WRITES", cls.max_auto_writes),
        )


SETTINGS = Settings.from_env()
