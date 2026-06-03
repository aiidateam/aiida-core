---
name: adding-a-cli-command
description: Use when adding a new `verdi` subcommand in `src/aiida/cmdline/`.
---

# Adding a new verdi CLI command

## Steps

1. Create the command under `src/aiida/cmdline/commands/`, typically as part of an existing `cmd_*.py` file (`cmd_process.py`, `cmd_calcjob.py`, `cmd_devel.py`, etc.).
2. Use Click decorators plus AiiDA's custom decorators from `aiida.cmdline.utils.decorators` (e.g. `@decorators.with_dbenv()` for commands that need the storage backend loaded).
3. Register the command in the appropriate command group (usually via `@<group>.command()`).
4. Add tests in `tests/cmdline/commands/`.

## Import-time constraint (CRITICAL)

`verdi` must load quickly even for `verdi --help`, so `aiida.*` imports inside `src/aiida/cmdline/` **must be deferred to inside the function body**, not placed at module top level:

```python
# WRONG - will break CI via verdi devel check-load-time
from aiida.orm import QueryBuilder

@cmd_something.command()
def my_command():
    qb = QueryBuilder()
    ...

# RIGHT
@cmd_something.command()
def my_command():
    from aiida.orm import QueryBuilder
    qb = QueryBuilder()
    ...
```

CI enforces this via `verdi devel check-load-time`, which fails if any module outside `aiida.brokers`, `aiida.cmdline`, `aiida.common`, `aiida.manage`, `aiida.plugins`, or `aiida.restapi` is imported at startup.

At the top level of a `cmd_*.py` file, only `click`, standard library, and the whitelisted `aiida.*` submodules listed above may be imported.

## Reusable arguments and options

AiiDA provides a library of reusable, ALL_CAPS Click parameters in `src/aiida/cmdline/params/`: `arguments` (positional) and `options` (flags).
Always check for an existing one before defining ad-hoc `click.argument()` / `click.option()` calls.

```python
from aiida.cmdline.params import arguments, options

@verdi_process.command('show')
@arguments.PROCESSES()
@options.RAW()
def process_show(processes, raw):
    ...
```

Both are wrapped in `OverridableArgument` / `OverridableOption` classes that store defaults but allow per-command customization via `.clone()`.

## Relevant source

- Decorators: `src/aiida/cmdline/utils/decorators.py`
- Existing commands: `src/aiida/cmdline/commands/cmd_*.py`
- Reusable arguments: `src/aiida/cmdline/params/arguments/main.py`
- Reusable options: `src/aiida/cmdline/params/options/main.py`
- Custom option types: `src/aiida/cmdline/params/options/{callable,conditional,interactive,multivalue,config}.py`
- Parameter types (ParamType subclasses): `src/aiida/cmdline/params/types/`
- Load-time check implementation: `src/aiida/cmdline/commands/cmd_devel.py` (`check-load-time`)
