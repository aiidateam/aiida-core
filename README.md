# AiiDA monorepo

This repository hosts multiple Python subpackages, each in its own
directory with its own `pyproject.toml`.

## Packages

- [`aiida-core/`](aiida-core/) — the AiiDA workflow manager
  ([README](aiida-core/README.md), [changelog](aiida-core/CHANGELOG.md)).

## Development

Developer tooling (CI workflows, pre-commit config, Docker setups and helper
scripts) stays at the repository root:

- `pixi.toml` — development environment definition
- `.pre-commit-config.yaml` — linting / formatting hooks
- `utils/` — helper scripts (dependency management, consistency checks)
- `.github/` — CI workflows and issue templates
- `.docker/` — container images for testing and development

See [`aiida-core/README.md`](aiida-core/README.md) for package-specific
documentation.
