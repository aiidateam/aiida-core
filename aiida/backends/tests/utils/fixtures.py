# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Test utility to import fixtures, such as export archives."""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import os


def get_archive_file(archive, filepath=None):
    """
    Return the absolute path of the archive file used for testing purposes. The expected path for these files:

        aiida.backends.tests.fixtures.filepath

    :param archive: the relative filename of the archive
    :param filepath: str of directories of where to find archive (a **single** starting `/` is irrelevant)
    :returns: absolute filepath of the archive test file
    """
    dirpath_current = os.path.dirname(os.path.realpath(__file__))
    dirpath_fixtures = os.path.join(dirpath_current, os.pardir, 'fixtures')

    if filepath:
        # NOTE: This part should be changed, ending with:
        # dirpath_archive = os.path.join(dirpath_fixtures, *filepath, archive)
        # When support for python 2 is dropped.
        # This will allow `filepath` to be a str or list/tuple,
        # and there will be no need to "take care" of misplaced dashes (`/`), ideally
        if isinstance(filepath, str):
            if filepath.startswith('/'):
                filepath = filepath[1:]
            dirpath_archive = os.path.join(dirpath_fixtures, filepath, archive)
        else:
            raise TypeError('filepath must be a string starting with a maximum of one `/`')
    else:
        dirpath_archive = os.path.join(dirpath_fixtures, archive)

    if not os.path.isfile(dirpath_archive):
        dirpath_parent = os.path.dirname(dirpath_archive)
        raise ValueError('archive {} does not exist in the fixture directory {}'.format(archive, dirpath_parent))

    return dirpath_archive


def import_archive_fixture(archive, filepath=None):
    """Import a test fixture that is an AiiDA export archive

    :param archive: the relative filename of the archive
    :param filepath: the relative path of the archive file within the fixture directory
    """
    from aiida.orm.importexport import import_data

    dirpath_archive = get_archive_file(archive, filepath)

    import_data(dirpath_archive, silent=True)
