# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for the AiiDA workchain Sphinx directive."""

from os.path import join, dirname

WORKCHAIN = join(dirname(__file__), 'workchain_source')


def test_workchain_build(build_sphinx, xml_equal, reference_result):
    """Test building sphinx documentation for WorkChain.

    Builds Sphinx documentation for workchain and compares against expected XML result.
    """
    out_dir = build_sphinx(WORKCHAIN)
    index_file = join(out_dir, 'index.xml')
    xml_equal(index_file, reference_result('workchain.py3.xml'))
