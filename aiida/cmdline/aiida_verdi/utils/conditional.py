#-*- coding: utf8 -*-
"""
.. py:module::conditional
    :synopsis: Tools for options which are required only if a a set of
    conditions on the context are fulfilled
"""
import click


class ConditionalOption(click.Option):
    """
    This cli option takes an additional callable parameter and uses that
    to determine wether a MissingParam should be raised if the option is
    not given on the cli.

    The callable takes the context as an argument and can look up any
    amount of other parameter values etc.

    :param required_fn: callable(ctx) -> True | False, returns True
        if the parameter is required to have a value
    """
    def __init__(self, param_decls=None, required_fn=lambda ctx: True, **kwargs):
        self.required_fn = required_fn
        super(ConditionalOption, self).__init__(param_decls=param_decls, **kwargs)
        self.required = True

    def full_process_value(self, ctx, value):
        try:
            value = super(ConditionalOption, self).full_process_value(ctx, value)
        except click.MissingParameter as e:
            if self.is_required(ctx):
                raise e
        return value

    def is_required(self, ctx):
        """runs the given check on the context to determine requiredness"""
        return self.required_fn(ctx)
