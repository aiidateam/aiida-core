###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for the :mod:`aiida.tools.shell` module."""

import datetime
import json
import logging
import pathlib
import shutil

import pytest

from aiida.calculations.shell import ShellJob
from aiida.engine import WorkChain, run_get_node, workfunction
from aiida.orm import (
    AbstractCode,
    Computer,
    Float,
    InstalledCode,
    Int,
    PortableCode,
    RemoteData,
    ShellCode,
    SinglefileData,
    Str,
)
from aiida.tools.shell import launch_shell_job, prepare_computer

DATE_COMMAND = shutil.which('date')
assert DATE_COMMAND is not None, 'The `date` command must be available in order to run the tests.'

ECHO_COMMAND = shutil.which('echo')
assert ECHO_COMMAND is not None, 'The `echo` command must be available in order to run the tests.'


class ShellWorkChain(WorkChain):
    """Implementation of :class:`aiida.engine.processes.workchains.workchain.WorkChain` that submits a ``ShellJob``."""

    @classmethod
    def define(cls, spec):
        """Define the process specification."""
        super().define(spec)
        spec.outline(cls.run_step, cls.results)
        spec.output('stdout')

    def run_step(self):
        """Submit a shell job to the daemon."""
        _, node = launch_shell_job('date', submit=True)
        self.to_context(shell_job=node)

    def results(self):
        """Attach the results."""
        self.out('stdout', self.ctx.shell_job.outputs.stdout)


def test_error_command_not_found():
    """Test :func:`aiida.tools.launch_shell_job` with non-existing ``command``."""
    with pytest.raises(ValueError, match=r'failed to determine the absolute path of the command on the computer.*'):
        launch_shell_job('unknown-command')


def test_error_command_failed():
    """Test that the shellfunction process fails if the command fails.

    Running ``tar`` without arguments should cause it to return a non-zero exit status.
    """
    _, node = launch_shell_job('tar')
    assert node.is_failed
    assert node.exit_status == ShellJob.exit_codes.ERROR_COMMAND_FAILED.status


def test_multi_command_raise():
    """Test :func:`aiida.tools.launch_shell_job` raises if ``command`` is passed with arguments.

    Tests if the command is correctly resolved and raises an error message.
    """
    with pytest.raises(ValueError, match=r'failed to determine the absolute path of the command on the computer.*'):
        launch_shell_job('git diff')


def test_default():
    """Test :func:`aiida.tools.launch_shell_job` with default arguments."""
    results, node = launch_shell_job('date')
    assert node.is_finished_ok
    assert isinstance(results['stdout'], SinglefileData)
    assert results['stdout'].get_content()


def test_command(aiida_code_installed):
    """Test the ``command`` argument accepts a pre-configured code instance."""
    code = aiida_code_installed(filepath_executable='/bin/true', default_calc_job_plugin='core.shell')
    assert isinstance(code, AbstractCode)

    _, node = launch_shell_job(code)
    assert node.is_finished_ok


def test_command_invalid():
    """Test the ``command`` argument raises a ``TypeError`` if anything but a ``str`` or ``AbstractCode`` is passed."""
    with pytest.raises(TypeError, match=r'Got object of type .*, expecting .*'):
        launch_shell_job(None)


def test_arguments():
    """Test a shellfunction that specifies positional CLI arguments.

    Have ``date`` print the current date without time in ISO 8601 format. Note that if we are very unlucky, the
    shellfunction runs just before midnight and the comparison ``datetime`` call runs in the next day causing the test
    to fail, but that seems extremely unlikely.
    """
    arguments = ['-I']  # equivalent to --iso-8601, but supported also on MacOS
    results, node = launch_shell_job('date', arguments=arguments)

    assert node.is_finished_ok
    assert results['stdout'].get_content().strip() == datetime.datetime.now().strftime('%Y-%m-%d')


def test_arguments_string():
    """Test that the ``arguments`` argument accepts a string that automatically splits it in a list of arguments."""
    arguments = '--iso-8601 --universal'
    _, node = launch_shell_job('date', arguments=arguments)
    assert node.inputs.arguments.get_list() == ['--iso-8601', '--universal']


def test_nodes_single_file_data():
    """Test a shellfunction that specifies positional CLI arguments that are interpolated by the ``kwargs``."""
    content_a = 'content_a'
    content_b = 'content_b'
    nodes = {
        'file_a': SinglefileData.from_string(content_a),
        'file_b': SinglefileData.from_string(content_b),
    }
    arguments = ['{file_a}', '{file_b}']
    results, node = launch_shell_job('cat', arguments=arguments, nodes=nodes)

    assert node.is_finished_ok
    assert results['stdout'].get_content().strip() == content_a + content_b


@pytest.mark.parametrize('use_symlinks', (True, False))
def test_nodes_remote_data(tmp_path, aiida_localhost, use_symlinks):
    """Test the ``nodes`` input with ``RemoteData`` nodes.

    The test creates an ``RemoteData`` node containing a zip archive, which is then passed as an input to a shell job
    that unzips it and registers the file it contains as an output.
    """
    dirpath_source = tmp_path / 'source'
    dirpath_archive = tmp_path / 'archive'

    dirpath_source.mkdir()
    dirpath_archive.mkdir()

    # Write a dummy file to the ``source`` directory and create an archive of that dir in the ``archive`` directory.
    (dirpath_source / 'file_a.txt').write_text('content a')
    shutil.make_archive(dirpath_archive / 'archive', 'zip', dirpath_source)

    # Also create an empty directory and directory containing a file.
    dirpath_sub_empty = dirpath_archive / 'empty'
    dirpath_sub_filled = dirpath_archive / 'filled'
    dirpath_sub_empty.mkdir()
    dirpath_sub_filled.mkdir()
    (dirpath_sub_filled / 'file_b.txt').write_text('content b')

    # Create a ``RemoteData`` node of the ``archive`` directory which should contain only the ``archive.zip`` file.
    remote_data = RemoteData(remote_path=str(dirpath_archive), computer=aiida_localhost)

    results, node = launch_shell_job(
        'unzip',
        arguments=['archive.zip'],
        nodes={'remote': remote_data},
        outputs=['file_a.txt'],
        metadata={
            'options': {'use_symlinks': use_symlinks},
        },
    )
    assert node.is_finished_ok
    assert results['file_a_txt'].get_content() == 'content a'

    dirpath_working = pathlib.Path(node.outputs.remote_folder.get_remote_path())
    filepath_archive = dirpath_working / 'archive.zip'
    assert filepath_archive.is_file()
    assert filepath_archive.is_symlink() == use_symlinks
    assert (dirpath_working / 'empty').is_dir()
    assert (dirpath_working / 'filled').is_dir()
    assert (dirpath_working / 'filled' / 'file_b.txt').is_file()
    assert (dirpath_working / 'filled' / 'file_b.txt').read_text() == 'content b'


def test_nodes_remote_data_filename(tmp_path_factory, aiida_localhost):
    """Test copying contents of a ``RemoteData`` to specific subdirectory."""
    dirpath_remote = tmp_path_factory.mktemp('remote')
    dirpath_source = dirpath_remote / 'source'
    dirpath_source.mkdir()
    (dirpath_source / 'file.txt').touch()
    remote_data = RemoteData(remote_path=str(dirpath_remote), computer=aiida_localhost)

    results, node = launch_shell_job(
        'echo',
        arguments=['{remote}'],
        nodes={'remote': remote_data},
        filenames={'remote': 'sub_directory'},
    )
    assert node.is_finished_ok
    assert results['stdout'].get_content().strip() == 'sub_directory'
    dirpath_working = pathlib.Path(node.outputs.remote_folder.get_remote_path())
    assert (dirpath_working / 'sub_directory').is_dir()
    assert (dirpath_working / 'sub_directory' / 'source').is_dir()
    assert (dirpath_working / 'sub_directory' / 'source' / 'file.txt').is_file()


def test_nodes_base_types():
    """Test a shellfunction that specifies positional CLI arguments that are interpolated by the ``kwargs``."""
    nodes = {
        'float': Float(1.0),
        'int': Int(2),
        'str': Str('string'),
    }
    arguments = ['{float}', '{int}', '{str}']
    results, node = launch_shell_job('echo', arguments=arguments, nodes=nodes)

    assert node.is_finished_ok
    assert results['stdout'].get_content().strip() == '1.0 2 string'


@pytest.mark.parametrize('filename', ('filename.txt', pathlib.Path('filename.txt')))
def test_files_type(tmp_path, filename):
    """Test that ``nodes`` accepts ``str`` and ``pathlib.Path`` as values and converts them in ``SinglefileData``."""
    filepath = tmp_path / filename
    filepath.write_text('content')

    if isinstance(filename, str):
        results, node = launch_shell_job('cat', arguments=['{filename}'], nodes={'filename': str(filepath)})
    else:
        results, node = launch_shell_job('cat', arguments=['{filename}'], nodes={'filename': filepath})

    assert node.is_finished_ok
    assert results['stdout'].get_content() == 'content'


def test_files_invalid_type():
    """Test the function raises a ``TypeError`` for an invalid type in ``nodes``."""
    with pytest.raises(TypeError, match=r'received type .* for `filename` in `nodes`.*'):
        launch_shell_job('cat', nodes={'filename': True})


def test_files_not_exist():
    """Test the function raises a ``FileNotFoundError`` if a file in ``nodes`` does not exist."""
    with pytest.raises(FileNotFoundError, match=r'the path `.*` specified in `nodes` does not exist.'):
        launch_shell_job('cat', nodes={'filename': 'non-existing.txt'})


def test_arguments_files():
    """Test a shellfunction that specifies positional and keyword CLI arguments interpolated by the ``kwargs``."""
    content = 'line 1\nline 2'
    arguments = ['-n', '1', '{single_file}']
    nodes = {'single_file': SinglefileData.from_string(content)}
    results, node = launch_shell_job('head', arguments=arguments, nodes=nodes)

    assert node.is_finished_ok
    assert results['stdout'].get_content().strip() == content.split('\n', maxsplit=1)[0]


def test_submit(submit_and_await):
    """Test the ``submit`` argument."""
    _, node = launch_shell_job('date', submit=True)
    submit_and_await(node)
    assert node.is_finished_ok
    assert isinstance(node.outputs.stdout, SinglefileData)
    assert node.outputs.stdout.get_content()


@pytest.mark.usefixtures('started_daemon_client')
def test_submit_inside_workchain():
    """Test the ``submit`` argument when used inside a work chain."""
    results, node = run_get_node(ShellWorkChain)
    assert node.is_finished_ok, (node.process_state, node.exit_status)
    assert isinstance(results['stdout'], SinglefileData)


@pytest.mark.usefixtures('started_daemon_client')
def test_submit_inside_workfunction(submit_and_await):
    """Test the ``submit`` argument when used inside a work function."""

    @workfunction
    def job_function():
        _, node = launch_shell_job('date', submit=True)
        submit_and_await(node)
        return {'stdout': node.outputs['stdout']}

    results, node = job_function.run_get_node()  # type: ignore[attr-defined]
    assert node.is_finished_ok, (node.process_state, node.exit_status)
    assert isinstance(results['stdout'], SinglefileData)


@pytest.mark.parametrize(
    'resolve_command, executable',
    (
        (True, DATE_COMMAND),
        (False, 'date'),
    ),
)
def test_resolve_command(aiida_profile_clean, resolve_command, executable):
    """Test the ``resolve_command`` argument."""
    _, node = launch_shell_job('date', resolve_command=resolve_command)
    assert str(node.inputs.code.filepath_executable) == executable


def test_parser():
    """Test the ``parser`` argument."""

    def parser(dirpath):
        from aiida.orm import Str

        return {'string': Str((dirpath / 'stdout').read_text().strip())}

    value = 'test_string'
    arguments = [value]
    results, node = launch_shell_job('echo', arguments=arguments, parser=parser)

    assert node.is_finished_ok
    assert results['string'] == value


def test_parser_non_stdout():
    """Test the ``parser`` argument when parsing a file that is not retrieved by default.

    If the output file is custom and not retrieved by default, the
    """
    filename = 'results.json'

    def parser(dirpath):
        import json

        from aiida.orm import Dict

        return {'json': Dict(json.load((dirpath / filename).open()))}

    dictionary = {'a': 1}
    results, node = launch_shell_job(
        'cat',
        arguments=['{json}'],
        nodes={'json': SinglefileData.from_string(json.dumps(dictionary))},
        parser=parser,
        metadata={'options': {'output_filename': filename, 'additional_retrieve': [filename]}},
    )

    assert node.is_finished_ok
    assert results['json'] == dictionary


def test_parser_with_parser_argument():
    """Test the ``parser`` argument for callable that specifies optional ``parser`` argument."""

    def parser(dirpath, parser):
        from aiida.orm import Str

        return {'arguments': Str(parser.node.inputs.arguments[0])}

    value = 'test_string'
    arguments = [value]
    results, node = launch_shell_job('echo', arguments=arguments, parser=parser)

    assert node.is_finished_ok
    assert results['arguments'] == value


@pytest.mark.parametrize('scheduler_type', ('core.direct', 'core.sge'))
def test_preexisting_localhost_no_default_mpiprocs_per_machine(
    aiida_profile_clean, aiida_computer, scheduler_type, caplog
):
    """Test that ``prepare_computer`` sets ``default_mpiprocs_per_machine`` if not set on pre-existing computer.

    If the ``localhost`` is created before ``prepare_computer`` is ever called, it is possible that the property
    ``default_mpiprocs_per_machine`` is not set. This would result the ``ShellJob`` validation to fail if the scheduler
    type has a job resource class that is a subclass of :class:`~aiida.schedulers.datastructures.NodeNumberJobResource`.
    """
    computer = aiida_computer(label='localhost', scheduler_type=scheduler_type)

    try:
        computer.set_default_mpiprocs_per_machine(None)
        assert computer.get_default_mpiprocs_per_machine() is None

        prepare_computer()

        warnings = [record for record in caplog.records if record.levelno == logging.WARNING]

        if scheduler_type == 'core.direct':
            assert computer.get_default_mpiprocs_per_machine() == 1
            assert len(warnings) == 1
            assert 'already exist but does not define `default_mpiprocs_per_machine' in warnings[0].message
        else:
            assert computer.get_default_mpiprocs_per_machine() is None
            assert warnings == []
    finally:
        Computer.collection.delete(computer.pk)


@pytest.mark.parametrize('code_type', ('string', 'shell', 'installed', 'portable'))
def test_metadata_computer(code_type, aiida_computer_local, tmp_path):
    """Test that ``metadata.computer`` is respected for different code types."""
    computer = aiida_computer_local(label=f'computer-{code_type}')

    if code_type == 'string':
        command = 'echo'
    elif code_type == 'shell':
        command = ShellCode(
            computer=computer, filepath_executable=ECHO_COMMAND, default_calc_job_plugin='core.shell'
        ).store()
    elif code_type == 'installed':
        command = InstalledCode(computer=computer, filepath_executable=ECHO_COMMAND).store()
    else:
        filepath_executable = tmp_path / 'echo.sh'
        filepath_executable.write_text('#!/bin/bash\necho "$@"\n')
        filepath_executable.chmod(0o755)
        command = PortableCode(filepath_executable='echo.sh', filepath_files=tmp_path).store()

    results, node = launch_shell_job(command, arguments=['hello'], metadata={'computer': computer})
    assert node.is_finished_ok
    assert results['stdout'].get_content().strip() == 'hello'
    assert node.computer.uuid == computer.uuid


def test_monitors():
    """Test the ``monitors`` input."""
    from aiida.orm import Dict

    # Create simple monitor configurations
    dict_one = {'entry_point': 'core.always_kill', 'minimum_poll_interval': 60}
    dict_two = {'entry_point': 'core.always_kill', 'minimum_poll_interval': 120}
    monitors = {
        'monitor_one': Dict(dict_one),
        'monitor_two': Dict(dict_two),
    }

    _, node = launch_shell_job('date', monitors=monitors)
    assert node.is_finished_ok
    assert 'monitors' in node.inputs
    assert 'monitor_one' in node.inputs.monitors
    assert 'monitor_two' in node.inputs.monitors

    assert node.inputs.monitors.monitor_one.get_dict() == dict_one
    assert node.inputs.monitors.monitor_two.get_dict() == dict_two
