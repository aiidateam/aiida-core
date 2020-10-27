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
import pytest


def test_workchain_build(sphinx_build_factory, xml_equal, reference_result):
    """Test building sphinx documentation for WorkChain.

    Builds Sphinx documentation for workchain and compares against expected XML result.
    """
    sphinx_build = sphinx_build_factory('workchain', buildername='xml')
    sphinx_build.build(assert_pass=True)

    index_file = sphinx_build.outdir / 'index.xml'
    xml_equal(index_file, reference_result('workchain.xml'))


def test_broken_workchain_build(sphinx_build_factory):
    """Test building sphinx documentation with a broken WorkChain.

    This test checks that the error raised in the WorkChain's define is correctly
    shown when building the documentation.
    """
    sphinx_build = sphinx_build_factory('workchain_broken')
    with pytest.raises(RuntimeError, match='The broken workchain says hi!'):
        sphinx_build.build()
