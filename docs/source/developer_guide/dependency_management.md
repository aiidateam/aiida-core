# Dependency management

Dependencies for `aiida-core` are managed according to the principles of [AEP 002](https://github.com/aiidateam/AEP/tree/master/002_dependency_management).
The key principles are:

- **Loose constraints in `pyproject.toml`**: use the compatible release operator (`~=`) or wide version ranges to allow flexibility when installing aiida-core alongside other packages.
- **Pinned lock file (`uv.lock`)**: records exact versions of a tested, reproducible environment for development and CI.
- **Dual CI testing**: tests run against both loose constraints (to catch new incompatibilities early) and the pinned lock file (to ensure reproducibility).
- **Proactive monitoring**: when a dependency releases a new version, incompatibilities should be addressed promptly — via hotfix, patch release, or by constraining the dependency until a fix is available.

## Specification

The `pyproject.toml` file is the **authoritative source** for all dependency specifications.
Dependencies are divided into:

- Main dependencies in the `dependencies` list
- Optional dependencies (extras) in the `project.optional-dependencies` table

Other files that must stay in sync with `pyproject.toml`:

- `uv.lock` -- lock file used for development and CI (kept in sync via the `uv-lock` pre-commit hook)
- `environment.yml` -- conda environment specification (kept in sync via the `generate-conda-environment` pre-commit hook)

## Prerequisites for adding a dependency

Before adding a new dependency, ensure it meets all of the following:

- Fills a non-trivial feature gap that could not be resolved easily otherwise
- Supports all Python versions supported by aiida-core (as specified in `pyproject.toml`)
- Is available on [PyPI](https://pypi.org/) **and** [conda-forge](https://conda-forge.org/)
- Appears to be in a stable development stage (e.g., has reached version 1.0)
- Uses an MIT-compatible license (MIT, BSD, Apache, LGPL, but **not** GPL)

:::{note}
If a critical dependency is not yet available on PyPI or conda-forge:

1. For lightweight packages, consider vendoring if the license permits.
1. Request the maintainer to publish to PyPI/conda-forge.
   :::

## Updating dependencies

1. Modify the affected entries in `pyproject.toml`.
1. Update `uv.lock` by running `uv lock` (alternatively, done automatically by the `uv-lock` pre-commit hook).
1. The `environment.yml` will be regenerated automatically by the `generate-conda-environment` pre-commit hook.

For packages named differently between PyPI and conda-forge, add an entry to the `SETUPTOOLS_CONDA_MAPPINGS` variable in `utils/dependency_management.py`.

## Continuous integration

Consistency of `environment.yml` with `pyproject.toml` is checked by the `generate-conda-environment` and `validate-conda-environment` pre-commit hooks.
These also run in CI.

Changes to `pyproject.toml` trigger the `test-install` workflow, which checks whether the package can be installed with pip and conda.
The `test-install` workflow also runs weekly to catch issues from changes in the Python ecosystem.

[Dependabot](https://docs.github.com/en/code-security/dependabot) is configured to automatically open PRs for dependency updates (see `.github/dependabot.yml`).

## Constrained dependencies

Dependencies that are currently constrained (where we should work towards loosening them) are tracked as GitHub issues with the [`topic/dependencies/constraint`](https://github.com/aiidateam/aiida-core/issues?q=is%3Aopen+is%3Aissue+label%3Atopic%2Fdependencies%2Fconstraint) label.
