# Development environment

You are likely both an `aiida-core` developer and user, so you probably don't want to break your production AiiDA setup with development code.
There are different ways to create an independent development environment.

## Using the Docker container

By using a container, you also get independent prerequisite services (PostgreSQL and RabbitMQ), already configured and running.
You need Docker installed on your machine; see the [AiiDA Docker documentation](https://aiida.readthedocs.io/projects/aiida-core/en/latest/intro/run_docker.html) for instructions.

Once Docker is installed, start the environment with:

```console
$ docker run -it --name aiida-dev aiidateam/aiida-core-with-services:latest bash
```

You can use VS Code to attach to the container and modify code directly.
GitHub credentials are automatically synchronized into the container when using VS Code.

## Using a Python virtual environment

Please refer to the [installation instructions](https://aiida.readthedocs.io/projects/aiida-core/en/latest/installation/index.html) in the documentation.

## Getting the code

1. [Fork](https://help.github.com/articles/fork-a-repo/) the [aiida-core](https://github.com/aiidateam/aiida-core) repository.

1. Clone your fork locally.

1. Install development dependencies:

   ```console
   $ uv sync
   ```

   This creates a `.venv` and installs all dependencies (including test and development extras) from the lock file `uv.lock`.

1. Create a branch for your development using the naming convention `<prefix>/<issue>/<short_description>`:

   ```console
   $ git switch -c fix/1234/querybuilder_improvements
   ```

   Common prefixes: `feature/`, `fix/`, `docs/`, `ci/`, `refactor/`.

## Running tests

Run the test suite with:

```console
$ uv run pytest                        # run all tests
$ uv run pytest -m presto              # fast tests (no PostgreSQL/RabbitMQ required)
$ uv run pytest -n auto                # run tests in parallel (via pytest-xdist)
$ uv run pytest tests/orm/             # run tests for a specific module
$ uv run pytest tests/orm/test_nodes.py::test_node_label  # run a specific test
```

Use `AIIDA_TEST_PROFILE=<profile>` to run against a specific test profile.

Tests for the transport plugins require that your default SSH key can be used to connect to `localhost`.

## Pre-commit hooks

The AiiDA pre-commit hooks help you write clean code by running code formatting, syntax checking, static analysis, and more locally at every commit.

All pre-commit dependencies are included in `uv sync`, so no separate install step is needed:

```console
$ uv run pre-commit run                          # check staged files only
$ uv run pre-commit run --from-ref main --to-ref HEAD  # all changes since branching off main
$ uv run pre-commit run mypy                     # run a specific hook
$ uv run pre-commit install                      # optional: run automatically on each commit
```

### Useful commands

- Use `uv run pre-commit run` to run the checks without committing.
- If you ever need to commit a "work in progress", you may skip the checks with `git commit --no-verify`.
  Keep in mind that the pre-commit hooks will also run (and fail) in CI when you push.

## Using Windows Subsystem for Linux (WSL)

WSL 2 is recommended for speed.
It provides a full VM with faster I/O and no need for Windows-side RabbitMQ services.

:::{tip}
Consider using Visual Studio Code with the [Remote WSL extension](https://code.visualstudio.com/docs/remote/wsl) for a full IDE experience.
:::

## Useful `verdi` commands for development

```console
$ verdi status                    # Check status of services (daemon, PostgreSQL, RabbitMQ)
$ verdi daemon start/stop/restart # Manage the daemon
$ verdi shell                     # Interactive IPython shell with AiiDA loaded
$ verdi devel launch-add          # Launch a test ArithmeticAddCalculation
$ verdi devel launch-multiply-add # Launch a test MultiplyAddWorkChain
$ verdi devel check-load-time     # Check for import slowdowns
$ verdi devel run-sql "SELECT ..." # Run raw SQL against the profile database
```

Set `AIIDA_WARN_v3=1` to surface deprecation warnings.
