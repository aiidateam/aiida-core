# Writing tests

## Testing philosophy

* Whenever you encounter a bug, add a (failing) test for it. Then fix the bug.
* Whenever you modify or add a feature, write a test for it.
  Writing tests [before the implementation](http://en.wikipedia.org/wiki/Test_Driven_Development) helps keep your API clean.
* Make unit tests as atomic as possible. A unit test should run in the blink of an eye.
* Document *why* you wrote your test -- developers will thank you for it once it fails.

## Types of tests

| Type | Location | Description |
|------|----------|-------------|
| Local tests | `tests/` | Extensive suite of Python API and CLI tests. Run locally and on GitHub Actions for every PR. |
| Benchmark tests | `tests/benchmark/` | Performance benchmarks of common operations. Run on GitHub Actions for commits to `main`. |
| System tests | `.github/system_tests/` | Tests requiring infrastructure like a running daemon or remote computer. Run on GitHub Actions. |
| Stress tests | `.molecule/` | Medium- to long-running engine stress tests. Not part of CI. |

## Setting up your test environment

1. Install extra dependencies:

   ```console
   $ pip install -e .[tests]
   ```

2. Optionally, set up a test profile for faster testing:

   ```console
   $ verdi quicksetup --profile test_profile --test-profile
   ```

   :::{note}
   The database name and repository folder must start with `test_` to avoid accidental data loss, since tests modify the database.
   :::

You can also use [tox](https://tox.readthedocs.io) to automate the creation of local virtual environments for tests.
The configuration is in `pyproject.toml`.

## Running the test suite

* Run all tests (uses `pgtest` for a temporary postgres cluster by default):

  ```console
  $ pytest
  ```

* Run with a specific test profile:

  ```console
  $ AIIDA_TEST_PROFILE=test_profile pytest
  ```

* Run a subset of tests:

  ```console
  $ pytest tests/path/to/test
  ```

### Transport tests

For transport tests, you need passwordless SSH to `localhost`:

* Make sure you have an SSH server running.
* Configure an SSH key and add your public key to `~/.ssh/authorized_keys`:

  ```console
  $ sudo apt install openssh-server  # Linux/Ubuntu
  $ ssh-copy-id localhost
  ```

* For security, restrict SSH to local connections by editing `/etc/ssh/sshd_config`:
  change `#ListenAddress 0.0.0.0` to `ListenAddress 127.0.0.1`.

### RabbitMQ tests

For tests that require the RabbitMQ message broker, set up RabbitMQ locally or use the Docker configuration in `.docker/docker-rabbitmq.yml`.

## Writing new tests

AiiDA uses `pytest` as the testing framework.

* Create a `test_MODULENAME.py` in the appropriate subfolder of `tests/`, or add to an existing file.
* Write test functions starting with `test_`.
* Reuse existing [fixtures](https://docs.pytest.org/en/latest/how-to/fixtures.html) where possible, or add your own.

:::{note}
Some tests still use the `AiidaTestCase` unittest class.
Make an effort to migrate such cases to `pytest` when you are touching them.
:::
