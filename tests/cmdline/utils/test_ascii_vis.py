###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for the :mod:`aiida.cmdline.utils.ascii_vis` module."""

from aiida.orm.nodes.process.process import ProcessNode


def test_build_call_graph():
    from aiida.cmdline.utils.ascii_vis import build_call_graph

    node = ProcessNode()

    call_graph = build_call_graph(node)
    assert call_graph == 'None<None> None'
