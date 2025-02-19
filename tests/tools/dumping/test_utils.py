
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for the dumping of process data to disk."""

import pytest 
from aiida.tools.dumping.utils import generate_group_default_dump_path,  generate_process_default_dump_path, generate_profile_default_dump_path

@pytest.mark.usefixtures('aiida_profile_clean')
def test_generate_process_default_dump_path(
    generate_calculation_node_add,
    generate_workchain_multiply_add,
):
    add_node = generate_calculation_node_add()
    multiply_add_node = generate_workchain_multiply_add()
    add_path = generate_process_default_dump_path(process_node=add_node)
    multiply_add_path = generate_process_default_dump_path(process_node=multiply_add_node)

    assert str(add_path) == f'dump-ArithmeticAddCalculation-{add_node.pk}'
    assert str(multiply_add_path) == f'dump-MultiplyAddWorkChain-{multiply_add_node.pk}'