# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Test the AiiDA iPython magics."""
from IPython.testing.globalipapp import get_ipython

from aiida.tools.ipython.ipython_magics import register_ipython_extension


def test_ipython_magics():
    """Test that the %aiida magic can be loaded and adds the QueryBuilder and Node variables."""
    ipy = get_ipython()
    register_ipython_extension(ipy)

    cell = """
%aiida
qb=QueryBuilder()
qb.append(Node)
qb.all()
Dict().store()
"""
    result = ipy.run_cell(cell)

    assert result.success
