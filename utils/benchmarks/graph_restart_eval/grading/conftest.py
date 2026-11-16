###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                   #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Local-only pytest configuration for the hidden acceptance tests.

Tracked with the v2 grader (committed). NEVER copy into solver worktrees,
NEVER show to solvers.

`tests/`-level `conftest.py` does not cover files under `utils/`, so this
module loads the AiiDA pytest fixtures directly and mirrors the repository's
`--broker-backend` / `--db-backend` options with no-external-service defaults
(SQLite storage + ZeroMQ broker, matching a `-m presto` run).
"""

from __future__ import annotations

import os

import pytest

pytest_plugins = ['aiida.tools.pytest_fixtures']


def pytest_addoption(parser) -> None:  # type: ignore[no-untyped-def]
    """Register backend options (guarded: tests/conftest.py defines the same names)."""
    for option, kwargs in (
        ('--broker-backend', {'action': 'store', 'default': 'zmq', 'choices': ('rmq', 'zmq', 'none')}),
        ('--db-backend', {'action': 'store', 'default': 'sqlite', 'choices': ('sqlite', 'psql')}),
    ):
        try:
            parser.addoption(option, **kwargs)  # type: ignore[arg-type]
        except ValueError:
            pass


@pytest.fixture(scope='session')
def aiida_profile(  # type: ignore[no-untyped-def]
    pytestconfig, tmp_path_factory, aiida_config, aiida_profile_factory, config_psql_dos, config_sqlite_dos
):
    """Create a throwaway profile: SQLite storage, broker per `--broker-backend`.

    Mirrors `tests/conftest.py`: a `-m presto` selection forces ZeroMQ so the
    verification needs no external services.
    """
    broker_backend = pytestconfig.getoption('--broker-backend')
    broker = {'rmq': 'core.rabbitmq', 'zmq': 'core.zeromq', 'none': None}[broker_backend]
    if 'presto' in pytestconfig.getoption('-m'):
        broker = 'core.zeromq'

    if pytestconfig.getoption('--db-backend') == 'psql':
        storage = 'core.psql_dos'
        storage_config = config_psql_dos()
    else:
        storage = 'core.sqlite_dos'
        worker_id = os.environ.get('PYTEST_XDIST_WORKER', 'master')
        storage_config = config_sqlite_dos(tmp_path_factory.mktemp(f'test_sqlite_dos_storage_{worker_id}'))

    with aiida_profile_factory(
        aiida_config, storage_backend=storage, storage_config=storage_config, broker_backend=broker
    ) as profile:
        yield profile
