###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Unit tests for the :class:`aiida.cmdline.params.options.config.ConfigOption`."""

import functools
import io
import textwrap

import click
import pytest

from aiida.cmdline.params.options import CONFIG_FILE, NON_INTERACTIVE, TEMPLATE_VARS
from aiida.cmdline.params.options.config import configuration_callback, yaml_config_file_provider

TEMPLATED_CONFIG = textwrap.dedent(
    """\
    label: '{{ label }}'
    hostname: localhost
    metadata:
        template_variables:
            label:
                key_display: Computer Label
                description: A short name
                default: default-label
    """
)


@pytest.fixture
def run_cli_command(run_cli_command):
    """Override the ``run_cli_command`` fixture to always run with ``use_subprocess=False`` for tests in this module."""
    return functools.partial(run_cli_command, use_subprocess=False)


@click.command()
@click.option('--integer', type=int)
@click.option('--boolean', type=bool)
@CONFIG_FILE()
def cmd(integer, boolean):
    """Test command for :class:`aiida.cmdline.params.options.config.ConfigOption`."""
    click.echo(f'Integer: {integer}')
    click.echo(f'Boolean: {boolean}')


@click.command()
@click.option('--label', type=str)
@click.option('--hostname', type=str)
@TEMPLATE_VARS()
@CONFIG_FILE()
def cmd_with_template(label, hostname):
    """Test command with a template-aware config file and deliberately no ``--non-interactive``.

    Declaring ``CONFIG_FILE`` without ``NON_INTERACTIVE`` is allowed, so the provider has to cope with the option
    being absent entirely; ``cmd_non_interactive`` covers the case where it is present.
    """
    click.echo(f'Label: {label}')
    click.echo(f'Hostname: {hostname}')


@click.command()
@click.option('--label', type=str)
@click.option('--hostname', type=str)
@NON_INTERACTIVE()
@TEMPLATE_VARS()
@CONFIG_FILE()
def cmd_non_interactive(label, hostname, non_interactive):
    """Test command combining ``--non-interactive`` with template-aware config files."""
    click.echo(f'Label: {label}')
    click.echo(f'Hostname: {hostname}')


@pytest.mark.parametrize(
    'contents, error',
    [
        ('unknown: 1', click.BadParameter),
        ('invalid: [', click.BadOptionUsage),
    ],
)
def test_config_handle_closed_on_callback_error(contents, error, tmp_path):
    """Release the Click-owned config handle when reading or validating it fails."""
    path = tmp_path / 'config.yml'
    path.write_text(contents)
    context = click.Context(cmd)
    param = next(param for param in cmd.params if param.name == 'config')
    handle = param.type.convert(str(path), param, context)

    with pytest.raises(error):
        configuration_callback(
            None, '--config', 'config', None, yaml_config_file_provider, False, context, param, handle
        )

    assert handle.closed


def test_config_url_closed_on_callback_error(monkeypatch):
    """Register URL responses for the same Click context cleanup as local files."""
    response = io.BytesIO(b'unknown: 1')
    monkeypatch.setattr('aiida.cmdline.params.types.path.convert_possible_url', lambda value, timeout: response)
    context = click.Context(cmd)
    param = next(param for param in cmd.params if param.name == 'config')
    handle = param.type.convert('https://example.invalid/config.yml', param, context)

    with pytest.raises(click.BadParameter):
        configuration_callback(
            None, '--config', 'config', None, yaml_config_file_provider, False, context, param, handle
        )

    assert response.closed


def test_template_abort_closes_handle(tmp_path, monkeypatch):
    """An aborted template prompt still releases the Click-owned config handle.

    ``click.Abort`` bypasses the ``BadOptionUsage`` wrap so the user sees ``Aborted!``, but the base
    ``ExitStack`` cleanup must still close the handle.
    """
    from aiida.cmdline.params.options.config import _template_aware_yaml_provider

    path = tmp_path / 'config.yml'
    path.write_text("label: '{{ label }}'\n")
    context = click.Context(cmd_with_template)
    param = next(param for param in cmd_with_template.params if param.name == 'config')
    handle = param.type.convert(str(path), param, context)
    monkeypatch.setattr(click, 'prompt', lambda *args, **kwargs: (_ for _ in ()).throw(click.Abort()))

    with pytest.raises(click.Abort):
        configuration_callback(
            None, '--config', 'config', None, _template_aware_yaml_provider, False, context, param, handle
        )

    assert handle.closed


def test_config_handle_left_open_for_saved_callback(tmp_path):
    """Click still owns the handle after a successful config callback."""
    path = tmp_path / 'config.yml'
    path.write_text('integer: 1')
    context = click.Context(cmd)
    param = next(param for param in cmd.params if param.name == 'config')
    handle = param.type.convert(str(path), param, context)

    def saved_callback(ctx, option, value):
        assert not value.closed
        return value

    result = configuration_callback(
        None, '--config', 'config', saved_callback, yaml_config_file_provider, False, context, param, handle
    )
    assert result is handle
    assert not handle.closed
    context.close()
    assert handle.closed


def test_valid(run_cli_command, tmp_path):
    """Test the option for a valid configuration file."""
    filepath = tmp_path / 'config.yml'
    filepath.write_text(
        textwrap.dedent(
            """
            integer: 1
            boolean: false
            """
        )
    )

    result = run_cli_command(cmd, ['--config', str(filepath)])
    assert 'Integer: 1' in result.output_lines[0]
    assert 'Boolean: False' in result.output_lines[1]


def test_invalid_unknown_keys(run_cli_command, tmp_path):
    """Test the option for a configuration file containing unknown keys."""
    filepath = tmp_path / 'config.yml'
    filepath.write_text(
        textwrap.dedent(
            """
            integer: 1
            unknown: 2.0
            """
        )
    )

    result = run_cli_command(cmd, ['--config', str(filepath)], raises=True)
    assert "Error: Invalid value for '--config': Invalid configuration file" in result.stderr
    assert "the following keys are not supported: {'unknown'}" in result.stderr


@pytest.fixture
def templated_config(tmp_path):
    """Write a templated config file declaring a single ``label`` variable and return its path."""
    filepath = tmp_path / 'config.yml'
    filepath.write_text(TEMPLATED_CONFIG)
    return filepath


@pytest.mark.parametrize(
    'template_vars_arg',
    [
        '{"label": "my-computer"}',
        pytest.param('vars_file', id='yaml_file'),
    ],
)
@pytest.mark.parametrize('config_first', (False, True), ids=('template_vars_first', 'config_first'))
def test_template_config_with_template_vars(
    run_cli_command, tmp_path, templated_config, template_vars_arg, config_first
):
    """Test that a templated config file is resolved via ``--template-vars``, whichever option is typed first."""
    if template_vars_arg == 'vars_file':
        vars_file = tmp_path / 'vars.yaml'
        vars_file.write_text('label: my-computer\n')
        template_vars_arg = str(vars_file)

    config_args = ['--config', str(templated_config)]
    template_args = ['--template-vars', template_vars_arg]
    args = config_args + template_args if config_first else template_args + config_args

    result = run_cli_command(cmd_with_template, args)
    assert 'Label: my-computer' in result.output
    assert 'Hostname: localhost' in result.output


@pytest.mark.parametrize(
    ('user_input', 'expected_label'),
    [
        pytest.param('my-prompted-label\n', 'my-prompted-label', id='typed_value'),
        pytest.param('\n', 'default-label', id='accept_default'),
    ],
)
def test_template_config_interactive_prompting(run_cli_command, templated_config, user_input, expected_label):
    """Interactive mode prompts for template variables; Enter accepts the default."""
    result = run_cli_command(cmd_with_template, ['--config', str(templated_config)], user_input=user_input)
    assert f'Label: {expected_label}' in result.output
    assert 'Hostname: localhost' in result.output


def test_template_config_interactive_choice(run_cli_command, tmp_path):
    """Interactive mode with ``type: list`` constrains input to the given options."""
    filepath = tmp_path / 'config.yml'
    filepath.write_text(
        textwrap.dedent(
            """\
            label: '{{ binary }}'
            hostname: localhost
            metadata:
                template_variables:
                    binary:
                        type: list
                        options:
                            - pw
                            - ph
            """
        )
    )

    result = run_cli_command(cmd_with_template, ['--config', str(filepath)], user_input='pw\n')
    assert 'Label: pw' in result.output


def test_template_config_template_vars_outside_choices_raises(run_cli_command, tmp_path):
    """``--template-vars`` values face the same ``type: list`` constraint as prompted answers."""
    filepath = tmp_path / 'config.yml'
    filepath.write_text(
        textwrap.dedent(
            """\
            label: '{{ binary }}'
            hostname: localhost
            metadata:
                template_variables:
                    binary:
                        type: list
                        options:
                            - pw
                            - ph
            """
        )
    )

    result = run_cli_command(
        cmd_with_template, ['--config', str(filepath), '--template-vars', '{"binary": "vim"}'], raises=True
    )
    assert 'not one of pw, ph' in result.stderr


def test_template_aware_option_rejects_type_override():
    """The provider needs a handle, so an explicit ``type`` fails at construction, not at runtime."""
    from aiida.cmdline.params.options.config import TemplateAwareConfigFileOption

    with pytest.raises(TypeError, match='does not accept `type`'):
        TemplateAwareConfigFileOption('--config', type=click.Path())


@pytest.mark.parametrize('config_first', (False, True), ids=('non_interactive_first', 'config_first'))
def test_template_config_non_interactive_never_prompts(run_cli_command, templated_config, config_first):
    """``--non-interactive`` must be honoured whichever side of ``--config`` it is typed on.

    Click orders eager options by invocation, so ``--config`` first used to leave ``non_interactive`` unseen and the
    command prompted anyway, blocking on a terminal.
    """
    config_args = ['--config', str(templated_config)]
    args = config_args + ['-n'] if config_first else ['-n'] + config_args

    result = run_cli_command(cmd_non_interactive, args, raises=True)
    assert 'No value provided for the template variables: label' in result.stderr
    assert 'Enter value' not in result.output


def test_template_config_aborted_prompt_reports_abort(run_cli_command, templated_config):
    """Aborting the template prompt reports ``Aborted!``, not a blank configuration read failure."""
    result = run_cli_command(cmd_with_template, ['--config', str(templated_config)], user_input='', raises=True)
    assert 'Aborted!' in result.output + result.stderr
    assert 'Error reading configuration file: \n' not in result.stderr


@pytest.mark.parametrize('config_first', (False, True), ids=('template_vars_first', 'config_first'))
def test_template_config_template_vars_path_typo(run_cli_command, templated_config, config_first):
    """A ``--template-vars`` value that is neither a file, a URL, nor JSON names all three, whichever order is used."""
    config_args = ['--config', str(templated_config)]
    template_args = ['--template-vars', 'does-not-exist.yaml']
    args = config_args + template_args if config_first else template_args + config_args

    result = run_cli_command(cmd_with_template, args, raises=True)
    assert '`does-not-exist.yaml` is not an existing file, a URL, or a valid inline JSON mapping' in result.stderr
    assert 'No value provided' not in result.stderr
