# Coding style

If you follow the instructions to {doc}`set up your development environment <development_environment>`, the AiiDA coding style is largely **enforced automatically using pre-commit hooks** (configured in `.pre-commit-config.yaml`).
Run `uv run pre-commit run` to check staged files, or `uv run pre-commit run --all-files` to check everything.

This document mainly acts as a reference.

## Pre-commit hooks overview

The following hooks run automatically on staged files (see `.pre-commit-config.yaml` for the full configuration):

**Formatting and linting** ([ruff](https://docs.astral.sh/ruff/)):

- `ruff format` — auto-formats code (single quotes, PEP 8 compliance)
- `ruff` — linting with rule sets: `E`/`W` (pycodestyle), `F` (pyflakes), `I` (isort), `N` (pep8-naming), `PLC`/`PLE`/`PLR`/`PLW` (pylint), `RUF` (ruff-specific), `FLY` (f-string enforcement), `NPY201` (NumPy 2.0 compatibility)

**Type checking:**

- `mypy` — static type checking (many files are currently excluded; see below)

**File checks:**

- `check-merge-conflict`, `check-added-large-files`, `check-yaml` — basic file validation
- `double-quote-string-fixer` — converts double quotes to single quotes
- `end-of-file-fixer`, `trailing-whitespace`, `mixed-line-ending` — whitespace normalization
- `fix-encoding-pragma` — removes outdated `# -*- coding: utf-8 -*-` lines

**Dependency and project maintenance:**

- `uv-lock` — validates lockfile consistency
- `pretty-format-toml`, `pretty-format-yaml` — auto-format TOML/YAML files
- `nbstripout` — strips output from Jupyter notebooks
- `imports` — auto-generates `__all__` imports for `src/aiida/`
- `generate-conda-environment`, `validate-conda-environment` — keeps `environment.yml` in sync with `pyproject.toml`
- `verdi-autodocs` — auto-generates verdi CLI documentation

## General rules

- Code should conform to [PEP 8](https://peps.python.org/pep-0008/).
- When compatible, follow the [Google Python Style Guide](https://github.com/google/styleguide/blob/gh-pages/pyguide.md).

## AiiDA-specific conventions

### File operations

- When opening a general file for reading or writing, use [`open()`](https://docs.python.org/3/library/functions.html#open) as a context manager with UTF-8 encoding for formatted files, e.g., `with open(path, 'w', encoding='utf8') as handle:`.
- When opening a file from the AiiDA repository, use `aiida.common.folders.Folder.open()`.

### Source file headers

Each source file should start with the following copyright header:

```python
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
```

## Python style

### F-strings

Prefer f-strings over `.format()` or `%` formatting:

```python
value = 'test'
f'Variable {value}'

a = 1
b = 2
f'{a} + {b} = {a + b}'  # '1 + 2 = 3'
```

F-strings are easier to read, save characters, and are more efficient.
One exception: when you have a string with many placeholders, it is acceptable to use `.format(**dictionary)`.

**Logging calls** are another exception — use `%` formatting so string interpolation is deferred until the message is actually emitted:

```python
# Preferred — interpolation is skipped if the log level is disabled
logger.info('Processing node %s', node.pk)

# Not ideal — string is always constructed, regardless of log level
logger.info(f'Processing node {node.pk}')
```

### Pathlib

Prefer [`pathlib`](https://docs.python.org/3/library/pathlib.html) over `os.path` for file and folder manipulation.
This is not currently enforced; legacy `os.path` usage exists throughout the codebase.
Refer to the official documentation for a [translation table between os and pathlib](https://docs.python.org/3/library/pathlib.html#corresponding-tools).

### Type hinting

Add [type hints](https://docs.python.org/3/library/typing.html) to new code and update existing code when possible.
Type hints allow static type checkers to validate the code and IDEs to provide improved auto-completion.
They also make the code easier to read and serve as verified documentation of the API contract.

The pre-commit hooks include [mypy](https://mypy-lang.org/) for type checking.
CI runs the same pre-commit hooks, so it catches anything missed locally.

:::{note}
`mypy` runs in pre-commit/CI but various legacy files are currently excluded (see the `exclude` list for the `mypy` hook in `.pre-commit-config.yaml`).
New files are checked by default.
:::
