# Deprecations and API changes

Following semantic versioning, changes to the public-facing API of AiiDA require a bump in the major version number.

As a rule of thumb, anything importable from a second-level package (e.g., `from aiida.orm import ...`, `from aiida.engine import ...`) is considered public API.
Deeper imports (e.g., `from aiida.engine.processes.calcjobs.tasks import Waiting`) are implementation details and not covered by deprecation guarantees — though in practice the boundary is not strictly enforced, especially for workflow or plugin developers where the line between user and developer becomes blurry.

## Gathering usage information

Before deprecating an API or making a change, it is often useful to know how much the API in question is used in practice.
Since many AiiDA plugins are hosted on GitHub, GitHub's global code search can be very helpful.

For example, to see how much `_get_base_folder` is used in files that also contain "aiida":

```
https://github.com/search?q=%22_get_base_folder%22+aiida&type=Code
```

## Deprecating the CLI

CLI changes also require proper deprecation warnings, as users may rely on `verdi` commands in scripts and automation.

To deprecate a CLI command, use the `deprecated` argument in the Click command decorator.
Examples from the codebase:

```python
@verdi.command('setup', deprecated='Please use `verdi profile setup` instead.')
def setup():
    ...

@verdi.command(
    'quicksetup',
    deprecated='This command is deprecated. For a fully automated alternative, use `verdi presto --use-postgres` '
    'or `verdi profile setup` for the interactive alternative.',
)
def quicksetup():
    ...
```

## Deprecating the Python API

Use `warn_deprecation` from `aiida.common.warnings` to emit deprecation warnings.
Examples from the codebase:

```python
from aiida.common.warnings import warn_deprecation

# Property renamed
warn_deprecation('`objects` property is deprecated, use `collection` instead.', version=3)

# Method renamed
warn_deprecation('This method will be removed, use `get_source_code_file` instead.', version=3)

# Fixture replaced
warn_deprecation('the clear_database_after_test fixture is deprecated, use aiida_profile_clean instead', version=3)
```

When deprecating a method, move the code to the new function name and change the old function to call the new one with the deprecation warning.
Add a `.. deprecated:: vX.Y.Z` note to the old function's docstring with a reference to the replacement.

`AiidaDeprecationWarning` does not inherit from Python's `DeprecationWarning`, so it is not hidden by default.
Users can disable AiiDA deprecation warnings with:

```console
$ verdi config set warnings.showdeprecations False
```

:::{tip}
Set `AIIDA_WARN_v3=1` to surface deprecation warnings during development and testing.
:::
