###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for `verdi process`."""

import functools
import re
import time
import typing as t
import uuid

import pytest
from aiida import get_profile
from aiida.cmdline.commands import cmd_process
from aiida.cmdline.utils.echo import ExitCode
from aiida.common.links import LinkType
from aiida.common.log import LOG_LEVEL_REPORT
from aiida.engine import Process, ProcessState
from aiida.engine.processes import control as process_control
from aiida.orm import CalcJobNode, Group, WorkChainNode, WorkflowNode, WorkFunctionNode

from tests.utils.processes import WaitProcess


def await_condition(condition: t.Callable, timeout: int = 1):
    """Wait for the ``condition`` to evaluate to ``True`` within the ``timeout`` or raise."""
    start_time = time.time()

    while not condition():
        if time.time() - start_time > timeout:
            raise RuntimeError(f'waiting for {condition} to evaluate to `True` timed out after {timeout} seconds.')


class TestVerdiProcess:
    """Tests for `verdi process`."""

    TEST_TIMEOUT = 5.0

    def test_list_non_raw(self, run_cli_command):
        """Test the list command as the user would run it (e.g. without -r)."""
        result = run_cli_command(cmd_process.process_list)

        assert 'Total results:' in result.output
        assert 'Last time an entry changed state' in result.output

    @pytest.mark.usefixtures('aiida_profile_clean')
    def test_list(self, run_cli_command):
        """Test the list command."""
        calcs = []
        process_label = 'SomeDummyWorkFunctionNode'

        # Create 6 WorkFunctionNodes and WorkChainNodes (one for each ProcessState)
        for state in ProcessState:
            calc = WorkFunctionNode()
            calc.set_process_state(state)

            # Set the WorkFunctionNode as successful
            if state == ProcessState.FINISHED:
                calc.set_exit_status(0)

            # Give a `process_label` to the `WorkFunctionNodes` so the `--process-label` option can be tested
            calc.base.attributes.set('process_label', process_label)

            calc.store()
            calcs.append(calc)

            calc = WorkChainNode()
            calc.set_process_state(state)

            # Set the WorkChainNode as failed
            if state == ProcessState.FINISHED:
                exit_code = Process.exit_codes.ERROR_UNSPECIFIED
                calc.set_exit_status(exit_code.status)
                calc.set_exit_message(exit_code.message)

            # Set the waiting work chain as paused as well
            if state == ProcessState.WAITING:
                calc.pause()

            calc.store()
            calcs.append(calc)

        group = Group(str(uuid.uuid4())).store()
        group.add_nodes(calcs[0])

        run_cli_command = functools.partial(run_cli_command, suppress_warnings=True)

        # Default behavior should yield all active states (CREATED, RUNNING and WAITING) so six in total
        result = run_cli_command(cmd_process.process_list, ['-r'])

        assert len(result.output_lines) == 6

        # Ordering shouldn't change the number of results,
        for flag in ['-O', '--order-by']:
            for flag_value in ['id', 'ctime']:
                result = run_cli_command(cmd_process.process_list, ['-r', flag, flag_value])

                assert len(result.output_lines) == 6

        # but the orders should be inverse
        for flag in ['-D', '--order-direction']:
            flag_value = 'asc'
            result = run_cli_command(cmd_process.process_list, ['-r', '-O', 'id', flag, flag_value])

            result_num_asc = [line.split()[0] for line in result.output_lines]
            assert len(result_num_asc) == 6

            flag_value = 'desc'
            result = run_cli_command(cmd_process.process_list, ['-r', '-O', 'id', flag, flag_value])

            result_num_desc = [line.split()[0] for line in result.output_lines]
            assert len(result_num_desc) == 6

            assert result_num_asc == list(reversed(result_num_desc))

        # Adding the all option should return all entries regardless of process state
        for flag in ['-a', '--all']:
            result = run_cli_command(cmd_process.process_list, ['-r', flag])

            assert len(result.output_lines) == 12

        # Passing the limit option should limit the results
        for flag in ['-l', '--limit']:
            result = run_cli_command(cmd_process.process_list, ['-r', flag, '6'])
            assert len(result.output_lines) == 6

        # Filtering for a specific process state
        for flag in ['-S', '--process-state']:
            for flag_value in ['created', 'running', 'waiting', 'killed', 'excepted', 'finished']:
                result = run_cli_command(cmd_process.process_list, ['-r', flag, flag_value])
                assert len(result.output_lines) == 2

        # Filtering for exit status should only get us one
        for flag in ['-E', '--exit-status']:
            for exit_status in ['0', '1']:
                result = run_cli_command(cmd_process.process_list, ['-r', flag, exit_status])
                assert len(result.output_lines) == 1

        # Passing the failed flag as a shortcut for FINISHED + non-zero exit status
        for flag in ['-X', '--failed']:
            result = run_cli_command(cmd_process.process_list, ['-r', flag])

            assert len(result.output_lines) == 1

        # Projecting on pk should allow us to verify all the pks
        for flag in ['-P', '--project']:
            result = run_cli_command(cmd_process.process_list, ['-r', flag, 'pk'])

            assert len(result.output_lines) == 6

            for line in result.output_lines:
                assert line.strip() in [str(calc.pk) for calc in calcs]

        # The group option should limit the query set to nodes in the group
        for flag in ['-G', '--group']:
            result = run_cli_command(cmd_process.process_list, ['-r', '-P', 'pk', flag, str(group.pk)])

            assert len(result.output_lines) == 1
            assert result.output_lines[0] == str(calcs[0].pk)

        # The process label should limit the query set to nodes with the given `process_label` attribute
        for flag in ['-L', '--process-label']:
            for label in [process_label, process_label.replace('Dummy', '%')]:
                result = run_cli_command(cmd_process.process_list, ['-r', flag, label])

                assert len(result.output_lines) == 3  # Should only match the active `WorkFunctionNodes`
                for line in result.output_lines:
                    assert process_label in line.strip()

        # There should be exactly one paused
        for flag in ['--paused']:
            result = run_cli_command(cmd_process.process_list, ['-r', flag])

            assert len(result.output_lines) == 1

        # There should be a failed WorkChain with exit status 1
        for flag in ['-P', '--project']:
            result = run_cli_command(cmd_process.process_list, ['-r', '-X', flag, 'exit_message'])
            assert Process.exit_codes.ERROR_UNSPECIFIED.message in result.output

    def test_process_show(self, run_cli_command):
        """Test verdi process show"""
        workchain_one = WorkChainNode()
        workchain_two = WorkChainNode()
        workchains = [workchain_one, workchain_two]

        workchain_two.base.attributes.set('process_label', 'workchain_one_caller')
        workchain_two.store()
        workchain_one.base.links.add_incoming(workchain_two, link_type=LinkType.CALL_WORK, link_label='called')
        workchain_one.store()

        calcjob_one = CalcJobNode()
        calcjob_two = CalcJobNode()

        calcjob_one.base.attributes.set('process_label', 'process_label_one')
        calcjob_two.base.attributes.set('process_label', 'process_label_two')

        calcjob_one.base.links.add_incoming(workchain_one, link_type=LinkType.CALL_CALC, link_label='one')
        calcjob_two.base.links.add_incoming(workchain_one, link_type=LinkType.CALL_CALC, link_label='two')

        calcjob_one.store()
        calcjob_two.store()

        # Running without identifiers should except and print something
        options = []
        result = run_cli_command(cmd_process.process_show, options, raises=True)
        assert result.exit_code == ExitCode.USAGE_ERROR
        assert len(result.output_lines) > 0

        # Giving a single identifier should print a non empty string message
        options = [str(workchain_one.pk)]
        result = run_cli_command(cmd_process.process_show, options)
        lines = result.output_lines

        assert len(lines) > 0
        assert 'workchain_one_caller' in result.output
        assert 'process_label_one' in lines[-2]
        assert 'process_label_two' in lines[-1]

        # Giving multiple identifiers should print a non empty string message
        options = [str(node.pk) for node in workchains]
        result = run_cli_command(cmd_process.process_show, options)

        assert len(result.output_lines) > 0

    def test_process_report(self, run_cli_command):
        """Test verdi process report"""
        node = WorkflowNode().store()

        # Running without identifiers should except and print something
        options = []
        result = run_cli_command(cmd_process.process_report, options, raises=True)
        assert result.exit_code == ExitCode.USAGE_ERROR
        assert len(result.output_lines) > 0

        # Giving a single identifier should print a non empty string message
        options = [str(node.pk)]
        result = run_cli_command(cmd_process.process_report, options)

        assert len(result.output_lines) > 0

        # Giving multiple identifiers should print a non empty string message
        options = [str(calc.pk) for calc in [node]]
        result = run_cli_command(cmd_process.process_report, options)

        assert len(result.output_lines) > 0

    def test_process_status(self, run_cli_command):
        """Test verdi process status"""
        node = WorkflowNode().store()
        node.set_process_state(ProcessState.RUNNING)

        # Running without identifiers should except and print something
        options = []
        result = run_cli_command(cmd_process.process_status, options, raises=True)
        assert result.exit_code == ExitCode.USAGE_ERROR
        assert len(result.output_lines) > 0

        # Giving a single identifier should print a non empty string message
        options = [str(node.pk)]
        result = run_cli_command(cmd_process.process_status, options)
        assert result.exception is None, result.output
        assert len(result.output_lines) > 0

        # With max depth 0, the output should be empty
        options = ['--max-depth', 0, str(node.pk)]
        result = run_cli_command(cmd_process.process_status, options)
        assert result.exception is None, result.output
        assert len(result.output_lines) == 0

    @pytest.mark.requires_rmq
    def test_process_watch(self, run_cli_command):
        """Test verdi process watch"""
        # Running without identifiers should except and print something
        options = []
        result = run_cli_command(cmd_process.process_watch, options, raises=True)
        assert result.exit_code == ExitCode.USAGE_ERROR
        assert len(result.output_lines) > 0

        # Running with both identifiers should raise an error and print something
        options = ['--most-recent-node', '1']
        result = run_cli_command(cmd_process.process_watch, options, raises=True)
        assert result.exit_code == ExitCode.USAGE_ERROR
        assert len(result.output_lines) > 0

    def test_process_status_call_link_label(self, run_cli_command):
        """Test ``verdi process status --call-link-label``."""
        node = WorkflowNode().store()
        node.set_process_state(ProcessState.RUNNING)

        # Create subprocess with specific call link label.
        child1 = CalcJobNode()
        child1.set_process_state(ProcessState.FINISHED)
        child1.base.links.add_incoming(node, link_type=LinkType.CALL_CALC, link_label='call_label')
        child1.store()

        # Create subprocess with default call link label, which should not show up.
        child2 = CalcJobNode()
        child2.set_process_state(ProcessState.FINISHED)
        child2.base.links.add_incoming(node, link_type=LinkType.CALL_CALC, link_label='CALL')
        child2.store()

        result = run_cli_command(cmd_process.process_status, [str(node.pk), '--call-link-label'])
        assert result.exception is None, result.output
        assert re.match(
            r'None<.*> Running\n    ├── None<.* | call_label> Finished\n    └── None<.*> Finished\n', result.output
        )

    def test_report(self, run_cli_command):
        """Test the report command."""
        grandparent = WorkChainNode().store()
        parent = WorkChainNode()
        child = WorkChainNode()

        parent.base.links.add_incoming(grandparent, link_type=LinkType.CALL_WORK, link_label='link')
        parent.store()
        child.base.links.add_incoming(parent, link_type=LinkType.CALL_WORK, link_label='link')
        child.store()

        grandparent.logger.log(LOG_LEVEL_REPORT, 'grandparent_message')
        parent.logger.log(LOG_LEVEL_REPORT, 'parent_message')
        child.logger.log(LOG_LEVEL_REPORT, 'child_message')

        result = run_cli_command(cmd_process.process_report, [str(grandparent.pk)])

        assert len(result.output_lines) == 3

        result = run_cli_command(cmd_process.process_report, [str(parent.pk)])

        assert len(result.output_lines) == 2

        result = run_cli_command(cmd_process.process_report, [str(child.pk)])

        assert len(result.output_lines) == 1

        # Max depth should limit nesting level
        for flag in ['-m', '--max-depth']:
            for flag_value in [1, 2]:
                result = run_cli_command(cmd_process.process_report, [str(grandparent.pk), flag, str(flag_value)])

                assert len(result.output_lines) == flag_value

        # Filtering for other level name such as WARNING should not have any hits and only print the no log message
        for flag in ['-l', '--levelname']:
            result = run_cli_command(cmd_process.process_report, [str(grandparent.pk), flag, 'WARNING'])

            assert len(result.output_lines) == 1, result.output_lines
            assert result.output_lines[0] == 'No log messages recorded for this entry'

    def test_process_dump(self, run_cli_command, tmp_path, generate_workchain_multiply_add):
        """Test verdi process dump"""

        # Only test CLI interface here, the actual functionalities of the Python API are tested in `test_processes.py`
        test_path = tmp_path / 'cli-dump'
        node = generate_workchain_multiply_add()

        # Giving a single identifier should print a non empty string message
        options = [str(node.pk), '-p', str(test_path)]
        result = run_cli_command(cmd_process.process_dump, options)
        assert result.exception is None, result.output
        assert 'Success:' in result.output

        # Trying to run the dumping again in the same path but without overwrite=True should raise exception
        options = [str(node.pk), '-p', str(test_path)]
        result = run_cli_command(cmd_process.process_dump, options, raises=True)
        assert result.exit_code is ExitCode.CRITICAL

        # Works fine when using overwrite=True
        options = [str(node.pk), '-p', str(test_path), '-o']
        result = run_cli_command(cmd_process.process_dump, options)
        assert result.exception is None, result.output
        assert 'Success:' in result.output

        # Set overwrite=True but provide bad directory, i.e. missing metadata file
        (test_path / '.aiida_node_metadata.yaml').unlink()

        options = [str(node.pk), '-p', str(test_path), '-o']
        result = run_cli_command(cmd_process.process_dump, options, raises=True)
        assert result.exit_code is ExitCode.CRITICAL


@pytest.mark.usefixtures('aiida_profile_clean')
@pytest.mark.parametrize('numprocesses, percentage', ((0, 100), (1, 90)))
@pytest.mark.requires_rmq
def test_list_worker_slot_warning(run_cli_command, monkeypatch, numprocesses, percentage):
    """Test that the if the number of used worker process slots exceeds a threshold,
    that the warning message is displayed to the user when running `verdi process list`
    """
    from aiida.engine import DaemonClient
    from aiida.manage.configuration import get_config

    monkeypatch.setattr(DaemonClient, 'get_numprocesses', lambda _: {'numprocesses': numprocesses})
    monkeypatch.setattr(DaemonClient, 'is_daemon_running', lambda: True)

    # Get the number of allowed processes per worker:
    config = get_config()
    worker_process_slots = config.get_option('daemon.worker_process_slots', get_profile().name)
    limit = int(worker_process_slots * 0.9)

    # Create additional active nodes such that we have 90% of the active slot limit
    for _ in range(limit):
        calc = WorkFunctionNode()
        calc.set_process_state(ProcessState.RUNNING)
        calc.store()

    result = run_cli_command(cmd_process.process_list, use_subprocess=False)

    if numprocesses == 0:
        warning_phrase = 'The daemon has no active workers!'
        assert any(warning_phrase in line for line in result.output_lines)
    else:
        # Default cmd should not throw the warning as we are below the limit
        warning_phrase = 'of the available daemon worker slots have been used!'
        assert all(warning_phrase not in line for line in result.output_lines), result.output

    # Add one more running node to put us over the limit
    calc = WorkFunctionNode()
    calc.set_process_state(ProcessState.RUNNING)
    calc.store()

    if numprocesses != 0:
        # Now the warning should fire
        result = run_cli_command(cmd_process.process_list, use_subprocess=False)
        warning_phrase = f'{percentage}% of the available daemon worker slots have been used!'
        assert any(warning_phrase in line for line in result.output_lines)


class TestVerdiProcessCallRoot:
    """Tests for `verdi process call-root`."""

    @pytest.fixture(autouse=True)
    def init_profile(self):
        """Initialize the profile."""
        self.node_root = WorkflowNode()
        self.node_middle = WorkflowNode()
        self.node_terminal = WorkflowNode()

        self.node_root.store()

        self.node_middle.base.links.add_incoming(self.node_root, link_type=LinkType.CALL_WORK, link_label='call_middle')
        self.node_middle.store()

        self.node_terminal.base.links.add_incoming(
            self.node_middle, link_type=LinkType.CALL_WORK, link_label='call_terminal'
        )
        self.node_terminal.store()

    def test_no_caller(self, run_cli_command):
        """Test `verdi process call-root` when passing single process without caller."""
        options = [str(self.node_root.pk)]
        result = run_cli_command(cmd_process.process_call_root, options)
        assert len(result.output_lines) == 1
        assert 'No callers found' in result.output_lines[0]

    def test_single_caller(self, run_cli_command):
        """Test `verdi process call-root` when passing single process with call root."""
        # Both the middle and terminal node should have the `root` node as call root.
        for node in [self.node_middle, self.node_terminal]:
            options = [str(node.pk)]
            result = run_cli_command(cmd_process.process_call_root, options)
            assert len(result.output_lines) == 1
            assert str(self.node_root.pk) in result.output_lines[0]

    def test_multiple_processes(self, run_cli_command):
        """Test `verdi process call-root` when passing multiple processes."""
        options = [str(self.node_root.pk), str(self.node_middle.pk), str(self.node_terminal.pk)]
        result = run_cli_command(cmd_process.process_call_root, options)
        assert len(result.output_lines) == 3
        assert 'No callers found' in result.output_lines[0]
        assert str(self.node_root.pk) in result.output_lines[1]
        assert str(self.node_root.pk) in result.output_lines[2]

    def test_no_process_argument(self, run_cli_command):
        # Running without identifiers should except and print something
        options = []
        result = run_cli_command(cmd_process.process_call_root, options, raises=True)
        assert result.exit_code == ExitCode.USAGE_ERROR
        assert len(result.output_lines) > 0


@pytest.mark.requires_rmq
@pytest.mark.usefixtures('started_daemon_client')
def test_process_pause(submit_and_await, run_cli_command):
    """Test the ``verdi process pause`` command."""
    node = submit_and_await(WaitProcess, ProcessState.WAITING)
    assert not node.paused

    run_cli_command(cmd_process.process_pause, [str(node.pk), '--wait'])
    await_condition(lambda: node.paused)

    # Running without identifiers should except and print something
    options = []
    result = run_cli_command(cmd_process.process_pause, options, raises=True)
    assert result.exit_code == ExitCode.USAGE_ERROR
    assert len(result.output_lines) > 0


@pytest.mark.requires_rmq
@pytest.mark.usefixtures('started_daemon_client')
def test_process_play(submit_and_await, run_cli_command):
    """Test the ``verdi process play`` command."""
    node = submit_and_await(WaitProcess, ProcessState.WAITING)

    run_cli_command(cmd_process.process_pause, [str(node.pk), '--wait'])
    await_condition(lambda: node.paused)

    run_cli_command(cmd_process.process_play, [str(node.pk), '--wait'])
    await_condition(lambda: not node.paused)

    # Running without identifiers should except and print something
    options = []
    result = run_cli_command(cmd_process.process_play, options, raises=True)
    assert result.exit_code == ExitCode.USAGE_ERROR
    assert len(result.output_lines) > 0


@pytest.mark.requires_rmq
@pytest.mark.usefixtures('started_daemon_client')
def test_process_play_all(submit_and_await, run_cli_command):
    """Test the ``verdi process play`` command with the ``--all`` option."""
    node_one = submit_and_await(WaitProcess, ProcessState.WAITING)
    node_two = submit_and_await(WaitProcess, ProcessState.WAITING)

    run_cli_command(cmd_process.process_pause, ['--all', '--wait'])
    await_condition(lambda: node_one.paused)
    await_condition(lambda: node_two.paused)

    run_cli_command(cmd_process.process_play, ['--all', '--wait'])
    await_condition(lambda: not node_one.paused)
    await_condition(lambda: not node_two.paused)


@pytest.mark.requires_rmq
@pytest.mark.usefixtures('started_daemon_client')
def test_process_kill(submit_and_await, run_cli_command):
    """Test the ``verdi process kill`` command."""
    node = submit_and_await(WaitProcess, ProcessState.WAITING)

    run_cli_command(cmd_process.process_pause, [str(node.pk), '--wait'])
    await_condition(lambda: node.paused)
    assert node.process_status == 'Paused through `verdi process pause`'

    run_cli_command(cmd_process.process_kill, [str(node.pk), '--wait'])
    await_condition(lambda: node.is_killed)
    assert node.process_status == 'Killed through `verdi process kill`'

    # Running without identifiers should except and print something
    options = []
    result = run_cli_command(cmd_process.process_kill, options, raises=True)
    assert result.exit_code == ExitCode.USAGE_ERROR
    assert len(result.output_lines) > 0


@pytest.mark.requires_rmq
@pytest.mark.usefixtures('started_daemon_client')
def test_process_kill_all(submit_and_await, run_cli_command):
    """Test the ``verdi process kill --all`` command."""
    node = submit_and_await(WaitProcess, ProcessState.WAITING)

    run_cli_command(cmd_process.process_kill, ['--all', '--wait'], user_input='y')
    await_condition(lambda: node.is_killed)
    assert node.process_status == 'Killed through `verdi process kill`'


@pytest.mark.usefixtures('started_daemon_client')
def test_process_repair_running_daemon(run_cli_command):
    """Test the ``verdi process repair`` command excepts when the daemon is running."""
    result = run_cli_command(cmd_process.process_repair, raises=True, use_subprocess=False)
    assert 'The daemon needs to be stopped before running this command.' in result.output


@pytest.mark.usefixtures('stopped_daemon_client')
def test_process_repair_consistent(monkeypatch, run_cli_command):
    """Test the ``verdi process repair`` command when everything is consistent."""
    monkeypatch.setattr(process_control, 'get_active_processes', lambda *args, **kwargs: [1, 2, 3])
    monkeypatch.setattr(process_control, 'get_process_tasks', lambda *args: [1, 2, 3])

    result = run_cli_command(cmd_process.process_repair, use_subprocess=False)
    assert 'No inconsistencies detected between database and RabbitMQ.' in result.output


@pytest.mark.usefixtures('stopped_daemon_client')
def test_process_repair_duplicate_tasks(monkeypatch, run_cli_command):
    """Test the ``verdi process repair`` command when there are duplicate tasks."""
    monkeypatch.setattr(process_control, 'get_active_processes', lambda *args, **kwargs: [1, 2])
    monkeypatch.setattr(process_control, 'get_process_tasks', lambda *args: [1, 2, 2])

    result = run_cli_command(cmd_process.process_repair, use_subprocess=False)
    assert 'There are duplicates process tasks:' in result.output
    assert 'Inconsistencies detected between database and RabbitMQ.' in result.output


@pytest.mark.usefixtures('stopped_daemon_client')
def test_process_repair_additional_tasks(monkeypatch, run_cli_command):
    """Test the ``verdi process repair`` command when there are additional tasks."""
    monkeypatch.setattr(process_control, 'get_active_processes', lambda *args, **kwargs: [1, 2])
    monkeypatch.setattr(process_control, 'get_process_tasks', lambda *args: [1, 2, 3])

    result = run_cli_command(cmd_process.process_repair, use_subprocess=False)
    assert 'There are process tasks for terminated processes:' in result.output
    assert 'Inconsistencies detected between database and RabbitMQ.' in result.output
    assert 'Attempting to fix inconsistencies' in result.output


@pytest.mark.usefixtures('stopped_daemon_client')
def test_process_repair_missing_tasks(monkeypatch, run_cli_command):
    """Test the ``verdi process repair`` command when there are missing tasks."""
    monkeypatch.setattr(process_control, 'get_active_processes', lambda *args, **kwargs: [1, 2, 3])
    monkeypatch.setattr(process_control, 'get_process_tasks', lambda *args: [1, 2])

    result = run_cli_command(cmd_process.process_repair, use_subprocess=False)
    assert 'There are active processes without process task:' in result.output
    assert 'Inconsistencies detected between database and RabbitMQ.' in result.output
    assert 'Attempting to fix inconsistencies' in result.output


@pytest.mark.usefixtures('stopped_daemon_client')
def test_process_repair_dry_run(monkeypatch, run_cli_command):
    """Test the ``verdi process repair`` command with ``--dry-run```."""
    monkeypatch.setattr(process_control, 'get_active_processes', lambda *args, **kwargs: [1, 2, 3, 4])
    monkeypatch.setattr(process_control, 'get_process_tasks', lambda *args: [1, 2])

    result = run_cli_command(cmd_process.process_repair, ['--dry-run'], raises=True, use_subprocess=False)
    assert 'Inconsistencies detected between database and RabbitMQ.' in result.output
    assert 'This was a dry-run, no changes will be made.' in result.output


@pytest.mark.usefixtures('stopped_daemon_client')
def test_process_repair_verbosity(monkeypatch, run_cli_command):
    """Test the ``verdi process repair`` command with ``-v INFO```."""
    monkeypatch.setattr(process_control, 'get_active_processes', lambda *args, **kwargs: [1, 2, 3, 4])
    monkeypatch.setattr(process_control, 'get_process_tasks', lambda *args: [1, 2])

    result = run_cli_command(cmd_process.process_repair, ['-v', 'INFO'], use_subprocess=False)
    assert 'Active processes: [1, 2, 3, 4]' in result.output
    assert 'Process tasks: [1, 2]' in result.output


@pytest.fixture
def process_nodes():
    """Return a list of two stored ``CalcJobNode`` instances with a finished process state."""
    nodes = [CalcJobNode(), CalcJobNode()]
    for node in nodes:
        node.set_process_state(ProcessState.FINISHED)
        node.store()
    return nodes


def test_process_report_most_recent_node(run_cli_command, process_nodes):
    """Test ``verdi process report --most-recent-node``."""
    result = run_cli_command(cmd_process.process_report, ['--most-recent-node'])
    assert f'*** {process_nodes[0].pk}:' not in result.output
    assert f'*** {process_nodes[1].pk}:' in result.output


def test_process_show_most_recent_node(run_cli_command, process_nodes):
    """Test ``verdi process show --most-recent-node``."""
    result = run_cli_command(cmd_process.process_show, ['--most-recent-node'])
    assert process_nodes[0].uuid not in result.output
    assert process_nodes[1].uuid in result.output


def test_process_status_most_recent_node(run_cli_command, process_nodes):
    """Test ``verdi process status --most-recent-node``."""
    result = run_cli_command(cmd_process.process_status, ['--most-recent-node'])
    assert f'<{process_nodes[0].pk}>' not in result.output
    assert f'<{process_nodes[1].pk}>' in result.output


@pytest.mark.parametrize('command', (cmd_process.process_report, cmd_process.process_show, cmd_process.process_status))
def test_process_most_recent_node_exclusive(run_cli_command, process_nodes, command):
    """Test command raises if ``-M`` is specified as well as explicit process nodes."""
    result = run_cli_command(command, ['-M', str(process_nodes[0].pk)], raises=True)
    assert 'cannot specify individual processes and the `-M/--most-recent-node` flag at the same time.' in result.output
