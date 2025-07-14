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
Except for the `submit_custom_code` mode, which is not performed via func::execmanager::stash_calculation,
but via the `StashCalculation` itself. Therefore this one is tested in details.
"""

import pytest

from aiida import orm
from aiida.common.datastructures import StashMode
from aiida.plugins import CalculationFactory


@pytest.mark.requires_rmq
def test_stash_calculation_basic(fixture_sandbox, aiida_localhost, generate_calc_job, tmp_path):
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
def test_stash_calculation_different_computer(
    fixture_sandbox, aiida_computer_local, generate_calc_job, tmp_path, caplog
):
    """Test it emits a warning if the source node is on a different computer."""

    target_base = tmp_path / 'target'
    source = tmp_path / 'source'
    source.mkdir()

    a_computer = aiida_computer_local()
    a_different_computer = aiida_computer_local()
    assert a_computer.uuid != a_different_computer.uuid

    inputs = {
        'metadata': {
            'computer': a_computer,
            'options': {
                'resources': {'num_machines': 1},
                'stash': {
                    'stash_mode': StashMode.COPY.value,
                    'target_base': str(target_base),
                    'source_list': ['*'],
                },
            },
        },
        'source_node': orm.RemoteData(computer=a_different_computer, remote_path=str(source)),
    }
    entry_point_name = 'core.stash'
    generate_calc_job(fixture_sandbox, entry_point_name, inputs)

    import logging

    with caplog.at_level(logging.WARNING):
        assert any(
            'YOUR SETTING MIGHT RESULT IN A SILENT FAILURE!'
            ' The computer of the source node and the computer of the calculation are strongly advised be the same.'
            in message
            for message in caplog.messages
        )


@pytest.mark.parametrize(
    'stash_mode',
    [mode for mode in StashMode],
)
def test_code_vs_stash_mode_conflict(stash_mode, fixture_sandbox, aiida_localhost, generate_calc_job, tmp_path):
    """Test that the `StashCalculation` raises an error if the `code` input is not compatible with the `stash_mode`."""

    from aiida import orm

    target_base = tmp_path / 'target'
    source = tmp_path / 'source'
    source.mkdir()

    inputs = {
        'metadata': {
            'computer': aiida_localhost,
            'options': {
                'resources': {'num_machines': 1},
                'stash': {
                    'stash_mode': stash_mode.value,
                    'target_base': str(target_base),
                    'source_list': ['*'],
                },
            },
        },
        'source_node': orm.RemoteData(computer=aiida_localhost, remote_path=str(source)),
        'code': orm.InstalledCode(
            label='dummy_code',
            default_calc_job_plugin='core.stash',
            computer=orm.load_computer(label='localhost'),
            filepath_executable='/doesnot/exist/script.sh',
        ),
    }

    if stash_mode == StashMode.SUBMIT_CUSTOM_CODE:
        # 'code' has to be provided
        generate_calc_job(fixture_sandbox, 'core.stash', inputs)
        with pytest.raises(ValueError, match=f"Input 'code' is required for `StashMode.{StashMode(stash_mode)}` mode."):
            inputs.pop('code')
            generate_calc_job(fixture_sandbox, 'core.stash', inputs)

    elif stash_mode in (
        StashMode.COMPRESS_TAR,
        StashMode.COMPRESS_TARBZ2,
        StashMode.COMPRESS_TARGZ,
        StashMode.COMPRESS_TARXZ,
    ):
        inputs['metadata']['options']['stash']['dereference'] = True
        with pytest.raises(
            ValueError,
            match=f"Input 'code' cannot be used for `StashMode.{StashMode(stash_mode)}` mode. "
            'This Stash mode is performed on the login node, no submission is planned therefore no code is needed.',
        ):
            generate_calc_job(fixture_sandbox, 'core.stash', inputs)
    else:
        with pytest.raises(
            ValueError,
            match=f"Input 'code' cannot be used for `StashMode.{StashMode(stash_mode)}` mode. "
            'This Stash mode is performed on the login node, no submission is planned therefore no code is needed.',
        ):
            generate_calc_job(fixture_sandbox, 'core.stash', inputs)


@pytest.mark.requires_rmq
def test_submit_custom_code(fixture_sandbox, aiida_localhost, generate_calc_job, tmp_path):
    """Test the full functionality of the `StashCalculation` with a custom code submission."""

    from pathlib import Path

    from aiida.engine import run

    source = tmp_path / 'source'
    source.mkdir()
    # create a dummy file in the source directory
    (source / 'dummy.txt').write_text('This is a dummy file.')
    (source / 'very_dummy.txt').write_text('This is a very dummy file.')

    target_base = tmp_path / 'target'
    executable = tmp_path / 'script.sh'
    executable.write_text("""#!/bin/bash\n\n
json=$(cat)
# Extract variables using jq
working_directory=$(echo "$json" | jq -r '.working_directory')
source_list=$(echo "$json" | jq -r '.source_list[]')
target_base=$(echo "$json" | jq -r '.target_base')

mkdir $target_base
for item in $source_list; do
    cp "$working_directory/$item" "$target_base/"
    echo "$working_directory/$item copied successfully."
done
\n""")

    executable.chmod(0o755)  # Make the script executable

    code = orm.InstalledCode(
        label='xx',
        default_calc_job_plugin='core.stash',
        computer=orm.load_computer(label='localhost'),
        filepath_executable=str(executable),
    )
    code.store()

    source_node = orm.RemoteData(computer=aiida_localhost, remote_path=str(source))
    source_node.store()

    stashcalculation_ = CalculationFactory('core.stash')
    inputs = {
        'metadata': {
            'computer': aiida_localhost,
            'options': {
                'resources': {'num_machines': 1},
                'stash': {
                    'stash_mode': StashMode.SUBMIT_CUSTOM_CODE.value,
                    'target_base': str(target_base),
                    'source_list': ['dummy.txt', 'very_dummy.txt'],
                },
            },
        },
        'source_node': source_node,
        'code': orm.load_code(label='xx'),
    }

    # TODO, check if 'code' is provided it should raise

    # Check if calc_info is generated correctly
    calc_info = generate_calc_job(fixture_sandbox, 'core.stash', inputs)
    code_info = calc_info.codes_info[0]

    assert calc_info.skip_submit is not True  # the value could be None or False
    assert code_info.stdout_name in calc_info.retrieve_list
    assert calc_info.local_copy_list == []
    assert calc_info.remote_copy_list == []
    assert calc_info.remote_symlink_list == []

    # Ignore the calc_info, and now actually run the calculation
    result = run(stashcalculation_, **inputs)
    calcjob_remote_path = result['remote_folder'].get_remote_path()

    # Check that the input file `aiida.in` is created with the expected content
    assert (
        Path(calcjob_remote_path).joinpath('aiida.in').read_text().strip()
        == '{"working_directory": "'
        + str(source)
        + '", "source_list": ["dummy.txt", "very_dummy.txt"], "target_base": "'
        + str(target_base)
        + '"}'
    )

    # Check if stashing was successful
    Path(target_base).joinpath('dummy.txt').exists()
    Path(target_base).joinpath('very_dummy.txt').exists()
    assert Path(target_base).joinpath('dummy.txt').read_text() == 'This is a dummy file.'
    assert Path(target_base).joinpath('very_dummy.txt').read_text() == 'This is a very dummy file.'
