# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Test utility to import, inspect, or migrate AiiDA export archives."""

import os

from aiida.tools.importexport.common.archive import Archive


def get_archive_file(archive, filepath=None, external_module=None):
    """Return the absolute path of the archive file used for testing purposes.

    The expected path for these files:

        aiida.backends.tests.fixtures.filepath

    :param archive: the relative filename of the archive
    :param filepath: str of directories of where to find archive (starting "/"s are irrelevant)
    :param external_module: string with name of external module, where archive can be found
    :return: absolute filepath of the archive test file
    """
    import importlib

    # Initialize
    dirpath_archive = archive

    # If the complete path has already been given, return archive immediately
    if os.path.isabs(dirpath_archive):
        return dirpath_archive

    # Add possible filepath
    if filepath and not isinstance(filepath, str):
        raise TypeError('filepath must be a string')
    elif filepath:
        dirpath_archive = os.path.join(*filepath.split(os.sep), dirpath_archive)

    # Use possible external module (otherwise use default, see above)
    if external_module and not isinstance(external_module, str):
        raise TypeError('external_module must be a string')
    elif external_module:
        # Use external module (will prepend the absolute path to `external_module`)
        external_path = os.path.dirname(os.path.realpath(importlib.import_module(external_module).__file__))

        dirpath_archive = os.path.join(external_path, dirpath_archive)
    else:
        # Add absolute path to local repo's fixtures
        dirpath_current = os.path.dirname(os.path.realpath(__file__))
        dirpath_migrate = os.path.join(dirpath_current, os.pardir, 'fixtures')

        dirpath_archive = os.path.join(dirpath_migrate, dirpath_archive)

    if not os.path.isfile(dirpath_archive):
        dirpath_parent = os.path.dirname(dirpath_archive)
        raise ValueError('archive {} does not exist in the archives directory {}'.format(archive, dirpath_parent))

    return dirpath_archive


def import_archive(archive, filepath=None, external_module=None):
    """Import a test archive that is an AiiDA export archive

    :param archive: the relative filename of the archive
    :param filepath: str of directories of where to find archive (starting "/"s are irrelevant)
    :param external_module: string with name of external module, where archive can be found
    """
    from aiida.tools.importexport import import_data

    dirpath_archive = get_archive_file(archive, filepath=filepath, external_module=external_module)

    import_data(dirpath_archive, silent=True)


class NoContextArchive(Archive):
    """Test class for :py:class:`aiida.tools.importexport.common.archive.Archive` that breaks rule of context"""

    def __init__(self, filepath='_test_filename.aiida', metadata=None, data=None, unpacked=True, **kwargs):
        super(NoContextArchive, self).__init__(filepath, **kwargs)
        self._silent = True
        self._meta_data = metadata
        self._data = data
        self._unpacked = unpacked

    def _ensure_within_context(self):
        """Do not raise if not within context"""
