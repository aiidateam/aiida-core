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
import os
import functools
import sys
import warnings

import click

from aiida.cmdline.commands.cmd_verdi import verdi
from aiida.cmdline.params.options.multivalue import MultipleValueOption
from aiida.cmdline.utils import decorators, echo
from aiida.common.warnings import AiidaDeprecationWarning


@contextlib.contextmanager
def update_environment(argv):
    """Context manager that temporarily replaces `sys.argv` with `argv` and adds current working dir to the path."""
    try:
        # Store a copy of the current path and argv as a backup variable so it can be restored later
        _path = sys.path[:]
        _argv = sys.argv[:]

        # Add the current working directory to the path, such that local modules can be imported
        sys.path.append(os.getcwd())
        sys.argv = argv[:]
        yield
    finally:
        # Restore old parameters when exiting from the context manager
        sys.argv = _argv
        sys.path = _path


def validate_entrypoint_string(ctx, param, value):  # pylint: disable=unused-argument,invalid-name
    """Validate that `value` is a valid entrypoint string."""
    from aiida.orm import autogroup

    try:
        autogroup.Autogroup.validate(value)
    except Exception as exc:
        raise click.BadParameter(f'{str(exc)} ({value})')

    return value


@verdi.command('run', context_settings=dict(ignore_unknown_options=True,))
@click.argument('scriptname', type=click.STRING)
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
    '-n',
    '--group-name',
    type=click.STRING,
    required=False,
    help='Specify the name of the auto group [DEPRECATED, USE --auto-group-label-prefix instead]. '
    'This also enables auto-grouping.'
)
@click.option(
    '-e',
    '--exclude',
    cls=MultipleValueOption,
    default=None,
    help='Exclude these classes from auto grouping (use full entrypoint strings).',
    callback=functools.partial(validate_entrypoint_string)
)
@click.option(
    '-i',
    '--include',
    cls=MultipleValueOption,
    default=None,
    help='Include these classes from auto grouping  (use full entrypoint strings or "all").',
    callback=validate_entrypoint_string
)
@decorators.with_dbenv()
def run(scriptname, varargs, auto_group, auto_group_label_prefix, group_name, exclude, include):
    # pylint: disable=too-many-arguments,exec-used
    """Execute scripts with preloaded AiiDA environment."""
    from aiida.cmdline.utils.shell import DEFAULT_MODULES_LIST
    from aiida.orm import autogroup

    # Prepare the environment for the script to be run
    globals_dict = {
        '__builtins__': globals()['__builtins__'],
        '__name__': '__main__',
        '__file__': scriptname,
        '__doc__': None,
        '__package__': None
    }

    # Dynamically load modules (the same of verdi shell) - but in globals_dict, not in the current environment
    for app_mod, model_name, alias in DEFAULT_MODULES_LIST:
        globals_dict[f'{alias}'] = getattr(__import__(app_mod, {}, {}, model_name), model_name)

    if group_name:
        warnings.warn('--group-name is deprecated, use `--auto-group-label-prefix` instead', AiidaDeprecationWarning)  # pylint: disable=no-member
        if auto_group_label_prefix:
            raise click.BadParameter(
                'You cannot specify both --group-name and --auto-group-label-prefix; '
                'use --auto-group-label-prefix only'
            )
        auto_group_label_prefix = group_name
        # To have the old behavior, with auto-group enabled.
        auto_group = True

    if auto_group:
        aiida_verdilib_autogroup = autogroup.Autogroup()
        # Set the ``group_label_prefix`` if defined, otherwise a default prefix will be used
        if auto_group_label_prefix is not None:
            aiida_verdilib_autogroup.set_group_label_prefix(auto_group_label_prefix)
        aiida_verdilib_autogroup.set_exclude(exclude)
        aiida_verdilib_autogroup.set_include(include)

        # Note: this is also set in the exec environment! This is the intended behavior
        autogroup.CURRENT_AUTOGROUP = aiida_verdilib_autogroup

    # Initialize the variable here, otherwise we get UnboundLocalError in the finally clause if it fails to open
    handle = None

    try:
        # Here we use a standard open and not open, as exec will later fail if passed a unicode type string.
        handle = open(scriptname, 'r')
    except IOError:
        echo.echo_critical(f"Unable to load file '{scriptname}'")
    else:
        try:
            # Must add also argv[0]
            argv = [scriptname] + list(varargs)
            with update_environment(argv=argv):
                # Compile the script for execution and pass it to exec with the globals_dict
                exec(compile(handle.read(), scriptname, 'exec', dont_inherit=True), globals_dict)  # yapf: disable # pylint: disable=exec-used
        except SystemExit:  # pylint: disable=try-except-raise
            # Script called sys.exit()
            # Re-raise the exception to have the error code properly returned at the end
            raise
    finally:
        autogroup.current_autogroup = None
        if handle:
            handle.close()
