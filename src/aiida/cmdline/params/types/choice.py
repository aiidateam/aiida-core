###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""A custom click type that defines a lazy choice"""

from __future__ import annotations

import typing as t

import click

from .._shims import shim_add_ctx

if t.TYPE_CHECKING:
    from collections.abc import Sequence

__all__ = ('LazyChoice',)

T = t.TypeVar('T')


class LazyChoice(click.ParamType, t.Generic[T]):
    """This is a delegate of click's Choice ParamType that evaluates the set of choices
    lazily. This is useful if the choices set requires an import that is slow. Using
    the vanilla click.Choice will call this on import which will slow down verdi and
    its autocomplete. This type will generate the choices set lazily through the
    choices property
    """

    name = 'choice'

    def __init__(self, get_choices: t.Callable[[], t.Iterable[T]]):
        """Construct a new instance."""
        if not callable(get_choices):
            raise TypeError(f"Must pass a callable, got '{get_choices}'")

        super().__init__()
        self._get_choices = get_choices
        self.__click_choice: click.Choice[T] | None = None

    @property
    def _click_choice(self) -> click.Choice[T]:
        """Get the internal click Choice object that we delegate functionality to.
        Will construct it lazily if necessary.

        :return: The click Choice
        :rtype: :class:`click.Choice`
        """
        if self.__click_choice is None:
            self.__click_choice = click.Choice(self._get_choices())
        return self.__click_choice

    @property
    def choices(self) -> Sequence[T]:
        return self._click_choice.choices

    @shim_add_ctx
    def get_metavar(self, param: click.Parameter, ctx: click.Context | None) -> str | None:
        if ctx is not None:
            return self._click_choice.get_metavar(param, ctx)
        else:
            return self._click_choice.get_metavar(param)  # type: ignore[call-arg]

    @shim_add_ctx
    def get_missing_message(self, param: click.Parameter, ctx: click.Context | None) -> str:
        if ctx is not None:
            return self._click_choice.get_missing_message(param, ctx)
        else:
            return self._click_choice.get_missing_message(param)  # type: ignore[call-arg]

    def convert(self, value: t.Any, param: click.Parameter | None, ctx: click.Context | None) -> t.Any:
        return self._click_choice.convert(value, param, ctx)

    def __repr__(self) -> str:
        if self.__click_choice is None:
            return 'LazyChoice(UNINITIALISED)'

        return f'LazyChoice({list(self.choices)!r})'
