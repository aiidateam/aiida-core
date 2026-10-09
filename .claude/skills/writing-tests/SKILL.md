---
name: writing-tests
description: Use for pytest tests, fixtures, and regression tests.
---

# Writing tests

## Layout

* Mirror `src/aiida/` in `tests/`; new test modules require a corresponding source module/package.
* Place regression and cross-module tests with the source behavior they verify; no unmatched bug/issue/feature modules. For genuinely cross-module coverage, place with the primary asserting package and name the collaborators in the test module docstring.
* Reuse fixtures from `tests/conftest.py` and subtree `conftest.py` before adding setup.

## Design

* Real collaborators; mocks only for external dependencies, prohibitive setup, or unreachable exception paths.
* Observable contracts; exact values, types, lengths.
* Regressions: run the reproducer before the fix.
* Boundaries, empty inputs, invalid arguments, failures.
* Independent, deterministic tests; one behavior each.
* No shallow coverage or tests of Python, SQLAlchemy, or Click behavior.
* Parametrize repeated cases; use `pytest.param(..., id='name')` for large parametrizations:

```python
import pytest

@pytest.mark.parametrize('value,expected', [(1, 2), (2, 4), (3, 6)])
def test_double(value, expected):
    assert double(value) == expected
```

## Markers (`@pytest.mark.<name>`)

* `presto`: prefer where possible; no external services; SQLite/ZeroMQ fixtures.
* `requires_rmq`: RabbitMQ; `requires_psql`: PostgreSQL.
* `nightly`: nightly CI only.
* Transport tests require passwordless SSH to localhost.

Commands and infrastructure: see `running-tests`.
