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
def test_stash_calculation_basic(fixture_sandbox, aiida_localhost, generate_calc_job, tmp_path):
    """Test that the basic implementation of `StashCalculation` functions."""

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
