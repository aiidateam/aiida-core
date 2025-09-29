###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Option whose requiredness is determined by a callback function."""

from __future__ import annotations

import typing as t

import click

if t.TYPE_CHECKING:
    from collections.abc import Sequence


class ConditionalOption(click.Option):
    """Option whose requiredness is determined by a callback function.

    This option takes an additional callable parameter ``required_fn`` and uses that to determine whether a
    ``MissingParameter`` exception should be raised if no value is specified for the parameters.

    The callable should take the context as an argument which it can use to inspect the value of other parameters that
    have been passed to the command invocation.

    :param required_fn: callable(ctx) -> True | False, returns True if the parameter is required to have a value. This
        is typically used when the condition depends on other parameters specified on the command line.
    """

    def __init__(
        self,
        param_decls: Sequence[str] | None = None,
        required_fn: t.Callable[[click.Context], bool] | None = None,
        **kwargs: t.Any,
    ):
        self.required_fn = required_fn

        # If there is not callback to determine requiredness, assume the option is not required.
        if required_fn is not None:
            self.required = False

        super().__init__(param_decls=param_decls, **kwargs)

    def process_value(self, ctx: click.Context, value: t.Any) -> t.Any:
        try:
            value = super().process_value(ctx, value)
        except click.MissingParameter:
            if self.is_required(ctx):
                raise
        else:
            if self.required_fn and self.value_is_missing(value) and self.is_required(ctx):
                raise click.MissingParameter(ctx=ctx, param=self)

        return value

    def is_required(self, ctx: click.Context) -> bool:
        """Runs the given check on the context to determine requiredness"""
        if self.required_fn:
            return self.required_fn(ctx)

        return self.required
