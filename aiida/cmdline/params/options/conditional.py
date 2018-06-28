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
    to determine weather a MissingParam should be raised if the option is
    not given on the cli.

    The callable takes the context as an argument and can look up any
    amount of other parameter values etc.

    :param required_fn: callable(ctx) -> True | False, returns True
        if the parameter is required to have a value.
        This is typically used when the condition depends on other
        parameters specified on the command line.
    """

    def __init__(self, param_decls=None, required_fn=None, **kwargs):

        # note default behaviour for required: False
        self.required_fn = required_fn

        # Required_fn overrides 'required', if defined
        if required_fn is not None:
            # There is a required_fn
            self.required = False  # So it does not show up as 'required'

        super(ConditionalOption, self).__init__(param_decls=param_decls, **kwargs)

    def full_process_value(self, ctx, value):
        try:
            value = super(ConditionalOption, self).full_process_value(ctx, value)
            if self.required_fn and self.value_is_missing(value):
                if self.is_required(ctx):
                    raise click.MissingParameter(ctx=ctx, param=self)
        except click.MissingParameter as err:
            if self.is_required(ctx):
                raise
        return value

    def is_required(self, ctx):
        """runs the given check on the context to determine requiredness"""

        if self.required_fn:
            return self.required_fn(ctx)
        else:
            return self.required
