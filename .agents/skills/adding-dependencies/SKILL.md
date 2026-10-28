---
name: adding-dependencies
description: Use when adding third-party dependencies to `pyproject.toml`.
---

# Adding dependencies

* Substantial gap that existing code cannot readily fill.
* Active maintenance; all project Python versions supported.
* Available on [PyPI](https://pypi.org/) and [conda-forge](https://conda-forge.org/).
* MIT-compatible license: MIT, BSD, Apache, LGPL. GPL excluded.

Edit `pyproject.toml`; run `uv run pre-commit`.
Hooks `uv-lock` and `generate-conda-environment` update `uv.lock` and `environment.yml`.
