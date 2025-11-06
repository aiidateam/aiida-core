###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Module with implementation of the storage backend,
using an SQLite database and repository files, within a zipfile.

The content of the zip file is::

    |- storage.zip
        |- metadata.json
        |- db.sqlite3
        |- repo/
            |- hashkey1
            |- hashkey2
            ...

For quick access, the metadata (such as the version) is stored in a `metadata.json` file,
at the "top" of the zip file, with the sqlite database, just below it, then the repository files.
Repository files are named by their SHA256 content hash.

This storage method is primarily intended for the AiiDA archive,
as a read-only storage method.
This is because sqlite and zip are not suitable for concurrent write access.

The archive format originally used a JSON file to store the database,
and these revisions are handled by the `version_profile` and `migrate` backend methods.
"""

# AUTO-GENERATED
# fmt: off
from .backend import *

__all__ = (
    'SqliteZipBackend',
)
# fmt: on
