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
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch

import pytest

from aiida import get_profile
from aiida.cmdline.commands import cmd_process
from aiida.cmdline.utils.echo import ExitCode
from aiida.common.links import LinkType
from aiida.common.log import LOG_LEVEL_REPORT
from aiida.engine import Process, ProcessState
from aiida.engine.processes import control as process_control
from aiida.engine.utils import exponential_backoff_retry
from aiida.orm import CalcJobNode, Group, Int, WorkChainNode, WorkflowNode, WorkFunctionNode
from aiida.tools.archive.exceptions import ExportValidationError
from tests.utils.processes import WaitProcess

FuncArgs = tuple[t.Any, ...]


def start_daemon_worker_in_foreground_and_redirect_streams(
    aiida_profile_name: str, log_dir: Path, prepare_func: t.Callable[[FuncArgs], t.Any], prepare_func_args: FuncArgs
):
    """Starts a daemon worker and logs its stdout and and stderr streams to a file in the daemon log directory.

    :param aiida_profile_name: The name of the profile the daemon worker should load.
    :param log_dir: The directory the log of the worker is put
    :param prepare_func: Called before the worker is started
    :param prepare_func_args: The arguments passed to the `prepare_func`
    """
    import os
    import sys

    from aiida.engine.daemon.worker import start_daemon_worker

    prepare_func(*prepare_func_args)

    original_stdout = sys.stdout
    original_stderr = sys.stderr

    try:
        pid = os.getpid()
        # For easier debugging you can change these to stdout
        sys.stdout = open(log_dir / f'worker-{pid}.out', 'w')
        sys.stderr = open(log_dir / f'worker-{pid}.err', 'w')
        start_daemon_worker(False, aiida_profile_name)
    finally:
        if sys.stdout != original_stdout:
            sys.stdout.close()
            sys.stdout = original_stdout
        if sys.stderr != original_stderr:
            sys.stderr.close()
            sys.stderr = original_stderr


# We have to define the mock functions globally as we cannot pass local function to a spawn process
class MockFunctions:
    @staticmethod
    def mock_open(_):
        raise Exception('Mock open exception')

    @staticmethod
    async def exponential_backoff_retry_fail_upload(fct: t.Callable[..., t.Any], *args, **kwargs):
        from aiida.common.exceptions import TransportTaskException

        if 'do_upload' in fct.__name__:
            raise TransportTaskException
        else:
            return await exponential_backoff_retry(fct, *args, **kwargs)

    @staticmethod
    async def exponential_backoff_retry_fail_kill(fct: t.Callable[..., t.Any], *args, **kwargs):
        from aiida.common.exceptions import TransportTaskException

        if 'do_kill' in fct.__name__:
            raise TransportTaskException
        else:
            return await exponential_backoff_retry(fct, *args, **kwargs)


@pytest.fixture(scope='function')
def fork_worker_context(aiida_profile, started_daemon_client):
    """Runs daemon worker on a new process with redirected stdout and stderr streams."""
    import multiprocessing

    client = started_daemon_client
    nb_workers = client.get_number_of_workers()
    # The workers are decreased to zero to ensure that the worker that is
    # subsequently started through this fixture is the one that receives all
    # submitted processes.
    client.decrease_workers(nb_workers)
    daemon_log_dir = Path(client.daemon_log_file).parent

    @contextmanager
    def fork_worker(func, func_args):
        # It is important that we spawn the process to not inherit the sql and
        # broker connection that cannot be shared over procesess
        ctx = multiprocessing.get_context('spawn')
        # we need to pass the aiida profile so it uses the same configuration
        process = ctx.Process(
            target=start_daemon_worker_in_foreground_and_redirect_streams,
            args=(aiida_profile.name, daemon_log_dir, func, func_args),
        )
        process.start()

        yield process

        process.terminate()
        process.join()

    yield fork_worker

    client.increase_workers(nb_workers)


def await_condition(condition: t.Callable, timeout: int = 1) -> t.Any:
    """Wait for the ``condition`` to evaluate to ``True`` within the ``timeout`` or raise."""
    start_time = time.time()

    while not (result := condition()):
        if time.time() - start_time > timeout:
            raise RuntimeError(f'waiting for {condition} to evaluate to `True` timed out after {timeout} seconds.')
        time.sleep(0.1)

    return result


@pytest.mark.requires_rmq
@pytest.mark.usefixtures('started_daemon_client')
def test_process_kill_failing_transport(
    fork_worker_context, submit_and_await, aiida_code_installed, run_cli_command, monkeypatch
):
    """Tests if a process that is unable to open a transport connection can be force killed.

    A failure in opening a transport connection results in the EBM to be fired blocking a regular kill command.
    The force kill command will ignore the EBM and kill the process in any case."""
    from aiida.cmdline.utils.common import get_process_function_report

    code = aiida_code_installed(default_calc_job_plugin='core.arithmetic.add', filepath_executable='/bin/bash')

    def make_a_builder(sleep_seconds=0):
        builder = code.get_builder()
        builder.x = Int(1)
        builder.y = Int(1)
        builder.metadata.options.sleep = sleep_seconds
        return builder

    kill_timeout = 10

    # patch a faulty transport open
    mokeypatch_args = ('aiida.transports.plugins.local.LocalTransport.open', MockFunctions.mock_open)
    with fork_worker_context(monkeypatch.setattr, mokeypatch_args):
        node = submit_and_await(make_a_builder(100), ProcessState.WAITING)
        result = await_condition(lambda: get_process_function_report(node), timeout=kill_timeout)
        assert 'Mock open exception' in result
        assert 'exponential_backoff_retry' in result

        # force kill the process
        run_cli_command(cmd_process.process_kill, [str(node.pk), '-F'])
        await_condition(lambda: node.is_killed, timeout=kill_timeout)
        assert node.is_killed
        assert node.process_status == 'Force killed through `verdi process kill`'


@pytest.mark.requires_rmq
@pytest.mark.usefixtures('started_daemon_client')
def test_process_kill_failing_transport_failed_kill(
    fork_worker_context, submit_and_await, aiida_code_installed, run_cli_command, monkeypatch
):
    """Tests if a process that is unable to open a transport connection can be force killed.

    A process that has stuck in EBM, cannot get killed directly by `verdi process kill`.
    Such a process with a history of failed attempts, should still be able to get force killed.
    `verdi process kill -F` --as the second attempt--
    """

    from aiida.cmdline.utils.common import get_process_function_report

    code = aiida_code_installed(default_calc_job_plugin='core.arithmetic.add', filepath_executable='/bin/bash')

    def make_a_builder(sleep_seconds=0):
        builder = code.get_builder()
        builder.x = Int(1)
        builder.y = Int(1)
        builder.metadata.options.sleep = sleep_seconds
        return builder

    kill_timeout = 10

    monkeypatch_args = ('aiida.transports.plugins.local.LocalTransport.open', MockFunctions.mock_open)
    with fork_worker_context(monkeypatch.setattr, monkeypatch_args):
        node = submit_and_await(make_a_builder(5), ProcessState.WAITING)

        # assert the process is stuck in EBM
        result = await_condition(lambda: get_process_function_report(node), timeout=kill_timeout)
        assert 'Mock open exception' in result
        assert 'exponential_backoff_retry' in result

        # practice a normal kill, which should fail
        result = run_cli_command(cmd_process.process_kill, [str(node.pk), '--timeout', '1.0'])
        assert f'Error: Call to kill Process<{node.pk}> timed out' in result.stdout

        # force kill the process
        result = run_cli_command(cmd_process.process_kill, [str(node.pk), '-F'])
        await_condition(lambda: node.is_killed, timeout=kill_timeout)
        assert node.process_status == 'Force killed through `verdi process kill`'


@pytest.mark.requires_rmq
@pytest.mark.usefixtures('started_daemon_client')
def test_process_kill_failing_ebm_transport(
    fork_worker_context, submit_and_await, aiida_code_installed, run_cli_command, monkeypatch
):
    """Kill a process that is waiting after failed EBM during a transport task.

    It should be possible to kill it normally. A process that failed upload (e.g. in scenarios that transport is working
    again) and is then killed
    """
    code = aiida_code_installed(default_calc_job_plugin='core.arithmetic.add', filepath_executable='/bin/bash')

    def make_a_builder(sleep_seconds=0):
        builder = code.get_builder()
        builder.x = Int(1)
        builder.y = Int(1)
        builder.metadata.options.sleep = sleep_seconds
        return builder

    kill_timeout = 10

    monkeypatch_args = (
        'aiida.engine.utils.exponential_backoff_retry',
        MockFunctions.exponential_backoff_retry_fail_upload,
    )
    with fork_worker_context(monkeypatch.setattr, monkeypatch_args):
        node = submit_and_await(make_a_builder(), ProcessState.WAITING)
        await_condition(
            lambda: node.process_status
            == 'Pausing after failed transport task: upload_calculation failed 5 times consecutively',
            timeout=kill_timeout,
        )

        # kill should start EBM and should successfully kill
        run_cli_command(cmd_process.process_kill, [str(node.pk)])
        await_condition(lambda: node.is_killed, timeout=kill_timeout)


@pytest.mark.requires_rmq
@pytest.mark.usefixtures('started_daemon_client')
def test_process_kill_failing_ebm_kill(
    fork_worker_context, submit_and_await, aiida_code_installed, run_cli_command, monkeypatch
):
    """Kill a process that had previously failed with an EBM.

    Killing a process tries to gracefully cancel the job on the remote node. If there are connection problems it retries
    it in using the EBM. If this fails another kill command can be send to restart the cancelation of the job scheduler.
    """
    from aiida.cmdline.utils.common import get_process_function_report

    code = aiida_code_installed(default_calc_job_plugin='core.arithmetic.add', filepath_executable='/bin/bash')

    def make_a_builder(sleep_seconds=0):
        builder = code.get_builder()
        builder.x = Int(1)
        builder.y = Int(1)
        builder.metadata.options.sleep = sleep_seconds
        return builder

    kill_timeout = 10

    monkeypatch_args = (
        'aiida.engine.utils.exponential_backoff_retry',
        MockFunctions.exponential_backoff_retry_fail_kill,
    )
    with fork_worker_context(monkeypatch.setattr, monkeypatch_args):
        node = submit_and_await(make_a_builder(kill_timeout + 10), ProcessState.WAITING, timeout=kill_timeout)
        await_condition(
            lambda: node.process_status == 'Monitoring scheduler: job state RUNNING',
            timeout=kill_timeout,
        )

        # kill should start EBM and be not successful in EBM
        run_cli_command(cmd_process.process_kill, [str(node.pk)])
        await_condition(lambda: not node.is_killed, timeout=kill_timeout)

        # kill should restart EBM and be not successful in EBM
        # this tests if the old task is cancelled and restarted successfully
        run_cli_command(cmd_process.process_kill, [str(node.pk)])
        await_condition(
            lambda: 'Found active scheduler job cancelation that will be rescheduled.'
            in get_process_function_report(node),
            timeout=kill_timeout,
        )

        # force kill should skip EBM and successfully kill the process
        run_cli_command(cmd_process.process_kill, [str(node.pk), '-F'])
        await_condition(lambda: node.is_killed, timeout=kill_timeout)


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

    def test_dump_basic(self, run_cli_command, tmp_path, generate_calculation_node_add):
        """Test basic dump functionality"""
        test_path = tmp_path / 'cli-dump'
        node = generate_calculation_node_add()

        options = [str(node.pk), '--path', str(test_path)]
        result = run_cli_command(cmd_process.process_dump, options)
        assert result.exception is None, result.output
        assert 'Success:' in result.output
        assert test_path.exists()

    def test_dump_dry_run(self, run_cli_command, tmp_path, generate_calculation_node_add):
        """Test dry run behavior"""
        test_path = tmp_path / 'cli-dump'
        node = generate_calculation_node_add()

        options = [str(node.pk), '--path', str(test_path / 'dry'), '--dry-run']
        result = run_cli_command(cmd_process.process_dump, options)
        assert result.exception is None, result.output
        assert 'Dry run completed' in result.output
        assert not test_path.exists()

    def test_dump_overwrite(self, run_cli_command, tmp_path, generate_calculation_node_add):
        """Test overwrite functionality"""
        test_path = tmp_path / 'cli-dump'
        node = generate_calculation_node_add()

        # First dump
        options = [str(node.pk), '--path', str(test_path)]
        result = run_cli_command(cmd_process.process_dump, options)
        assert result.exception is None, result.output
        assert test_path.exists()

        # Test overwrite
        options = [str(node.pk), '--path', str(test_path), '--overwrite']
        result = run_cli_command(cmd_process.process_dump, options)
        assert result.exception is None, result.output
        assert 'Success:' in result.output

    def test_dump_dry_run_with_overwrite_warning(self, run_cli_command, generate_calculation_node_add):
        """Test that dry_run + overwrite shows warning and returns early"""
        node = generate_calculation_node_add()

        options = [str(node.pk), '--dry-run', '--overwrite']
        result = run_cli_command(cmd_process.process_dump, options)
        assert result.exception is None, result.output
        assert 'Both `dry_run` and `overwrite` set to true' in result.output
        assert 'Operation will NOT be performed' in result.output

    def test_dump_specified_path_message(self, run_cli_command, tmp_path, generate_calculation_node_add):
        """Test that specified path is reported correctly"""
        test_path = tmp_path / 'specified-path'
        node = generate_calculation_node_add()

        options = [str(node.pk), '--path', str(test_path)]
        result = run_cli_command(cmd_process.process_dump, options)
        assert result.exception is None, result.output
        assert f'Using specified output path: `{test_path}`' in result.output

    def test_dump_warning_message_displayed(self, run_cli_command, generate_calculation_node_add):
        """Test that warning message about new feature is displayed"""
        node = generate_calculation_node_add()

        options = [str(node.pk)]
        result = run_cli_command(cmd_process.process_dump, options)
        assert result.exception is None, result.output
        assert 'This is a new feature which is still in its testing phase' in result.output
        assert 'If you encounter unexpected behavior or bugs' in result.output

    @patch('aiida.orm.nodes.process.process.ProcessNode.dump')
    def test_dump_calls_process_dump_with_correct_args(
        self, mock_dump, run_cli_command, tmp_path, generate_calculation_node_add
    ):
        """Test that process.dump is called with correct arguments"""
        test_path = tmp_path / 'test-args'
        node = generate_calculation_node_add()

        options = [
            str(node.pk),
            '--path',
            str(test_path),
            '--include-inputs',
            '--include-outputs',
            '--include-attributes',
            '--include-extras',
            '--flat',
            '--dump-unsealed',
        ]
        _ = run_cli_command(cmd_process.process_dump, options)

        # Verify the dump method was called with expected arguments
        node.dump.assert_called_once_with(
            output_path=test_path.resolve(),
            dry_run=False,
            overwrite=False,
            include_inputs=True,
            include_outputs=True,
            include_attributes=True,
            include_extras=True,
            flat=True,
            dump_unsealed=True,
        )

    @patch('aiida.orm.nodes.process.process.ProcessNode.dump')
    def test_dump_export_validation_error_handling(
        self, mock_dump, run_cli_command, tmp_path, generate_calculation_node_io
    ):
        """Test handling of ExportValidationError"""
        test_path = tmp_path / 'validation-error'
        node = generate_calculation_node_io()

        # Mock dump to raise ExportValidationError
        mock_dump.side_effect = ExportValidationError('Test validation error')

        options = [str(node.pk), '--path', str(test_path)]
        result = run_cli_command(cmd_process.process_dump, options, raises=True)

        assert 'Data validation error during dump: Test validation error' in result.output

    @patch('aiida.orm.nodes.process.process.ProcessNode.dump')
    def test_dump_unexpected_error_handling(self, mock_dump, run_cli_command, tmp_path, generate_calculation_node_add):
        """Test handling of unexpected exceptions"""
        test_path = tmp_path / 'unexpected-error'
        node = generate_calculation_node_add()

        # Mock dump to raise generic exception
        mock_dump.side_effect = RuntimeError('Unexpected error')

        options = [str(node.pk), '--path', str(test_path)]
        result = run_cli_command(cmd_process.process_dump, options, raises=True)

        assert f'Unexpected error during dump of process {node.pk}:' in result.output
        assert 'RuntimeError: Unexpected error' in result.output
        # Should include traceback
        assert 'Traceback' in result.output

    def test_dump_success_message_format(self, run_cli_command, tmp_path, generate_calculation_node_add):
        """Test success message format"""
        test_path = tmp_path / 'success-test'
        node = generate_calculation_node_add()

        options = [str(node.pk), '--path', str(test_path)]
        result = run_cli_command(cmd_process.process_dump, options)
        assert result.exception is None, result.output

        expected_msg = f'Raw files for process `{node.pk}` dumped into folder `{test_path.name}`'
        assert expected_msg in result.output


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

    run_cli_command(cmd_process.process_pause, [str(node.pk)])
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

    run_cli_command(cmd_process.process_pause, [str(node.pk)])
    await_condition(lambda: node.paused)

    run_cli_command(cmd_process.process_play, [str(node.pk)])
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

    run_cli_command(cmd_process.process_pause, ['--all'])
    await_condition(lambda: node_one.paused)
    await_condition(lambda: node_two.paused)

    run_cli_command(cmd_process.process_play, ['--all'])
    await_condition(lambda: not node_one.paused)
    await_condition(lambda: not node_two.paused)


@pytest.mark.requires_rmq
@pytest.mark.usefixtures('started_daemon_client')
def test_process_kill(submit_and_await, run_cli_command, aiida_code_installed):
    """Test the ``verdi process kill`` command.
    It tries to cover all the possible scenarios of killing a process.
    """

    kill_timeout = 20

    # 0) Running without identifiers should except and print something
    result = run_cli_command(cmd_process.process_kill, raises=True)
    assert result.exit_code == ExitCode.USAGE_ERROR
    assert len(result.output_lines) > 0

    code = aiida_code_installed(default_calc_job_plugin='core.arithmetic.add', filepath_executable='/bin/bash')
    builder = code.get_builder()
    builder.x = Int(2)
    builder.y = Int(3)
    builder.metadata.options.sleep = 20

    # Kill a paused process
    node = submit_and_await(builder, ProcessState.WAITING)

    run_cli_command(cmd_process.process_pause, [str(node.pk)])
    await_condition(lambda: node.paused)
    assert node.process_status == 'Paused through `verdi process pause`'

    run_cli_command(cmd_process.process_kill, [str(node.pk)])
    await_condition(lambda: node.is_killed)
    assert node.process_status == 'Killed through `verdi process kill`'

    # Force kill a paused process
    node = submit_and_await(builder, ProcessState.WAITING)

    run_cli_command(cmd_process.process_pause, [str(node.pk)])
    await_condition(lambda: node.paused)
    assert node.process_status == 'Paused through `verdi process pause`'

    run_cli_command(cmd_process.process_kill, [str(node.pk), '-F'])
    await_condition(lambda: node.is_killed)
    assert node.process_status == 'Force killed through `verdi process kill`'

    # `verdi process kill --all` should kill all processes
    node_1 = submit_and_await(builder, ProcessState.WAITING)
    run_cli_command(cmd_process.process_pause, [str(node_1.pk)])
    await_condition(lambda: node_1.paused)
    node_2 = submit_and_await(builder, ProcessState.WAITING)

    run_cli_command(cmd_process.process_kill, ['--all'], user_input='y')
    await_condition(lambda: node_1.is_killed, timeout=kill_timeout)
    await_condition(lambda: node_2.is_killed, timeout=kill_timeout)
    assert node_1.process_status == 'Killed through `verdi process kill`'
    assert node_2.process_status == 'Killed through `verdi process kill`'

    # `verdi process kill --all -F` should Force kill all processes (running / not running)
    node_1 = submit_and_await(builder, ProcessState.WAITING)
    run_cli_command(cmd_process.process_pause, [str(node_1.pk)])
    await_condition(lambda: node_1.paused)
    node_2 = submit_and_await(builder, ProcessState.WAITING)

    run_cli_command(cmd_process.process_kill, ['--all', '-F'], user_input='y')
    await_condition(lambda: node_1.is_killed, timeout=kill_timeout)
    await_condition(lambda: node_2.is_killed, timeout=kill_timeout)
    assert node_1.process_status == 'Force killed through `verdi process kill`'
    assert node_2.process_status == 'Force killed through `verdi process kill`'


@pytest.mark.requires_rmq
@pytest.mark.usefixtures('started_daemon_client')
def test_process_kill_all(submit_and_await, run_cli_command):
    """Test the ``verdi process kill --all`` command."""
    node = submit_and_await(WaitProcess, ProcessState.WAITING)

    run_cli_command(cmd_process.process_kill, ['--all'], user_input='y')
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
