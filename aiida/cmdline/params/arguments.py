# -*- coding: utf-8 -*-
import click

from . import types


class OverridableArgument(object):
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
        else:
        	return click.argument(*self.args, **kw_copy)


CODE = OverridableArgument('code', type=types.CodeParam())
COMPUTER = OverridableArgument('code', type=types.ComputerParam())
GROUP = OverridableArgument('group', type=types.GroupParam())
NODE = OverridableArgument('node', type=types.NodeParam())
