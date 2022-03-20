# Molecule System Integration/Stress Testing

This folder contains configuration for running automated system integration tests against an isolated AiiDA environment.

This utilises [molecule](https://molecule.readthedocs.io) to automate the creation/destruction of a docker container environment and the setup and testing within it.

The tests are currently set up to stress-test the AiiDA engine by launching a number of workchains of varying complexity, defined by [reverse polish notation](https://en.wikipedia.org/wiki/Reverse_Polish_notation).

## Running the tests locally

The simplest way to run these tests is to use the `tox` environment provided in this repository's `pyproject.toml` file:

```console
$ pip install tox
$ tox -e molecule
```

**NOTE**: if you wan to run molecule directly, ensure that you set `export MOLECULE_GLOB=.molecule/*/config_local.yml`.

This runs the `test` scenario (defined in `config_local.yml`) which:

1. Deletes any existing container with the same label
2. Creates a docker container, based on the `Dockerfile` in this folder, which also copies the repository code into the container (see `create_docker.yml`).
3. Installs aiida-core (see `setup_python.yml`)
4. Sets up an AiiDA profile and computer (see `setup_aiida.yml`).
5. Sets up a number of workchains of varying complexity,defined by [reverse polish notation](https://en.wikipedia.org/wiki/Reverse_Polish_notation), and runs them (see `run_tests.yml`).
6. Deletes the container.

If you wish to setup the container for manual inspection (i.e. only run steps 2 - 4) you can run:

```console
$ tox -e molecule converge
```

Then you can jump into this container or run the tests (step 5) separately with:

```console
$ tox -e molecule validate
```

and finally run step 6:

```console
$ tox -e molecule destroy
```

## Additional variables

You can specify the number of daemon workers to spawn using the `AIIDA_TEST_WORKERS` environment variable:

```console
$ AIIDA_TEST_WORKERS=4 tox -e molecule
```
