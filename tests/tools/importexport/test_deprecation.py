# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Test deprecated parts still work and emit deprecations warnings"""
# pylint: disable=invalid-name
import os

import pytest

from aiida.common.warnings import AiidaDeprecationWarning
from aiida.tools.importexport import dbexport

pytestmark = pytest.mark.usefixtures('clear_database_before_test')


def test_export_functions(temp_dir):
    """Check `what` and `outfile` in export(), export_tar() and export_zip()"""
    what = []
    outfile = os.path.join(temp_dir, 'deprecated.aiida')

    for export_function in (dbexport.export, dbexport.export_tar, dbexport.export_zip):
        if os.path.exists(outfile):
            os.remove(outfile)
        with pytest.warns(AiidaDeprecationWarning, match='`what` is deprecated, please use `entities` instead'):
            export_function(what=what, filename=outfile)

        if os.path.exists(outfile):
            os.remove(outfile)
        with pytest.warns(
            AiidaDeprecationWarning, match='`what` is deprecated, the supplied `entities` input will be used'
        ):
            export_function(entities=what, what=what, filename=outfile)

        if os.path.exists(outfile):
            os.remove(outfile)
        with pytest.warns(
            AiidaDeprecationWarning,
            match='`outfile` is deprecated, please use `filename` instead',
        ):
            export_function(what, outfile=outfile)

        if os.path.exists(outfile):
            os.remove(outfile)
        with pytest.warns(
            AiidaDeprecationWarning, match='`outfile` is deprecated, the supplied `filename` input will be used'
        ):
            export_function(what, filename=outfile, outfile=outfile)

        if os.path.exists(outfile):
            os.remove(outfile)
        with pytest.raises(TypeError, match='`entities` must be specified'):
            export_function(filename=outfile)


def test_export_tree():
    """Check `what` in export_tree()"""
    from aiida.common.folders import SandboxFolder

    what = []

    with SandboxFolder() as folder:
        with pytest.warns(AiidaDeprecationWarning, match='`what` is deprecated, please use `entities` instead'):
            dbexport.export_tree(what=what, folder=folder)

        folder.erase(create_empty_folder=True)
        with pytest.warns(
            AiidaDeprecationWarning, match='`what` is deprecated, the supplied `entities` input will be used'
        ):
            dbexport.export_tree(entities=what, what=what, folder=folder)

        folder.erase(create_empty_folder=True)
        with pytest.raises(TypeError, match='`entities` must be specified'):
            dbexport.export_tree(folder=folder)

        folder.erase(create_empty_folder=True)
        with pytest.raises(TypeError, match='`folder` must be specified'):
            dbexport.export_tree(entities=what)
