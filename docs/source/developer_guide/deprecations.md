# Deprecations and API changes

Following semantic versioning, changes to the public-facing API of AiiDA require a bump in the major version number.

## Gathering usage information

Before deprecating an API or making a change, it is often useful to know how much the API in question is used in practice.
Since many AiiDA plugins are hosted on GitHub, GitHub's global code search can be very helpful.

For example, to see how much `_get_base_folder` is used in files that also contain "aiida":

```
https://github.com/search?q=%22_get_base_folder%22+aiida&type=Code
```

## Deprecating the CLI

CLI commands can be modified or removed more freely because users should not be relying on them for automated processes.
However, proper deprecation warnings must still be provided.

To deprecate a CLI command:

1. Add a `.. deprecated:: vX.Y.Z` note in the docstring indicating the release in which the deprecation was introduced.
2. Decorate the function with the `deprecated_command` decorator from `aiida.cmdline.utils.decorators`.

```python
@verdi_database.command('version')
@decorators.deprecated_command(
    'This command has been deprecated and will be removed soon. '
    'The same information is now available through `verdi status`.\n'
)
def database_version():
    """Show the version of the database.

    .. deprecated:: v2.1.0
    """
```

:::{important}
The `@decorators.deprecated_command` decorator must go **below** the `verdi` decorator.
It only has an effect on proper click commands, not on groups of commands.
:::

If the procedure needs to be forwarded to another command, use the `Context.forward()` method (see the [click docs](https://click.palletsprojects.com/en/5.x/advanced/#invoking-other-commands)).

## Deprecating the Python API

Use `AiidaDeprecationWarning` to emit deprecation warnings:

```python
import warnings
from aiida.common.warnings import AiidaDeprecationWarning as DeprecationWarning

warnings.warn(
    "Specific deprecation message describing what to use instead",
    DeprecationWarning,
)
```

Advantages of this approach:

* PyCharm will show the method as crossed out.
* `AiidaDeprecationWarning` does not inherit from Python's `DeprecationWarning`, so it will not be hidden by default.
* Users can disable AiiDA deprecation warnings with:

  ```console
  $ verdi config set warnings.showdeprecations False
  ```

When deprecating a method, move the code to the new function name and change the old function to call the new one with the deprecation warning.
Add a `.. deprecated:: vX.Y.Z` note to the old function's docstring with a reference to the replacement.
