---
name: adding-a-cli-command
description: Use when adding a `verdi` subcommand in `src/aiida/cmdline/`.
---

# Adding a CLI command

* Commands: `src/aiida/cmdline/commands/cmd_*.py`; reuse existing modules.
* Register with `@<group>.command()` and Click decorators.
* Storage access (commands needing storage): `@decorators.with_dbenv()` from `aiida.cmdline.utils.decorators`.
* Tests: matching module under `tests/cmdline/commands/`.

## Startup imports

Defer heavy imports to function bodies for fast `verdi --help`.
Module-level imports: standard library, `click`, and `aiida.brokers`, `aiida.cmdline`, `aiida.common`, `aiida.manage`, `aiida.plugins`, `aiida.restapi`.
CI checks this with `verdi devel check-load-time` in `src/aiida/cmdline/commands/cmd_devel.py`.

## Reusable parameters

Reuse ALL_CAPS parameters from `aiida.cmdline.params.{arguments,options}` before adding `click.argument()` or `click.option()`.
Pass overrides when calling them; `OverridableOption` also provides `.clone()`.

```python
from aiida.cmdline.params import arguments, options

@verdi_process.command('show')
@arguments.PROCESSES()
@options.RAW()
def process_show(processes, raw):
    ...
```

## Source

* Decorators: `src/aiida/cmdline/utils/decorators.py`
* Arguments and options: `src/aiida/cmdline/params/{arguments,options}/main.py`
* Custom options: `src/aiida/cmdline/params/options/{callable,conditional,interactive,multivalue,config}.py`
* Parameter types: `src/aiida/cmdline/params/types/`
