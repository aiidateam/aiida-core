# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Test run on containrized code."""
from aiida import orm
from aiida.engine import run_get_node
from aiida.plugins import CalculationFactory

ArithmeticAddCalculation = CalculationFactory('core.arithmetic.add')

inputs = {
    'code': orm.load_code('add-docker@localhost'),
    'x': orm.Int(4),
    'y': orm.Int(6),
    'metadata': {
        'options': {
            'resources': {
                'num_machines': 1,
                'num_mpiprocs_per_machine': 1
            }
        }
    }
}

res, node = run_get_node(ArithmeticAddCalculation, **inputs)
assert 'sum' in res
assert 'remote_folder' in res
assert 'retrieved' in res
assert res['sum'].value == 10
