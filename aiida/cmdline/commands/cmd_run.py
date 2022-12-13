# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""`verdi run` command."""
import contextlib
import pathlib
import sys

import click

from aiida.cmdline.commands.cmd_verdi import verdi
from aiida.cmdline.params.options.multivalue import MultipleValueOption
from aiida.cmdline.utils import decorators


@contextlib.contextmanager
def update_environment(argv):
    """Context manager that temporarily replaces `sys.argv` with `argv` and adds current working dir to the path."""
    try:
        # Store a copy of the current path and argv as a backup variable so it can be restored later
        _path = sys.path[:]
        _argv = sys.argv[:]

        # Add the current working directory to the path, such that local modules can be imported
        sys.path.append(str(pathlib.Path.cwd().resolve()))
        sys.argv = argv[:]
        yield
    finally:
        # Restore old parameters when exiting from the context manager
        sys.argv = _argv
        sys.path = _path


def validate_entry_point_strings(_, __, value):
    """Validate that `value` is a valid entrypoint string."""
    from aiida.orm import autogroup

    try:
        autogroup.AutogroupManager.validate(value)
    except (TypeError, ValueError) as exc:
        raise click.BadParameter(f'{str(exc)}: `{value}`')

    return value


@verdi.command('run', context_settings=dict(ignore_unknown_options=True,))
@click.argument('filepath', type=click.Path(exists=True, readable=True, dir_okay=False, path_type=pathlib.Path))
@click.argument('varargs', nargs=-1, type=click.UNPROCESSED)
@click.option('--auto-group', is_flag=True, help='Enables the autogrouping')
@click.option(
    '-l',
    '--auto-group-label-prefix',
    type=click.STRING,
    required=False,
    help='Specify the prefix of the label of the auto group (numbers might be automatically '
    'appended to generate unique names per run).'
)
@click.option(
    '-e',
    '--exclude',
    type=str,
    cls=MultipleValueOption,
    default=None,
    help='Exclude these classes from auto grouping (use full entrypoint strings).',
    callback=validate_entry_point_strings
)
@click.option(
    '-i',
    '--include',
    type=str,
    cls=MultipleValueOption,
    default=None,
    help='Include these classes from auto grouping (use full entrypoint strings or "all").',
    callback=validate_entry_point_strings
)
@decorators.with_dbenv()
def run(filepath, varargs, auto_group, auto_group_label_prefix, exclude, include):
    """Execute scripts with preloaded AiiDA environment."""
    from aiida.cmdline.utils.shell import DEFAULT_MODULES_LIST
    from aiida.manage import get_manager

    filepath.resolve()

    # Prepare the environment for the script to be run
    globals_dict = {
        '__builtins__': globals()['__builtins__'],
        '__name__': '__main__',
        '__file__': filepath.name,
        '__doc__': None,
        '__package__': None
    }

    # Dynamically load modules (the same of verdi shell) - but in globals_dict, not in the current environment
    for app_mod, model_name, alias in DEFAULT_MODULES_LIST:
        globals_dict[f'{alias}'] = getattr(__import__(app_mod, {}, {}, model_name), model_name)

    if auto_group:
        storage_backend = get_manager().get_profile_storage()
        storage_backend.autogroup.enable()
        # Set the ``group_label_prefix`` if defined, otherwise a default prefix will be used
        storage_backend.autogroup.set_group_label_prefix(auto_group_label_prefix)
        storage_backend.autogroup.set_exclude(exclude)
        storage_backend.autogroup.set_include(include)

    try:
        with filepath.open('r', encoding='utf-8') as handle:
            with update_environment(argv=[str(filepath)] + list(varargs)):
                # Compile the script for execution and pass it to exec with the globals_dict
                exec(compile(handle.read(), str(filepath), 'exec', dont_inherit=True), globals_dict)  # pylint: disable=exec-used
    except SystemExit:  # pylint: disable=try-except-raise
        # Script called ``sys.exit()``, re-raise the exception to have the error code properly returned at the end
        raise
    finally:
        storage_backend = get_manager().get_profile_storage()
        storage_backend.autogroup.disable()
