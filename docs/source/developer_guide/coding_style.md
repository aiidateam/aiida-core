# Coding style

If you follow the instructions to {doc}`set up your development environment <development_environment>`, the AiiDA coding style is largely **enforced automatically using pre-commit hooks**.

This document mainly acts as a reference.

## General rules

* Code should conform to [PEP 8](https://www.python.org/dev/peps/pep-0008/).
* When compatible, follow the [Google Python Style Guide](https://github.com/google/styleguide/blob/gh-pages/pyguide.md).

## AiiDA-specific conventions

### File operations

* When opening a general file for reading or writing, use [`open()`](https://docs.python.org/3/library/functions.html#open) with UTF-8 encoding for formatted files, e.g., `open(path, 'w', encoding='utf8')`.
* When opening a file from the AiiDA repository, use `aiida.common.folders.Folder.open()`.

### Source file headers

Each source file should start with the following copyright header (added automatically by helper scripts before a release):

```python
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
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

### Pathlib

Use [`pathlib`](https://docs.python.org/3/library/pathlib.html) instead of `os.path` for file and folder manipulation.
Refer to the official documentation for a [translation table between os and pathlib](https://docs.python.org/3/library/pathlib.html#correspondence-to-tools-in-the-os-module).

### Type hinting

Add [type hints](https://docs.python.org/3/library/typing.html) to new code and update existing code when possible.
Type hints allow static type checkers to validate the code and IDEs to provide improved auto-completion.
They also make the code easier to read.

The pre-commit hooks include [mypy](http://mypy-lang.org/) for type checking.
If you add a file with type hinting, please add it to the include list in the `.pre-commit-config.yaml` file.
