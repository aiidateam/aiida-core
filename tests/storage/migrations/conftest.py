###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Backend matrix fixtures for shared storage migration tests."""

import pytest

from tests.storage.psql_dos.migrations.fixtures import (  # noqa: F401
    empty_pg_cluster,
    psql_dos_migration_profile,
)
from tests.storage.sqlite_dos.migrations.fixtures import sqlite_dos_migration_profile  # noqa: F401


@pytest.fixture(params=(pytest.param('psql_dos', marks=pytest.mark.requires_psql), 'sqlite_dos'))
def migration_backend(request) -> str:
    """Return the storage backend under test."""
    return request.param


@pytest.fixture
def migration_profile(migration_backend: str, request):
    """Return an uninitialised profile provided by the selected backend."""
    return request.getfixturevalue(f'{migration_backend}_migration_profile')
