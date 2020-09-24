# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Reusable command line interface options for Code commands."""
import click

from aiida.cmdline.params import options, types
from aiida.cmdline.params.options.interactive import InteractiveOption, TemplateInteractiveOption
from aiida.cmdline.params.options.overridable import OverridableOption


def is_on_computer(ctx):
    return bool(ctx.params.get('on_computer'))


def is_not_on_computer(ctx):
    return bool(not is_on_computer(ctx))


ON_COMPUTER = OverridableOption(
    '--on-computer/--store-in-db',
    is_eager=False,
    default=True,
    cls=InteractiveOption,
    prompt='Installed on target computer?',
    help='Whether the code is installed on the target computer, or should be copied to the target computer each time '
    'from a local path.'
)

REMOTE_ABS_PATH = OverridableOption(
    '--remote-abs-path',
    prompt='Remote absolute path',
    required_fn=is_on_computer,
    prompt_fn=is_on_computer,
    type=types.AbsolutePathParamType(dir_okay=False),
    cls=InteractiveOption,
    help='[if --on-computer]: Absolute path to the executable on the target computer.'
)

FOLDER = OverridableOption(
    '--code-folder',
    prompt='Local directory containing the code',
    required_fn=is_not_on_computer,
    prompt_fn=is_not_on_computer,
    type=click.Path(file_okay=False, exists=True, readable=True),
    cls=InteractiveOption,
    help='[if --store-in-db]: Absolute path to directory containing the executable and all other files necessary for '
    'running it (to be copied to target computer).'
)

REL_PATH = OverridableOption(
    '--code-rel-path',
    prompt='Relative path of executable inside code folder',
    required_fn=is_not_on_computer,
    prompt_fn=is_not_on_computer,
    type=click.Path(dir_okay=False),
    cls=InteractiveOption,
    help='[if --store-in-db]: Relative path of the executable inside the code-folder.'
)

LABEL = options.LABEL.clone(
    prompt='Label',
    cls=InteractiveOption,
    help="This label can be used to identify the code (using 'label@computerlabel'), as long as labels are unique per "
    'computer.'
)

DESCRIPTION = options.DESCRIPTION.clone(
    prompt='Description',
    cls=InteractiveOption,
    help='A human-readable description of this code, ideally including version and compilation environment.'
)

INPUT_PLUGIN = options.INPUT_PLUGIN.clone(
    prompt='Default calculation input plugin',
    cls=InteractiveOption,
    help="Entry point name of the default calculation plugin (as listed in 'verdi plugin list aiida.calculations')."
)

COMPUTER = options.COMPUTER.clone(
    prompt='Computer',
    cls=InteractiveOption,
    required_fn=is_on_computer,
    prompt_fn=is_on_computer,
    help='Name of the computer, on which the code is installed.'
)

PREPEND_TEXT = OverridableOption(
    '--prepend-text',
    cls=TemplateInteractiveOption,
    prompt='Prepend script',
    type=click.STRING,
    default='',
    help='Bash commands that should be prepended to the executable call in all submit scripts for this code.',
    extension='.bash',
    header='PREPEND_TEXT: if there is any bash commands that should be prepended to the executable call in all '
    'submit scripts for this code, type that between the equal signs below and save the file.',
    footer='All lines that start with `#=` will be ignored.'
)

APPEND_TEXT = OverridableOption(
    '--append-text',
    cls=TemplateInteractiveOption,
    prompt='Append script',
    type=click.STRING,
    default='',
    help='Bash commands that should be appended to the executable call in all submit scripts for this code.',
    extension='.bash',
    header='APPEND_TEXT: if there is any bash commands that should be appended to the executable call in all '
    'submit scripts for this code, type that between the equal signs below and save the file.',
    footer='All lines that start with `#=` will be ignored.'
)
