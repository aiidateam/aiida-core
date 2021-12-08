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

def is_on_container(ctx):
    return bool(ctx.params.get('on_container'))

def is_not_on_container(ctx):
    return bool(not is_on_container(ctx))

def is_on_computer(ctx):
    return bool(ctx.params.get('on_computer'))

def is_not_on_computer(ctx):
    return bool(not is_on_computer(ctx))

def is_on_computer_or_container(ctx):
    return is_on_computer(ctx) or is_on_container(ctx)

def is_on_sarus(ctx):
    return bool(ctx.params.get('container_tech') == 'sarus')

def validate_label_uniqueness(ctx, _, value):
    """Validate the uniqueness of the label of the code.

    The exact uniqueness criterion depends on the type of the code, whether it is "local" or "remote". For the former,
    the `label` itself should be unique, whereas for the latter it is the full label, i.e., `label@computer.label`.

    .. note:: For this to work in the case of the remote code, the computer parameter already needs to have been parsed
        In interactive mode, this means that the computer parameter needs to be defined after the label parameter in the
        command definition. For non-interactive mode, the parsing order will always be determined by the order the
        parameters are specified by the caller and so this validator may get called before the computer is parsed. For
        that reason, this validator should also be called in the command itself, to ensure it has both the label and
        computer parameter available.

    """
    from aiida.common import exceptions
    from aiida.orm import load_code

    computer = ctx.params.get('computer', None)
    on_computer = ctx.params.get('on_computer', None)

    if on_computer is False:
        try:
            load_code(value)
        except exceptions.NotExistent:
            pass
        except exceptions.MultipleObjectsError:
            raise click.BadParameter(f'multiple copies of the remote code `{value}` already exist.')
        else:
            raise click.BadParameter(f'the code `{value}` already exists.')

    if computer is not None:
        full_label = f'{value}@{computer.label}'

        try:
            load_code(full_label)
        except exceptions.NotExistent:
            pass
        except exceptions.MultipleObjectsError:
            raise click.BadParameter(f'multiple copies of the local code `{full_label}` already exist.')
        else:
            raise click.BadParameter(f'the code `{full_label}` already exists.')

    return value

ON_CONTAINER = OverridableOption(
    '--on-container/--not-on-container',
    is_eager=False,
    default=False,
    help='Whether the code is installed on the container.'
)

IMAGE = OverridableOption(
    '--image',
    prompt='image name.',
    required_fn=is_on_container,
    prompt_fn=is_on_container,
    cls=InteractiveOption,
    help='image name.'
)

CONTAINER_TECH = OverridableOption(
    '--container-tech',
    prompt='container tech',
    required_fn=is_on_container,
    prompt_fn=is_on_container,
    cls=InteractiveOption,
    help='container tech.'
)

SARUS_CMD_PARAMS = OverridableOption(
    '--sarus-params',
    prompt='sarus params',
    default='{sarus_exec} run --mount=src={source_dir},dst={dist_dir},type=bind  --workdir {workdir} {image}',
    required_fn=is_on_sarus,
    prompt_fn=is_on_sarus,
    cls=InteractiveOption,
    help='sarus params.'
)

SARUS_EXEC = OverridableOption(
    '--sarus-exec',
    prompt='sarus executable path',
    default='/usr/bin/sarus',
    required_fn=is_on_sarus,
    prompt_fn=is_on_sarus,
    type=types.AbsolutePathParamType(dir_okay=False),
    cls=InteractiveOption,
    help='sarus executable path.'
)

MOUNT_SOURCE_DIR = OverridableOption(
    '--mount-source-dir',
    prompt='sarus bind source dir',
    default='${PWD}',
    required_fn=is_on_sarus,
    prompt_fn=is_on_sarus,
    cls=InteractiveOption,
    help='sarus bind source dir.'
)

MOUNT_DIST_DIR = OverridableOption(
    '--mount-dist-dir',
    prompt='sarus bind dist dir',
    default='/workdir',
    required_fn=is_on_sarus,
    prompt_fn=is_on_sarus,
    cls=InteractiveOption,
    help='sarus bind dist dir.'
)

WORK_DIR = OverridableOption(
    '--work-dir',
    prompt='sarus work dir',
    default='/workdir',
    required_fn=is_on_sarus,
    prompt_fn=is_on_sarus,
    cls=InteractiveOption,
    help='sarus workdir dir.'
)

ON_COMPUTER = OverridableOption(
    '--on-computer/--store-in-db',
    is_eager=False,
    default=True,
    cls=InteractiveOption,
    required_fn=is_not_on_container,
    prompt_fn=is_not_on_container,
    prompt='Installed on target computer?',
    help='Whether the code is installed on the target computer, or should be copied to the target computer each time '
    'from a local path.'
)

REMOTE_ABS_PATH = OverridableOption(
    '--remote-abs-path',
    prompt='Remote absolute path',
    required_fn=is_on_computer_or_container,
    prompt_fn=is_on_computer_or_container,
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

USE_DOUBLE_QUOTES = OverridableOption(
    '--use-double-quotes/--not-use-double-quotes',
    is_eager=False,
    default=False,
    cls=InteractiveOption,
    prompt='Whether use double quotes for code cmdline params?',
    help='Whether the code executable parameters in script using the double quotes to escape.'
)

LABEL = options.LABEL.clone(
    prompt='Label',
    callback=validate_label_uniqueness,
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
    required_fn=is_on_computer_or_container,
    prompt_fn=is_on_computer_or_container,
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
