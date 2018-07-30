# -*- coding: utf-8 -*-
"""The verdi shell command"""
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
from __future__ import absolute_import

import os
import click

from aiida.cmdline.commands import verdi
from aiida.cmdline.utils import decorators, echo


def get_start_namespace():
    """Load all default and custom modules"""
    from aiida.cmdline.utils.shell import DEFAULT_MODULES_LIST
    from aiida.common.setup import get_property

    user_ns = {}
    # load default modules
    for app_mod, model_name, alias in DEFAULT_MODULES_LIST:
        user_ns[alias] = getattr(__import__(app_mod, {}, {}, model_name), model_name)

    # load custom modules
    custom_modules_list = [
        (str(e[0]), str(e[2]))
        for e in [p.rpartition('.') for p in get_property('verdishell.modules', default="").split(':')]
        if e[1] == '.'
    ]

    for app_mod, model_name in custom_modules_list:
        try:
            user_ns[model_name] = getattr(__import__(app_mod, {}, {}, model_name), model_name)
        except AttributeError:
            # if the module does not exist, we ignore it
            pass

    return user_ns


def _ipython_pre_011():
    """Start IPython pre-0.11"""
    from IPython.Shell import IPShell  # pylint: disable=import-error,no-name-in-module

    user_ns = get_start_namespace()
    if user_ns:
        ipy_shell = IPShell(argv=[], user_ns=user_ns)
    else:
        ipy_shell = IPShell(argv=[])
    ipy_shell.mainloop()


def _ipython_pre_100():
    """Start IPython pre-1.0.0"""
    from IPython.frontend.terminal.ipapp import TerminalIPythonApp  # pylint: disable=import-error,no-name-in-module

    app = TerminalIPythonApp.instance()
    app.initialize(argv=[])
    user_ns = get_start_namespace()
    if user_ns:
        app.shell.user_ns.update(user_ns)
    app.start()


def _ipython():
    """Start IPython >= 1.0"""
    from IPython import start_ipython  # pylint: disable=import-error

    user_ns = get_start_namespace()
    if user_ns:
        start_ipython(argv=[], user_ns=user_ns)
    else:
        start_ipython(argv=[])


def ipython():
    """Start any version of IPython"""
    for ipy_version in (_ipython, _ipython_pre_100, _ipython_pre_011):
        try:
            ipy_version()
        except ImportError:
            pass
        else:
            return
    # no IPython, raise ImportError
    raise ImportError("No IPython")


def bpython():
    """Start a bpython shell."""
    import bpython as bpy_shell  # pylint: disable=import-error

    user_ns = get_start_namespace()
    if user_ns:
        bpy_shell.embed(user_ns)
    else:
        bpy_shell.embed()


SHELLS = {'ipython': ipython, 'bpython': bpython}


@verdi.command('shell')
@decorators.with_dbenv()
@click.option('--plain', is_flag=True, help='Tells Django to use plain Python, not IPython or bpython.)')
@click.option(
    '--no-startup',
    is_flag=True,
    help='When using plain Python, ignore the PYTHONSTARTUP environment '
    'variable and ~/.pythonrc.py script.')
@click.option(
    '-i', '--interface', type=click.Choice(SHELLS.keys()), help='Specify an interactive interpreter interface.')
def shell(plain, no_startup, interface):
    """Start a python shell with preloaded AiiDA environment."""

    def run_shell(interface=None):
        """Start the chosen external shell."""

        # Check that there is at least one type of shell declared
        if not SHELLS:
            echo.echo_critical("No shells are available")

        available_shells = [SHELLS[interface]] if interface else SHELLS.values()

        # Try the specified or the available shells one by one until you
        # find one that is available. If the wanted shell is not available
        # then an ImportError is raised leading the the loading of a generic
        # shell.
        for curr_shell in available_shells:
            try:
                curr_shell()
                return
            except ImportError:
                pass
        raise ImportError

    try:
        if plain:
            # Don't bother loading IPython, because the user wants plain Python.
            raise ImportError

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
            readline.parse_and_bind("tab:complete")

        # We want to honor both $PYTHONSTARTUP and .pythonrc.py, so follow system
        # conventions and get $PYTHONSTARTUP first then .pythonrc.py.
        if not no_startup:
            for pythonrc in (os.environ.get("PYTHONSTARTUP"), '~/.pythonrc.py'):
                if not pythonrc:
                    continue
                pythonrc = os.path.expanduser(pythonrc)
                if not os.path.isfile(pythonrc):
                    continue
                try:
                    with open(pythonrc) as handle:
                        exec (compile(handle.read(), pythonrc, 'exec'), imported_objects)  # pylint: disable=exec-used
                except NameError:
                    pass
        # The pylint disabler is necessary because the builtin code module
        # clashes with the local commands.code module here.
        code.interact(local=imported_objects)  # pylint: disable=no-member
