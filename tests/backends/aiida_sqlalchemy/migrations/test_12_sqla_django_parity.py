# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for migrations to bring parity between SQLAlchemy and Django."""
from .conftest import Migrator


def test_part_1(perform_migrations: Migrator):
    """Ensure fields to make non-nullable are not currently null."""
    # starting revision
    perform_migrations.migrate_down('34a831f4286d')

    perform_migrations.migrate_up('2b40c8131fe0')
