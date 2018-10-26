# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Definition of modules that are to be automatically loaded for `verdi shell`."""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

DEFAULT_MODULES_LIST = [
    ('aiida.orm', 'Node', 'Node'),
    ('aiida.orm', 'Calculation', 'Calculation'),
    ('aiida.orm', 'load_workflow', 'load_workflow'),
    ('aiida.orm', 'JobCalculation', 'JobCalculation'),
    ('aiida.orm', 'Data', 'Data'),
    ('aiida.orm', 'CalculationFactory', 'CalculationFactory'),
    ('aiida.orm', 'DataFactory', 'DataFactory'),
    ('aiida.orm', 'WorkflowFactory', 'WorkflowFactory'),
    ('aiida.orm', 'Code', 'Code'),
    ('aiida.orm', 'Computer', 'Computer'),
    ('aiida.orm', 'Group', 'Group'),
    ('aiida.orm.workflow', 'Workflow', 'Workflow'),
    ('aiida.orm', 'QueryBuilder', 'QueryBuilder'),
    ('aiida.orm.utils', 'load_node', 'load_node'),
]


def ipython():
    """Start any version of IPython"""
    for ipy_version in (_ipython, _ipython_pre_100, _ipython_pre_011):
        try:
            ipy_version()
        except ImportError:
            pass
        else:
            return

    raise ImportError('No IPython available')


def bpython():
    """Start a bpython shell."""
    import bpython as bpy_shell  # pylint: disable=import-error

    user_ns = get_start_namespace()
    if user_ns:
        bpy_shell.embed(user_ns)
    else:
        bpy_shell.embed()


AVAILABLE_SHELLS = {'ipython': ipython, 'bpython': bpython}


def run_shell(interface=None):
    """Start the chosen external shell."""

    available_shells = [AVAILABLE_SHELLS[interface]] if interface else AVAILABLE_SHELLS.values()

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


def get_start_namespace():
    """Load all default and custom modules"""
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
    from IPython import start_ipython  # pylint: disable=import-error,no-name-in-module

    user_ns = get_start_namespace()
    if user_ns:
        start_ipython(argv=[], user_ns=user_ns)
    else:
        start_ipython(argv=[])
