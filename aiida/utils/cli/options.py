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
import click
from . import validators


class overridable_option(object):
    """
    Wrapper around click option that allows to store the name
    and some defaults but also to override them later, for example
    to change the help message for a certain command.
    """

    def __init__(self, *args, **kwargs):
        """
        Store the defaults
        """
        self.args = args
        self.kwargs = kwargs

    def __call__(self, *args, **kwargs):
        """
        Override args if passed and update the kwargs and return the click.option
        If a callback is specified in the kwargs make sure to bind the callback_kwargs
        to it using the partial lambda construct of functools
        """
        import functools

        if not args:
            args_copy = self.args
        else:
            args_copy = args

        kw_copy = self.kwargs.copy()
        kw_copy.update(kwargs)

        # Pop the optional callback_kwargs if present
        callback_kwargs = kw_copy.pop('callback_kwargs', {})

        if 'callback' in kw_copy:
            callback_plain = kw_copy['callback']
            callback_bound = functools.partial(callback_plain, callback_kwargs)
            kw_copy['callback'] = callback_bound

        return click.option(*args_copy, **kw_copy)


code = overridable_option(
    '-c', '--code', type=click.STRING, required=True,
    callback=validators.validate_code,
    help='the label of the AiiDA code object to use'
)


structure = overridable_option(
    '-s', '--structure', type=click.INT, required=True,
    callback=validators.validate_structure,
    help='the pk of a structure node'
)


pseudo_family = overridable_option(
    '-p', '--pseudo-family', type=click.STRING, required=True,
    callback=validators.validate_pseudo_family,
    help='the name of the pseudo potential family to use'
)


kpoint_mesh = overridable_option(
    '-k', '--kpoint-mesh', 'kpoints', nargs=3, type=click.INT, default=[2, 2, 2], show_default=True,
    callback=validators.validate_kpoint_mesh,
    help='the number of points in the kpoint mesh along each basis vector'
)


calculation = overridable_option(
    '-C', '--calculation', type=click.INT, required=True,
    callback=validators.validate_calculation,
    help='the pk of a calculation node'
)


max_num_machines = overridable_option(
    '-m', '--max-num-machines', type=click.INT, default=1, show_default=True,
    help='the maximum number of machines (nodes) to use for the calculations'
)


max_wallclock_seconds = overridable_option(
    '-w', '--max-wallclock-seconds', type=click.INT, default=1800, show_default=True,
    help='the maximum wallclock time in seconds to set for the calculations'
)


daemon = overridable_option(
    '-d', '--daemon', is_flag=True, default=False, show_default=True,
    help='submit the workchain to the daemon instead of running it locally'
)


group = overridable_option(
    '-g', '--group', type=click.STRING, required=True,
    callback=validators.validate_group,
    help='the name or pk of a Group'
)