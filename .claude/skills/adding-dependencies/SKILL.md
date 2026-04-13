---
name: adding-dependencies
description: Use when adding a new third-party dependency to aiida-core's `pyproject.toml`. Covers the checklist for maintenance, Python version support, package registry availability, and license compatibility.
---

# Adding dependencies to aiida-core

Before adding a new dependency to `pyproject.toml`, ensure it:

- Fills a non-trivial feature gap not easily resolved otherwise
- Is actively maintained
- Supports all Python versions supported by aiida-core
- Is available on both [PyPI](https://pypi.org/) and [conda-forge](https://conda-forge.org/)
- Uses an MIT-compatible license (MIT, BSD, Apache, LGPL &mdash; **not** GPL)
