# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""The verdi shell command"""

import os

import click

from aiida.cmdline.commands.cmd_verdi import verdi
from aiida.cmdline.utils import decorators, echo
from aiida.cmdline.utils.shell import AVAILABLE_SHELLS, run_shell


@verdi.command('shell')
@decorators.with_dbenv()
@click.option('--plain', is_flag=True, help='Use a plain Python shell.')
@click.option(
    '--no-startup',
    is_flag=True,
    help='When using plain Python, ignore the PYTHONSTARTUP environment variable and ~/.pythonrc.py script.'
)
@click.option(
    '-i',
    '--interface',
    type=click.Choice(AVAILABLE_SHELLS.keys()),
    help='Specify an interactive interpreter interface.'
)
def shell(plain, no_startup, interface):
    """Start a python shell with preloaded AiiDA environment."""

    try:
        if plain:
            # Don't bother loading IPython, because the user wants plain Python.
            raise ImportError

        # If a non-plain python interpreter is requested, check that there is at least one type of shell available
        if not AVAILABLE_SHELLS:
            echo.echo_critical('No shells are available')

        run_shell(interface=interface)
    except ImportError:
        import code

        # Set up a dictionary to serve as the environment for the shell, so
        # that tab completion works on objects that are imported at runtime.
        # See ticket 5082.
        imported_objects = {}
        try:  # Try activating rlcompleter, because it's handy.
            import readline
        except ImportError:
            pass
        else:
            # We don't have to wrap the following import in a 'try', because
            # we already know 'readline' was imported successfully.
            import rlcompleter

            readline.set_completer(rlcompleter.Completer(imported_objects).complete)
            readline.parse_and_bind('tab:complete')

        # We want to honor both $PYTHONSTARTUP and .pythonrc.py, so follow system
        # conventions and get $PYTHONSTARTUP first then .pythonrc.py.
        if not no_startup:
            for pythonrc in (os.environ.get('PYTHONSTARTUP'), '~/.pythonrc.py'):
                if not pythonrc:
                    continue
                pythonrc = os.path.expanduser(pythonrc)
                if not os.path.isfile(pythonrc):
                    continue
                try:
                    with open(pythonrc, encoding='utf8') as handle:
                        exec(compile(handle.read(), pythonrc, 'exec'), imported_objects)  # pylint: disable=exec-used
                except NameError:
                    pass

        # The pylint disabler is necessary because the builtin code module
        # clashes with the local commands.code module here.
        code.interact(local=imported_objects)  # pylint: disable=no-member
