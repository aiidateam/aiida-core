# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Generic functions to verify the integrity of the database and optionally apply patches to fix problems."""
from sqlalchemy import text

from aiida.common import exceptions

TABLES_UUID_DEDUPLICATION = ('db_dbcomment', 'db_dbcomputer', 'db_dbgroup', 'db_dbnode')


def _get_duplicate_uuids(table: str, connection):
    """Check whether database table contains rows with duplicate UUIDS."""
    return connection.execute(
        text(
            f"""
        SELECT s.id, s.uuid FROM (SELECT *, COUNT(*) OVER(PARTITION BY uuid) AS c FROM {table})
        AS s WHERE c > 1
        """
        )
    )


def verify_uuid_uniqueness(table: str, connection):
    """Check whether database table contains rows with duplicate UUIDS."""
    duplicates = _get_duplicate_uuids(table=table, connection=connection)
    if duplicates.rowcount > 0:
        raise exceptions.IntegrityError(f'Table {table} contains rows with duplicate UUIDS')
