# Writing tests

## Testing philosophy

- Whenever you encounter a bug, add a (failing) test for it. Then fix the bug.
- Whenever you modify or add a feature, write a test for it.
  Writing tests [before the implementation](https://en.wikipedia.org/wiki/Test_Driven_Development) helps keep your API clean.
- Make unit tests as atomic as possible. A unit test should run in the blink of an eye.
- Document *why* you wrote your test -- developers will thank you for it once it fails.
- **Prefer real objects over mocks**: Use fixtures to create real nodes, processes, etc.
  Mocks should only be used for truly external dependencies (e.g., network calls, SSH connections), cases where setup would be too complex, or where it is otherwise difficult to get the desired behavior (e.g., mocking to enforce exceptions being raised that would not appear naturally).
- **Don't chase coverage with shallow tests**: A test that mocks everything tests nothing.
  Tests should exercise actual behavior.
- **Test the contract, not the implementation**: Don't assert internal method calls; assert observable outcomes.

## Types of tests

| Type | Location | Description |
|------|----------|-------------|
| Local tests | `tests/` | Extensive suite of Python API and CLI tests. Run locally and on GitHub Actions for every PR. |
| Benchmark tests | `tests/benchmark/` | Performance benchmarks of common operations. Run on GitHub Actions for commits to `main`. |
| System tests | `.github/system_tests/` | Tests requiring infrastructure like a running daemon or remote computer. Run on GitHub Actions. |
| Stress tests | `.molecule/` | Medium- to long-running engine stress tests. Not part of CI. |

## Setting up your test environment

Install all dependencies (including test extras) with:

```console
$ uv sync
```

Optionally, set up a dedicated test profile:

```console
$ verdi presto --profile-name test
```

Use `--use-postgres` for a PostgreSQL-backed profile instead of SQLite.

## Running the test suite

```console
$ uv run pytest                                    # run all tests (uses pgtest for a temporary postgres cluster by default)
$ uv run pytest -m presto                          # tests that don't require PostgreSQL/RabbitMQ
$ uv run pytest -n auto                            # run in parallel on all CPU cores (-n 4 for 4 cores, etc.)
$ uv run pytest tests/path/to/test                 # run a subset of tests
$ uv run pytest --cov aiida                        # run with coverage
$ AIIDA_TEST_PROFILE=test uv run pytest            # run against a specific test profile
```

### Test markers

- `presto` — tests that use `SqliteTempBackend` (in-memory, no external services required).
  Add this marker to new tests that don't need PostgreSQL or RabbitMQ.
- `requires_rmq` — requires RabbitMQ
- `requires_psql` — requires PostgreSQL
- `nightly` — long-running tests (CI only)

### Transport tests

For transport tests, you need passwordless SSH to `localhost`:

- Make sure you have an SSH server running:

  ```console
  $ sudo apt install openssh-server  # Ubuntu/Debian
  ```

  On other distributions, install the equivalent `openssh-server` package.

- Configure an SSH key and add your public key to `~/.ssh/authorized_keys`:

  ```console
  $ ssh-copy-id localhost
  ```

- For security, restrict SSH to local connections by editing `/etc/ssh/sshd_config`:
  change `#ListenAddress 0.0.0.0` to `ListenAddress 127.0.0.1`.

### RabbitMQ tests

For tests that require the RabbitMQ message broker, set up RabbitMQ locally or use the Docker configuration in `.docker/docker-rabbitmq.yml`.

## Writing new tests

AiiDA uses `pytest` as the testing framework.

- Create a `test_MODULENAME.py` in the appropriate subfolder of `tests/`.
  Tests should mirror the source structure so it is easy to find the test for any given module.
- Write test functions starting with `test_`.
- Reuse existing [fixtures](https://docs.pytest.org/en/latest/how-to/fixtures.html) where possible (many are available in `tests/conftest.py`), or add your own.
