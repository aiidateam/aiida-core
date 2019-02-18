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


def import_archive_fixture(filepath):
    """Import a test fixture that is an AiiDA export archive

    :param filepath: the relative path of the archive file within the fixture directory
    """
    from aiida.orm.importexport import import_data

    filepath_current = os.path.dirname(os.path.realpath(__file__))
    filepath_fixtures = os.path.join(filepath_current, os.pardir, 'fixtures')
    filepath_archive = os.path.join(filepath_fixtures, filepath)

    if not os.path.isfile(filepath_archive):
        raise ValueError('archive {} does not exist in the fixture directory {}'.format(filepath, filepath_fixtures))

    import_data(filepath_archive, silent=True)
