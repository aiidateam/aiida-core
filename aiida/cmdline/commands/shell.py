# -*- coding: utf-8 -*-
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

from aiida.cmdline.baseclass import VerdiCommand



default_modules_list = [
    ("aiida.orm", "Node", "Node"),
    ("aiida.orm.utils", "load_node", "load_node"),
    ("aiida.orm", "Calculation", "Calculation"),
    ("aiida.orm", "JobCalculation", "JobCalculation"),
    ("aiida.orm.code", "Code", "Code"),
    ("aiida.orm", "Data", "Data"),
    ("aiida.orm", "CalculationFactory", "CalculationFactory"),
    ("aiida.orm", "DataFactory", "DataFactory"),
    ("aiida.orm", "WorkflowFactory", "WorkflowFactory"),
    ("aiida.orm.computer", "Computer", "Computer"),
    ("aiida.orm.group", "Group", "Group"),
    ("aiida.orm.workflow", "Workflow", "Workflow"),
    ("aiida.orm", "load_workflow", "load_workflow"),
    ("aiida.orm.querybuilder", "QueryBuilder", "QueryBuilder"),
    # ("aiida.backends.djsite.db", "models", "models"),
    # ("aiida.backends.sqlalchemy", "models", "models"),
]

class Shell(VerdiCommand):
    """
    Run the interactive shell with the AiiDA environment loaded.

    This command opens an ipython shell with the AiiDA environment loaded.
    """

    shells = ['ipython', 'bpython']

    def get_start_namespace(self):
        """Load all default and custom modules"""
        from aiida import load_dbenv, is_dbenv_loaded
        from aiida.backends import settings
        if not is_dbenv_loaded():
            load_dbenv(profile=settings.AIIDADB_PROFILE)

        from aiida.common.setup import get_property
        user_ns = {}
        # load default modules
        for app_mod, model_name, alias in default_modules_list:
            user_ns[alias] = getattr(__import__(app_mod, {}, {},
                                                model_name), model_name)

        # load custom modules
        custom_modules_list = [(str(e[0]), str(e[2])) for e in
                               [p.rpartition('.') for p in get_property(
                                   'verdishell.modules', default="").split(
                                   ':')]
                               if e[1] == '.']

        for app_mod, model_name in custom_modules_list:
            try:
                user_ns[model_name] = getattr(
                    __import__(app_mod, {}, {}, model_name), model_name)
            except AttributeError:
                # if the module does not exist, we ignore it
                pass

        return user_ns

    def _ipython_pre_011(self):
        """Start IPython pre-0.11"""
        from IPython.Shell import IPShell

        user_ns = self.get_start_namespace()
        if user_ns:
            shell = IPShell(argv=[], user_ns=user_ns)
        else:
            shell = IPShell(argv=[])
        shell.mainloop()

    def _ipython_pre_100(self):
        """Start IPython pre-1.0.0"""
        from IPython.frontend.terminal.ipapp import TerminalIPythonApp

        app = TerminalIPythonApp.instance()
        app.initialize(argv=[])
        user_ns = self.get_start_namespace()
        if user_ns:
            app.shell.user_ns.update(user_ns)
        app.start()

    def _ipython(self):
        """Start IPython >= 1.0"""
        from IPython import start_ipython

        user_ns = self.get_start_namespace()
        if user_ns:
            start_ipython(argv=[], user_ns=user_ns)
        else:
            start_ipython(argv=[])

    def ipython(self):
        """Start any version of IPython"""
        for ip in (
        self._ipython, self._ipython_pre_100, self._ipython_pre_011):
            try:
                ip()
            except ImportError as ie:
                pass
            else:
                return
        # no IPython, raise ImportError
        raise ImportError("No IPython")

    def bpython(self):
        import bpython

        user_ns = self.get_start_namespace()
        if user_ns:
            bpython.embed(user_ns)
        else:
            bpython.embed()

    def run_shell(self, shell=None):
        available_shells = [shell] if shell else self.shells

        for shell in available_shells:
            try:
                return getattr(self, shell)()
            except ImportError:
                pass
        raise ImportError

    def handle_noargs(self, *args):
        import argparse
        parser = argparse.ArgumentParser(prog='verdi shell')

        parser.add_argument('--plain', dest='plain', action='store_true',
                            help='Tells Django to use plain Python, not '
                                 'IPython or bpython.)')

        parser.add_argument('--no-startup', action='store_true',
                            dest='no_startup',
                            help='When using plain Python, ignore the '
                                 'PYTHONSTARTUP environment variable and '
                                 '~/.pythonrc.py script.')

        parser.add_argument('-i', '--interface', action='store',
                            choices=self.shells, dest='interface',
                            help='Specify an interactive interpreter '
                                 'interface. Available options: "ipython" '
                                 'and "bpython"')

        parsed_args = parser.parse_args(args)

        use_plain = parsed_args.plain
        no_startup = parsed_args.no_startup
        interface = parsed_args.interface

        try:
            if use_plain:
                # Don't bother loading IPython, because the user wants plain Python.
                raise ImportError

            self.run_shell(shell=interface)
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

                readline.set_completer(
                    rlcompleter.Completer(imported_objects).complete)
                readline.parse_and_bind("tab:complete")

            # We want to honor both $PYTHONSTARTUP and .pythonrc.py, so follow system
            # conventions and get $PYTHONSTARTUP first then .pythonrc.py.
            if not no_startup:
                for pythonrc in (
                        os.environ.get("PYTHONSTARTUP"), '~/.pythonrc.py'):
                    if not pythonrc:
                        continue
                    pythonrc = os.path.expanduser(pythonrc)
                    if not os.path.isfile(pythonrc):
                        continue
                    try:
                        with open(pythonrc) as handle:
                            exec (compile(handle.read(), pythonrc, 'exec'),
                                  imported_objects)
                    except NameError:
                        pass
            code.interact(local=imported_objects)

    def run(self, *args):
        # pass_to_django_manage([execname, 'customshell'] + list(args))
        self.handle_noargs(*args)

    def complete(self, subargs_idx, subargs):
        # disable further completion
        print ""
