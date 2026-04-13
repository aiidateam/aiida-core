---
name: writing-tests
description: Use when writing new pytest tests, fixtures, or regression tests for aiida-core. Covers the preference for real objects over mocks, `presto` marker semantics, assertion strength, parametrization, and fixture reuse.
---

# Writing tests for aiida-core

Tests live under `tests/` and mirror the source layout in `src/aiida/`.
Reusable fixtures live in `tests/conftest.py` and per-subtree `conftest.py` files.

## Philosophy

- **Prefer real objects over mocks.** Use fixtures to create real nodes, processes, computers, etc.
  Mocks should only be used for genuinely external dependencies (network, SSH), cases where setup would be prohibitively complex, or when you need to force an exception that would not otherwise appear naturally.
- **Don't chase coverage with shallow tests.** A test that mocks everything tests nothing.
- **Test the contract, not the implementation.** Assert observable outcomes, not internal method calls.
- **Make assertions as strong as possible.** `assert result == expected_value`, not `assert result is not None`.
  Check exact values, types, and lengths.
- **Regression tests for bugs.** First write a test that reproduces the bug, then fix the code.
- **Test edge cases and failure paths.** Don't just test the happy path. Test boundary values, empty inputs, invalid arguments, and expected exceptions.
- **One behavior per test.** Each test must be independent, deterministic, and must not test framework behavior (Python, SQLAlchemy, Click).

## Marker conventions

- `@pytest.mark.presto` &mdash; runs against `SqliteTempBackend` (in-memory, no PostgreSQL / RabbitMQ).
  Prefer `presto`-compatible tests where possible: they are much faster and runnable in any environment.
- `@pytest.mark.requires_rmq` &mdash; requires a running RabbitMQ instance.
- `@pytest.mark.requires_psql` &mdash; requires a running PostgreSQL instance.
- `@pytest.mark.nightly` &mdash; long-running tests, only executed in nightly CI.
- Transport tests require passwordless SSH to localhost.

## Parametrization

Use `pytest.mark.parametrize` instead of duplicating test bodies:

```python
import pytest

@pytest.mark.parametrize('value,expected', [
    (1, 2),
    (2, 4),
    (3, 6),
])
def test_double(value, expected):
    assert double(value) == expected
```

## Fixtures

Check `tests/conftest.py` before writing ad-hoc setup.
If you find yourself reinventing a fixture, it probably already exists.

## Running the tests

See the `running-tests-and-tooling` skill for the full `uv run pytest` cheatsheet.
