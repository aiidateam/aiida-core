# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# pylint: disable=no-self-use
"""Tests for `verdi process`."""
import functools
import time
import typing as t
import uuid

import pytest

from aiida import get_profile
from aiida.cmdline.commands import cmd_process
from aiida.common.links import LinkType
from aiida.common.log import LOG_LEVEL_REPORT
from aiida.engine import Process, ProcessState
from aiida.orm import CalcJobNode, Group, WorkChainNode, WorkflowNode, WorkFunctionNode
from tests.utils.processes import WaitProcess


def await_condition(condition: t.Callable, timeout: int = 1):
    """Wait for the ``condition`` to evaluate to ``True`` within the ``timeout`` or raise."""
    start_time = time.time()

    while not condition:  # type: ignore
        if time.time() - start_time > timeout:
            raise RuntimeError(f'waiting for {condition} to evaluate to `True` timed out after {timeout} seconds.')


class TestVerdiProcess:
    """Tests for `verdi process`."""

    TEST_TIMEOUT = 5.

    def test_list_non_raw(self, run_cli_command):
        """Test the list command as the user would run it (e.g. without -r)."""

        result = run_cli_command(cmd_process.process_list)

        assert 'Total results:' in result.output
        assert 'last time an entry changed state' in result.output

    def test_list(self, run_cli_command):
        """Test the list command."""
        # pylint: disable=too-many-branches,too-many-statements
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

        # Running without identifiers should not except and not print anything
        options = []
        result = run_cli_command(cmd_process.process_show, options)

        assert len(result.output_lines) == 0

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

        # Running without identifiers should not except and not print anything
        options = []
        result = run_cli_command(cmd_process.process_report, options)

        assert len(result.output_lines) == 0

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

        # Running without identifiers should not except and not print anything
        options = []
        result = run_cli_command(cmd_process.process_status, options)
        assert result.exception is None, result.output
        assert len(result.output_lines) == 0

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


@pytest.mark.usefixtures('aiida_profile_clean')
def test_list_worker_slot_warning(run_cli_command, monkeypatch):
    """
    Test that the if the number of used worker process slots exceeds a threshold,
    that the warning message is displayed to the user when running `verdi process list`
    """
    from aiida.engine import DaemonClient
    from aiida.manage.configuration import get_config

    monkeypatch.setattr(DaemonClient, 'get_numprocesses', lambda _: {'numprocesses': 1})
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

    # Default cmd should not throw the warning as we are below the limit
    result = run_cli_command(cmd_process.process_list, use_subprocess=False)
    warning_phrase = 'of the available daemon worker slots have been used!'
    assert all(warning_phrase not in line for line in result.output_lines), result.output

    # Add one more running node to put us over the limit
    calc = WorkFunctionNode()
    calc.set_process_state(ProcessState.RUNNING)
    calc.store()

    # Now the warning should fire
    result = run_cli_command(cmd_process.process_list, use_subprocess=False)
    warning_phrase = '% of the available daemon worker slots have been used!'
    assert any(warning_phrase in line for line in result.output_lines)


class TestVerdiProcessCallRoot:
    """Tests for `verdi process call-root`."""

    @pytest.fixture(autouse=True)
    def init_profile(self):
        """Initialize the profile."""
        # pylint: disable=attribute-defined-outside-init
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


@pytest.mark.requires_rmq
@pytest.mark.usefixtures('started_daemon_client')
def test_process_pause(submit_and_await, run_cli_command):
    """Test the ``verdi process pause`` command."""
    node = submit_and_await(WaitProcess, ProcessState.WAITING)
    assert not node.paused

    run_cli_command(cmd_process.process_pause, [str(node.pk), '--wait'])
    await_condition(lambda: node.paused)


@pytest.mark.requires_rmq
@pytest.mark.usefixtures('started_daemon_client')
def test_process_play(submit_and_await, run_cli_command):
    """Test the ``verdi process play`` command."""
    node = submit_and_await(WaitProcess, ProcessState.WAITING)

    run_cli_command(cmd_process.process_pause, [str(node.pk), '--wait'])
    await_condition(lambda: node.paused)

    run_cli_command(cmd_process.process_play, [str(node.pk), '--wait'])
    await_condition(lambda: not node.paused)


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
