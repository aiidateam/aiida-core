---
name: deprecating-api
description: Use when deprecating public Python APIs or `verdi` commands.
---

# Deprecating API

* API boundary and compatibility: `AGENTS.md`.
* Deprecate public API before removal; preserve older data through migrations.

## Python

`warn_deprecation` (`src/aiida/common/warnings.py`) uses `stacklevel=2` and configured warning visibility.
Record replacement and removal major version:

```python
from aiida.common.warnings import warn_deprecation

def old_function(x):
    """Perform the operation.

    .. deprecated:: 2.7
       Use :func:`new_function` instead. Removal in 3.0.
    """
    warn_deprecation('`old_function` is deprecated; use `new_function`.', version=3)
    return new_function(x)
```

## CLI

Use the command's `deprecated` argument; `deprecated_command` is deprecated:

```python
@verdi_group.command('old-command', deprecated='Use `verdi new-command` instead.')
def old_command():
    ...
```

## Timeline

* Minor release: warnings, docstrings, user docs.
* Next major: removal.
* `AIIDA_WARN_v3=1`: pending v3 warnings.
