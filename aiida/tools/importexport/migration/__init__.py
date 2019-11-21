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

from aiida.cmdline.utils import echo
from aiida.tools.importexport.common.exceptions import DanglingLinkError

from .utils import verify_metadata_version
from .v01_to_v02 import migrate_v1_to_v2
from .v02_to_v03 import migrate_v2_to_v3
from .v03_to_v04 import migrate_v3_to_v4
from .v04_to_v05 import migrate_v4_to_v5
from .v05_to_v06 import migrate_v5_to_v6
from .v06_to_v07 import migrate_v6_to_v7
from .v07_to_v08 import migrate_v7_to_v8

__all__ = ('migrate_recursively', 'verify_metadata_version')

MIGRATE_FUNCTIONS = {
    '0.1': migrate_v1_to_v2,
    '0.2': migrate_v2_to_v3,
    '0.3': migrate_v3_to_v4,
    '0.4': migrate_v4_to_v5,
    '0.5': migrate_v5_to_v6,
    '0.6': migrate_v6_to_v7,
    '0.7': migrate_v7_to_v8,
}


def migrate_recursively(metadata, data, folder):
    """
    Recursive migration of export files from v0.1 to newest version,
    See specific migration functions for detailed descriptions.

    :param metadata: the content of an export archive metadata.json file
    :param data: the content of an export archive data.json file
    :param folder: SandboxFolder in which the archive has been unpacked (workdir)
    """
    from aiida.tools.importexport import EXPORT_VERSION as newest_version

    old_version = verify_metadata_version(metadata)

    try:
        if old_version == newest_version:
            echo.echo_critical('Your export file is already at the newest export version {}'.format(newest_version))
        elif old_version in MIGRATE_FUNCTIONS:
            MIGRATE_FUNCTIONS[old_version](metadata, data, folder)
        else:
            echo.echo_critical('Cannot migrate from version {}'.format(old_version))
    except ValueError as exception:
        echo.echo_critical(exception)
    except DanglingLinkError:
        echo.echo_critical('Export file is invalid because it contains dangling links')

    new_version = verify_metadata_version(metadata)

    if new_version < newest_version:
        new_version = migrate_recursively(metadata, data, folder)

    return new_version
