###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for the `StashCalculation` plugin.

Note: testing the main functionality is done in via `test_execmanager.py`.
Here, we mainly check for redirection, of the calcjob.
"""

import pytest

from aiida import orm
from aiida.common.datastructures import StashMode


@pytest.mark.requires_rmq
def test_basic(fixture_sandbox, aiida_localhost, generate_calc_job, tmp_path):
    """Test that the `StashCalculation` basic implementation."""

    target_base = tmp_path / 'target'
    source = tmp_path / 'source'
    source.mkdir()

    inputs = {
        'metadata': {
            'computer': aiida_localhost,
            'options': {
                'resources': {'num_machines': 1},
                'stash': {
                    'stash_mode': StashMode.COPY.value,
                    'target_base': str(target_base),
                    'source_list': ['*'],
                },
            },
        },
        'source_node': orm.RemoteData(computer=aiida_localhost, remote_path=str(source)),
    }
    entry_point_name = 'core.stash'
    calc_info = generate_calc_job(fixture_sandbox, entry_point_name, inputs)

    assert calc_info.skip_submit is True

    assert calc_info.codes_info == []
    assert calc_info.retrieve_list == []
    assert calc_info.local_copy_list == []
    assert calc_info.remote_copy_list == []
    assert calc_info.remote_symlink_list == []


@pytest.mark.requires_rmq
def test_custom_script(fixture_sandbox, aiida_localhost, generate_calc_job, tmp_path):
    """Test basic implementation of `StashCalculation`."""

    source = tmp_path / 'source'
    source.mkdir()

    source_node = orm.RemoteData(computer=aiida_localhost, remote_path=str(source))
    source_node.store()
    the_command = 'rsync -av aiida.in _aiidasubmit.sh /scratch/my_stashing/'
    inputs = {
        'metadata': {
            'computer': aiida_localhost,
            'options': {
                'resources': {'num_machines': 1},
                'stash': {
                    'stash_mode': StashMode.CUSTOM_SCRIPT.value,
                    'custom_command': the_command,
                },
            },
        },
        'source_node': source_node,
    }
    entry_point_name = 'core.stash'
    calc_info = generate_calc_job(fixture_sandbox, entry_point_name, inputs)
    code_info = calc_info.codes_info[0]

    assert calc_info.skip_submit is not True  # the value could be None or False
    assert code_info.stdout_name in calc_info.retrieve_list
    assert calc_info.local_copy_list == []
    assert calc_info.remote_copy_list == []
    assert calc_info.remote_symlink_list == []

    # Tests here could be more sophisticated
    # with open(tmp_path / code_info.stdin_name, 'r') as handle:
    #     content = handle.read()

    #     assert f'cd {str(source)}\n' in content
    #     assert the_command in content
