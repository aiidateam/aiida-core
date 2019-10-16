#!/usr/bin/env python
# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Validate consistency of versions and dependencies.

Validates consistency of setup.json and

 * environment.yml
 * version in aiida/__init__.py
 * reentry dependency in pyproject.toml

"""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import io
import os
import sys
import json
from collections import OrderedDict
import toml
import click

FILENAME_TOML = 'pyproject.toml'
FILENAME_SETUP_JSON = 'setup.json'
SCRIPT_PATH = os.path.split(os.path.realpath(__file__))[0]
ROOT_DIR = os.path.join(SCRIPT_PATH, os.pardir)
FILEPATH_SETUP_JSON = os.path.join(ROOT_DIR, FILENAME_SETUP_JSON)
FILEPATH_TOML = os.path.join(ROOT_DIR, FILENAME_TOML)


def get_setup_json():
    """Return the `setup.json` as a python dictionary """
    with io.open(FILEPATH_SETUP_JSON, 'r') as fil:
        return json.load(fil, object_pairs_hook=OrderedDict)


def write_setup_json(data):
    """Write the contents of `data` to the `setup.json`.

    If an exception is encountered during writing, the old content is restored.

    :param data: the dictionary to write to the `setup.json`
    """
    backup = get_setup_json()

    try:
        dump_setup_json(data)
    except Exception:  # pylint: disable=broad-except
        dump_setup_json(backup)


def dump_setup_json(data):
    """Write the contents of `data` to the `setup.json`.

    .. warning:: If the writing of the file excepts, the current file will be overwritten and will be left in an
        incomplete state. To write with a backup safety use the `write_setup_json` function instead.

    :param data: the dictionary to write to the `setup.json`
    """
    with io.open(FILEPATH_SETUP_JSON, 'w') as handle:
        # Write with indentation of two spaces and explicitly define separators to not have spaces at end of lines
        return json.dump(data, handle, indent=2, separators=(',', ': '))


def determine_block_positions(lines, block_start_marker, block_end_marker):
    """Determine the line indices of a block in a list of lines indicated by a given start and end marker.

    :param lines: list of strings
    :param block_start_marker: string marking the beginning of the block
    :param block_end_marker: string marking the end of the block
    :return: tuple of two integers representing the line indices that indicate the start and end of the block
    """
    block_start_index = -1
    block_end_index = -1

    for line_number, line in enumerate(lines):
        if block_start_marker in line:
            block_start_index = line_number + 1

        if block_end_marker in line:
            block_end_index = line_number
            break

    if block_start_index < 0 or block_end_index < 0:
        raise RuntimeError('failed to determine the starting or end point of the block')

    return block_start_index, block_end_index


def replace_line_block(lines, block, index_start, index_end):
    """Replace a block of lines between two line indices with a new set of lines.

    :param lines: list of lines representing the whole file
    :param block: list of lines representing the new block that should be inserted after old block is removed
    :param index_start: start of the block to be removed
    :param index_end: end of the block to be removed
    :return: list of lines with block of lines replaced
    """
    # Slice out the old block by removing the lines between the markers of the block
    lines = lines[:index_start] + lines[index_end:]

    # Now insert the new block starting at the beginning of the original block
    lines[index_start:index_start] = block

    return lines


def replace_block_in_file(filepath, block_start_marker, block_end_marker, block):
    """Replace a block of text between the given string markers with the provided new block of lines.

    :param filepath: absolute path of the file
    :param block_start_marker: string marking the beginning of the block
    :param block_end_marker: string marking the end of the block
    :param block: list of lines representing the new block that should be inserted after old block is removed
    """
    with io.open(filepath) as handle:
        lines = handle.readlines()

    try:
        index_start, index_end = determine_block_positions(lines, block_start_marker, block_end_marker)
    except RuntimeError as exception:
        raise RuntimeError('problem rewriting file `{}`:: {}'.format(filepath, exception))

    lines = replace_line_block(lines, block, index_start, index_end)

    with io.open(filepath, 'w') as handle:
        for line in lines:
            handle.write(line)


@click.group()
def cli():
    pass


@cli.command('verdi-autodocs')
def validate_verdi_documentation():
    """Auto-generate the documentation for `verdi` through `click`."""
    from click import Context
    from aiida.cmdline.commands.cmd_verdi import verdi

    # Set the `verdi data` command to isolated mode such that external plugin commands are not discovered
    ctx = Context(verdi)
    command = verdi.get_command(ctx, 'data')
    command.set_exclude_external_plugins(True)

    # Replacing the block with the overview of `verdi`
    filepath_verdi_overview = os.path.join(ROOT_DIR, 'docs', 'source', 'working_with_aiida', 'index.rst')
    overview_block_start_marker = '.. _verdi_overview:'
    overview_block_end_marker = '.. END_OF_VERDI_OVERVIEW_MARKER'

    # Generate the new block with the command index
    block = []
    for name, command in sorted(verdi.commands.items()):
        short_help = command.help.split('\n')[0]
        block.append(u'* :ref:`{name:}<verdi_{name:}>`:  {help:}\n'.format(name=name, help=short_help))

    # New block should start and end with an empty line after and before the literal block marker
    block.insert(0, u'\n')
    block.append(u'\n')

    replace_block_in_file(filepath_verdi_overview, overview_block_start_marker, overview_block_end_marker, block)

    # Replacing the block with the commands of `verdi`
    filepath_verdi_commands = os.path.join(ROOT_DIR, 'docs', 'source', 'verdi', 'verdi_user_guide.rst')
    commands_block_start_marker = '.. _verdi_commands:'
    commands_block_end_marker = '.. END_OF_VERDI_COMMANDS_MARKER'

    # Generate the new block with the command help strings
    header = u'Commands'
    message = u'Below is a list with all available subcommands.'
    block = [u'{}\n{}\n{}\n\n'.format(header, '=' * len(header), message)]

    for name, command in sorted(verdi.commands.items()):
        ctx = click.Context(command)

        header_label = u'.. _verdi_{name:}:'.format(name=name)
        header_string = u'``verdi {name:}``'.format(name=name)
        header_underline = u'-' * len(header_string)

        block.append(header_label + '\n\n')
        block.append(header_string + '\n')
        block.append(header_underline + '\n\n')
        block.append(u'::\n\n')  # Mark the beginning of a literal block
        for line in ctx.get_help().split('\n'):
            if line:
                block.append(u'    {}\n'.format(line))
            else:
                block.append(u'\n')
        block.append(u'\n\n')

    # New block should start and end with an empty line after and before the literal block marker
    block.insert(0, u'\n')
    block.append(u'\n')

    replace_block_in_file(filepath_verdi_commands, commands_block_start_marker, commands_block_end_marker, block)


@cli.command('version')
def validate_version():
    """Check that version numbers match.

    Check version number in setup.json and aiida-core/__init__.py and make sure they match.
    """
    import pkgutil

    # Get version from python package
    loaders = [
        module_loader for (module_loader, name, ispkg) in pkgutil.iter_modules(path=[ROOT_DIR])
        if name == 'aiida' and ispkg
    ]
    version = loaders[0].find_module('aiida').load_module('aiida').__version__

    setup_content = get_setup_json()
    if version != setup_content['version']:
        click.echo('Version number mismatch detected:')
        click.echo("Version number in '{}': {}".format(FILENAME_SETUP_JSON, setup_content['version']))
        click.echo("Version number in '{}/__init__.py': {}".format('aiida', version))
        click.echo("Updating version in '{}' to: {}".format(FILENAME_SETUP_JSON, version))

        setup_content['version'] = version
        write_setup_json(setup_content)

        sys.exit(1)


@cli.command('toml')
def validate_pyproject():
    """Ensure that the version of reentry in setup.json and pyproject.toml are identical."""
    reentry_requirement = None
    for requirement in get_setup_json()['install_requires']:
        if 'reentry' in requirement:
            reentry_requirement = requirement
            break

    if reentry_requirement is None:
        click.echo('Could not find the reentry requirement in {}'.format(FILEPATH_SETUP_JSON), err=True)
        sys.exit(1)

    try:
        with io.open(FILEPATH_TOML, 'r') as handle:
            toml_string = handle.read()
    except IOError as exception:
        click.echo('Could not read the required file: {}'.format(FILEPATH_TOML), err=True)
        sys.exit(1)

    try:
        parsed_toml = toml.loads(toml_string)
    except Exception as exception:  # pylint: disable=broad-except
        click.echo('Could not parse {}: {}'.format(FILEPATH_TOML, exception), err=True)
        sys.exit(1)

    try:
        pyproject_toml_requires = parsed_toml['build-system']['requires']
    except KeyError as exception:
        click.echo('Could not retrieve the build-system requires list from {}'.format(FILEPATH_TOML), err=True)
        sys.exit(1)

    if reentry_requirement not in pyproject_toml_requires:
        click.echo(
            'Reentry requirement from {} {} is not mirrored in {}'.format(
                FILEPATH_SETUP_JSON, reentry_requirement, FILEPATH_TOML
            ),
            err=True
        )
        sys.exit(1)


@cli.command('conda')
def update_environment_yml():
    """Update `environment.yml` file for conda."""
    import yaml
    import re

    # needed for ordered dict, see https://stackoverflow.com/a/52621703
    yaml.add_representer(
        OrderedDict,
        lambda self, data: yaml.representer.SafeRepresenter.represent_dict(self, data.items()),
        Dumper=yaml.SafeDumper
    )

    # fix incompatibilities between conda and pypi
    replacements = {'psycopg2-binary': 'psycopg2', 'graphviz': 'python-graphviz'}
    install_requires = get_setup_json()['install_requires']

    conda_requires = []
    for req in install_requires:
        # skip packages required for specific python versions
        # (environment.yml aims at the latest python version)
        if req.find('python_version') != -1:
            continue

        for (regex, replacement) in iter(replacements.items()):
            req = re.sub(regex, replacement, req)

        conda_requires.append(req)

    environment = OrderedDict([
        ('name', 'aiida'),
        ('channels', ['defaults', 'conda-forge', 'etetoolkit']),
        ('dependencies', conda_requires),
    ])

    environment_filename = 'environment.yml'
    file_path = os.path.join(ROOT_DIR, environment_filename)
    with io.open(file_path, 'w') as env_file:
        env_file.write(u'# Usage: conda env create -n myenvname -f environment.yml python=3.6\n')
        yaml.safe_dump(
            environment, env_file, explicit_start=True, default_flow_style=False, encoding='utf-8', allow_unicode=True
        )


if __name__ == '__main__':
    cli()  # pylint: disable=no-value-for-parameter
