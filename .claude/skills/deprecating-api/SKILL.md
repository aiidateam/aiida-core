---
name: deprecating-api
description: Use when deprecating a public Python API or `verdi` CLI command in aiida-core.
---

# Deprecating API in aiida-core

Public API is anything importable from a second-level package (`from aiida.orm import ...`, `from aiida.engine import ...`).
Public API must go through a deprecation cycle before removal.
Data created with older AiiDA versions is guaranteed to work with newer versions (database migrations are applied automatically), so backwards compatibility matters.

## Python API

Use the `warn_deprecation` helper, which handles `stacklevel=2` and respects the user's deprecation-visibility config:

```python
from aiida.common.warnings import warn_deprecation

def old_function(x):
    warn_deprecation('`old_function` is deprecated, use `new_function` instead.', version=3)
    return new_function(x)
```

Add a `.. deprecated::` note to the docstring with replacement guidance:

```python
def old_function(x):
    """Do the thing.

    .. deprecated:: 2.7
       Use :func:`new_function` instead. Will be removed in 3.0.
    """
```

## CLI commands

Use `@decorators.deprecated_command()` from `aiida.cmdline.utils.decorators`:

```python
from aiida.cmdline.utils import decorators

@verdi_group.command('old-command')
@decorators.deprecated_command('Use `verdi new-command` instead.')
def old_command():
    ...
```

## Removal timeline

- Minor release: add the deprecation warning, update docstrings and user-facing docs.
- Next major release: remove the deprecated API.
- Users can surface all pending deprecation warnings by setting `AIIDA_WARN_v3=1`.

## Relevant source

- Warning classes: `src/aiida/common/warnings.py`
- CLI deprecation decorator: `src/aiida/cmdline/utils/decorators.py`
