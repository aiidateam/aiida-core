---
name: deprecating-api
description: Use when deprecating a public Python API or `verdi` CLI command in aiida-core. Covers `AiidaDeprecationWarning` with `stacklevel=2`, the `deprecated_command` decorator, docstring notes, and the removal timeline convention.
---

# Deprecating API in aiida-core

Public API is anything importable from a second-level package (`from aiida.orm import ...`, `from aiida.engine import ...`).
Public API must go through a deprecation cycle before removal.

## Python API

Emit `AiidaDeprecationWarning` at the call site with `stacklevel=2` so the warning points at the user's code, not at `aiida-core` itself:

```python
import warnings
from aiida.common.warnings import AiidaDeprecationWarning

def old_function(x):
    msg = '`old_function` is deprecated, use `new_function` instead.'
    warnings.warn(msg, AiidaDeprecationWarning, stacklevel=2)
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
