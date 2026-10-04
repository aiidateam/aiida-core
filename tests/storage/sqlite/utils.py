###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Utilities for testing SQLite storage backends."""

from pathlib import Path

from aiida.storage.sqlite_zip.utils import create_sqla_engine
from tests.storage.migrations.utils import reflect_schema as reflect_migration_schema


def reflect_schema(database_path: Path) -> dict:
    """Create a semantic representation of a SQLite database schema."""
    return reflect_migration_schema(create_sqla_engine(database_path))
