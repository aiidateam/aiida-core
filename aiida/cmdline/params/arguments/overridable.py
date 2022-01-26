# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""
.. py:module::overridable
    :synopsis: Convenience class which can be used to defined a set of commonly used arguments that
        can be easily reused and which improves consistency across the command line interface
"""
import click

__all__ = ('OverridableArgument',)


class OverridableArgument:
    """
    Wrapper around click.argument that increases reusability

    Once defined, the argument can be reused with a consistent name and sensible defaults while
    other details can be customized on a per-command basis

    Example::

        @click.command()
        @CODE('code')
        def print_code_pk(code):
            click.echo(code.pk)

        @click.command()
        @CODE('codes', nargs=-1)
        def print_code_pks(codes):
            click.echo([c.pk for c in codes])

    Notice that the arguments, which are used to define the name of the argument and based on which
    the function argument name is determined, can be overriden
    """

    def __init__(self, *args, **kwargs):
        """
        Store the default args and kwargs
        """
        self.args = args
        self.kwargs = kwargs

    def __call__(self, *args, **kwargs):
        """
        Override the stored kwargs with the passed kwargs and return the argument, using the stored args
        only if they are not provided. This allows the user to override the variable name, which is
        useful if for example they want to allow multiple value with nargs=-1 and want to pluralize
        the function argument for consistency
        """
        kw_copy = self.kwargs.copy()
        kw_copy.update(kwargs)

        if args:
            return click.argument(*args, **kw_copy)

        return click.argument(*self.args, **kw_copy)
