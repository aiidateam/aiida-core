###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""The `verdi smart` command line interface."""

import json
import pathlib
import subprocess
from typing import Callable, Optional

import click

from aiida.cmdline.commands.cmd_verdi import verdi

from .llm_backend import groc_command_generator


@verdi.group('smart')
def verdi_smart():
    """Use LLM to query to find out how to do things."""


def _validate_backend(ctx, param, value):
    """Validate the backend option."""
    value = value.lower() if value else None
    if value and value not in ['groq']:
        raise click.BadParameter('The only available options are: [groq]')
    return value


def _prompt(message: str, validation: Optional[Callable] = None):
    """Prompt to user until the validation passes."""
    while True:
        value = click.prompt(message, type=str)
        if validation:
            try:
                validation(None, None, value)
            except click.BadParameter as e:
                click.echo(str(e))
                continue
        break
    return value


def _execute_command(command):
    """Execute a command via subprocess and print the output."""

    try:
        click.echo('$ ' + command)
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        click.echo('Command output:')
        click.echo(result.stderr)
        click.echo(result.stdout)
    except subprocess.CalledProcessError as e:
        click.echo('Error running command:')
        click.echo(e.stderr)
    except Exception as e:
        click.echo('An unexpected error occurred:')
        click.echo(str(e))


def load_smart_config(func):
    """Decorator to load the smart config file."""

    def wrapper(*args, **kwargs):
        config_file = pathlib.Path.home() / '.aiida' / 'llm_config.json'
        if not config_file.exists():
            click.echo('No configuration file found. Please run `verdi smart configure` first.')
            return None
        with config_file.open('r') as f:
            config_data = json.load(f)
        if config_data is None:
            click.echo('No configuration file found. Please run `verdi smart configure` first.')
            return

        return func(config_data['backend'], config_data['api_key'], *args, **kwargs)

    return wrapper


@verdi_smart.command('configure')
@click.option(
    '-b',
    '--backend',
    type=str,
    required=False,
    help='The LLM backend to use. Available options: groq.',
    callback=_validate_backend,
)
@click.option('-b', '--api-key', type=str, required=False, help='Your API key for the LLM backend.')
def smart_configure(backend, api_key):
    """Choose and configure an LLM backend."""
    click.echo('This command will help you choose and configure an LLM backend for AiiDA.\n')
    if not backend:
        click.echo('Please follow the instructions below to set up your preferred LLM backend.')
        click.echo('Step #1 Choose a backend:')
        click.echo('      groq')
        backend_choice = _prompt('Your choice', _validate_backend)

    if not api_key:
        click.echo(f'Step #2 Enter your API key for {backend_choice}:')
        api_key = _prompt('Your API key')

    # This is a temporary solution to store the configuration.
    # Just for proof of concept and testing purposes.
    # TODO: properly and safely store this data after merging this PR:
    # https://github.com/aiidateam/aiida-core/pull/6761

    config_file = pathlib.Path.home() / '.aiida' / 'llm_config.json'
    config_file.parent.mkdir(parents=True, exist_ok=True)
    config_data = {'backend': backend_choice, 'api_key': api_key}
    with config_file.open('w') as f:
        json.dump(config_data, f)
    click.echo(f'Configuration saved to {config_file}. You can change it later by editing this file.\n')
    click.echo('You can now use the `verdi smart` command to interact with the LLM backend.\n')


@verdi_smart.command('cli')
@click.argument('something-to-ask', type=str)
@load_smart_config
def smart_generate(backend, api_key, something_to_ask):
    """Generate a command based on a natural language something-to-ask."""

    if backend == 'groq':
        suggestion = groc_command_generator(something_to_ask, api_key)
        click.echo(f'Generated command: `{suggestion}`\n')
        action = click.prompt('Execute[e], Modify[m], or Cancel[c]:')
        if action.lower() == 'e':
            command = suggestion
            _execute_command(command)
        elif action.lower() == 'm':
            command = click.prompt('Please modify the command:')
            _execute_command(command)
        elif action.lower() == 'c':
            click.echo('Command cancelled.')
        else:
            click.echo('Invalid option. Command cancelled.')
    else:
        click.echo('No valid backend found. Please run `verdi smart configure` to set up a backend.')
