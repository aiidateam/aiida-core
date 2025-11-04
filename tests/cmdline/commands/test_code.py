###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for the 'verdi code' command."""

import io
import os
import pathlib
import tempfile
import textwrap
import uuid

import click
import pytest

from aiida.cmdline.commands import cmd_code
from aiida.cmdline.params.options.commands.code import validate_label_uniqueness
from aiida.common.exceptions import MultipleObjectsError, NotExistent
from aiida.orm import Code, Computer, InstalledCode, PortableCode, QueryBuilder, load_code
from aiida.plugins import DataFactory


@pytest.fixture
def code(aiida_localhost):
    """Return a ``Code`` instance."""
    code = InstalledCode(
        default_calc_job_plugin='core.arithmetic.add',
        computer=aiida_localhost,
        filepath_executable='/remote/abs/path',
    )
    code.label = 'code'
    code.description = 'desc'
    code.prepend_text = 'text to prepend'
    code.append_text = 'text to append'
    code.store()

    return code


def test_help(run_cli_command):
    """Test the help message."""
    run_cli_command(cmd_code.setup_code, ['--help'])


def test_code_setup_deprecation(run_cli_command):
    """Checks if a deprecation warning is printed in stdout and stderr."""
    # Checks if the deprecation warning is present when invoking the help page
    result = run_cli_command(cmd_code.setup_code, ['--help'])
    assert 'Deprecated:' in result.output
    assert 'Deprecated:' in result.stderr

    # Checks if the deprecation warning is present when invoking the command
    # Runs setup in interactive mode and sends Ctrl+D (\x04) as input so we exit the prompts.
    # This way we can check if the deprecated message was printed with the first prompt.
    result = run_cli_command(cmd_code.setup_code, user_input='\x04', use_subprocess=True, raises=True)
    assert 'Deprecated:' in result.output
    assert 'Deprecated:' in result.stderr


@pytest.mark.usefixtures('aiida_profile_clean')
def test_code_list_no_codes_error_message(run_cli_command):
    """Test ``verdi code list`` when no codes exist."""
    result = run_cli_command(cmd_code.code_list)
    assert 'No codes found matching the specified criteria.' in result.output


def test_code_list(run_cli_command, code):
    """Test ``verdi code list``."""
    code2 = InstalledCode(
        default_calc_job_plugin='core.templatereplacer',
        computer=code.computer,
        filepath_executable='/remote/abs/path',
    )
    code2.label = 'code2'
    code2.store()

    options = ['-A', '-a', '-o', '-d', 'core.arithmetic.add', f'--computer={code.computer.label}']
    result = run_cli_command(cmd_code.code_list, options)
    assert str(code.pk) in result.output
    assert code2.label not in result.output
    assert code.computer.label in result.output
    assert 'No codes found matching the specified criteria.' not in result.output


@pytest.mark.usefixtures('aiida_profile_clean')
def test_code_list_hide(run_cli_command, code):
    """Test that hidden codes are shown (or not) properly."""
    code.is_hidden = True
    options = ['-A']
    result = run_cli_command(cmd_code.code_list, options)
    assert code.full_label not in result.output

    options = ['-a']
    result = run_cli_command(cmd_code.code_list, options)
    assert code.full_label in result.output


@pytest.mark.usefixtures('aiida_profile')
def test_code_list_raw(run_cli_command, code):
    """Test ``verdi code list --raw``."""
    options = ['--raw']
    result = run_cli_command(cmd_code.code_list, options)
    assert str(code.pk) in result.output
    assert 'Full label' not in result.output
    assert 'Use `verdi code show IDENTIFIER`' not in result.output


@pytest.mark.usefixtures('aiida_profile')
def test_hide_one(run_cli_command, code):
    """Test ``verdi code hide``."""
    run_cli_command(cmd_code.hide, [str(code.pk)])
    assert code.is_hidden


def test_reveal_one(run_cli_command, code):
    """Test ``verdi code reveal``."""
    run_cli_command(cmd_code.reveal, [str(code.pk)])
    assert not code.is_hidden


def test_relabel_code(run_cli_command, code):
    """Test ``verdi code relabel``."""
    run_cli_command(cmd_code.relabel, [str(code.pk), 'new_code'])
    assert load_code(code.pk).label == 'new_code'


def test_relabel_code_full_bad(run_cli_command, code):
    """Test ``verdi code relabel`` with an incorrect full code label."""
    run_cli_command(cmd_code.relabel, [str(code.pk), 'new_code@otherstuff'], raises=True)


@pytest.mark.usefixtures('aiida_profile_clean')
def test_code_delete_one_force(run_cli_command, code):
    """Test force code deletion."""
    run_cli_command(cmd_code.delete, [str(code.pk), '--force'], use_subprocess=True)

    with pytest.raises(NotExistent):
        load_code('code')


def _normalize_code_show_output(output, code_pk, code_uuid, computer_pk, hostname) -> str:
    """Normalize dynamic values in CLI output for stable regression testing.

    Args:
        output: The raw CLI output string
        code_pk: The actual PK to be replaced with placeholder
        code_uuid: The actual UUID to be replaced with placeholder
        computer_pk: Optional computer PK to be replaced with placeholder
        hostname: Optional hostname to be replaced with placeholder

    Returns:
        Normalized output string with placeholders
    """
    import re

    # Remove the first and last lines (separator lines with hyphens)
    lines = output.strip().split('\n')
    if lines and lines[0].strip().startswith('-'):
        lines = lines[1:]
    if lines and lines[-1].strip().startswith('-'):
        lines = lines[:-1]

    normalized = '\n'.join(lines)

    # Replace UUID first (before PK, as PK digits might appear in UUID)
    normalized = normalized.replace(code_uuid, '<UUID>')

    # Replace hostname if provided
    if hostname:
        normalized = normalized.replace(hostname, '<hostname>')

    # Replace computer PK if provided
    if computer_pk is not None:
        normalized = normalized.replace(f'pk: {computer_pk}', 'pk: <COMPUTER_PK>')

    # Replace code PK (as whole word to avoid replacing parts of other numbers)
    normalized = re.sub(rf'\b{code_pk}\b', '<PK>', normalized)

    return normalized


@pytest.mark.usefixtures('aiida_profile_clean')  # Clean profile for this test to ensure number of digits for PKs
@pytest.mark.parametrize(
    'code_type',
    ['installed', 'portable', 'containerized'],
)
def test_code_show(run_cli_command, aiida_localhost, tmp_path, bash_path, aiida_code, code_type, file_regression):
    """Test ``verdi code show`` for different code types."""
    # Create code based on type
    if code_type == 'installed':
        code = aiida_code(
            f'core.code.{code_type}',
            label='test_installed_code',
            description='Test installed code',
            default_calc_job_plugin='core.arithmetic.add',
            computer=aiida_localhost,
            filepath_executable='/remote/abs/path',
            prepend_text='text to prepend',
            append_text='text to append',
        )
        computer = aiida_localhost
    elif code_type == 'portable':
        filepath_executable = 'bash'
        (tmp_path / filepath_executable).touch()
        code = aiida_code(
            f'core.code.{code_type}',
            label='test_portable_code',
            description='Test portable code',
            default_calc_job_plugin='core.arithmetic.add',
            filepath_executable=filepath_executable,
            filepath_files=tmp_path,
            prepend_text='text to prepend',
            append_text='text to append',
        )
        computer = None
    elif code_type == 'containerized':
        code = aiida_code(
            f'core.code.{code_type}',
            label='test_containerized_code',
            description='Test containerized code',
            default_calc_job_plugin='core.arithmetic.add',
            computer=aiida_localhost,
            filepath_executable=str(bash_path.absolute()),
            engine_command='singularity exec --bind $PWD:$PWD {image_name}',
            image_name='ubuntu',
            prepend_text='text to prepend',
            append_text='text to append',
        )
        computer = aiida_localhost

    result = run_cli_command(cmd_code.show, [str(code.pk)])

    # Normalize dynamic values for regression testing
    normalized_output = _normalize_code_show_output(
        result.output,
        code_pk=code.pk,
        code_uuid=code.uuid,
        computer_pk=computer.pk if computer else None,
        hostname=computer.hostname if computer else None,
    )

    # Check against regression fixture
    file_regression.check(normalized_output, basename=f'test_code_show_{code_type}', extension='.txt')


@pytest.mark.parametrize('non_interactive_editor', ('vim -cwq',), indirect=True)
def test_code_duplicate_non_interactive(run_cli_command, code, non_interactive_editor):
    """Test code duplication non-interactive."""
    label = 'code_duplicate_noninteractive'
    run_cli_command(cmd_code.code_duplicate, ['--non-interactive', f'--label={label}', str(code.pk)])

    duplicate = load_code(label)
    assert code.description == duplicate.description
    assert code.prepend_text == duplicate.prepend_text
    assert code.append_text == duplicate.append_text
    assert code.default_calc_job_plugin == duplicate.default_calc_job_plugin


@pytest.mark.parametrize('non_interactive_editor', ('vim -cwq',), indirect=True)
def test_noninteractive_remote(run_cli_command, aiida_localhost, non_interactive_editor):
    """Test non-interactive remote code setup."""
    label = 'noninteractive_remote'
    options = [
        '--non-interactive',
        f'--label={label}',
        '--description=description',
        '--input-plugin=core.arithmetic.add',
        '--on-computer',
        f'--computer={aiida_localhost.label}',
        '--remote-abs-path=/remote/abs/path',
    ]
    run_cli_command(cmd_code.setup_code, options)
    assert isinstance(load_code(label), InstalledCode)


@pytest.mark.parametrize('non_interactive_editor', ('vim -cwq',), indirect=True)
def test_noninteractive_upload(run_cli_command, non_interactive_editor):
    """Test non-interactive code setup."""
    label = 'noninteractive_upload'
    options = [
        '--non-interactive',
        f'--label={label}',
        '--description=description',
        '--input-plugin=core.arithmetic.add',
        '--store-in-db',
        f'--code-folder={os.path.dirname(__file__)}',
        f'--code-rel-path={os.path.basename(__file__)}',
    ]
    run_cli_command(cmd_code.setup_code, options)
    assert isinstance(load_code(label), PortableCode)


@pytest.mark.parametrize('non_interactive_editor', ('vim -cwq',), indirect=True)
def test_interactive_remote(run_cli_command, aiida_localhost, non_interactive_editor):
    """Test interactive remote code setup."""
    label = 'interactive_remote'
    user_input = '\n'.join(['yes', aiida_localhost.label, label, 'desc', 'core.arithmetic.add', '/remote/path', 'y'])  # noqa: FLY002
    run_cli_command(cmd_code.setup_code, user_input=user_input)
    assert isinstance(load_code(label), InstalledCode)


@pytest.mark.parametrize('non_interactive_editor', ('vim -cwq',), indirect=True)
def test_interactive_upload(run_cli_command, non_interactive_editor):
    """Test interactive code setup."""
    label = 'interactive_upload'
    dirname = os.path.dirname(__file__)
    basename = os.path.basename(__file__)
    user_input = '\n'.join(['no', label, 'description', 'core.arithmetic.add', dirname, basename, 'y'])  # noqa: FLY002
    run_cli_command(cmd_code.setup_code, user_input=user_input)
    assert isinstance(load_code(label), PortableCode)


@pytest.mark.parametrize('non_interactive_editor', ('vim -cwq',), indirect=True)
def test_mixed(run_cli_command, aiida_localhost, non_interactive_editor):
    """Test mixed (interactive/from config) code setup."""
    label = 'mixed_remote'
    options = ['--description=description', '--on-computer', '--remote-abs-path=/remote/path']
    user_input = '\n'.join([aiida_localhost.label, label, 'core.arithmetic.add', 'y'])  # noqa: FLY002
    run_cli_command(cmd_code.setup_code, options, user_input=user_input)
    assert isinstance(load_code(label), InstalledCode)


@pytest.mark.parametrize('non_interactive_editor', ('vim -cwq',), indirect=True)
def test_code_duplicate_interactive(run_cli_command, aiida_code_installed, non_interactive_editor):
    """Test code duplication interactive."""
    label = 'code_duplicate_interactive'
    user_input = f'\n\n{label}\n\n\n\n'
    code = aiida_code_installed(
        default_calc_job_plugin='core.arithmetic.add', filepath_executable='/bin/cat', description='code'
    )
    run_cli_command(cmd_code.code_duplicate, [str(code.pk)], user_input=user_input)

    duplicate = load_code(label)
    assert code.description == duplicate.description
    assert code.prepend_text == duplicate.prepend_text
    assert code.append_text == duplicate.append_text


@pytest.mark.usefixtures('aiida_profile_clean')
@pytest.mark.parametrize('non_interactive_editor', ('vim -cwq',), indirect=True)
def test_code_duplicate_ignore(run_cli_command, aiida_code_installed, non_interactive_editor):
    """Providing "!" to description should lead to empty description.

    Regression test for: https://github.com/aiidateam/aiida-core/issues/3770
    """
    label = 'code_duplicate_interactive'
    user_input = f'\n\n{label}\n!\n\n\n'
    code = aiida_code_installed(
        default_calc_job_plugin='core.arithmetic.add', filepath_executable='/bin/cat', label='code'
    )
    run_cli_command(cmd_code.code_duplicate, [str(code.pk)], user_input=user_input)

    duplicate = load_code(label)
    assert duplicate.description == ''


@pytest.mark.usefixtures('aiida_profile_clean')
@pytest.mark.parametrize('sort_option', ('--sort', '--no-sort'))
def test_code_export(run_cli_command, aiida_code_installed, tmp_path, file_regression, sort_option):
    """Test export the code setup to str."""
    prepend_text = 'module load something\n    some command'
    code = aiida_code_installed(
        default_calc_job_plugin='core.arithmetic.add',
        filepath_executable='/bin/cat',
        label='code',
        prepend_text=prepend_text,
    )
    filepath = tmp_path / 'code.yml'

    options = [str(code.pk), str(filepath), sort_option]
    result = run_cli_command(cmd_code.export, options)
    assert str(filepath) in result.output, 'Filename should be in terminal output but was not found.'
    # file regression check
    content = filepath.read_text()
    file_regression.check(content, extension='.yml')

    # round trip test by create code from the config file
    # we pass the new label to override since cannot have two code with same labels
    new_label = 'code0'
    run_cli_command(
        cmd_code.code_create, ['core.code.installed', '--non-interactive', '--config', filepath, '--label', new_label]
    )
    new_code = load_code(new_label)
    assert code.base.attributes.all == new_code.base.attributes.all
    assert isinstance(new_code, InstalledCode)


@pytest.mark.usefixtures('aiida_profile_clean')
def test_code_export_overwrite(run_cli_command, aiida_code_installed, tmp_path):
    prepend_text = 'module load something\n    some command'
    code = aiida_code_installed(
        default_calc_job_plugin='core.arithmetic.add',
        filepath_executable='/bin/cat',
        label='code',
        prepend_text=prepend_text,
    )
    filepath = tmp_path / 'code.yml'

    options = [str(code.pk), str(filepath)]

    # Create directory with the same name and check that command fails
    filepath.mkdir()
    result = run_cli_command(cmd_code.export, options, raises=True)
    assert f'A directory with the name `{filepath}` already exists' in result.output
    filepath.rmdir()

    # Export fails if file already exists and overwrite set to False
    filepath.touch()
    result = run_cli_command(cmd_code.export, options, raises=True)
    assert f'File `{filepath}` already exists' in result.output

    # Check that overwrite actually overwrites the exported Code config with the new data
    code_echo = aiida_code_installed(
        default_calc_job_plugin='core.arithmetic.add',
        filepath_executable='/bin/echo',
        # Need to set different label, therefore manually specify the same output filename
        label='code_echo',
        prepend_text=prepend_text,
    )

    options = [str(code_echo.pk), str(filepath), '--overwrite']
    run_cli_command(cmd_code.export, options)

    content = filepath.read_text()
    assert '/bin/echo' in content


@pytest.mark.usefixtures('aiida_profile_clean')
@pytest.mark.usefixtures('chdir_tmp_path')
def test_code_export_default_filename(run_cli_command, aiida_code_installed):
    """Test default filename being created if no argument passed."""

    prepend_text = 'module load something\n    some command'
    code = aiida_code_installed(
        default_calc_job_plugin='core.arithmetic.add',
        filepath_executable='/bin/cat',
        label='code',
        prepend_text=prepend_text,
    )

    options = [str(code.pk)]
    run_cli_command(cmd_code.export, options)

    assert pathlib.Path('code@localhost.yaml').is_file()


@pytest.mark.parametrize('non_interactive_editor', ('vim -cwq',), indirect=True)
def test_from_config_local_file(non_interactive_editor, run_cli_command, aiida_localhost):
    """Test setting up a code from a config file on disk."""
    config_file_template = textwrap.dedent(
        """
        label: {label}
        computer: {computer}
        input_plugin: core.arithmetic.add
        remote_abs_path: /remote/abs/path
        """
    )

    label = 'noninteractive_config'
    with tempfile.NamedTemporaryFile('w') as handle:
        handle.write(config_file_template.format(label=label, computer=aiida_localhost.label))
        handle.flush()
        run_cli_command(cmd_code.setup_code, ['--non-interactive', '--config', os.path.realpath(handle.name)])
        assert isinstance(load_code(label), InstalledCode)


@pytest.mark.parametrize('non_interactive_editor', ('vim -cwq',), indirect=True)
def test_from_config_url(non_interactive_editor, run_cli_command, aiida_localhost, monkeypatch):
    """Test setting up a code from a config file from URL."""
    from urllib import request

    monkeypatch.setattr(
        request,
        'urlopen',
        lambda *args, **kwargs: config_file_template.format(label=label, computer=aiida_localhost.label),
    )

    config_file_template = textwrap.dedent(
        """
        label: {label}
        computer: {computer}
        input_plugin: core.arithmetic.add
        remote_abs_path: /remote/abs/path
        """
    )

    label = 'noninteractive_config_url'
    fake_url = 'https://my.url.com'
    run_cli_command(cmd_code.setup_code, ['--non-interactive', '--config', fake_url], use_subprocess=False)
    assert isinstance(load_code(label), InstalledCode)


@pytest.mark.parametrize('non_interactive_editor', ('sleep 1; vim -cwq',), indirect=True)
def test_code_setup_remote_duplicate_full_label_interactive(
    run_cli_command, aiida_code_installed, aiida_localhost, non_interactive_editor
):
    """Test ``verdi code setup`` for a remote code in interactive mode specifying an existing full label."""
    label = 'some-label'
    aiida_code_installed(
        default_calc_job_plugin='core.arithmetic.add',
        filepath_executable='/bin/cat',
        computer=aiida_localhost,
        label=label,
    )
    assert isinstance(load_code(label), InstalledCode)

    label_unique = 'label-unique'
    user_input = '\n'.join(  # noqa: FLY002
        ['yes', aiida_localhost.label, label, label_unique, 'd', 'core.arithmetic.add', '/bin/bash', 'y']
    )
    run_cli_command(cmd_code.setup_code, user_input=user_input)
    assert isinstance(load_code(label_unique), InstalledCode)


@pytest.mark.parametrize('label_first', (True, False))
def test_code_setup_remote_duplicate_full_label_non_interactive(
    run_cli_command, aiida_code_installed, aiida_localhost, label_first
):
    """Test ``verdi code setup`` for a remote code in non-interactive mode specifying an existing full label."""
    label = f'some-label-{label_first}'
    aiida_code_installed(
        default_calc_job_plugin='core.arithmetic.add',
        filepath_executable='/bin/cat',
        computer=aiida_localhost,
        label=label,
    )
    assert isinstance(load_code(label), InstalledCode)

    options = ['-n', '-D', 'd', '-P', 'core.arithmetic.add', '--on-computer', '--remote-abs-path=/remote/abs/path']

    if label_first:
        options.extend(['--label', label, '--computer', aiida_localhost.label])
    else:
        options.extend(['--computer', aiida_localhost.label, '--label', label])

    result = run_cli_command(cmd_code.setup_code, options, raises=True)
    assert f'the code `{label}@{aiida_localhost.label}` already exists.' in result.output


@pytest.mark.usefixtures('aiida_profile_clean')
@pytest.mark.parametrize('non_interactive_editor', ('sleep 1; vim -cwq',), indirect=True)
def test_code_setup_local_duplicate_full_label_interactive(run_cli_command, non_interactive_editor, tmp_path):
    """Test ``verdi code setup`` for a local code in interactive mode specifying an existing full label."""
    filepath = tmp_path / 'bash'
    filepath.write_text('fake bash')

    label = 'some-label'
    code = PortableCode(filepath_executable='bash', filepath_files=tmp_path)
    code.label = label
    code.store()
    assert isinstance(load_code(label), PortableCode)

    label_unique = 'label-unique'
    user_input = '\n'.join(['no', label, label_unique, 'd', 'core.arithmetic.add', str(tmp_path), filepath.name, 'y'])
    run_cli_command(cmd_code.setup_code, user_input=user_input)
    assert isinstance(load_code(label_unique), PortableCode)


@pytest.mark.usefixtures('aiida_profile_clean')
def test_code_setup_local_duplicate_full_label_non_interactive(run_cli_command, tmp_path):
    """Test ``verdi code setup`` for a local code in non-interactive mode specifying an existing full label."""
    label = 'some-label'
    tmp_bin_dir = tmp_path / 'bin'
    tmp_bin_dir.mkdir()
    (tmp_bin_dir / 'bash').touch()
    code = PortableCode(filepath_executable='bash', filepath_files=tmp_bin_dir)
    code.label = label
    code.base.repository.put_object_from_filelike(io.BytesIO(b''), 'bash')
    code.store()
    assert isinstance(load_code(label), PortableCode)

    options = [
        '-n',
        '-D',
        'd',
        '-P',
        'core.arithmetic.add',
        '--store-in-db',
        f'--code-folder={tmp_bin_dir}',
        '--code-rel-path=bash',
        '--label',
        label,
    ]

    result = run_cli_command(cmd_code.setup_code, options, raises=True)
    assert f'the code `{label}` already exists.' in result.output


def test_validate_label_uniqueness(monkeypatch, aiida_localhost):
    """Test the ``validate_label_uniqueness`` validator."""
    from aiida import orm

    def load_code(*args, **kwargs):
        raise MultipleObjectsError()

    monkeypatch.setattr(orm, 'load_code', load_code)

    ctx = click.Context(cmd_code.setup_code)
    ctx.params = {'on_computer': False}

    with pytest.raises(click.BadParameter, match=r'multiple copies of the remote code `.*` already exist.'):
        validate_label_uniqueness(ctx, None, 'some-code')

    ctx = click.Context(cmd_code.setup_code)
    ctx.params = {'on_computer': None, 'computer': aiida_localhost}

    with pytest.raises(click.BadParameter, match=r'multiple copies of the local code `.*` already exist.'):
        validate_label_uniqueness(ctx, None, 'some-code')


def test_code_test(run_cli_command):
    """Test the ``verdi code test`` command."""
    computer = Computer(
        label='test-code-computer', transport_type='core.local', hostname='localhost', scheduler_type='core.slurm'
    ).store()
    code = InstalledCode(computer=computer, filepath_executable='/bin/invalid').store()

    result = run_cli_command(cmd_code.code_test, [str(code.pk)], raises=True)
    assert 'Could not connect to the configured computer' in result.output

    computer.configure()

    result = run_cli_command(cmd_code.code_test, [str(code.pk)], raises=True)
    assert 'The provided remote absolute path `/bin/invalid` does not exist' in result.output

    code = InstalledCode(computer=computer, filepath_executable='/bin/bash').store()
    result = run_cli_command(cmd_code.code_test, [str(code.pk)])
    assert 'all tests succeeded.' in result.output


@pytest.fixture
def command_options(request, aiida_localhost, tmp_path, bash_path):
    """Return tuple of list of options and entry point."""
    options = [request.param, '-n', '--label', str(uuid.uuid4())]

    if 'installed' in request.param:
        options.extend(['--computer', str(aiida_localhost.pk), '--filepath-executable', '/usr/bin/bash'])

    if 'portable' in request.param:
        filepath_executable = 'bash'
        (tmp_path / filepath_executable).touch()
        options.extend(['--filepath-executable', filepath_executable, '--filepath-files', tmp_path])

    if 'containerized' in request.param:
        engine_command = 'singularity exec --bind $PWD:$PWD {image_name}'
        image_name = 'ubuntu'
        options.extend(
            [
                '--computer',
                str(aiida_localhost.pk),
                '--filepath-executable',
                str(bash_path.absolute()),
                '--engine-command',
                engine_command,
                '--image-name',
                image_name,
            ]
        )

    return options, request.param


@pytest.mark.usefixtures('aiida_profile_clean')
@pytest.mark.parametrize(
    'command_options',
    (
        'core.code.installed',
        'core.code.portable',
        'core.code.containerized',
    ),
    indirect=True,
)
@pytest.mark.parametrize('non_interactive_editor', ('sleep 1; vim -cwq',), indirect=True)
def test_code_create(run_cli_command, command_options, non_interactive_editor):
    """Test the ``verdi code create`` command."""
    options, entry_point = command_options
    cls = DataFactory(entry_point)
    result = run_cli_command(cmd_code.code_create, options)
    assert f'Success: Created {cls.__name__}' in result.output
    code = QueryBuilder().append(Code).one()[0]
    assert code.entry_point.name == entry_point
