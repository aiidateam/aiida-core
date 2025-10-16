###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for the `TemplatereplacerCalculation` plugin."""

import io

import pytest

from aiida import orm
from aiida.common import datastructures


@pytest.mark.requires_rmq
def test_base_template(fixture_sandbox, aiida_localhost, generate_calc_job):
    """Test a base template that emulates the arithmetic add."""
    entry_point_name = 'core.templatereplacer'
    inputs = {
        'code': orm.InstalledCode(computer=aiida_localhost, filepath_executable='/bin/bash'),
        'metadata': {'options': {'resources': {'num_machines': 1, 'tot_num_mpiprocs': 1}}},
        'template': orm.Dict(
            dict={
                'input_file_template': 'echo $(({x} + {y}))',
                'input_file_name': 'input.txt',
                'cmdline_params': ['input.txt'],
                'output_file_name': 'output.txt',
            }
        ),
        'parameters': orm.Dict(dict={'x': 1, 'y': 2}),
    }

    # Check the attributes of the resulting `CalcInfo`
    calc_info = generate_calc_job(fixture_sandbox, entry_point_name, inputs)
    assert isinstance(calc_info, datastructures.CalcInfo)
    assert sorted(calc_info.retrieve_list) == sorted([inputs['template']['output_file_name']])

    # Check the integrity of the `codes_info`
    codes_info = calc_info.codes_info
    assert isinstance(codes_info, list)
    assert len(codes_info) == 1

    # Check the attributes of the resulting `CodeInfo`
    code_info = codes_info[0]
    assert isinstance(code_info, datastructures.CodeInfo)
    assert code_info.code_uuid == inputs['code'].uuid
    assert code_info.stdout_name == inputs['template']['output_file_name']
    assert sorted(code_info.cmdline_params) == sorted(inputs['template']['cmdline_params'])

    # Check the content of the generated script
    with fixture_sandbox.open(inputs['template']['input_file_name']) as handle:
        input_written = handle.read()
        assert input_written == f"echo $(({inputs['parameters']['x']} + {inputs['parameters']['y']}))"


@pytest.mark.requires_rmq
def test_file_usage(fixture_sandbox, aiida_localhost, generate_calc_job):
    """Test a base template that uses two files."""
    file1_node = orm.SinglefileData(io.BytesIO(b'Content of file 1'))
    file2_node = orm.SinglefileData(io.BytesIO(b'Content of file 2'))

    # Check that the files are correctly copied to the copy list
    entry_point_name = 'core.templatereplacer'
    inputs = {
        'code': orm.InstalledCode(computer=aiida_localhost, filepath_executable='/bin/bash'),
        'metadata': {'options': {'resources': {'num_machines': 1, 'tot_num_mpiprocs': 1}}},
        'template': orm.Dict(
            dict={
                'files_to_copy': [('filenode1', 'file1.txt'), ('filenode2', 'file2.txt')],
            }
        ),
        'files': {'filenode1': file1_node, 'filenode2': file2_node},
    }

    calc_info = generate_calc_job(fixture_sandbox, entry_point_name, inputs)
    reference_copy_list = []
    for node_idname, target_path in inputs['template']['files_to_copy']:
        file_node = inputs['files'][node_idname]
        reference_copy_list.append((file_node.uuid, file_node.filename, target_path))

    assert sorted(calc_info.local_copy_list) == sorted(reference_copy_list)
