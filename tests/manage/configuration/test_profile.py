###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for the :class:`aiida.manage.configuration.profile.Profile` class."""

import uuid
from datetime import datetime, timedelta

import pytest

from aiida import orm
from aiida.tools._dumping.utils import DumpPaths


def test_base_properties(profile_factory):
    """Test the basic properties of a ``Profile`` instance."""
    kwargs = {
        'name': 'profile-name',
        'storage_backend': 'core.psql_dos',
        'process_control_backend': 'rabbitmq',
    }
    profile = profile_factory(**kwargs)

    assert profile.name == kwargs['name']
    assert profile.storage_backend == kwargs['storage_backend']
    assert profile.process_control_backend == kwargs['process_control_backend']

    # Verify that the uuid property returns a valid UUID by attempting to construct an UUID instance from it
    uuid.UUID(profile.uuid)

    # Check that the default user email field is not None
    assert profile.default_user_email is not None


@pytest.mark.parametrize('test_profile', (True, False))
def test_is_test_profile(profile_factory, test_profile):
    """Test the :meth:`aiida.manage.configuration.profile.is_test_profile` property."""
    profile = profile_factory(test_profile=test_profile)
    assert profile.is_test_profile is test_profile


def test_set_option(profile_factory):
    """Test the `set_option` method."""
    profile = profile_factory()
    option_key = 'daemon.timeout'
    option_value_one = 999
    option_value_two = 666

    # Setting an option if it does not exist should work
    profile.set_option(option_key, option_value_one)
    assert profile.get_option(option_key) == option_value_one

    # Setting it again will override it by default
    profile.set_option(option_key, option_value_two)
    assert profile.get_option(option_key) == option_value_two

    # If we set override to False, it should not override, big surprise
    profile.set_option(option_key, option_value_one, override=False)
    assert profile.get_option(option_key) == option_value_two


TEST_GROUP_LABEL = 'test_profile_dump_group'


@pytest.fixture
@pytest.mark.usefixtures('aiida_profile_clean')
def profile_with_minimal_data():
    """Create a profile with some test data."""
    # Get current profile
    from aiida import load_profile

    profile = load_profile()

    # Create some test data
    group = orm.Group(label=TEST_GROUP_LABEL).store()
    calc_node = orm.CalculationNode().store().seal()
    data_node = orm.Int(42).store()
    _ = orm.WorkflowNode().store().seal()

    group.add_nodes([calc_node, data_node])

    return profile


@pytest.fixture
@pytest.mark.usefixtures('aiida_profile_clean')
def profile_with_actual_data(generate_calculation_node_io, generate_workchain_node_io):
    """Create a profile with some test data."""
    # Get current profile
    from aiida import load_profile

    profile = load_profile()

    # Create some test data
    group = orm.Group(label=TEST_GROUP_LABEL).store()
    cj_nodes = [
        generate_calculation_node_io(attach_outputs=False),
        generate_calculation_node_io(attach_outputs=False),
    ]
    wc_node = generate_workchain_node_io(cj_nodes=cj_nodes)

    group.add_nodes(cj_nodes + [wc_node])

    return profile


@pytest.mark.usefixtures('aiida_profile_clean')
class TestProfileDump:
    """Test the dump method of Profile."""

    def test_dump_dry_run(self, capsys, tmp_path, profile_with_minimal_data):
        """Test dry run mode doesn't create files."""
        profile = profile_with_minimal_data
        output_path = tmp_path / 'profile_dump'

        result_path = profile.dump(
            output_path=output_path,
            dry_run=True,
        )

        # In dry run, None is returned and no files are created
        assert result_path == output_path
        assert not result_path.exists()

        captured = capsys.readouterr()

        # Assert on the anticipated dump changes output
        assert 'Anticipated dump changes' in captured.out
        assert 'Nodes:' in captured.out
        assert 'Entity Type' in captured.out
        assert 'Count' in captured.out
        assert 'Status' in captured.out
        assert 'Calculations' in captured.out
        assert 'Workflows' in captured.out
        assert 'new/modified' in captured.out
        assert 'Groups:' in captured.out
        assert 'Node memberships' in captured.out

    def test_dump_overwrite(self, tmp_path, profile_with_minimal_data):
        """Test overwrite functionality."""
        profile = profile_with_minimal_data
        output_path = tmp_path / 'profile_dump_overwrite'

        # First dump
        result_path1 = profile.dump(output_path=output_path, all_entries=True)
        assert result_path1.exists()

        # Second dump with overwrite should succeed
        result_path2 = profile.dump(output_path=output_path, all_entries=True, overwrite=True)
        assert result_path2.exists()
        assert result_path1 == result_path2

    def test_dump_basic_all_entries(self, tmp_path, profile_with_minimal_data):
        """Test basic dumping of entire profile."""
        profile = profile_with_minimal_data
        output_path = tmp_path / 'profile_dump_all'

        result_path = profile.dump(output_path=output_path, all_entries=True)

        # Check that dump was created
        assert result_path.exists()
        assert result_path.is_dir()

        # Check for expected files
        assert (result_path / '.aiida_dump_safeguard').exists()

    def test_dump_specific_groups(self, tmp_path, profile_with_minimal_data):
        """Test dumping specific groups only."""
        profile = profile_with_minimal_data
        output_path = tmp_path / 'profile_dump_groups'

        # Get the test group we created
        group = orm.Group.collection.get(label=TEST_GROUP_LABEL)
        extra_group = orm.Group(label='extra_group').store()

        result_path = profile.dump(output_path=output_path, groups=[group])

        assert result_path.exists()
        assert result_path.is_dir()
        assert (result_path / 'groups' / group.label).exists()
        assert not (result_path / 'groups' / extra_group.label).exists()

        # Test dumping by label
        _ = DumpPaths._safe_delete_directory(path=result_path)
        result_path = profile.dump(output_path=output_path, groups=[TEST_GROUP_LABEL])

        assert result_path.exists()
        assert result_path.is_dir()
        assert (result_path / 'groups' / group.label).exists()
        assert not (result_path / 'groups' / extra_group.label).exists()

    def test_dump_by_user(self, tmp_path, profile_with_minimal_data):
        """Test dumping data for specific user."""
        profile = profile_with_minimal_data
        output_path = tmp_path / 'profile_dump_user'

        default_user = orm.User.collection.get_default()

        # Create a second user
        other_user = orm.User(email='other@example.com', first_name='Other', last_name='User')
        other_user.store()

        # Create a calculation node for the other user
        other_calc = orm.CalculationNode()
        other_calc.user = other_user
        other_calc.store().seal()

        group = orm.load_group(TEST_GROUP_LABEL)
        group.add_nodes(other_calc)

        result_path = profile.dump(
            output_path=output_path,
            user=default_user,
            groups=[TEST_GROUP_LABEL],
        )

        assert result_path.exists()
        assert result_path.is_dir()
        assert (result_path / 'groups' / TEST_GROUP_LABEL / 'calculations').exists()
        # Calculation created by other user is not dumped
        assert not (result_path / 'groups' / TEST_GROUP_LABEL / 'calculations' / f'{other_calc.pk}').exists()

    def test_dump_empty_scope_returns_none(self, tmp_path, profile_with_minimal_data, caplog):
        """Test that dumping with no scope returns None."""
        profile = profile_with_minimal_data
        output_path = tmp_path / 'profile_dump_empty'

        _ = profile.dump(output_path=output_path)

        assert 'No profile data explicitly selected. No dump will be performed.' in caplog.text
        assert caplog.records[-1].levelname == 'WARNING'

    def test_dump_with_time_filters(self, tmp_path, profile_with_minimal_data):
        """Test dumping with time-based filters."""
        profile = profile_with_minimal_data
        output_path = tmp_path / 'profile_dump_time'

        # Test with past_days filter
        result_path = profile.dump(output_path=output_path, all_entries=True, past_days=7)
        assert result_path.exists()

        # Test with date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=1)

        result_path2 = profile.dump(
            output_path=output_path / 'date_range', all_entries=True, start_date=start_date, end_date=end_date
        )
        assert result_path2.exists()

    def test_dump_organize_by_groups(self, tmp_path, profile_with_minimal_data):
        """Test dumping organized by groups."""
        profile = profile_with_minimal_data
        output_path = tmp_path / 'profile_dump_organized'

        result_path = profile.dump(
            output_path=output_path, all_entries=True, organize_by_groups=True, also_ungrouped=True
        )
        assert result_path.exists()
        assert (result_path / 'groups').exists()
        assert (result_path / 'ungrouped').exists()
        assert (result_path / 'ungrouped' / 'workflows').exists()

        _ = DumpPaths._safe_delete_directory(path=result_path)
        result_path = profile.dump(
            output_path=output_path, all_entries=True, organize_by_groups=False, also_ungrouped=True
        )
        assert result_path.exists()
        assert (result_path / 'calculations').exists()
        assert (result_path / 'workflows').exists()

    def test_dump_with_relabel_groups(self, tmp_path, profile_with_minimal_data):
        """Test dumping with group relabeling."""
        profile = profile_with_minimal_data
        output_path = tmp_path / 'profile_dump_relabel'

        result_path = profile.dump(
            output_path=output_path, all_entries=True, organize_by_groups=True, relabel_groups=True
        )
        assert result_path.exists()
        assert (result_path / 'groups' / TEST_GROUP_LABEL).exists()

        # Now relabel the group
        group = orm.load_group(TEST_GROUP_LABEL)
        group.label = 'relabeled'

        result_path = profile.dump(
            output_path=output_path, all_entries=True, organize_by_groups=True, relabel_groups=True
        )
        assert (result_path / 'groups' / 'relabeled').exists()

    def test_dump_only_top_level_calcs(self, tmp_path, profile_with_minimal_data, generate_workchain_multiply_add):
        """Test dumping with node collection filters."""
        profile = profile_with_minimal_data
        output_path = tmp_path / 'profile_dump_filters'
        _ = generate_workchain_multiply_add()

        result_path = profile.dump(
            output_path=output_path, all_entries=True, only_top_level_calcs=True, also_ungrouped=True
        )

        assert result_path.exists()
        assert not (result_path / 'ungrouped' / 'calculations').exists()

        _ = DumpPaths._safe_delete_directory(path=result_path)
        result_path = profile.dump(
            output_path=output_path,
            all_entries=True,
            only_top_level_calcs=False,
            also_ungrouped=True,
        )

        assert result_path.exists()
        assert (result_path / 'ungrouped' / 'calculations').exists()

    def test_dump_with_computers_and_codes(self, tmp_path, profile_with_minimal_data):
        """Test dumping with computer and code filters."""
        profile = profile_with_minimal_data
        output_path = tmp_path / 'profile_dump_comp_codes'

        # Create a computer and code for testing
        computer = orm.Computer(
            label='test_computer', hostname='localhost', transport_type='core.local', scheduler_type='core.direct'
        ).store()
        code = orm.InstalledCode(label='test_code', computer=computer, filepath_executable='/bin/bash').store()

        with pytest.raises(ValueError):
            result_path = profile.dump(output_path=output_path, computers=[computer], codes=[code])

        result_path = profile.dump(output_path=output_path, computers=[computer])
        assert result_path.exists()

        # Check that only aiida_dump_log.json file exists, no subdirectories
        contents = list(result_path.iterdir())
        # Only `.aiida_dump_safeguard` and `aiida_dump_log.json`
        assert len(contents) == 2

        # Same for the code, original data was created with
        _ = DumpPaths._safe_delete_directory(path=result_path)
        result_path = profile.dump(output_path=output_path, codes=[code])
        assert result_path.exists()

        # Check that only aiida_dump_log.json file exists, no subdirectories
        contents = list(result_path.iterdir())
        # Only `.aiida_dump_safeguard` and `aiida_dump_log.json`
        assert len(contents) == 2

    def test_dump_flat_structure(self, tmp_path, profile_with_minimal_data, generate_calculation_node_add):
        """Test dumping with flat directory structure."""
        profile = profile_with_minimal_data
        node = generate_calculation_node_add()
        output_path = tmp_path / 'profile_dump_flat'

        result_path = profile.dump(output_path=output_path, all_entries=True, also_ungrouped=True, flat=True)
        assert result_path.exists()
        target_path = result_path / 'ungrouped' / 'calculations' / f'ArithmeticAddCalculation-{node.pk}'
        assert target_path.exists()
        assert not (target_path / 'inputs').exists()
        assert not (target_path / 'outputs').exists()
        assert (target_path / 'aiida.in').exists()

    def test_dump_unsealed_nodes(self, tmp_path, profile_with_minimal_data):
        """Test dumping with unsealed nodes allowed."""
        from aiida.tools.archive import ExportValidationError

        profile = profile_with_minimal_data

        # Create an unsealed node
        unsealed_node = orm.CalculationNode()
        unsealed_node.store()  # Store but don't seal

        output_path = tmp_path / 'profile_dump_unsealed'

        with pytest.raises(ExportValidationError, match='must be sealed'):
            result_path = profile.dump(
                output_path=output_path, all_entries=True, also_ungrouped=True, dump_unsealed=False
            )

        result_path = profile.dump(output_path=output_path, all_entries=True, dump_unsealed=True)
        # Nothing dumped, so just check if completes without exception and main output directory exists
        assert result_path.exists()

    def test_dump_symlink_calcs(self, tmp_path, profile_with_minimal_data, generate_calculation_node_io):
        """Test dumping with symlinks for calculations."""
        profile = profile_with_minimal_data
        output_path = tmp_path / 'profile_dump_symlink'
        group1 = orm.Group(label='group1').store()
        group2 = orm.Group(label='group2').store()
        node = generate_calculation_node_io()
        node.seal()
        group1.add_nodes([node])
        group2.add_nodes([node])

        result_path = profile.dump(output_path=output_path, groups=[group1, group2], symlink_calcs=True)
        assert result_path.exists()

        # Check that the actual directory exists in group1
        target_path = result_path / 'groups' / 'group1' / 'calculations' / str(node.pk)
        assert target_path.exists()
        assert target_path.is_dir()
        assert not target_path.is_symlink()  # Should be the actual directory

        # Check that the symlink exists in group2
        symlink_path = result_path / 'groups' / 'group2' / 'calculations' / str(node.pk)
        assert symlink_path.exists()
        assert symlink_path.is_symlink()

        # Verify the symlink points to the correct target
        assert symlink_path.resolve() == target_path.resolve()

        # Check that the symlink is relative, not absolute
        symlink_target = symlink_path.readlink()
        assert not symlink_target.is_absolute()

        # Alternative way to check the symlink target (relative path)
        expected_relative_target = '../../group1/calculations/' + str(node.pk)
        assert str(symlink_path.readlink()) == expected_relative_target

        # Verify the symlinked content is accessible and identical
        assert (symlink_path / 'aiida_node_metadata.yaml').exists()
        assert (target_path / 'aiida_node_metadata.yaml').exists()

        # Check that both paths lead to the same content
        symlink_metadata = (symlink_path / 'aiida_node_metadata.yaml').read_text()
        target_metadata = (target_path / 'aiida_node_metadata.yaml').read_text()
        assert symlink_metadata == target_metadata

    def test_dump_delete_missing_node(self, tmp_path, profile_with_actual_data):
        """Test dumping with delete_missing option."""
        from aiida.tools.graph.deletions import delete_nodes

        profile = profile_with_actual_data
        output_path = tmp_path / 'profile_dump_delete'

        result_path = profile.dump(output_path=output_path, groups=[TEST_GROUP_LABEL], delete_missing=False)

        nodes = orm.load_group(TEST_GROUP_LABEL).nodes
        node = next(node for node in nodes if isinstance(node, orm.WorkflowNode))
        node_pk = node.pk

        assert result_path.exists()
        target_path = result_path / 'groups' / TEST_GROUP_LABEL / 'workflows'
        assert (target_path / f'{node_pk}').exists()

        delete_nodes(pks=[node_pk], dry_run=False)
        _ = profile.dump(output_path=output_path, groups=[TEST_GROUP_LABEL], delete_missing=True)

        assert not (target_path / f'{node_pk}').exists()

    def test_dump_delete_missing_group(self, tmp_path, profile_with_actual_data):
        """Test dumping with delete_missing option."""
        profile = profile_with_actual_data
        output_path = tmp_path / 'profile_dump_delete'

        result_path = profile.dump(output_path=output_path, all_entries=True, delete_missing=False)
        group = orm.load_group(TEST_GROUP_LABEL)
        node = next(node for node in group.nodes if isinstance(node, orm.WorkflowNode))

        assert result_path.exists()
        target_path = result_path / 'groups' / TEST_GROUP_LABEL
        assert target_path.exists()

        orm.Group.collection.delete(group.pk)

        _ = profile.dump(output_path=output_path, all_entries=True, delete_missing=True, also_ungrouped=True)
        ungrouped_wf_path = result_path / 'ungrouped' / 'workflows' / f'{node.pk}'

        # Group path doesn't exist anymore
        assert not target_path.exists()
        assert ungrouped_wf_path.exists()

        # FIXME: If `also_ungrouped=False` in the `dump` command above, the WF node that was previously in the group is
        # not being dumped. If one then runs the command again, one must set `filter_by_last_dump_time` to False,
        # otherwise it is not picked up. I thought for the ungrouped nodes, time filters are ignared anyway? Changes in
        # the DB structure are only evaluated between the previous dump and the next, so the node is by default
        # overlooked here, thus one needs to disable the time filter.
        # _ = profile.dump(
        #     output_path=output_path,
        #     all_entries=True,
        #     delete_missing=True,
        #     also_ungrouped=True,
        #     filter_by_last_dump_time=False,
        # )

        # # Workflow that was in the group now dumped in the ungrouped directory
        # assert ungrouped_wf_path.exists()

    def test_dump_filter_by_last_dump_time(self, tmp_path, profile_with_minimal_data, generate_calculation_node_io):
        """Test filtering by last dump time."""
        profile = profile_with_minimal_data
        output_path = tmp_path / 'profile_dump_last_time'

        # First dump
        node1 = generate_calculation_node_io()
        node1.seal().store()
        result_path = profile.dump(output_path=output_path, groups=[TEST_GROUP_LABEL])

        assert result_path.exists()

        result_path = profile.dump(output_path=output_path, groups=[TEST_GROUP_LABEL], also_ungrouped=True)
        # Node is filtered out because its mtime is before the previous dump, so no `ungrouped` directory is created
        assert not (result_path / 'ungrouped').exists()

        result_path = profile.dump(
            output_path=output_path, groups=[TEST_GROUP_LABEL], also_ungrouped=True, filter_by_last_dump_time=False
        )
        assert (result_path / 'ungrouped' / 'calculations' / f'{node1.pk}').exists()

    def test_dump_all_boolean_combinations(self, tmp_path, profile_with_minimal_data):
        """Test various boolean flag combinations.

        Smoke tests that nothing breaks with one of the parameter combinations.
        """
        profile = profile_with_minimal_data
        output_path = tmp_path / 'profile_dump_booleans'

        # Test all flags enabled
        result_path = profile.dump(
            output_path=output_path,
            all_entries=True,
            overwrite=True,
            filter_by_last_dump_time=True,
            only_top_level_calcs=True,
            only_top_level_workflows=True,
            delete_missing=True,
            symlink_calcs=True,
            organize_by_groups=True,
            also_ungrouped=True,
            relabel_groups=True,
            include_inputs=True,
            include_outputs=True,
            include_attributes=True,
            include_extras=True,
            flat=True,
            dump_unsealed=True,
        )
        assert result_path.exists()

        _ = DumpPaths._safe_delete_directory(path=result_path)

        # Test all flags disabled
        result_path2 = profile.dump(
            output_path=output_path / 'disabled',
            all_entries=True,
            overwrite=False,
            filter_by_last_dump_time=False,
            only_top_level_calcs=False,
            only_top_level_workflows=False,
            delete_missing=False,
            symlink_calcs=False,
            organize_by_groups=False,
            also_ungrouped=False,
            relabel_groups=False,
            include_inputs=False,
            include_outputs=False,
            include_attributes=False,
            include_extras=False,
            flat=False,
            dump_unsealed=False,
        )
        assert result_path2.exists()
