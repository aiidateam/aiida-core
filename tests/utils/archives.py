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

from aiida.common import json
from aiida.common.exceptions import NotExistent
from aiida.tools.importexport.common.archive import extract_tar, extract_zip
from aiida.common.folders import SandboxFolder


def get_archive_file(archive, filepath=None, external_module=None):
    """Return the absolute path of the archive file used for testing purposes.

    The expected path for these files:

        tests.fixtures.filepath

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


def get_json_files(archive, silent=True, filepath=None, external_module=None):
    """Get metadata.json and data.json from an exported AiiDA archive

    :param archive: the relative filename of the archive
    :param silent: Whether or not the extraction should be silent
    :param filepath: str of directories of where to find archive (starting "/"s are irrelevant)
    :param external_module: string with name of external module, where archive can be found
    """
    # Get archive
    dirpath_archive = get_archive_file(archive, filepath=filepath, external_module=external_module)

    # Unpack archive
    with SandboxFolder(sandbox_in_repo=False) as folder:
        if zipfile.is_zipfile(dirpath_archive):
            extract_zip(dirpath_archive, folder, silent=silent)
        elif tarfile.is_tarfile(dirpath_archive):
            extract_tar(dirpath_archive, folder, silent=silent)
        else:
            raise ValueError('invalid file format, expected either a zip archive or gzipped tarball')

        try:
            with open(folder.get_abs_path('data.json'), 'r', encoding='utf8') as fhandle:
                data = json.load(fhandle)
            with open(folder.get_abs_path('metadata.json'), 'r', encoding='utf8') as fhandle:
                metadata = json.load(fhandle)
        except IOError:
            raise NotExistent('export archive does not contain the required file {}'.format(fhandle.filename))

    # Return metadata.json and data.json
    return metadata, data


def migrate_archive(input_file, output_file, silent=True):
    """Migrate contents using `migrate_recursively`
    This is essentially similar to `verdi export migrate`.
    However, since this command may be disabled, this function simulates it and keeps the tests working.

    :param input_file: filename with full path for archive to be migrated
    :param output_file: filename with full path for archive to be created after migration
    """
    from aiida.tools.importexport.migration import migrate_recursively

    # Unpack archive, migrate, and re-pack archive
    with SandboxFolder(sandbox_in_repo=False) as folder:
        if zipfile.is_zipfile(input_file):
            extract_zip(input_file, folder, silent=silent)
        elif tarfile.is_tarfile(input_file):
            extract_tar(input_file, folder, silent=silent)
        else:
            raise ValueError('invalid file format, expected either a zip archive or gzipped tarball')

        try:
            with open(folder.get_abs_path('data.json'), 'r', encoding='utf8') as fhandle:
                data = json.load(fhandle)
            with open(folder.get_abs_path('metadata.json'), 'r', encoding='utf8') as fhandle:
                metadata = json.load(fhandle)
        except IOError:
            raise NotExistent('export archive does not contain the required file {}'.format(fhandle.filename))

        # Migrate
        migrate_recursively(metadata, data, folder)

        # Write json files
        with open(folder.get_abs_path('data.json'), 'wb') as fhandle:
            json.dump(data, fhandle, indent=4)

        with open(folder.get_abs_path('metadata.json'), 'wb') as fhandle:
            json.dump(metadata, fhandle, indent=4)

        # Pack archive
        compression = zipfile.ZIP_DEFLATED
        with zipfile.ZipFile(output_file, mode='w', compression=compression, allowZip64=True) as archive:
            src = folder.abspath
            for dirpath, dirnames, filenames in os.walk(src):
                relpath = os.path.relpath(dirpath, src)
                for filename in dirnames + filenames:
                    real_src = os.path.join(dirpath, filename)
                    real_dest = os.path.join(relpath, filename)
                    archive.write(real_src, real_dest)
