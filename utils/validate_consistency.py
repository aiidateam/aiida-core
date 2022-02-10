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

Validates consistency of

 * pyproject.toml
 * environment.yml

"""
import os

import click

SCRIPT_PATH = os.path.split(os.path.realpath(__file__))[0]
ROOT_DIR = os.path.join(SCRIPT_PATH, os.pardir)


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
    with open(filepath, encoding='utf8') as handle:
        lines = handle.readlines()

    try:
        index_start, index_end = determine_block_positions(lines, block_start_marker, block_end_marker)
    except RuntimeError as exception:
        raise RuntimeError(f'problem rewriting file `{filepath}`:: {exception}')

    lines = replace_line_block(lines, block, index_start, index_end)

    with open(filepath, 'w', encoding='utf8') as handle:
        for line in lines:
            handle.write(line)


@click.group()
def cli():
    pass


@cli.command('verdi-autodocs')
def validate_verdi_documentation():
    """Auto-generate the documentation for `verdi` through `click`."""
    from click import Context

    from aiida.manage.configuration import load_documentation_profile

    load_documentation_profile()

    from aiida.cmdline.commands.cmd_verdi import verdi

    width = 90  # The maximum width of the formatted help strings in characters

    # Set the `verdi data` command to isolated mode such that external plugin commands are not discovered
    ctx = Context(verdi, terminal_width=width)
    command = verdi.get_command(ctx, 'data')
    command.set_exclude_external_plugins(True)

    # Replacing the block with the commands of `verdi`
    filepath_verdi_commands = os.path.join(ROOT_DIR, 'docs', 'source', 'reference', 'command_line.rst')
    commands_block_start_marker = '.. _reference:command-line:verdi:'
    commands_block_end_marker = '.. END_OF_VERDI_COMMANDS_MARKER'

    # Generate the new block with the command help strings
    header = 'Commands'
    message = 'Below is a list with all available subcommands.'
    block = [f"{header}\n{'=' * len(header)}\n{message}\n\n"]

    for name, command in sorted(verdi.commands.items()):
        ctx = click.Context(command, terminal_width=width)

        header_label = f'.. _reference:command-line:verdi-{name}:'
        header_string = f'``verdi {name}``'
        header_underline = '-' * len(header_string)

        block.append(f'{header_label}\n\n')
        block.append(f'{header_string}\n')
        block.append(f'{header_underline}\n\n')
        block.append('.. code:: console\n\n')  # Mark the beginning of a literal block
        for line in ctx.get_help().split('\n'):
            if line:
                block.append(f'    {line}\n')
            else:
                block.append('\n')
        block.append('\n\n')

    # New block should start and end with an empty line after and before the literal block marker
    block.insert(0, '\n')
    block.append('\n')

    replace_block_in_file(filepath_verdi_commands, commands_block_start_marker, commands_block_end_marker, block)


if __name__ == '__main__':
    cli()  # pylint: disable=no-value-for-parameter
