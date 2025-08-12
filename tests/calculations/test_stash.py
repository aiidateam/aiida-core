###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for the `StashCalculation` and `UnstashCalculation` plugin.

Note: testing the main functionality is done in via `test_execmanager.py`.
Here, we mainly check for redirection, of the calcjob.
Except for the `submit_custom_code` mode, which is not performed via func::execmanager::stash_calculation,
but via the `StashCalculation` itself. Therefore this one is tested in details.
"""

import logging

import pytest

from aiida import orm
from aiida.common.datastructures import StashMode, UnstashTargetMode
from aiida.plugins import CalculationFactory


@pytest.mark.requires_rmq
@pytest.mark.parametrize(
    'operation_type,entry_point_name',
    [
        ('stash', 'core.stash'),
        ('unstash', 'core.unstash'),
    ],
)
def test_calculation_basic(
    fixture_sandbox, aiida_computer_local, generate_calc_job, tmp_path, caplog, operation_type, entry_point_name
):
    """Test the basic implematation.
    Also check if it emits a warning in case the source node is on a different computer."""

    target_base = tmp_path / 'target'
    source = tmp_path / 'source'
    source.mkdir()

    a_computer = aiida_computer_local()
    a_different_computer = aiida_computer_local()
    assert a_computer.uuid != a_different_computer.uuid

    if operation_type == 'stash':
        operation_config = {
            'stash_mode': StashMode.COPY.value,
            'target_base': str(target_base),
            'source_list': ['*'],
        }
        source_node = orm.RemoteData(computer=a_different_computer, remote_path=str(source))
    else:  # unstash
        operation_config = {
            'unstash_target_mode': UnstashTargetMode.NewRemoteData.value,
            'source_list': ['*'],
        }
        source_node = orm.RemoteStashFolderData(
            computer=a_different_computer,
            stash_mode=StashMode.COPY,
            target_basepath=str(target_base),
            source_list=['*'],
        )

    inputs = {
        'metadata': {
            'computer': a_computer,
            'options': {
                'resources': {'num_machines': 1},
                operation_type: operation_config,
            },
        },
        'source_node': source_node,
    }

    calc_info = generate_calc_job(fixture_sandbox, entry_point_name, inputs)

    assert calc_info.skip_submit is True
    assert calc_info.codes_info == []
    assert calc_info.retrieve_list == []
    assert calc_info.local_copy_list == []
    assert calc_info.remote_copy_list == []
    assert calc_info.remote_symlink_list == []

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

    code = orm.InstalledCode(
        label='dummy_code',
        default_calc_job_plugin='core.stash',
        computer=orm.load_computer(label='localhost'),
        filepath_executable='/doesnot/exist/script.sh',
    )

    # Helper to create appropriate source node for unstash
    def create_unstash_source_node():
        if stash_mode == StashMode.SUBMIT_CUSTOM_CODE:
            return orm.RemoteStashCustomData(
                stash_mode=stash_mode, target_basepath=str(target_base), source_list=['*'], computer=aiida_localhost
            )
        elif stash_mode in (
            StashMode.COMPRESS_TAR,
            StashMode.COMPRESS_TARBZ2,
            StashMode.COMPRESS_TARGZ,
            StashMode.COMPRESS_TARXZ,
        ):
            return orm.RemoteStashCompressedData(
                stash_mode=stash_mode,
                target_basepath=str(target_base),
                source_list=['*'],
                dereference=False,
                computer=aiida_localhost,
            )
        else:
            return orm.RemoteStashFolderData(
                stash_mode=stash_mode, target_basepath=str(target_base), source_list=['*'], computer=aiida_localhost
            )

    # Stash input
    stash_input = {
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
        'code': code,
    }

    # Unstash input
    unstash_input = {
        'metadata': {
            'computer': aiida_localhost,
            'options': {
                'resources': {'num_machines': 1},
                'unstash': {
                    'unstash_target_mode': UnstashTargetMode.NewRemoteData.value,
                    'source_list': ['*'],
                },
            },
        },
        'source_node': create_unstash_source_node(),
        'code': code,
    }

    if stash_mode == StashMode.SUBMIT_CUSTOM_CODE:
        # Code is required - these should succeed
        generate_calc_job(fixture_sandbox, 'core.stash', stash_input)
        generate_calc_job(fixture_sandbox, 'core.unstash', unstash_input)

        # Test missing code raises error
        stash_no_code = stash_input.copy()
        stash_no_code.pop('code')
        with pytest.raises(ValueError, match=f"Input 'code' is required for `StashMode.{stash_mode}` mode."):
            generate_calc_job(fixture_sandbox, 'core.stash', stash_no_code)

        unstash_no_code = unstash_input.copy()
        unstash_no_code.pop('code')
        with pytest.raises(
            ValueError,
            match=f"Input 'code' is required for `UnstashTargetMode.{UnstashTargetMode.NewRemoteData}` mode.",
        ):
            generate_calc_job(fixture_sandbox, 'core.unstash', unstash_no_code)

    else:
        # Code is not allowed - add dereference for compression modes
        if stash_mode in (
            StashMode.COMPRESS_TAR,
            StashMode.COMPRESS_TARBZ2,
            StashMode.COMPRESS_TARGZ,
            StashMode.COMPRESS_TARXZ,
        ):
            stash_input['metadata']['options']['stash']['dereference'] = True

        # Test that providing code raises error
        stash_error_msg = (
            f"Input 'code' cannot be used for `StashMode.{stash_mode}` mode. "
            'This Stash mode is performed on the login node, no submission is planned therefore no code is needed.'
        )
        with pytest.raises(ValueError, match=stash_error_msg):
            generate_calc_job(fixture_sandbox, 'core.stash', stash_input)

        unstash_error_msg = (
            f"Input 'code' cannot be used for `UnstashTargetMode.{UnstashTargetMode.NewRemoteData}` mode. "
            'This UnStash mode is performed on the login node, no submission is planned therefore no code is needed.'
        )
        with pytest.raises(ValueError, match=unstash_error_msg):
            generate_calc_job(fixture_sandbox, 'core.unstash', unstash_input)


@pytest.mark.requires_rmq
@pytest.mark.parametrize('unstash_target_mode', [UnstashTargetMode.NewRemoteData, UnstashTargetMode.OriginalPlace])
def test_submit_custom_code(fixture_sandbox, aiida_localhost, generate_calc_job, tmp_path, unstash_target_mode):
    """Test the full functionality of the `StashCalculation` and `UnstashCalculation` with a custom code submission."""
    from pathlib import Path

    from aiida.engine import run, run_get_node

    # Setup source directory and files
    source = tmp_path / 'source'
    source.mkdir()
    test_files = {'dummy.txt': 'This is a dummy file.', 'very_dummy.txt': 'This is a very dummy file.'}
    for filename, content in test_files.items():
        (source / filename).write_text(content)

    # Setup target and executable
    target_base = tmp_path / 'target'
    executable = tmp_path / 'script.sh'
    executable.write_text("""#!/bin/bash\n\n
json=$(cat)
# Extract variables using jq
source_path=$(echo "$json" | jq -r '.source_path')
source_list=$(echo "$json" | jq -r '.source_list[]')
target_base=$(echo "$json" | jq -r '.target_base')

mkdir -p $target_base
for item in $source_list; do
    cp "$source_path/$item" "$target_base/"
    echo "$source_path/$item copied successfully."
done
\n""")
    executable.chmod(0o755)

    # Create and store code
    code = orm.InstalledCode(
        label='test_code',
        default_calc_job_plugin='core.stash',
        computer=orm.load_computer(label='localhost'),
        filepath_executable=str(executable),
    )
    code.store()

    source_node = orm.RemoteData(computer=aiida_localhost, remote_path=str(source))
    source_node.store()

    ### StashCalculation
    stash_inputs = {
        'metadata': {
            'computer': aiida_localhost,
            'options': {
                'resources': {'num_machines': 1},
                'stash': {
                    'stash_mode': StashMode.SUBMIT_CUSTOM_CODE.value,
                    'target_base': str(target_base),
                    'source_list': list(test_files.keys()),
                },
            },
        },
        'source_node': source_node,
        'code': code,
    }

    # Verify calc_info for stash
    calc_info = generate_calc_job(fixture_sandbox, 'core.stash', stash_inputs)
    code_info = calc_info.codes_info[0]
    assert calc_info.skip_submit is not True
    assert code_info.stdout_name in calc_info.retrieve_list
    assert calc_info.local_copy_list == []
    assert calc_info.remote_copy_list == []
    assert calc_info.remote_symlink_list == []

    # Run stash calculation
    stash_result = run_get_node(CalculationFactory('core.stash'), **stash_inputs)
    calcjob_remote_path_stash = stash_result[0]['remote_folder'].get_remote_path()

    # Find the stash data node
    stash_data_node = next(
        (
            link.node
            for link in stash_result[1].base.links.get_outgoing()
            if isinstance(link.node, orm.RemoteStashCustomData)
        ),
        None,
    )
    assert stash_data_node

    # Verify stash input file and results
    expected_stash_input = {
        'source_path': str(source),
        'source_list': list(test_files.keys()),
        'target_base': str(target_base),
    }
    actual_stash_input = Path(calcjob_remote_path_stash).joinpath('aiida.in').read_text().strip()
    assert actual_stash_input == str(expected_stash_input).replace("'", '"')

    # Verify files were stashed
    for filename, expected_content in test_files.items():
        stashed_file = Path(target_base) / filename
        assert stashed_file.exists()
        assert stashed_file.read_text() == expected_content

    ## Before Unstash we delete all files in the source directory
    for filename, content in test_files.items():
        Path(source / filename).unlink()

    ### UnstashCalculation
    unstash_inputs = {
        'metadata': {
            'computer': aiida_localhost,
            'options': {
                'resources': {'num_machines': 1},
                'unstash': {
                    'unstash_target_mode': unstash_target_mode.value,
                    'source_list': list(test_files.keys()),
                },
            },
        },
        'source_node': stash_data_node,
        'code': code,
    }

    # Verify calc_info for unstash
    calc_info = generate_calc_job(fixture_sandbox, 'core.unstash', unstash_inputs)
    code_info = calc_info.codes_info[0]
    assert calc_info.skip_submit is not True  # the value could be None or False
    assert code_info.stdout_name in calc_info.retrieve_list
    assert calc_info.local_copy_list == []
    assert calc_info.remote_copy_list == []
    assert calc_info.remote_symlink_list == []

    # Run unstash calculation
    unstash_result = run(CalculationFactory('core.unstash'), **unstash_inputs)
    calcjob_remote_path_unstash = unstash_result['remote_folder'].get_remote_path()
    expected_target_base = (
        source if unstash_target_mode == UnstashTargetMode.OriginalPlace else calcjob_remote_path_unstash
    )

    # Verify unstash input file
    expected_unstash_input = {
        'source_path': str(stash_data_node.target_basepath),
        'source_list': list(test_files.keys()),
        'target_base': str(expected_target_base),
    }
    actual_unstash_input = Path(calcjob_remote_path_unstash).joinpath('aiida.in').read_text().strip()
    assert actual_unstash_input == str(expected_unstash_input).replace("'", '"')

    # Verify files were unstashed
    for filename, expected_content in test_files.items():
        unstashed_file = Path(expected_target_base) / filename
        assert unstashed_file.exists()
        assert unstashed_file.read_text() == expected_content


@pytest.mark.usefixtures('aiida_profile_clean')
@pytest.mark.requires_rmq
@pytest.mark.parametrize(
    'unstash_target_mode', [UnstashTargetMode.OriginalPlace.value, UnstashTargetMode.NewRemoteData.value]
)
@pytest.mark.parametrize(
    'stash_mode',
    [
        StashMode.COPY.value,
        StashMode.COMPRESS_TAR.value,
        StashMode.COMPRESS_TARBZ2.value,
        StashMode.COMPRESS_TARGZ.value,
        StashMode.COMPRESS_TARXZ.value,
    ],
)
def test_all_modes(fixture_sandbox, aiida_localhost, generate_calc_job, tmp_path, stash_mode, unstash_target_mode):
    """Test the full functionality of the `StashCalculation` and `UnstashCalculation` for all other modes"""
    from pathlib import Path

    # Setup source directory and files
    from aiida.common.utils import get_new_uuid
    from aiida.engine import run, run_get_node

    uuid = get_new_uuid()
    source = tmp_path / uuid[:2] / uuid[2:4] / uuid[4:]
    source.mkdir(parents=True)
    test_files = {'dummy.txt': 'This is a dummy file.', 'very_dummy.txt': 'This is a very dummy file.'}
    for filename, content in test_files.items():
        (source / filename).write_text(content)

    # Setup target and executable
    target_base = tmp_path / 'target'

    source_node = orm.RemoteData(computer=aiida_localhost, remote_path=str(source))
    source_node.store()

    ### StashCalculation
    stash_inputs = {
        'metadata': {
            'computer': aiida_localhost,
            'options': {
                'resources': {'num_machines': 1},
                'stash': {
                    'stash_mode': stash_mode,
                    'target_base': str(target_base),
                    'source_list': list(test_files.keys()),
                },
            },
        },
        'source_node': source_node,
    }
    if stash_mode in [
        StashMode.COMPRESS_TAR.value,
        StashMode.COMPRESS_TARBZ2.value,
        StashMode.COMPRESS_TARGZ.value,
        StashMode.COMPRESS_TARXZ.value,
    ]:
        stash_inputs['metadata']['options']['stash']['dereference'] = True

    # Run stash calculation
    stash_result = run_get_node(CalculationFactory('core.stash'), **stash_inputs)
    stash_result[0]['remote_folder'].get_remote_path()
    # Find the stash data node
    stash_data_node = next(
        (
            link.node
            for link in stash_result[1].base.links.get_outgoing()
            if isinstance(
                link.node,
                orm.RemoteStashFolderData if stash_mode == StashMode.COPY.value else orm.RemoteStashCompressedData,
            )
        ),
        None,
    )
    assert stash_data_node

    # Verify files were stashed
    if stash_mode == StashMode.COPY.value:
        expected_base = Path(target_base) / source_node.uuid[0:2] / source_node.uuid[2:4] / source_node.uuid[4:]
    else:
        temp_for_extract = tmp_path / 'extract'
        temp_for_extract.mkdir()
        with aiida_localhost.get_transport() as transport:
            transport.extract(stash_data_node.target_basepath, temp_for_extract, strip_components=3)

        expected_base = temp_for_extract

    for filename, expected_content in test_files.items():
        stashed_file = expected_base / filename
        assert stashed_file.exists()
        assert stashed_file.read_text() == expected_content

    ## Before Unstash we delete all files in the source directory
    for filename, content in test_files.items():
        Path(source / filename).unlink()

    ### UnstashCalculation
    unstash_inputs = {
        'metadata': {
            'computer': aiida_localhost,
            'options': {
                'resources': {'num_machines': 1},
                'unstash': {
                    'unstash_target_mode': unstash_target_mode,
                    'source_list': list(test_files.keys()),
                },
            },
        },
        'source_node': stash_data_node,
    }

    # Run unstash calculation
    unstash_result = run(CalculationFactory('core.unstash'), **unstash_inputs)
    calcjob_remote_path_unstash = unstash_result['remote_folder'].get_remote_path()
    expected_target_base = (
        source if unstash_target_mode == UnstashTargetMode.OriginalPlace.value else calcjob_remote_path_unstash
    )

    # Verify files were unstashed
    for filename, expected_content in test_files.items():
        unstashed_file = Path(expected_target_base) / filename
        assert unstashed_file.exists()
        assert unstashed_file.read_text() == expected_content
