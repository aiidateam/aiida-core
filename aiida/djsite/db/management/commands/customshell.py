# -*- coding: utf-8 -*-
"""
This file was copied and edited from Django 1.5.1, and modified to allow to define default loads in ipython.

.. note: Only ipython and bpython do the auto import, not the plain shell.

.. note: This command should be updated when we upgrade to a more recent version of django.

.. todo: Move the list of commands to import from here (method get_start_namespace) to
    the settings.py module, probably.
"""
import os
from django.core.management.base import NoArgsCommand
from optparse import make_option


__author__ = "Giovanni Pizzi, Andrea Cepellotti, Riccardo Sabatini, Nicola Marzari, and Boris Kozinsky"
__copyright__ = u"Copyright (c), 2012-2014, École Polytechnique Fédérale de Lausanne (EPFL), Laboratory of Theory and Simulation of Materials (THEOS), MXC - Station 12, 1015 Lausanne, Switzerland. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file"
__version__ = "0.2.0"

class Command(NoArgsCommand):
    shells = ['ipython', 'bpython']

    option_list = NoArgsCommand.option_list + (
        make_option('--plain', action='store_true', dest='plain',
            help='Tells Django to use plain Python, not IPython or bpython.'),
        make_option('-i', '--interface', action='store', type='choice', choices=shells,
                    dest='interface',
            help='Specify an interactive interpreter interface. Available options: "ipython" and "bpython"'),

    )
    help = "Runs a Python interactive interpreter. Tries to use IPython or bpython, if one of them is available."
    requires_model_validation = False

    def get_start_namespace(self):
        user_ns = {}
        for app_mod, model_name, alias in [
            #    ("aiida.djsite.db.models","DbNode","DbNode"),
            ("aiida.orm","Node","Node"),
            ("aiida.orm","Calculation","Calculation"),
            ("aiida.orm","Code","Code"),
            ("aiida.orm","Data","Data"),
            ("aiida.orm","CalculationFactory","CalculationFactory"),
            ("aiida.orm","DataFactory","DataFactory"),
            ("aiida.orm","Computer","Computer"),
            ("aiida.orm","Group","Group"),
            ("aiida.djsite.db","models","models"),
            ]:
            user_ns[alias] = getattr(__import__(app_mod, {}, {}, model_name), model_name)
        
        return user_ns


    def ipython(self):
        user_ns = self.get_start_namespace()
        try:
            from IPython import embed
            if user_ns:
                embed(user_ns=user_ns)
            else:
                embed()
        except ImportError:
            # IPython < 0.11
            # Explicitly pass an empty list as arguments, because otherwise
            # IPython would use sys.argv from this script.
            try:
                from IPython.Shell import IPShell
                if user_ns:
                    shell = IPShell(argv=[],user_ns=user_ns)
                else:
                    shell = IPShell(argv=[])
                shell.mainloop()
            except ImportError:
                # IPython not found at all, raise ImportError
                raise

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

    def handle_noargs(self, **options):
        # XXX: (Temporary) workaround for ticket #1796: force early loading of all
        # models from installed apps.
        from django.db.models.loading import get_models
        get_models()

        use_plain = options.get('plain', False)
        interface = options.get('interface', None)

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
                readline.set_completer(rlcompleter.Completer(imported_objects).complete)
                readline.parse_and_bind("tab:complete")

            # We want to honor both $PYTHONSTARTUP and .pythonrc.py, so follow system
            # conventions and get $PYTHONSTARTUP first then .pythonrc.py.
            if not use_plain:
                for pythonrc in (os.environ.get("PYTHONSTARTUP"),
                                 os.path.expanduser('~/.pythonrc.py')):
                    if pythonrc and os.path.isfile(pythonrc):
                        try:
                            with open(pythonrc) as handle:
                                exec(compile(handle.read(), pythonrc, 'exec'))
                        except NameError:
                            pass
            code.interact(local=imported_objects)
