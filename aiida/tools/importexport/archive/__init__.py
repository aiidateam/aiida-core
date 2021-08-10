# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# type: ignore
"""Readers and writers for archive formats, that work independently of a connection to an AiiDA profile."""

# AUTO-GENERATED

# yapf: disable
# pylint: disable=wildcard-import

from .common import *
from .migrators import *
from .readers import *
from .writers import *

__all__ = (
    'ARCHIVE_READER_LOGGER',
    'ArchiveMetadata',
    'ArchiveMigratorAbstract',
    'ArchiveMigratorJsonBase',
    'ArchiveMigratorJsonTar',
    'ArchiveMigratorJsonZip',
    'ArchiveReaderAbstract',
    'ArchiveWriterAbstract',
    'CacheFolder',
    'MIGRATE_LOGGER',
    'ReaderJsonBase',
    'ReaderJsonFolder',
    'ReaderJsonTar',
    'ReaderJsonZip',
    'WriterJsonFolder',
    'WriterJsonTar',
    'WriterJsonZip',
    'detect_archive_type',
    'get_migrator',
    'get_reader',
    'get_writer',
    'null_callback',
)

# yapf: enable
