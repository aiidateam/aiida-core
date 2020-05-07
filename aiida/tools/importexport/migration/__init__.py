# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Migration export files from old export versions to the newest, used by `verdi export migrate` command."""
from aiida.common.lang import type_check
from aiida.tools.importexport import EXPORT_VERSION
from aiida.tools.importexport.common.exceptions import DanglingLinkError, ArchiveMigrationError

from .utils import verify_metadata_version
from .v01_to_v02 import migrate_v1_to_v2
from .v02_to_v03 import migrate_v2_to_v3
from .v03_to_v04 import migrate_v3_to_v4
from .v04_to_v05 import migrate_v4_to_v5
from .v05_to_v06 import migrate_v5_to_v6
from .v06_to_v07 import migrate_v6_to_v7
from .v07_to_v08 import migrate_v7_to_v8
from .v08_to_v09 import migrate_v8_to_v9

__all__ = ('migrate_recursively', 'verify_metadata_version')

MIGRATE_FUNCTIONS = {
    '0.1': migrate_v1_to_v2,
    '0.2': migrate_v2_to_v3,
    '0.3': migrate_v3_to_v4,
    '0.4': migrate_v4_to_v5,
    '0.5': migrate_v5_to_v6,
    '0.6': migrate_v6_to_v7,
    '0.7': migrate_v7_to_v8,
    '0.8': migrate_v8_to_v9,
}


def migrate_recursively(metadata, data, folder, version=EXPORT_VERSION):
    """Recursive migration of export files from v0.1 to a newer version.

    See specific migration functions for detailed descriptions.

    :param metadata: the content of an export archive metadata.json file
    :param data: the content of an export archive data.json file
    :param folder: SandboxFolder in which the archive has been unpacked (workdir)
    :param version: the version to migrate to, by default the current export version
    """
    old_version = verify_metadata_version(metadata)

    type_check(version, str)

    try:
        if old_version == version:
            raise ArchiveMigrationError('Your export file is already at the version {}'.format(version))
        elif old_version > version:
            raise ArchiveMigrationError('Backward migrations are not supported')
        elif old_version in MIGRATE_FUNCTIONS:
            MIGRATE_FUNCTIONS[old_version](metadata, data, folder)
        else:
            raise ArchiveMigrationError('Cannot migrate from version {}'.format(old_version))
    except ValueError as exception:
        raise ArchiveMigrationError(exception)
    except DanglingLinkError:
        raise ArchiveMigrationError('Export file is invalid because it contains dangling links')

    new_version = verify_metadata_version(metadata)

    if new_version < version:
        new_version = migrate_recursively(metadata, data, folder, version)

    return new_version
