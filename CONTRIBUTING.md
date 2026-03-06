# Contributing to AiiDA

Thanks for your interest in contributing to AiiDA!

## Getting started

1. Fork and clone the repository
1. Install development dependencies: `uv sync` (creates a `.venv` and installs all dependencies)
1. Create a branch: `git switch -c feature/123/short-description`
1. Make your changes and ensure pre-commit passes: `uv run pre-commit run`
1. Run relevant tests: `uv run pytest tests/path/to/test_file.py` (use `-n auto` for parallel execution, `-m presto` to run only tests marked with `@pytest.mark.presto` — these require no external services; add this marker to new tests that don't need PostgreSQL or RabbitMQ)
1. Push and open a pull request against `main`

## Development guide

For in-depth development documentation, see the [Developer Guide](https://aiida.readthedocs.io/projects/aiida-core/en/latest/developer_guide/index.html) in the AiiDA docs (`docs/source/developer_guide/`), covering:

- Development environment setup
- Coding style and pre-commit hooks
- Writing tests and documentation
- Pull requests, code review, and commit conventions
- Deprecations, dependency management, releases
- AiiDA internals and design evolution

[`AGENTS.md`](AGENTS.md) provides a concise summary of the same conventions, optimized for AI coding assistants.

## Quick reference

| Task | Command |
|------|---------|
| Install dependencies | `uv sync` |
| Run quick tests | `uv run pytest -m presto` |
| Run full test suite | `uv run pytest` |
| Run pre-commit | `uv run pre-commit run` |
| Build docs | `uv run sphinx-build -b html docs/source docs/build/html` |

## Reporting issues

- Use [GitHub Issues](https://github.com/aiidateam/aiida-core/issues) to report bugs or request features
- Check existing issues before creating a new one
- Include a minimal reproducible example when reporting bugs

## Code of conduct

Please be respectful and constructive in all interactions.
See [`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md).
