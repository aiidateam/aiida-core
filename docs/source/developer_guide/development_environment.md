# Development environment

## Getting the code

1. [Fork](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/working-with-forks/fork-a-repo) the [aiida-core](https://github.com/aiidateam/aiida-core) repository.

1. Clone your fork locally:

   ```console
   $ git clone git@github.com:<your-username>/aiida-core.git  # using git directly
   $ gh repo clone <your-username>/aiida-core   # or the GitHub CLI
   ```

   :::{tip}
   `gh repo clone` automatically sets `origin` to your fork and `upstream` to `aiidateam/aiida-core`.
   With `git clone`, if you'd also like a direct reference to the upstream repo (e.g., to fetch the latest `main`), add it manually:

   ```console
   $ git remote add upstream git@github.com:aiidateam/aiida-core.git
   ```

   :::

1. Install development dependencies (we recommend [uv](https://docs.astral.sh/uv/) for dependency management):

   ```console
   $ uv sync
   ```

   This creates a `.venv` and installs all dependencies from the lock file `uv.lock`.
   The `dev` dependency group (installed by default) pulls in all optional extras — `tests`, `docs`, `pre-commit`, `rest`, and `atomic_tools` — so everything needed for development is available out of the box.

1. Create a branch for your development using the naming convention `<prefix>/<issue>/<short_description>`:

   ```console
   $ git switch -c fix/1234/querybuilder_improvements
   ```

   Common prefixes: `feature/`, `fix/`, `docs/`, `ci/`, `refactor/`.

## Isolating your development environment

If you also use AiiDA for production work, you will want to keep your development environment separate to avoid breaking your production setup.

### Separate AiiDA profile

You can create a separate AiiDA profile for development and testing, so your production data is never at risk:

```console
$ verdi presto --profile-name dev
```

This sets up a lightweight profile using `SQLite` and the `disk-objectstore` — no PostgreSQL or RabbitMQ required.
If RabbitMQ is available on the system, it will be used automatically.
To use PostgreSQL instead of SQLite, pass `--use-postgres`.
Use `AIIDA_TEST_PROFILE=dev` to run tests against this profile.

### Git worktrees for parallel development

If you work on multiple features or PRs in parallel, [git worktrees](https://git-scm.com/docs/git-worktree) let you check out multiple branches simultaneously, each in its own directory with its own `.venv`:

```console
$ git worktree add ../aiida-core.worktrees/fix/1234/querybuilder_improvements
$ cd ../aiida-core.worktrees/fix/1234/querybuilder_improvements
$ uv sync
```

This avoids the need to stash or commit in-progress work when switching context.

### Docker container

Alternatively, for a fully isolated environment with prerequisite services (PostgreSQL and RabbitMQ) pre-configured:

```console
$ docker run -it --name aiida-dev aiidateam/aiida-core-with-services:latest bash
```

You need Docker installed on your machine; see the [AiiDA Docker documentation](https://aiida.readthedocs.io/projects/aiida-core/en/latest/intro/run_docker.html) for instructions.
You can use VS Code to attach to the container and modify code directly.

## Running tests

Run the test suite with:

```console
$ uv run pytest                                            # run all tests
$ uv run pytest -m presto                                  # tests that don't require PostgreSQL/RabbitMQ
$ uv run pytest -n auto                                    # run in parallel on all CPU cores (-n 4 for 4 cores, etc.)
$ uv run pytest tests/orm/                                 # run tests for a specific module
$ uv run pytest tests/orm/test_nodes.py::test_node_label   # run a specific test
```

Use `AIIDA_TEST_PROFILE=<profile>` to run against a specific test profile.

Tests for the transport plugins require that your default SSH key can be used to connect to `localhost`.

## Pre-commit hooks

The AiiDA pre-commit hooks help you write clean code by running code formatting, syntax checking, static analysis, and more locally at every commit.

All pre-commit dependencies are included in `uv sync`, so no separate install step is needed:

```console
$ uv run pre-commit run                                # check staged files only
$ uv run pre-commit run --from-ref main --to-ref HEAD  # all changes since branching off main
$ uv run pre-commit run mypy                           # run a specific hook
$ uv run pre-commit install                            # optional: run automatically on each commit
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
$ verdi status                      # Check status of services (daemon, PostgreSQL, RabbitMQ)
$ verdi daemon start/stop/restart   # Manage the daemon
$ verdi shell                       # Interactive IPython shell with AiiDA loaded
$ verdi devel launch-add            # Launch a test ArithmeticAddCalculation
$ verdi devel launch-multiply-add   # Launch a test MultiplyAddWorkChain
$ verdi devel check-load-time       # Check for import slowdowns
$ verdi devel run-sql "SELECT ..."  # Run raw SQL against the profile database
```

Set `AIIDA_WARN_v3=1` to surface deprecation warnings.
