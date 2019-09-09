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
from aiida.tools.importexport.common import exceptions

from .utils import verify_archive_version
from .v01_to_v02 import migrate_v1_to_v2
from .v02_to_v03 import migrate_v2_to_v3
from .v03_to_v04 import migrate_v3_to_v4
from .v04_to_v05 import migrate_v4_to_v5
from .v05_to_v06 import migrate_v5_to_v6
from .v06_to_v07 import migrate_v6_to_v7
from .v07_to_v08 import migrate_v7_to_v8

__all__ = ('migrate_archive', 'verify_archive_version')

MIGRATE_FUNCTIONS = {
    '0.1': migrate_v1_to_v2,
    '0.2': migrate_v2_to_v3,
    '0.3': migrate_v3_to_v4,
    '0.4': migrate_v4_to_v5,
    '0.5': migrate_v5_to_v6,
    '0.6': migrate_v6_to_v7,
    '0.7': migrate_v7_to_v8,
}


def migrate_recursively(archive):
    """
    Recursive migration of export files from v0.1 to newest version,
    See specific migration functions for detailed descriptions.

    :param archive: The export archive to be migrated.
    :type archive: :py:class:`~aiida.tools.importexport.common.archive.Archive`
    """
    from aiida.tools.importexport import EXPORT_VERSION as newest_version

    old_version = archive.version_format

    if old_version == newest_version:
        raise exceptions.MigrationValidationError(
            'Your export file is already at the newest export version {}'.format(newest_version)
        )
    elif old_version in MIGRATE_FUNCTIONS:
        MIGRATE_FUNCTIONS[old_version](archive)
    else:
        raise exceptions.MigrationValidationError('Cannot migrate from version {}'.format(old_version))

    new_version = archive.version_format

    if new_version:
        if new_version < newest_version:
            new_version = migrate_recursively(archive)
    else:
        raise exceptions.MigrationValidationError('Archive version could not be determined')

    return new_version


def migrate_archive(source, output=None, overwrite=False, silent=False):
    """Unpack, migrate, and repack an export archive

    :param source: Path to source archive to be migrated.
    :type source: str
    :param output: Path to newly migrated archive.
    :type output: str
    :param overwrite: Whether or not to overwrite the newly migrated archive, if it already exists.
    :type overwrite: bool
    :param silent: Whether or not to unpack archive and migrate silently.
    :type silent: bool

    :return: Results overview
    :rtype: dict
    """
    import os
    from aiida.tools.importexport import Archive

    if output and os.path.exists(output) and not overwrite:
        raise exceptions.MigrationValidationError('The output file already exists')

    try:
        with Archive(
            source, output_filepath=output, overwrite=overwrite, silent=silent, sandbox_in_repo=False
        ) as archive:
            old_version = archive.version_format
            new_version = migrate_recursively(archive)

            archive.repack()
    except Exception as why:
        raise exceptions.ArchiveMigrationError(why)

    return old_version, new_version
