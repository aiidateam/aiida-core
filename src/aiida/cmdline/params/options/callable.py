###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""A monkey-patched subclass of click.Option that does not evaluate callable default during tab completion."""

import typing as t

import click

__all__ = ('CallableDefaultOption',)


class CallableDefaultOption(click.Option):
    """A monkeypatch for click.Option that does not evaluate default callbacks during tab completion

    This is a temporary solution until a proper fix is implemented in click, see:
    https://github.com/pallets/click/issues/2614
    """

    def get_default(self, ctx: click.Context, call: bool = True) -> t.Optional[t.Union[t.Any, t.Callable[[], t.Any]]]:
        """Return default unless in tab-completion context."""
        if ctx.resilient_parsing:
            return None
        return super().get_default(ctx=ctx, call=call)
