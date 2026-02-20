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
2. Clone your fork locally.
3. Check out the right branch and create a new one for your development:

```console
$ git checkout main
$ git checkout -b my-new-addition
```

## Running tests

Install the extra test packages and run the test suite:

```console
$ pip install -e .[tests]
$ pytest            # run all tests
$ pytest -m presto  # only run tests compatible with the presto profile
```

Tests for the transport plugins require that your default SSH key can be used to connect to `localhost`.

## Pre-commit hooks

The AiiDA pre-commit hooks help you write clean code by running code formatting, syntax checking, static analysis, and more locally at every commit.

Set up the hooks as follows:

```console
$ cd aiida-core
$ pip install -e .[pre-commit]
$ pre-commit run       # test running the hooks (only on staged files)
$ pre-commit install   # optional: run automatically on each commit
```

Besides `pre-commit`, you may want to install other extras such as `tests` and `docs` (see `pyproject.toml` for the full list).

### Useful commands

* Use `pre-commit run` to run the checks without committing.
* If you ever need to commit a "work in progress", you may skip the checks with `git commit --no-verify`.
  Keep in mind that the pre-commit hooks will also run (and fail) in CI when you push.

## Running with tox

You can use [tox](https://tox.wiki/en/latest/) to automate the creation of virtual environments for running tests:

```console
$ pip install --upgrade pip tox tox-conda
$ tox -av
$ tox path/to/test/file.py -- -x
```

Note: the tox configuration in `pyproject.toml` is not actively maintained and may have issues.

:::{note}
If you work in a `conda` environment on a system that also has `virtualenv` installed, you may need to `conda install virtualenv` to avoid problems.
:::

## Using Windows Subsystem for Linux (WSL)

WSL 2 is recommended for speed.
It provides a full VM with faster I/O and no need for Windows-side RabbitMQ services.

:::{tip}
Consider using Visual Studio Code with the [Remote WSL extension](https://code.visualstudio.com/docs/remote/wsl) for a full IDE experience.
:::
