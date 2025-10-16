###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for the `verdi group` command."""

from unittest.mock import patch

import pytest

from aiida import orm
from aiida.cmdline.commands import cmd_group
from aiida.cmdline.utils.echo import ExitCode
from aiida.common import exceptions


@pytest.fixture(autouse=True)
def groups():
    """Delete all groups first, then recreate a fixed set."""
    [orm.Group.collection.delete(group.pk) for group in orm.Group.collection.all()]
    for group in ['dummygroup1', 'dummygroup2', 'dummygroup3', 'dummygroup4']:
        orm.Group(label=group).store()


class TestVerdiGroup:
    """Tests for the `verdi group` command."""

    def test_help(self, run_cli_command):
        """Tests help text for all group sub commands."""
        options = ['--help']

        # verdi group list
        result = run_cli_command(cmd_group.group_list, options)
        assert 'Usage' in result.output

        # verdi group create
        result = run_cli_command(cmd_group.group_create, options)
        assert 'Usage' in result.output

        # verdi group delete
        result = run_cli_command(cmd_group.group_delete, options)
        assert 'Usage' in result.output

        # verdi group relabel
        result = run_cli_command(cmd_group.group_relabel, options)
        assert 'Usage' in result.output

        # verdi group description
        result = run_cli_command(cmd_group.group_description, options)
        assert 'Usage' in result.output

        # verdi group addnodes
        result = run_cli_command(cmd_group.group_add_nodes, options)
        assert 'Usage' in result.output

        # verdi group removenodes
        result = run_cli_command(cmd_group.group_remove_nodes, options)
        assert 'Usage' in result.output

        # verdi group show
        result = run_cli_command(cmd_group.group_show, options)
        assert 'Usage' in result.output

        # verdi group copy
        result = run_cli_command(cmd_group.group_copy, options)
        assert 'Usage' in result.output

    def test_create(self, run_cli_command):
        """Test `verdi group create` command."""
        result = run_cli_command(cmd_group.group_create, ['dummygroup5'], use_subprocess=True)

        # check if newly added group in present in list
        result = run_cli_command(cmd_group.group_list)
        assert 'dummygroup5' in result.output

    def test_list(self, run_cli_command):
        """Test `verdi group list` command."""
        result = run_cli_command(cmd_group.group_list, use_subprocess=True)
        for grp in ['dummygroup1', 'dummygroup2']:
            assert grp in result.output

    def test_list_order(self, run_cli_command):
        """Test `verdi group list` command with ordering options."""
        orm.Group(label='agroup').store()

        options = []
        result = run_cli_command(cmd_group.group_list, options, suppress_warnings=True, use_subprocess=True)
        group_ordering = [line.split()[1] for line in result.output.split('\n')[3:] if line]
        assert ['agroup', 'dummygroup1', 'dummygroup2', 'dummygroup3', 'dummygroup4'] == group_ordering

        options = ['--order-by', 'id']
        result = run_cli_command(cmd_group.group_list, options, suppress_warnings=True, use_subprocess=True)
        group_ordering = [line.split()[1] for line in result.output.split('\n')[3:] if line]
        assert ['dummygroup1', 'dummygroup2', 'dummygroup3', 'dummygroup4', 'agroup'] == group_ordering

        options = ['--order-by', 'id', '--order-direction', 'desc']
        result = run_cli_command(cmd_group.group_list, options, suppress_warnings=True, use_subprocess=True)
        group_ordering = [line.split()[1] for line in result.output.split('\n')[3:] if line]
        assert ['agroup', 'dummygroup4', 'dummygroup3', 'dummygroup2', 'dummygroup1'] == group_ordering

    def test_copy(self, run_cli_command):
        """Test `verdi group copy` command."""
        result = run_cli_command(cmd_group.group_copy, ['dummygroup1', 'dummygroup2'], use_subprocess=True)
        assert 'Success' in result.output

    def test_delete(self, run_cli_command):
        """Test `verdi group delete` command."""
        orm.Group(label='group_test_delete_01').store()
        orm.Group(label='group_test_delete_02').store()
        orm.Group(label='group_test_delete_03').store()
        do_not_delete_user = orm.User(email='user0@example.com')
        do_not_delete_group = orm.Group(label='do_not_delete_group', user=do_not_delete_user).store()
        do_not_delete_node = orm.CalculationNode().store()
        do_not_delete_group.add_nodes(do_not_delete_node)
        do_not_delete_user.store()

        # 0) do nothing if no groups or no filters are passed
        result = run_cli_command(cmd_group.group_delete, ['--force'])
        assert 'Nothing happened' in result.output

        # 1) dry run
        result = run_cli_command(
            cmd_group.group_delete,
            ['--dry-run', 'group_test_delete_01'],
        )
        orm.load_group(label='group_test_delete_01')

        # 2) Delete group, basic test
        result = run_cli_command(
            cmd_group.group_delete,
            ['--force', 'group_test_delete_01'],
        )
        assert 'do_not_delete_group' not in result.output

        result = run_cli_command(
            cmd_group.group_list,
        )
        assert 'group_test_delete_01' not in result.output

        # 3) Add some nodes and then use `verdi group delete` to delete a group that contains nodes
        node_01 = orm.CalculationNode().store()
        node_02 = orm.CalculationNode().store()
        node_pks = {node_01.pk, node_02.pk}

        group = orm.load_group(label='group_test_delete_02')
        group.add_nodes([node_01, node_02])
        assert group.count() == 2

        result = run_cli_command(
            cmd_group.group_delete,
            ['--force', 'group_test_delete_02'],
        )

        with pytest.raises(exceptions.NotExistent):
            orm.load_group(label='group_test_delete_02')

        for pk in node_pks:
            orm.load_node(pk)

        # 4) Delete the group and the nodes it contains
        group = orm.load_group(label='group_test_delete_03')
        group.add_nodes([node_01, node_02])
        result = run_cli_command(
            cmd_group.group_delete,
            ['--force', '--delete-nodes', 'group_test_delete_03'],
        )

        with pytest.raises(exceptions.NotExistent):
            orm.load_group(label='group_test_delete_03')
        for pk in node_pks:
            with pytest.raises(exceptions.NotExistent):
                orm.load_node(pk)

        # 5) Should delete an empty group even if --delete-nodes option is passed
        group = orm.Group(label='group_test_delete_04').store()
        result = run_cli_command(cmd_group.group_delete, ['--force', '--delete-nodes', 'group_test_delete_04'])
        with pytest.raises(exceptions.NotExistent):
            orm.load_group(label='group_test_delete_04')

        # 6) Should raise if a group does not exist
        result = run_cli_command(cmd_group.group_delete, ['--force', 'non_existent_group'], raises=True)
        assert b'no Group found with LABEL<non_existent_group>' in result.stderr_bytes

        # 7) Should delete multiple groups
        orm.Group(label='group_test_delete_05').store()
        orm.Group(label='group_test_delete_06').store()
        result = run_cli_command(
            cmd_group.group_delete,
            ['--force', 'group_test_delete_05', 'group_test_delete_06'],
        )
        with pytest.raises(exceptions.NotExistent):
            orm.load_group(label='group_test_delete_05')
        with pytest.raises(exceptions.NotExistent):
            orm.load_group(label='group_test_delete_06')
        assert 'do_not_delete_group' not in result.output

        # 8) Should raise if both groups and query options are passed
        result = run_cli_command(
            cmd_group.group_delete,
            ['--force', 'do_not_delete_group', '--all-users'],
            raises=True,
        )
        assert b'Cannot specify both GROUPS and any of the other filters' in result.stderr_bytes
        result = run_cli_command(
            cmd_group.group_delete,
            ['--force', 'do_not_delete_group', '--user', do_not_delete_user.email],
            raises=True,
        )
        assert b'Cannot specify both GROUPS and any of the other filters' in result.stderr_bytes
        result = run_cli_command(
            cmd_group.group_delete,
            ['--force', 'do_not_delete_group', '--type-string', 'non_existent'],
            raises=True,
        )
        assert b'Cannot specify both GROUPS and any of the other filters' in result.stderr_bytes
        result = run_cli_command(
            cmd_group.group_delete,
            ['--force', 'do_not_delete_group', '--past-days', '1'],
            raises=True,
        )
        assert b'Cannot specify both GROUPS and any of the other filters' in result.stderr_bytes
        result = run_cli_command(
            cmd_group.group_delete,
            ['--force', 'do_not_delete_group', '--startswith', 'non_existent'],
            raises=True,
        )
        assert b'Cannot specify both GROUPS and any of the other filters' in result.stderr_bytes
        result = run_cli_command(
            cmd_group.group_delete,
            ['--force', 'do_not_delete_group', '--endswith', 'non_existent'],
            raises=True,
        )
        assert b'Cannot specify both GROUPS and any of the other filters' in result.stderr_bytes
        result = run_cli_command(
            cmd_group.group_delete,
            ['--force', 'do_not_delete_group', '--contains', 'non_existent'],
            raises=True,
        )
        assert b'Cannot specify both GROUPS and any of the other filters' in result.stderr_bytes
        result = run_cli_command(
            cmd_group.group_delete,
            ['--force', 'do_not_delete_group', '--node', do_not_delete_node.pk],
            raises=True,
        )
        assert b'Cannot specify both GROUPS and any of the other filters' in result.stderr_bytes

        # 9) --user should delete groups for a specific user
        #   --all-users should delete groups for all users
        user1 = orm.User(email='user1@example.com')
        user2 = orm.User(email='user2@example.com')
        user3 = orm.User(email='user3@example.com')
        user1.store()
        user2.store()
        user3.store()

        orm.Group(label='group_test_delete_08', user=user1).store()
        orm.Group(label='group_test_delete_09', user=user2).store()
        orm.Group(label='group_test_delete_10', user=user3).store()

        result = run_cli_command(
            cmd_group.group_delete,
            ['--force', '--user', user1.email],
        )
        with pytest.raises(exceptions.NotExistent):
            orm.load_group(label='group_test_delete_08')
        assert 'group_test_delete_09' not in result.output
        assert 'group_test_delete_10' not in result.output

        result = run_cli_command(
            cmd_group.group_delete,
            ['--force', '--all-users'],
        )
        with pytest.raises(exceptions.NotExistent):
            orm.load_group(label='group_test_delete_09')
        with pytest.raises(exceptions.NotExistent):
            orm.load_group(label='group_test_delete_10')

        # 10) --startswith, --endswith, --contains should delete groups with labels that match the filter
        orm.Group(label='START_13').store()
        orm.Group(label='14_END').store()
        orm.Group(label='contains_SOMETHING_').store()

        result = run_cli_command(
            cmd_group.group_delete,
            ['--force', '--startswith', 'START'],
        )
        with pytest.raises(exceptions.NotExistent):
            orm.load_group(label='START_13')
        assert '14_END' not in result.output
        assert 'contains_SOMETHING_' not in result.output
        assert 'do_not_delete_group' not in result.output

        result = run_cli_command(
            cmd_group.group_delete,
            ['--force', '--endswith', 'END'],
        )
        with pytest.raises(exceptions.NotExistent):
            orm.load_group(label='14_END')
        assert 'contains_SOMETHING_' not in result.output
        assert 'do_not_delete_group' not in result.output

        result = run_cli_command(
            cmd_group.group_delete,
            ['--force', '--contains', 'SOMETHING'],
        )
        with pytest.raises(exceptions.NotExistent):
            orm.load_group(label='contains_SOMETHING_')
        assert 'do_not_delete_group' not in result.output

        # 11) --node should delete only groups that contain a specific node
        node = orm.CalculationNode().store()
        group = orm.Group(label='group_test_delete_15').store()
        group.add_nodes(node)

        result = run_cli_command(
            cmd_group.group_delete,
            ['--force', '--node', node.uuid],
        )
        with pytest.raises(exceptions.NotExistent):
            orm.load_group(label='group_test_delete_15')
        assert 'do_not_delete_group' not in result.output

    def test_show(self, run_cli_command):
        """Test `verdi group show` command."""
        result = run_cli_command(cmd_group.group_show, ['dummygroup1'], use_subprocess=True)
        for grpline in [
            'Group label',
            'dummygroup1',
            'Group type_string',
            'core',
            'Group description',
            '<no description>',
        ]:
            assert grpline in result.output

    @pytest.mark.usefixtures('aiida_profile_clean')
    def test_show_limit(self, run_cli_command):
        """Test `--limit` option of the `verdi group show` command."""
        label = 'test_group_limit'
        nodes = [orm.Data().store(), orm.Data().store()]
        group = orm.Group(label=label).store()
        group.add_nodes(nodes)

        # Default should include all nodes in the output
        result = run_cli_command(cmd_group.group_show, [label], use_subprocess=True)
        for node in nodes:
            assert str(node.pk) in result.output

        # Repeat test with `limit=1`, use also the `--raw` option to only display nodes
        result = run_cli_command(
            cmd_group.group_show, [label, '--limit', '1', '--raw'], suppress_warnings=True, use_subprocess=True
        )

        # The current `verdi group show` does not support ordering so we cannot rely on that for now to test if only
        # one of the nodes is shown
        assert len(result.output.strip().split('\n')) == 1
        assert str(nodes[0].pk) in result.output or str(nodes[1].pk) in result.output

        # Repeat test with `limit=1` but without the `--raw` flag as it has a different code path that is affected
        result = run_cli_command(cmd_group.group_show, [label, '--limit', '1'], use_subprocess=True)

        # Check that one, and only one pk appears in the output
        assert str(nodes[0].pk) in result.output or str(nodes[1].pk) in result.output
        assert not (str(nodes[0].pk) in result.output and str(nodes[1].pk) in result.output)

    def test_description(self, run_cli_command):
        """Test `verdi group description` command."""
        description = 'It is a new description'
        group = orm.load_group(label='dummygroup2')
        assert group.description != description

        # Change the description of the group
        result = run_cli_command(cmd_group.group_description, [group.label, description])
        assert group.description == description

        # When no description argument is passed the command should just echo the current description
        result = run_cli_command(cmd_group.group_description, [group.label])
        assert description in result.output

    def test_relabel(self, run_cli_command):
        """Test `verdi group relabel` command."""
        result = run_cli_command(cmd_group.group_relabel, ['dummygroup4', 'relabeled_group'])

        # check if group list command shows changed group name
        result = run_cli_command(cmd_group.group_list)

        assert 'dummygroup4' not in result.output
        assert 'relabeled_group' in result.output

    def test_add_remove_nodes(self, run_cli_command):
        """Test `verdi group remove-nodes` command."""
        node_01 = orm.CalculationNode().store()
        node_02 = orm.CalculationNode().store()
        node_03 = orm.CalculationNode().store()

        result = run_cli_command(
            cmd_group.group_add_nodes, ['--force', '--group=dummygroup1', node_01.uuid], use_subprocess=True
        )

        # Check if node is added in group using group show command
        result = run_cli_command(cmd_group.group_show, ['dummygroup1'], use_subprocess=True)

        assert 'CalculationNode' in result.output
        assert str(node_01.pk) in result.output

        # Remove same node
        result = run_cli_command(
            cmd_group.group_remove_nodes, ['--force', '--group=dummygroup1', node_01.uuid], use_subprocess=True
        )

        # Check that the node is no longer in the group
        result = run_cli_command(cmd_group.group_show, ['-r', 'dummygroup1'], use_subprocess=True)

        assert 'CalculationNode' not in result.output
        assert str(node_01.pk) not in result.output

        # Add all three nodes and then use `verdi group remove-nodes --clear` to remove them all
        group = orm.load_group(label='dummygroup1')
        group.add_nodes([node_01, node_02, node_03])
        assert group.count() == 3

        result = run_cli_command(
            cmd_group.group_remove_nodes, ['--force', '--clear', '--group=dummygroup1'], use_subprocess=True
        )

        assert group.count() == 0

        # Try to remove node that isn't in the group
        result = run_cli_command(
            cmd_group.group_remove_nodes, ['--group=dummygroup1', node_01.uuid], raises=True, use_subprocess=True
        )
        assert result.exit_code == ExitCode.CRITICAL

        # Try to remove no nodes nor clear the group
        result = run_cli_command(
            cmd_group.group_remove_nodes, ['--group=dummygroup1'], raises=True, use_subprocess=True
        )
        assert result.exit_code == ExitCode.CRITICAL

        # Try to remove both nodes and clear the group
        result = run_cli_command(
            cmd_group.group_remove_nodes, ['--group=dummygroup1', '--clear', node_01.uuid], raises=True
        )
        assert result.exit_code == ExitCode.CRITICAL

        # Add a node with confirmation
        result = run_cli_command(
            cmd_group.group_add_nodes, ['--group=dummygroup1', node_01.uuid], user_input='y', use_subprocess=True
        )
        assert group.count() == 1

        # Try to remove two nodes, one that isn't in the group, but abort
        result = run_cli_command(
            cmd_group.group_remove_nodes,
            ['--group=dummygroup1', node_01.uuid, node_02.uuid],
            user_input='N',
            raises=True,
            use_subprocess=True,
        )
        assert 'Warning' in result.output
        assert group.count() == 1

        # Try to clear all nodes from the group, but abort
        result = run_cli_command(
            cmd_group.group_remove_nodes,
            ['--group=dummygroup1', '--clear'],
            user_input='N',
            raises=True,
            use_subprocess=True,
        )
        assert 'Are you sure you want to remove ALL' in result.output
        assert 'Aborted' in result.output
        assert group.count() == 1

    def test_move_nodes(self, run_cli_command):
        """Test `verdi group move-nodes` command."""
        node_01 = orm.CalculationNode().store()
        node_02 = orm.Int(1).store()
        node_03 = orm.Bool(True).store()

        group1 = orm.load_group('dummygroup1')
        group2 = orm.load_group('dummygroup2')

        group1.add_nodes([node_01, node_02])

        # Moving the nodes to the same group
        result = run_cli_command(
            cmd_group.group_move_nodes,
            ['-s', 'dummygroup1', '-t', 'dummygroup1', node_01.uuid, node_02.uuid],
            raises=True,
            use_subprocess=True,
        )
        assert 'Source and target group are the same:' in result.output

        # Not specifying NODES or `--all`
        result = run_cli_command(
            cmd_group.group_move_nodes, ['-s', 'dummygroup1', '-t', 'dummygroup2'], raises=True, use_subprocess=True
        )
        assert 'Neither NODES or the `-a, --all` option was specified.' in result.output

        # Moving the nodes from the empty group
        result = run_cli_command(
            cmd_group.group_move_nodes,
            ['-s', 'dummygroup2', '-t', 'dummygroup1', node_01.uuid, node_02.uuid],
            raises=True,
            use_subprocess=True,
        )
        assert 'None of the specified nodes are in' in result.output

        # Move two nodes to the second dummy group, but specify a missing uuid
        result = run_cli_command(
            cmd_group.group_move_nodes,
            ['-s', 'dummygroup1', '-t', 'dummygroup2', node_01.uuid, node_03.uuid],
            raises=True,
            use_subprocess=True,
        )
        assert f'1 nodes with PK {{{node_03.pk}}} are not in' in result.output
        # Check that the node that is present is actually moved
        result = run_cli_command(
            cmd_group.group_move_nodes,
            ['-f', '-s', 'dummygroup1', '-t', 'dummygroup2', node_01.uuid, node_03.uuid],
            use_subprocess=True,
        )
        assert node_01 not in group1.nodes
        assert node_01 in group2.nodes

        # Add the first node back to the first group, and try to move it from the second one
        group1.add_nodes(node_01)
        result = run_cli_command(
            cmd_group.group_move_nodes,
            ['-s', 'dummygroup2', '-t', 'dummygroup1', node_01.uuid],
            raises=True,
            use_subprocess=True,
        )
        assert f'1 nodes with PK {{{node_01.pk}}} are already' in result.output
        # Check that it is still removed from the second group
        result = run_cli_command(
            cmd_group.group_move_nodes,
            ['-f', '-s', 'dummygroup2', '-t', 'dummygroup1', node_01.uuid],
            use_subprocess=True,
        )
        assert node_01 not in group2.nodes

        # Force move the two nodes to the second dummy group
        result = run_cli_command(
            cmd_group.group_move_nodes,
            ['-f', '-s', 'dummygroup1', '-t', 'dummygroup2', node_01.uuid, node_02.uuid],
            use_subprocess=True,
        )
        assert node_01 in group2.nodes
        assert node_02 in group2.nodes

        # Force move all nodes back to the first dummy group
        result = run_cli_command(
            cmd_group.group_move_nodes, ['-f', '-s', 'dummygroup2', '-t', 'dummygroup1', '--all'], use_subprocess=True
        )
        assert node_01 not in group2.nodes
        assert node_02 not in group2.nodes
        assert node_01 in group1.nodes
        assert node_02 in group1.nodes

    def test_copy_existing_group(self, run_cli_command):
        """Test user is prompted to continue if destination group exists and is not empty"""
        source_label = 'source_copy_existing_group'
        dest_label = 'dest_copy_existing_group'

        # Create source group with nodes
        calc_s1 = orm.CalculationNode().store()
        calc_s2 = orm.CalculationNode().store()
        nodes_source_group = {str(node.uuid) for node in [calc_s1, calc_s2]}
        source_group = orm.Group(label=source_label).store()
        source_group.add_nodes([calc_s1, calc_s2])

        # Copy using `verdi group copy` - making sure all is successful
        options = [source_label, dest_label]
        result = run_cli_command(cmd_group.group_copy, options, use_subprocess=True)
        assert (
            f'Success: Nodes copied from {source_group} to {source_group.__class__.__name__}<{dest_label}>.'
            in result.output
        ), result.exception

        # Check destination group exists with source group's nodes
        dest_group = orm.load_group(label=dest_label)
        assert dest_group.count() == 2
        nodes_dest_group = {str(node.uuid) for node in dest_group.nodes}
        assert nodes_source_group == nodes_dest_group

        # Copy again, making sure an abort error is raised, since no user input can be made and default is abort
        result = run_cli_command(cmd_group.group_copy, options, raises=True, use_subprocess=True)
        assert f'Warning: Destination {dest_group} already exists and is not empty.' in result.output, result.exception

        # Check destination group is unchanged
        dest_group = orm.load_group(label=dest_label)
        assert dest_group.count() == 2
        nodes_dest_group = {str(node.uuid) for node in dest_group.nodes}
        assert nodes_source_group == nodes_dest_group

    def test_dump_dry_run_with_overwrite_warning(self, run_cli_command):
        """Test that dry_run + overwrite shows warning and returns early"""
        group = orm.Group(label='test_warning_group').store()
        node = orm.CalculationNode().store().seal()
        group.add_nodes([node])

        options = [group.label, '--dry-run', '--overwrite']
        result = run_cli_command(cmd_group.group_dump, options)
        assert result.exception is None, result.output
        assert '`--dry-run` and `--overwrite` selected' in result.output
        assert 'Overwrite operation will NOT be performed' in result.output

    def test_dump_specified_path_message(self, run_cli_command, tmp_path):
        """Test that specified path is reported correctly"""
        group = orm.Group(label='test_path_group').store()
        node = orm.CalculationNode().store().seal()
        group.add_nodes([node])

        test_path = tmp_path / 'specified-path'

        options = [group.label, '--path', str(test_path)]
        result = run_cli_command(cmd_group.group_dump, options)
        assert result.exception is None, result.output
        assert f'Report: Using specified output path: `{test_path}`' in result.output

    @patch('aiida.orm.groups.Group.dump')
    def test_dump_calls_group_dump_with_correct_args(self, mock_dump, run_cli_command, tmp_path):
        """Test that group.dump is called with correct arguments"""
        group = orm.Group(label='test_args_group').store()
        node = orm.CalculationNode().store().seal()
        group.add_nodes([node])
        test_path = tmp_path / 'test-args'

        options = [
            group.label,
            '--path',
            str(test_path),
            '--past-days',
            '7',
            '--only-top-level-calcs',
            '--only-top-level-workflows',
            '--include-inputs',
            '--include-outputs',
            '--include-attributes',
            '--include-extras',
            '--flat',
            '--dump-unsealed',
            '--symlink-calcs',
        ]
        _ = run_cli_command(cmd_group.group_dump, options)

        # Verify the dump method was called with expected arguments
        group.dump.assert_called_once_with(
            output_path=test_path.resolve(),
            dry_run=False,
            overwrite=False,
            past_days=7,
            start_date=None,
            end_date=None,
            filter_by_last_dump_time=True,
            only_top_level_calcs=True,
            only_top_level_workflows=True,
            include_inputs=True,
            include_outputs=True,
            include_attributes=True,
            include_extras=True,
            flat=True,
            dump_unsealed=True,
            symlink_calcs=True,
        )

    def test_dump_time_filtering_options(self, run_cli_command, tmp_path):
        """Test time-based filtering options"""
        group = orm.Group(label='test_time_filtering_group').store()
        node = orm.CalculationNode().store().seal()
        group.add_nodes([node])
        test_path = tmp_path / 'time-filtering'

        # Test past-days option
        options = [group.label, '--path', str(test_path), '--past-days', '30']
        result = run_cli_command(cmd_group.group_dump, options)
        assert result.exception is None, result.output

        # Test start-date and end-date options
        options = [
            group.label,
            '--path',
            str(test_path / 'dates'),
            '--start-date',
            '2024-01-01',
            '--end-date',
            '2024-12-31',
            '--overwrite',
        ]
        result = run_cli_command(cmd_group.group_dump, options)
        assert result.exception is None, result.output

    def test_dump_node_collection_options(self, run_cli_command, tmp_path):
        """Test node collection filtering options"""
        group = orm.Group(label='test_collection_group').store()
        calc_node = orm.CalculationNode().store().seal()
        workflow_node = orm.WorkflowNode().store().seal()
        group.add_nodes([calc_node, workflow_node])
        test_path = tmp_path / 'collection-test'

        # Test with only calculations
        options = [group.label, '--path', str(test_path), '--only-top-level-calcs', '--no-only-top-level-workflows']
        result = run_cli_command(cmd_group.group_dump, options)
        assert result.exception is None, result.output

    # NOTE: Possibly remove
    def test_dump_metadata_inclusion_options(self, run_cli_command, tmp_path):
        """Test metadata inclusion options"""
        group = orm.Group(label='test_metadata_group').store()
        node = orm.CalculationNode()
        node.base.attributes.set('test_attr', 'value')
        node.base.extras.set('test_extra', 'value')
        node.store().seal()
        group.add_nodes([node])
        test_path = tmp_path / 'metadata-test'

        options = [
            group.label,
            '--path',
            str(test_path),
            '--exclude-inputs',
            '--include-outputs',
            '--include-attributes',
            '--exclude-extras',
        ]
        result = run_cli_command(cmd_group.group_dump, options)
        assert result.exception is None, result.output

    @patch('aiida.orm.groups.Group.dump')
    def test_dump_unexpected_error_handling(self, mock_dump, run_cli_command, tmp_path):
        """Test handling of unexpected exceptions"""
        group = orm.Group(label='test_error_group').store()
        node = orm.CalculationNode().store().seal()
        group.add_nodes([node])
        test_path = tmp_path / 'unexpected-error'

        # Mock dump to raise generic exception
        mock_dump.side_effect = RuntimeError('Unexpected error')

        options = [group.label, '--path', str(test_path)]
        result = run_cli_command(cmd_group.group_dump, options, raises=True)

        assert f'Unexpected error during dump of group {group.label}:' in result.output
        assert 'RuntimeError: Unexpected error' in result.output
        # Should include traceback
        assert 'Traceback' in result.output

    def test_dump_success_message_format(self, run_cli_command, tmp_path):
        """Test success message format"""
        group = orm.Group(label='test_success_group').store()
        node = orm.CalculationNode().store().seal()
        group.add_nodes([node])
        test_path = tmp_path / 'success-test'

        options = [group.label, '--path', str(test_path)]
        result = run_cli_command(cmd_group.group_dump, options)
        assert result.exception is None, result.output

        expected_msg = f'Raw files for group `{group.label}` dumped into folder `{test_path.name}`'
        assert expected_msg in result.output

    def test_dump_filter_by_last_dump_time_option(self, run_cli_command, tmp_path):
        """Test filter-by-last-dump-time option"""
        group = orm.Group(label='test_filter_time_group').store()
        node = orm.CalculationNode().store().seal()
        group.add_nodes([node])
        test_path = tmp_path / 'filter-time-test'

        options = [group.label, '--path', str(test_path), '--no-filter-by-last-dump-time']
        result = run_cli_command(cmd_group.group_dump, options)
        assert result.exception is None, result.output

    def test_dump_empty_group_handling(self, run_cli_command, tmp_path):
        """Test dumping an empty group"""
        group = orm.Group(label='empty_test_group').store()
        # Don't add any nodes
        test_path = tmp_path / 'empty-group-test'

        options = [group.label, '--path', str(test_path)]
        result = run_cli_command(cmd_group.group_dump, options)
        assert result.exception is None, result.output
        assert 'Success:' in result.output

    def test_dump_nonexistent_group(self, run_cli_command):
        """Test error handling for non-existent group"""
        options = ['nonexistent_group_label']
        result = run_cli_command(cmd_group.group_dump, options, raises=True)
        assert 'no Group found with LABEL<nonexistent_group_label>' in result.stderr
