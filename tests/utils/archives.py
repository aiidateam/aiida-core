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
import tarfile
import zipfile
from typing import List

from archive_path import read_file_in_tar, read_file_in_zip

from aiida.common import json
from tests.static import STATIC_DIR


def get_archive_file(archive: str, filepath=None, external_module=None) -> str:
    """Return the absolute path of the archive file used for testing purposes.

    The expected path for these files:

        tests.static.filepath

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
        # Add absolute path to local repo's static
        dirpath_archive = os.path.join(STATIC_DIR, dirpath_archive)

    if not os.path.isfile(dirpath_archive):
        dirpath_parent = os.path.dirname(dirpath_archive)
        raise ValueError(f'archive {archive} does not exist in the archives directory {dirpath_parent}')

    return dirpath_archive


def import_archive(archive, filepath=None, external_module=None):
    """Import a test archive that is an AiiDA export archive

    :param archive: the relative filename of the archive
    :param filepath: str of directories of where to find archive (starting "/"s are irrelevant)
    :param external_module: string with name of external module, where archive can be found
    """
    from aiida.tools.importexport import import_data

    dirpath_archive = get_archive_file(archive, filepath=filepath, external_module=external_module)

    import_data(dirpath_archive)


def read_json_files(path, *, names=('metadata.json', 'data.json')) -> List[dict]:
    """Get metadata.json and data.json from an exported AiiDA archive

    :param path: the filepath of the archive
    :param names: the files to retrieve

    """
    jsons: List[dict] = []

    if zipfile.is_zipfile(path):
        for name in names:
            jsons.append(json.loads(read_file_in_zip(path, name)))
    elif tarfile.is_tarfile(path):
        for name in names:
            jsons.append(json.loads(read_file_in_tar(path, name)))
    else:
        raise ValueError('invalid file format, expected either a zip archive or gzipped tarball')

    return jsons
