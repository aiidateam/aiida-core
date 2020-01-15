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
    out_dir, completed_proc = build_sphinx(WORKCHAIN)
    assert completed_proc.returncode == 0
    index_file = join(out_dir, 'index.xml')
    xml_equal(index_file, reference_result('workchain.xml'))


def test_broken_workchain_build(build_sphinx):
    """Test building sphinx documentation with a broken WorkChain.

    This test checks that the error raised in the WorkChain's define is correctly
    shown when building the documentation.
    """
    _, completed_proc = build_sphinx(join(dirname(__file__), 'workchain_source_broken'))
    assert completed_proc.returncode != 0
    stderr_decoded = completed_proc.stderr.decode('utf-8')
    assert 'The broken workchain says hi!' in stderr_decoded
    assert 'ValueError' in stderr_decoded
