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


def is_on_computer(ctx: click.Context) -> bool:
    return bool(ctx.params.get('on_computer'))


def is_not_on_computer(ctx: click.Context) -> bool:
    return bool(not is_on_computer(ctx))


def validate_label_uniqueness(ctx: click.Context, _: None, value: str) -> str:
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


ON_COMPUTER = OverridableOption(
    '--on-computer/--store-in-db',
    is_eager=False,
    default=True,
    cls=InteractiveOption,
    prompt='Installed on target computer?',
    help='Whether the code is installed on the target computer, or should be copied to the target computer each time '
    'from a local path.',
)

REMOTE_ABS_PATH = OverridableOption(
    '--remote-abs-path',
    prompt='Remote absolute path',
    required_fn=is_on_computer,
    prompt_fn=is_on_computer,
    type=types.AbsolutePathParamType(dir_okay=False),
    cls=InteractiveOption,
    help='[if --on-computer]: Absolute path to the executable on the target computer.',
)

FOLDER = OverridableOption(
    '--code-folder',
    prompt='Local directory containing the code',
    required_fn=is_not_on_computer,
    prompt_fn=is_not_on_computer,
    type=click.Path(file_okay=False, exists=True, readable=True),
    cls=InteractiveOption,
    help='[if --store-in-db]: Absolute path to directory containing the executable and all other files necessary for '
    'running it (to be copied to target computer).',
)

REL_PATH = OverridableOption(
    '--code-rel-path',
    prompt='Relative path of executable inside code folder',
    required_fn=is_not_on_computer,
    prompt_fn=is_not_on_computer,
    type=click.Path(dir_okay=False),
    cls=InteractiveOption,
    help='[if --store-in-db]: Relative path of the executable inside the code-folder.',
)

USE_DOUBLE_QUOTES = OverridableOption(
    '--use-double-quotes/--not-use-double-quotes',
    default=False,
    cls=InteractiveOption,
    prompt='Escape CLI arguments in double quotes',
    help='Whether the executable and arguments of the code in the submission script should be escaped with single '
    'or double quotes.',
)

LABEL = options.LABEL.clone(
    prompt='Label',
    callback=validate_label_uniqueness,
    cls=InteractiveOption,
    help="This label can be used to identify the code (using 'label@computerlabel'), as long as labels are unique per "
    'computer.',
)

DESCRIPTION = options.DESCRIPTION.clone(
    prompt='Description',
    cls=InteractiveOption,
    help='A human-readable description of this code, ideally including version and compilation environment.',
)

INPUT_PLUGIN = options.INPUT_PLUGIN.clone(
    required=False,
    prompt='Default calculation input plugin',
    cls=InteractiveOption,
    help="Entry point name of the default calculation plugin (as listed in 'verdi plugin list aiida.calculations').",
)

COMPUTER = options.COMPUTER.clone(
    prompt='Computer',
    cls=InteractiveOption,
    required_fn=is_on_computer,
    prompt_fn=is_on_computer,
    help='Name of the computer, on which the code is installed.',
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
    footer='All lines that start with `#=` will be ignored.',
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
    footer='All lines that start with `#=` will be ignored.',
)
