# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for the `ArithmeticAddCalculation` plugin."""
import pytest

from aiida import orm
from aiida.common import datastructures
from aiida.calculations.arithmetic.add import ArithmeticAddCalculation


@pytest.mark.usefixtures('clear_database_before_test')
def test_add_default(fixture_sandbox, aiida_localhost, generate_calc_job):
    """Test a default `ArithmeticAddCalculation`."""
    entry_point_name = 'arithmetic.add'
    inputs = {'x': orm.Int(1), 'y': orm.Int(2), 'code': orm.Code(remote_computer_exec=(aiida_localhost, '/bin/bash'))}

    calc_info = generate_calc_job(fixture_sandbox, entry_point_name, inputs)
    options = ArithmeticAddCalculation.spec().inputs['metadata']['options']

    # Check the attributes of the returned `CalcInfo`
    assert isinstance(calc_info, datastructures.CalcInfo)
    assert sorted(calc_info.retrieve_list) == sorted([options['output_filename'].default])

    codes_info = calc_info.codes_info
    assert isinstance(codes_info, list)
    assert len(codes_info) == 1

    code_info = codes_info[0]
    assert isinstance(code_info, datastructures.CodeInfo)
    assert code_info.code_uuid == inputs['code'].uuid
    assert code_info.stdin_name == options['input_filename'].default
    assert code_info.stdout_name == options['output_filename'].default

    with fixture_sandbox.open(options['input_filename'].default) as handle:
        input_written = handle.read()
        assert input_written == 'echo $(({} + {}))\n'.format(inputs['x'].value, inputs['y'].value)


@pytest.mark.usefixtures('clear_database_before_test')
def test_add_custom_filenames(fixture_sandbox, aiida_localhost, generate_calc_job):
    """Test an `ArithmeticAddCalculation` with non-default input and output filenames."""
    entry_point_name = 'arithmetic.add'
    input_filename = 'custom.in'
    output_filename = 'custom.out'
    inputs = {
        'x': orm.Int(1),
        'y': orm.Int(2),
        'code': orm.Code(remote_computer_exec=(aiida_localhost, '/bin/bash')),
        'metadata': {
            'options': {
                'input_filename': input_filename,
                'output_filename': output_filename,
            }
        }
    }

    calc_info = generate_calc_job(fixture_sandbox, entry_point_name, inputs)
    code_info = calc_info.codes_info[0]

    assert code_info.stdin_name == input_filename
    assert code_info.stdout_name == output_filename
    assert calc_info.retrieve_list == [output_filename]
