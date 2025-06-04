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
from aiida.manage.configuration import get_config


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


@pytest.fixture
def profile_with_data():
    """Create a profile with some test data."""
    # Get current profile
    profile = get_config().get_profile()

    # Create some test data
    group = orm.Group(label='test_profile_dump_group').store()
    calc_node = orm.CalculationNode().store().seal()
    data_node = orm.Int(42).store()
    _ = orm.WorkflowNode().store().seal()

    group.add_nodes([calc_node, data_node])

    return profile


@pytest.mark.usefixtures('aiida_profile_clean')
class TestProfileDump:
    """Test the dump method of Profile."""

    def test_dump_dry_run(self, capsys, tmp_path, profile_with_data):
        """Test dry run mode doesn't create files."""
        profile = profile_with_data
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

    def test_dump_overwrite(self, tmp_path, profile_with_data):
        """Test overwrite functionality."""
        profile = profile_with_data
        output_path = tmp_path / 'profile_dump_overwrite'

        # First dump
        result_path1 = profile.dump(output_path=output_path, all_entries=True)
        assert result_path1.exists()

        # Second dump with overwrite should succeed
        result_path2 = profile.dump(output_path=output_path, all_entries=True, overwrite=True)
        assert result_path2.exists()
        assert result_path1 == result_path2

    def test_dump_basic_all_entries(self, tmp_path, profile_with_data):
        """Test basic dumping of entire profile."""
        profile = profile_with_data
        output_path = tmp_path / 'profile_dump_all'

        result_path = profile.dump(output_path=output_path, all_entries=True)

        # Check that dump was created
        assert result_path.exists()
        assert result_path.is_dir()

        # Check for expected files
        assert (result_path / '.aiida_dump_safeguard').exists()

    def test_dump_specific_groups(self, tmp_path, profile_with_data):
        """Test dumping specific groups only."""
        profile = profile_with_data
        output_path = tmp_path / 'profile_dump_groups'

        # Get the test group we created
        group = orm.Group.collection.get(label='test_profile_dump_group')
        extra_group = orm.Group(label='extra_group').store()

        result_path = profile.dump(output_path=output_path, groups=[group])

        assert result_path.exists()
        assert result_path.is_dir()
        assert (result_path / 'groups' / group.label).exists()
        assert not (result_path / 'groups' / extra_group.label).exists()

        # Test dumping by label
        result_path = profile.dump(output_path=output_path, groups=['test_profile_dump_group'], overwrite=True)

        assert result_path.exists()
        assert result_path.is_dir()
        assert (result_path / 'groups' / group.label).exists()
        assert not (result_path / 'groups' / extra_group.label).exists()

    def test_dump_by_user(self, tmp_path, profile_with_data):
        """Test dumping data for specific user."""
        profile = profile_with_data
        output_path = tmp_path / 'profile_dump_user'

        default_user = orm.User.collection.get_default()

        # Create a second user
        other_user = orm.User(email='other@example.com', first_name='Other', last_name='User')
        other_user.store()

        # Create a calculation node for the other user
        other_calc = orm.CalculationNode()
        other_calc.user = other_user
        other_calc.store().seal()

        group = orm.load_group('test_profile_dump_group')
        group.add_nodes(other_calc)

        result_path = profile.dump(
            output_path=output_path,
            user=default_user,
            groups=['test_profile_dump_group'],
        )

        assert result_path.exists()
        assert result_path.is_dir()
        assert (result_path / 'groups' / 'test_profile_dump_group' / 'calculations').exists()
        # Calculation created by other user is not dumped
        assert not (result_path / 'groups' / 'test_profile_dump_group' / 'calculations' / f'{other_calc.pk}').exists()

    def test_dump_empty_scope_returns_none(self, tmp_path, profile_with_data, caplog):
        """Test that dumping with no scope returns None."""
        profile = profile_with_data
        output_path = tmp_path / 'profile_dump_empty'

        _ = profile.dump(output_path=output_path)

        assert 'No profile data explicitly selected. No dump will be performed.' in caplog.text
        assert caplog.records[-1].levelname == 'WARNING'

    def test_dump_with_time_filters(self, tmp_path, profile_with_data):
        """Test dumping with time-based filters."""
        profile = profile_with_data
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

    def test_dump_organize_by_groups(self, tmp_path, profile_with_data):
        """Test dumping organized by groups."""
        profile = profile_with_data
        output_path = tmp_path / 'profile_dump_organized'

        result_path = profile.dump(
            output_path=output_path, all_entries=True, organize_by_groups=True, also_ungrouped=True
        )
        assert result_path.exists()
        assert (result_path / 'groups').exists()
        assert (result_path / 'ungrouped').exists()
        assert (result_path / 'ungrouped' / 'workflows').exists()

        result_path = profile.dump(
            output_path=output_path, all_entries=True, organize_by_groups=False, overwrite=True, also_ungrouped=True
        )
        assert result_path.exists()
        assert (result_path / 'calculations').exists()
        assert (result_path / 'workflows').exists()

    def test_dump_with_relabel_groups(self, tmp_path, profile_with_data):
        """Test dumping with group relabeling."""
        profile = profile_with_data
        output_path = tmp_path / 'profile_dump_relabel'

        result_path = profile.dump(
            output_path=output_path, all_entries=True, organize_by_groups=True, relabel_groups=True
        )
        assert result_path.exists()
        assert (result_path / 'groups' / 'test_profile_dump_group').exists()

        # Now relabel the group
        group = orm.load_group('test_profile_dump_group')
        group.label = 'relabeled'

        result_path = profile.dump(
            output_path=output_path, all_entries=True, organize_by_groups=True, relabel_groups=True
        )
        assert (result_path / 'groups' / 'relabeled').exists()

    def test_dump_only_top_level_calcs(self, tmp_path, profile_with_data, generate_workchain_multiply_add):
        """Test dumping with node collection filters."""
        profile = profile_with_data
        output_path = tmp_path / 'profile_dump_filters'
        _ = generate_workchain_multiply_add()

        result_path = profile.dump(
            output_path=output_path, all_entries=True, only_top_level_calcs=True, also_ungrouped=True
        )

        assert result_path.exists()
        assert not (result_path / 'ungrouped' / 'calculations').exists()

        result_path = profile.dump(
            output_path=output_path, all_entries=True, only_top_level_calcs=False, also_ungrouped=True, overwrite=True
        )

        assert result_path.exists()
        assert (result_path / 'ungrouped' / 'calculations').exists()

    # FIXME: Cannot specify both code and computer. Make it either or
    def test_dump_with_computers_and_codes(self, tmp_path, profile_with_data):
        """Test dumping with computer and code filters."""
        profile = profile_with_data
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
        # TODO: Continue here. Check that _only_ aiida_dump_log.json file in output directory, but no subdirectories

    # def test_dump_include_file_options(self, tmp_path, profile_with_data):
    #     """Test dumping with different file inclusion options."""
    #     profile = profile_with_data
    #     output_path = tmp_path / 'profile_dump_files'

    #     result_path = profile.dump(
    #         output_path=output_path,
    #         all_entries=True,
    #         include_inputs=True,
    #         include_outputs=True,
    #         include_attributes=True,
    #         include_extras=True,
    #     )
    #     assert result_path.exists()

    # def test_dump_flat_structure(self, tmp_path, profile_with_data):
    #     """Test dumping with flat directory structure."""
    #     profile = profile_with_data
    #     output_path = tmp_path / 'profile_dump_flat'

    #     result_path = profile.dump(output_path=output_path, all_entries=True, flat=True)
    #     assert result_path.exists()

    # def test_dump_unsealed_nodes(self, tmp_path, profile_with_data):
    #     """Test dumping with unsealed nodes allowed."""
    #     profile = profile_with_data

    #     # Create an unsealed node
    #     unsealed_node = orm.CalculationNode()
    #     unsealed_node.store()  # Store but don't seal

    #     output_path = tmp_path / 'profile_dump_unsealed'

    #     result_path = profile.dump(output_path=output_path, all_entries=True, dump_unsealed=True)
    #     assert result_path.exists()

    # def test_dump_symlink_calcs(self, tmp_path, profile_with_data):
    #     """Test dumping with symlinks for calculations."""
    #     profile = profile_with_data
    #     output_path = tmp_path / 'profile_dump_symlink'

    #     result_path = profile.dump(output_path=output_path, all_entries=True, symlink_calcs=True)
    #     assert result_path.exists()

    # def test_dump_delete_missing(self, tmp_path, profile_with_data):
    #     """Test dumping with delete_missing option."""
    #     profile = profile_with_data
    #     output_path = tmp_path / 'profile_dump_delete'

    #     result_path = profile.dump(output_path=output_path, all_entries=True, delete_missing=False)
    #     assert result_path.exists()

    # def test_dump_filter_by_last_dump_time(self, tmp_path, profile_with_data):
    #     """Test filtering by last dump time."""
    #     profile = profile_with_data
    #     output_path = tmp_path / 'profile_dump_last_time'

    #     # First dump
    #     result_path1 = profile.dump(output_path=output_path, all_entries=True)
    #     assert result_path1.exists()

    #     # Second dump with filter_by_last_dump_time disabled
    #     result_path2 = profile.dump(
    #         output_path=output_path / 'no_filter', all_entries=True, filter_by_last_dump_time=False
    #     )
    #     assert result_path2.exists()

    # def test_dump_default_path(self, profile_with_data):
    #     """Test dumping with default path generation."""
    #     profile = profile_with_data

    #     # Call dump without specifying output_path
    #     result_path = profile.dump(all_entries=True)

    #     assert result_path.exists()
    #     assert result_path.is_dir()
    #     # Should contain the profile name in the path
    #     assert profile.name in str(result_path)

    #     # Clean up
    #     import shutil

    #     shutil.rmtree(result_path)

    # def test_dump_with_mixed_group_specifications(self, tmp_path, profile_with_data):
    #     """Test dumping with groups specified in different ways."""
    #     profile = profile_with_data
    #     output_path = tmp_path / 'profile_dump_mixed_groups'

    #     # Get the group object and create another one
    #     group1 = orm.Group.collection.get(label='test_profile_dump_group')
    #     group2 = orm.Group(label='test_profile_dump_group2').store()

    #     # Mix group objects and labels
    #     result_path = profile.dump(output_path=output_path, groups=[group1, 'test_profile_dump_group2'])
    #     assert result_path.exists()

    # def test_dump_dry_run_with_overwrite_returns_none(self, tmp_path, profile_with_data):
    #     """Test that dry_run + overwrite returns None."""
    #     profile = profile_with_data
    #     output_path = tmp_path / 'profile_dump_dry_overwrite'

    #     result_path = profile.dump(output_path=output_path, all_entries=True, dry_run=True, overwrite=True)
    #     assert result_path is None

    # def test_dump_all_boolean_combinations(self, tmp_path, profile_with_data):
    #     """Test various boolean flag combinations."""
    #     profile = profile_with_data
    #     output_path = tmp_path / 'profile_dump_booleans'

    #     # Test all flags enabled
    #     result_path = profile.dump(
    #         output_path=output_path,
    #         all_entries=True,
    #         overwrite=True,
    #         filter_by_last_dump_time=True,
    #         only_top_level_calcs=True,
    #         only_top_level_workflows=True,
    #         delete_missing=True,
    #         symlink_calcs=True,
    #         organize_by_groups=True,
    #         also_ungrouped=True,
    #         relabel_groups=True,
    #         include_inputs=True,
    #         include_outputs=True,
    #         include_attributes=True,
    #         include_extras=True,
    #         flat=True,
    #         dump_unsealed=True,
    #     )
    #     assert result_path.exists()

    #     # Test all flags disabled
    #     result_path2 = profile.dump(
    #         output_path=output_path / 'disabled',
    #         all_entries=True,
    #         overwrite=True,
    #         filter_by_last_dump_time=False,
    #         only_top_level_calcs=False,
    #         only_top_level_workflows=False,
    #         delete_missing=False,
    #         symlink_calcs=False,
    #         organize_by_groups=False,
    #         also_ungrouped=False,
    #         relabel_groups=False,
    #         include_inputs=False,
    #         include_outputs=False,
    #         include_attributes=False,
    #         include_extras=False,
    #         flat=False,
    #         dump_unsealed=False,
    #     )
    #     assert result_path2.exists()

    # def test_dump_with_user_list(self, tmp_path, profile_with_data):
    #     """Test dumping with multiple users specified."""
    #     profile = profile_with_data
    #     output_path = tmp_path / 'profile_dump_users'

    #     # Get default user (in a real test environment there might be multiple users)
    #     default_user = orm.User.collection.get_default()

    #     result_path = profile.dump(
    #         output_path=output_path,
    #         user=[default_user],  # Pass as list
    #     )
    #     assert result_path.exists()

    # def test_dump_computers_and_codes_by_label(self, tmp_path, profile_with_data):
    #     """Test dumping with computers and codes specified by labels."""
    #     profile = profile_with_data
    #     output_path = tmp_path / 'profile_dump_labels'

    #     # Create test computer and code
    #     computer = orm.Computer(
    #         label='test_computer_label', hostname='localhost', transport_type='core.local', scheduler_type='core.direct'
    #     ).store()

    #     code = orm.InstalledCode(label='test_code_label', computer=computer, filepath_executable='/bin/bash').store()

    #     result_path = profile.dump(
    #         output_path=output_path, computers=['test_computer_label'], codes=['test_code_label']
    #     )
    #     assert result_path.exists()
