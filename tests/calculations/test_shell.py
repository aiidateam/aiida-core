###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for the :mod:`aiida.calculations.shell` module."""

import pathlib
import shlex

import pytest

from aiida.calculations.shell import ShellJob
from aiida.common.datastructures import CodeInfo
from aiida.engine import run_get_node
from aiida.orm import (
    Data,
    EntryPointData,
    Float,
    FolderData,
    Int,
    List,
    Log,
    PickledData,
    RemoteData,
    SinglefileData,
    Str,
)


def custom_parser(dirpath):
    """Implement a custom parser to test the ``parser`` input for a ``ShellJob``."""


def custom_parser_with_parser_argument(dirpath, parser):
    """Implement a custom parser that defines the optional ``parser`` argument."""


def test_code(generate_shell_calc_job, generate_shell_code):
    """Test the ``code`` input."""
    code = generate_shell_code()
    inputs = {'code': code}
    dirpath, calc_info = generate_shell_calc_job('core.shell', inputs)

    assert len(calc_info.codes_info) == 1
    assert isinstance(calc_info.codes_info[0], CodeInfo)
    assert calc_info.codes_info[0].code_uuid == code.uuid
    assert calc_info.codes_info[0].cmdline_params == []
    assert calc_info.codes_info[0].stdout_name == ShellJob.FILENAME_STDOUT
    assert calc_info.retrieve_temporary_list == list(ShellJob.DEFAULT_RETRIEVED_TEMPORARY)
    assert not list(dirpath.iterdir())


def test_nodes_single_file_data(generate_shell_calc_job, generate_shell_code):
    """Test the ``nodes`` input with ``SinglefileData`` nodes ."""
    inputs = {
        'code': generate_shell_code(),
        'nodes': {
            'xa': SinglefileData.from_string('content'),
            'xb': SinglefileData.from_string('content'),
        },
    }
    dirpath, calc_info = generate_shell_calc_job('core.shell', inputs)
    code_info = calc_info.codes_info[0]

    assert code_info.cmdline_params == []
    assert code_info.stdout_name == ShellJob.FILENAME_STDOUT
    assert calc_info.retrieve_temporary_list == list(ShellJob.DEFAULT_RETRIEVED_TEMPORARY)
    assert sorted(calc_info.provenance_exclude_list) == ['xa', 'xb']
    assert sorted([p.name for p in dirpath.iterdir()]) == ['xa', 'xb']


def test_nodes_folder_data(generate_shell_calc_job, generate_shell_code, tmp_path):
    """Test the ``nodes`` input with ``FolderData`` nodes ."""
    (tmp_path / 'file_a.txt').write_text('content a')
    (tmp_path / 'file_b.txt').write_text('content b')

    folder_flat = FolderData(tree=tmp_path.absolute())
    folder_nested = FolderData()
    folder_nested.put_object_from_tree(tmp_path.absolute(), 'dir')
    inputs = {
        'code': generate_shell_code(),
        'arguments': ['{nested}', '{nested_explicit}'],
        'nodes': {
            'flat': folder_flat,
            'nested': folder_nested,
            'flat_explicit': folder_flat,
            'nested_explicit': folder_nested,
        },
        'filenames': {'flat_explicit': 'sub', 'nested_explicit': 'sub'},
    }
    dirpath, calc_info = generate_shell_calc_job('core.shell', inputs)
    code_info = calc_info.codes_info[0]

    assert code_info.cmdline_params == ['nested', 'sub']
    assert code_info.stdout_name == ShellJob.FILENAME_STDOUT
    assert calc_info.retrieve_temporary_list == list(ShellJob.DEFAULT_RETRIEVED_TEMPORARY)
    assert sorted(calc_info.provenance_exclude_list) == ['dir', 'file_a.txt', 'file_b.txt', 'sub']
    assert sorted([p.name for p in dirpath.iterdir()]) == ['dir', 'file_a.txt', 'file_b.txt', 'sub']
    assert sorted([p.name for p in (dirpath / 'dir').iterdir()]) == ['file_a.txt', 'file_b.txt']
    assert sorted([p.name for p in (dirpath / 'sub').iterdir()]) == ['dir', 'file_a.txt', 'file_b.txt']
    assert sorted([p.name for p in (dirpath / 'sub' / 'dir').iterdir()]) == ['file_a.txt', 'file_b.txt']
    assert (dirpath / 'file_a.txt').read_text() == 'content a'
    assert (dirpath / 'file_b.txt').read_text() == 'content b'


@pytest.mark.parametrize('use_symlinks', (True, False))
def test_nodes_remote_data(generate_shell_calc_job, generate_shell_code, tmp_path, aiida_localhost, use_symlinks):
    """Test the ``nodes`` input with ``RemoteData`` nodes."""
    inputs = {
        'code': generate_shell_code(computer_label=aiida_localhost.label),
        'arguments': [],
        'nodes': {
            'remote': RemoteData(remote_path=str(tmp_path.absolute()), computer=aiida_localhost),
        },
        'metadata': {'options': {'use_symlinks': use_symlinks}},
    }
    _, calc_info = generate_shell_calc_job('core.shell', inputs)

    if use_symlinks:
        assert calc_info.remote_copy_list == []
        assert sorted(calc_info.remote_symlink_list) == [(aiida_localhost.uuid, str(tmp_path / '*'), '.')]
    else:
        assert calc_info.remote_symlink_list == []
        assert sorted(calc_info.remote_copy_list) == [(aiida_localhost.uuid, str(tmp_path / '*'), '.')]


def test_nodes_remote_data_filename(generate_shell_calc_job, generate_shell_code, tmp_path, aiida_localhost):
    """Test the ``nodes`` and ``filenames`` inputs with ``RemoteData`` nodes."""
    remote_path_a = tmp_path / 'remote_a'
    remote_path_b = tmp_path / 'remote_b'
    remote_path_a.mkdir()
    remote_path_b.mkdir()
    (remote_path_a / 'file_a.txt').write_text('content a')
    (remote_path_b / 'file_b.txt').write_text('content b')
    remote_data_a = RemoteData(remote_path=str(remote_path_a.absolute()), computer=aiida_localhost)
    remote_data_b = RemoteData(remote_path=str(remote_path_b.absolute()), computer=aiida_localhost)

    inputs = {
        'code': generate_shell_code(computer_label=aiida_localhost.label),
        'arguments': ['{remote_a}'],
        'nodes': {
            'remote_a': remote_data_a,
            'remote_b': remote_data_b,
        },
        'filenames': {'remote_a': 'target_remote'},
    }
    dirpath, calc_info = generate_shell_calc_job('core.shell', inputs)

    code_info = calc_info.codes_info[0]
    assert code_info.cmdline_params == ['target_remote']

    assert calc_info.remote_symlink_list == []
    assert sorted(calc_info.remote_copy_list) == [
        (aiida_localhost.uuid, str(remote_path_a), 'target_remote'),
        (aiida_localhost.uuid, str(remote_path_b / '*'), '.'),
    ]
    assert sorted(p.name for p in dirpath.iterdir()) == []


def test_nodes_base_types(generate_shell_calc_job, generate_shell_code):
    """Test the ``nodes`` input with ``BaseType`` nodes ."""
    inputs = {
        'code': generate_shell_code(),
        'arguments': ['{float}', '{int}', '{str}'],
        'nodes': {
            'float': Float(1.0),
            'int': Int(2),
            'str': Str('string'),
        },
    }
    _, calc_info = generate_shell_calc_job('core.shell', inputs)
    code_info = calc_info.codes_info[0]

    assert code_info.cmdline_params == ['1.0', '2', 'string']
    assert code_info.stdout_name == ShellJob.FILENAME_STDOUT
    assert calc_info.retrieve_temporary_list == list(ShellJob.DEFAULT_RETRIEVED_TEMPORARY)


def test_nodes_single_file_data_filename(generate_shell_calc_job, generate_shell_code):
    """Test the selection rules for the filename used for ``SinglefileData`` nodes.

    The filename is determined in the following order:

     * Explicitly defined in ``filenames``,
     * The ``filename`` property of the ``SinglefileData`` node,
     * The key of the node in the ``nodes`` inputs dictionary.
    """
    inputs = {
        'code': generate_shell_code(),
        'nodes': {
            'xa': SinglefileData.from_string('content', filename='single_file_a'),
            'xb': SinglefileData.from_string('content'),
            'xc': SinglefileData.from_string('content'),
        },
        'filenames': {
            'xb': 'filename_b',
        },
    }
    dirpath, calc_info = generate_shell_calc_job('core.shell', inputs)
    code_info = calc_info.codes_info[0]

    assert code_info.cmdline_params == []
    assert code_info.stdout_name == ShellJob.FILENAME_STDOUT
    assert calc_info.retrieve_temporary_list == list(ShellJob.DEFAULT_RETRIEVED_TEMPORARY)
    assert sorted([p.name for p in dirpath.iterdir()]) == ['filename_b', 'single_file_a', 'xc']


@pytest.mark.parametrize(
    'arguments, exception',
    (
        (['{place}{holder}'], r'argument `.*` is invalid as it contains more than one placeholder.'),
        (['{placeholder}'], r'argument placeholder `.*` not specified in `nodes`.'),
    ),
)
def test_arguments_invalid(generate_shell_calc_job, generate_shell_code, arguments, exception):
    """Test the ``arguments`` input with invalid placeholders."""
    inputs = {
        'arguments': List(arguments),
        'code': generate_shell_code(),
    }
    with pytest.raises(ValueError, match=exception):
        generate_shell_calc_job('core.shell', inputs)


@pytest.mark.parametrize(
    'arguments',
    (
        '-a --flag local/filepath',
        ['-a', '--flag', 'local/filepath'],
    ),
)
def test_arguments(generate_shell_calc_job, generate_shell_code, arguments):
    """Test the ``arguments`` input."""
    inputs = {'code': generate_shell_code(), 'arguments': arguments}
    _, calc_info = generate_shell_calc_job('core.shell', inputs)
    code_info = calc_info.codes_info[0]
    if isinstance(arguments, str):
        assert code_info.cmdline_params == shlex.split(arguments)
    else:
        assert code_info.cmdline_params == arguments


def test_arguments_files(generate_shell_calc_job, generate_shell_code):
    """Test the ``arguments`` with placeholders for inputs."""
    arguments = List(['{file_a}'])
    inputs = {
        'code': generate_shell_code(),
        'arguments': arguments,
        'nodes': {'file_a': SinglefileData.from_string('content')},
    }
    _, calc_info = generate_shell_calc_job('core.shell', inputs)
    code_info = calc_info.codes_info[0]
    assert code_info.cmdline_params == ['file_a']


def test_arguments_files_filenames(generate_shell_calc_job, generate_shell_code):
    """Test the ``arguments`` with placeholders for files and explicit filenames.

    Nested directories should be created automatically.
    """
    arguments = List(['{file_a}'])
    inputs = {
        'code': generate_shell_code(),
        'arguments': arguments,
        'nodes': {
            'file_a': SinglefileData.from_string('content'),
            'file_b': SinglefileData.from_string('content'),
        },
        'filenames': {
            'file_a': 'custom_filename',
            'file_b': 'nested/custom_filename',
        },
    }
    _, calc_info = generate_shell_calc_job('core.shell', inputs)
    code_info = calc_info.codes_info[0]
    assert code_info.cmdline_params == ['custom_filename']


def test_arguments_escaped_braces(generate_shell_calc_job, generate_shell_code):
    """Test the ``arguments`` with arguments containing escaped curly braces."""
    arguments = List(['some{{escaped}}braces'])
    inputs = {
        'code': generate_shell_code(),
        'arguments': arguments,
    }
    _, calc_info = generate_shell_calc_job('core.shell', inputs)
    code_info = calc_info.codes_info[0]
    assert code_info.cmdline_params == ['some{escaped}braces']


def test_output_filename(generate_shell_calc_job, generate_shell_code, file_regression):
    """Test the ``metadata.options.output_filename`` input."""
    output_filename = 'custom_stdout'
    inputs = {
        'code': generate_shell_code('echo'),
        'arguments': 'test',
        'metadata': {'options': {'output_filename': output_filename}},
    }
    _tmp_path, calc_info = generate_shell_calc_job('core.shell', inputs, presubmit=True)
    assert output_filename in calc_info.retrieve_temporary_list


def test_filename_stdin(generate_shell_calc_job, generate_shell_code, file_regression):
    """Test the ``metadata.options.filename_stdin`` input."""
    inputs = {
        # even if 'cat' would be more natural, we use `diff` to avoid issues
        # in this specific test, because the exact path of the `cat` binary
        # may differ across systems (Linux vs. MacOS), while `diff` seems
        # to be (by default) more consistent (in /usr/bin).
        'code': generate_shell_code('diff'),
        'arguments': List(['{filename}']),
        'nodes': {'filename': SinglefileData.from_string('content')},
        'metadata': {'options': {'filename_stdin': 'filename'}},
    }
    tmp_path, calc_info = generate_shell_calc_job('core.shell', inputs, presubmit=True)
    code_info = calc_info.codes_info[0]
    assert code_info.stdin_name == 'filename'

    options = ShellJob.spec_metadata['options']
    filename_submit_script = options['submit_script_filename'].default
    file_regression.check((pathlib.Path(tmp_path) / filename_submit_script).read_text(), encoding='utf-8')


@pytest.mark.parametrize('redirect_stderr', (True, False, None))
def test_redirect_stderr(generate_shell_calc_job, generate_shell_code, redirect_stderr):
    """Test the ``metadata.options.redirect_stderr`` input."""
    inputs = {'code': generate_shell_code('cat'), 'metadata': {'options': {}}}

    if redirect_stderr is not None:
        inputs['metadata']['options']['redirect_stderr'] = redirect_stderr

    _, calc_info = generate_shell_calc_job('core.shell', inputs, presubmit=True)
    code_info = calc_info.codes_info[0]

    if redirect_stderr is True:
        assert code_info.join_files == redirect_stderr
    else:
        assert code_info.stderr_name == ShellJob.FILENAME_STDERR


@pytest.mark.parametrize(
    'outputs, message',
    (
        ([ShellJob.FILENAME_STATUS], r'`.*` is a reserved output filename and cannot be used in `outputs`.'),
        ([ShellJob.FILENAME_STDERR], r'`.*` is a reserved output filename and cannot be used in `outputs`.'),
        ([ShellJob.FILENAME_STDOUT], r'`.*` is a reserved output filename and cannot be used in `outputs`.'),
    ),
)
def test_validate_outputs(generate_shell_calc_job, generate_shell_code, outputs, message):
    """Test the validator for the ``outputs`` argument."""
    with pytest.raises(ValueError, match=message):
        generate_shell_calc_job('core.shell', {'code': generate_shell_code(), 'outputs': outputs})


@pytest.mark.parametrize(
    'node_cls, message',
    (
        (Data, r'.*Unsupported node type for `.*` in `nodes`: .* does not have the `value` property.'),
        (Int, r'.*Casting `value` to `str` for `.*` in `nodes` excepted: .*'),
    ),
)
def test_validate_nodes(generate_shell_calc_job, generate_shell_code, node_cls, message, monkeypatch):
    """Test the validator for the ``nodes`` argument."""
    nodes = {'node': node_cls()}

    if node_cls is Int:

        @property  # type: ignore[misc]
        def value_raises(self):
            """Raise an exception."""
            raise ValueError()

        monkeypatch.setattr(node_cls, 'value', value_raises)

    with pytest.raises(ValueError, match=message):
        generate_shell_calc_job('core.shell', {'code': generate_shell_code(), 'nodes': nodes})


@pytest.mark.parametrize(
    'arguments, message',
    (
        (['string', 1], r'.*all elements of the `arguments` input should be strings'),
        (['string', {input}], r'.*all elements of the `arguments` input should be strings'),
        (['<', '{filename}'], r'`<` cannot be specified in the `arguments`.*'),
        (['{filename}', '>'], r'the symbol `>` cannot be specified in the `arguments`.*'),
    ),
)
def test_validate_arguments(generate_shell_calc_job, generate_shell_code, arguments, message):
    """Test the validator for the ``arguments`` argument."""
    with pytest.raises(ValueError, match=message):
        generate_shell_calc_job('core.shell', {'code': generate_shell_code(), 'arguments': arguments})


def test_build_process_label(generate_shell_calc_job, generate_shell_code):
    """Test the :meth:`~aiida.calculations.shell.ShellJob._build_process_label` method."""
    computer = 'localhost'
    executable = '/bin/echo'
    code = generate_shell_code(executable, computer_label=computer, label='echo')
    process = generate_shell_calc_job('core.shell', {'code': code}, return_process=True)
    assert process._build_process_label() == f'ShellJob<{code.full_label}>'


def test_submit_to_daemon(generate_shell_code, submit_and_await):
    """Test submitting a ``ShellJob`` to the daemon."""
    builder = generate_shell_code('echo').get_builder()
    builder.arguments = ['testing']
    node = submit_and_await(builder)
    assert node.is_finished_ok, node.process_state
    assert node.outputs.stdout.get_content().strip() == 'testing'


def test_parser(generate_shell_calc_job, generate_shell_code):
    """Test the ``parser`` input for valid input."""
    process = generate_shell_calc_job(
        'core.shell', inputs={'code': generate_shell_code(), 'parser': custom_parser}, return_process=True
    )
    assert isinstance(process.inputs.parser, PickledData)


def test_parser_with_parser_argument(generate_shell_calc_job, generate_shell_code):
    """Test the ``parser`` input for valid input."""
    process = generate_shell_calc_job(
        'core.shell',
        inputs={'code': generate_shell_code(), 'parser': custom_parser_with_parser_argument},
        return_process=True,
    )
    assert isinstance(process.inputs.parser, PickledData)


def test_parser_entry_point(generate_shell_calc_job, generate_shell_code, entry_points):
    """Test the ``parser`` serialization and validation when input is an entry point."""
    entry_point_name = 'aiida.parsers:shell.parser'
    entry_points.add(custom_parser, entry_point_name)

    process = generate_shell_calc_job(
        'core.shell', inputs={'code': generate_shell_code(), 'parser': entry_point_name}, return_process=True
    )
    assert isinstance(process.inputs.parser, EntryPointData)


def test_parser_invalid_not_callable(generate_shell_calc_job, generate_shell_code):
    """Test the ``parser`` validation when input is not callable."""
    with pytest.raises(ValueError, match=r'The `parser` is not a callable function: .* is not a callable object'):
        generate_shell_calc_job(
            'core.shell', inputs={'code': generate_shell_code(), 'parser': PickledData('not-callable')}
        )


def test_parser_invalid_signature(generate_shell_calc_job, generate_shell_code):
    """Test the ``parser`` validation when the callable has an invalid signature."""
    with pytest.raises(ValueError, match=r'The `parser` has an invalid function signature, it should be:.*'):
        generate_shell_calc_job('core.shell', inputs={'code': generate_shell_code(), 'parser': lambda x: x})


def test_parser_over_daemon(generate_shell_code, submit_and_await):
    """Test submitting a ``ShellJob`` with a custom parser over the daemon."""
    value = 'testing'

    def parser(dirpath):
        from aiida.orm import Str

        return {'string': Str((dirpath / 'stdout').read_text().strip())}

    builder = generate_shell_code('/bin/echo').get_builder()
    builder.arguments = [value]
    builder.parser = parser

    node = submit_and_await(builder)
    assert node.is_finished_ok, (node.exit_status, node.exit_message)
    assert node.outputs.string == value


def test_input_output_filename_overlap(generate_shell_calc_job, generate_shell_code, tmp_path):
    """Test functionality when input and output filenames overlap."""
    code = generate_shell_code()

    # If an overlapping name is explicitly defined in the ``filenames`` input, then an exception is raised.
    with pytest.raises(ValueError, match=r'Input filename .* for node `file` overlaps .*'):
        generate_shell_calc_job(
            'core.shell',
            inputs={
                'code': code,
                'nodes': {'file': SinglefileData.from_string('content', filename='stdout')},
                'filenames': {'file': 'stdout'},
            },
        )

    # Same goes for ``FolderData`` nodes.
    with pytest.raises(ValueError, match=r'Input filename .* for node `folder` overlaps .*'):
        generate_shell_calc_job(
            'core.shell',
            inputs={
                'code': code,
                'nodes': {'folder': FolderData()},
                'filenames': {'folder': 'stdout'},
            },
        )

    # If the filename clash is due to an "implicit" filename, instead of raising, the filename of the node should be
    # automatically made unique and a warning logged to make the user aware.
    def generate_inputs():
        return {
            'code': code,
            'nodes': {'file': SinglefileData.from_string('content', filename='stdout')},
        }

    dirpath, calc_info = generate_shell_calc_job('core.shell', inputs=generate_inputs())
    process = generate_shell_calc_job('core.shell', inputs=generate_inputs(), return_process=True)

    code_info = calc_info.codes_info[0]
    filenames = [p.name for p in dirpath.iterdir()]
    assert code_info.stdout_name not in filenames
    assert code_info.stderr_name not in filenames

    message = 'filename `stdout` for node `file` overlaps'
    assert any(message in entry.message for entry in Log.collection.get_logs_for(process.node))

    # If the contents of a ``FolderData`` overlap with a reserved filename, an exception is raised. This is done because
    # not doing everything will most likely fail the calculation as some input files will be overwritten. The plugin can
    # also not automatically solve the problem by renaming the overlapping file/directory, as is done in the case of the
    # ``SinglefileData``, because it is not the plugin copying the content of the ``FolderData`` but the engine.
    (tmp_path / 'stdout').mkdir()
    folder_data = FolderData(tree=tmp_path)
    with pytest.raises(RuntimeError, match=r'node `.*` contains the file .* which overlaps with a reserved .*'):
        dirpath, calc_info = generate_shell_calc_job(
            'core.shell',
            inputs={
                'code': code,
                'nodes': {'folder': folder_data},
            },
        )


def test_remote_folder_copying_order(generate_shell_code, aiida_localhost, tmp_path):
    """Test that files in ``RemoteData`` input nodes do not overwrite files written by the ``ShellJob`` itself."""
    filename_submit_script = ShellJob.spec().inputs['metadata']['options']['submit_script_filename'].default

    # Create a ``RemoteData`` node containing a file with the default submit script name. The content is ``SENTINEL``
    # so that it can be easily detected in the final assert of this test.
    dirpath = tmp_path / 'remote'
    dirpath.mkdir()
    (dirpath / filename_submit_script).write_text('SENTINEL')

    inputs = {
        'code': generate_shell_code(),
        'arguments': [],
        'nodes': {
            'remote': RemoteData(remote_path=str(dirpath.absolute()), computer=aiida_localhost),
        },
    }
    _, node = run_get_node(ShellJob, inputs)

    # Now retrieve the content of the submit script that was written to the working directory. It should not be equal
    # to the content of the submit script in the ``remote`` input node which would mean it overwrote the submit script
    # of the shell job itself.
    filepath_submit_script = dirpath / 'output'
    node.outputs.remote_folder.getfile(filename_submit_script, str(filepath_submit_script))
    assert filepath_submit_script.read_text() != 'SENTINEL'
