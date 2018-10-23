# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Reusable command line interface options for Code commands."""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import click

from aiida.cmdline.params import options, types
from aiida.cmdline.params.options.interactive import InteractiveOption
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
    help='Whether the code is installed on the target computer or should be copied each time from a local path.')

REMOTE_ABS_PATH = OverridableOption(
    '--remote-abs-path',
    prompt='Remote absolute path',
    required_fn=is_on_computer,
    prompt_fn=is_on_computer,
    type=types.AbsolutePathParamType(dir_okay=False),
    cls=InteractiveOption,
    help=('[if --on-computer]: the absolute path to the executable on the remote machine.'))

FOLDER = OverridableOption(
    '--code-folder',
    prompt='Local directory containing the code',
    required_fn=is_not_on_computer,
    prompt_fn=is_not_on_computer,
    type=click.Path(file_okay=False, exists=True, readable=True),
    cls=InteractiveOption,
    help=('[if --store-in-db]: directory containing the executable and all other files necessary for running it.'))

REL_PATH = OverridableOption(
    '--code-rel-path',
    prompt='Relative path of executable inside code folder',
    required_fn=is_not_on_computer,
    prompt_fn=is_not_on_computer,
    type=click.Path(dir_okay=False),
    cls=InteractiveOption,
    help=('[if --store-in-db]: relative path of the executable inside the code-folder.'))

LABEL = options.LABEL.clone(prompt='Label', cls=InteractiveOption, help='A label to refer to this code.')

DESCRIPTION = options.DESCRIPTION.clone(
    prompt='Description', cls=InteractiveOption, help='A human-readable description of this code.')

INPUT_PLUGIN = options.INPUT_PLUGIN.clone(
    prompt='Default calculation input plugin',
    cls=InteractiveOption,
    help='Default calculation plugin to use for this code.')

COMPUTER = options.COMPUTER.clone(
    prompt='Computer',
    cls=InteractiveOption,
    required_fn=is_on_computer,
    prompt_fn=is_on_computer,
    help='Name of the computer, on which the code resides.')
