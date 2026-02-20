# Dependency management

Dependencies for `aiida-core` are managed according to [AEP 002](https://github.com/aiidateam/AEP/tree/master/002_dependency_management).

## Dependency Manager

| Period | DM |
|--------|----|
| 2020-02 | [@csadorf](https://github.com/csadorf) |
| 2022-10 | [@sphuber](https://github.com/sphuber) |
| 2024 | [@agoscinski](https://github.com/agoscinski) |

The current Dependency Manager should be a member of the [dependency-manager](https://github.com/orgs/aiidateam/teams/dependency-manager) team.

## Specification

The `pyproject.toml` file is the **authoritative source** for all dependency specifications.
Dependencies are divided into:

* Main dependencies in the `dependencies` list
* Optional dependencies (extras) in the `project.optional-dependencies` table

Other files that must stay in sync with `pyproject.toml`:

* `environment.yml` -- conda environment specification
* `uv.lock` -- lock file used for development and CI

## Prerequisites for adding a dependency

Before adding a new dependency, ensure it meets all of the following:

- [ ] Fills a non-trivial feature gap that could not be resolved easily otherwise
- [ ] Supports all Python versions supported by aiida-core (as specified in `pyproject.toml`)
- [ ] Is available on [PyPI](https://pypi.org/) **and** [conda-forge](https://conda-forge.org/)
- [ ] Appears to be in a stable development stage (e.g., has reached version 1.0)
- [ ] Uses an MIT-compatible license (MIT, BSD, Apache, LGPL, but **not** GPL)

:::{note}
If a critical dependency is not yet available on PyPI or conda-forge:
1. For lightweight packages, consider vendoring if the license permits.
2. Request the maintainer to publish to PyPI/conda-forge.
3. As a last resort, maintain the PyPI project and conda-forge recipes ourselves.
:::

## Updating dependencies

### 1. Update `pyproject.toml`

Modify the affected entries, then regenerate all dependent files:

```console
$ ./utils/dependency_management.py generate-all
```

This command is also executed by the pre-commit hook (if installed).

For packages named differently between PyPI and conda-forge, add an entry to the `SETUPTOOLS_CONDA_MAPPINGS` variable in the same script.

### 2. Update `uv.lock`

Update the lock file to reflect the new dependency specifications.

## Continuous integration

Consistency of the various files with `pyproject.toml` is checked by a pre-commit hook that executes the `generate-all` and `validate-*` commands of `utils/dependency_management.py`.
This hook also runs for all commits as part of the CI workflow.

Changes to `pyproject.toml` trigger the `test-install` workflow, which checks whether the package can be installed with pip and conda.
The `test-install` workflow also runs nightly to catch issues from changes in the Python ecosystem.

## Constrained dependencies

Dependencies that are currently constrained (where we should work towards loosening them) are tracked as GitHub issues with the [`topic/dependencies/constraint`](https://github.com/aiidateam/aiida-core/issues?q=is%3Aopen+is%3Aissue+label%3Atopic%2Fdependencies%2Fconstraint) label.
