###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Profile param type for click."""

from __future__ import annotations

import typing as t

import click
from click.shell_completion import CompletionItem

from .strings import LabelStringType

if t.TYPE_CHECKING:
    from aiida.manage.configuration import Profile

__all__ = ('ProfileParamType',)


class ProfileParamType(LabelStringType):
    """The profile parameter type for click.

    This parameter type requires the command that uses it to define the ``context_class`` class attribute to be the
    :class:`aiida.cmdline.groups.verdi.VerdiContext` class, as that is responsible for creating the user defined object
    ``obj`` on the context and loads the instance config.
    """

    name = 'profile'

    def __init__(self, *args: t.Any, **kwargs: t.Any):
        self._cannot_exist = kwargs.pop('cannot_exist', False)
        self._load_profile = kwargs.pop('load_profile', False)  # If True, will load the profile converted from value
        super().__init__(*args, **kwargs)

    @staticmethod
    def deconvert_default(value: t.Any) -> t.Any:
        return value.name

    def convert(self, value: t.Any, param: click.Parameter | None, ctx: click.Context | None) -> Profile:  # type: ignore[override]
        """Attempt to match the given value to a valid profile."""
        from aiida.common.exceptions import MissingConfigurationError, ProfileConfigurationError
        from aiida.manage.configuration import Profile, load_profile

        try:
            config = ctx.obj.config  # type: ignore[union-attr]
        except AttributeError:
            raise RuntimeError(
                'The context does not contain a user defined object with the loaded AiiDA configuration. '
                'Is your click command setting `context_class` to :class:`aiida.cmdline.groups.verdi.VerdiContext`?'
            )

        # If the value is already of the expected return type, simply return it. This behavior is new in `click==8.0`:
        # https://click.palletsprojects.com/en/8.0.x/parameters/#implementing-custom-types
        if isinstance(value, Profile):
            return value

        value = super().convert(value, param, ctx)

        try:
            profile = config.get_profile(value)
        except (MissingConfigurationError, ProfileConfigurationError) as exception:
            if not self._cannot_exist:
                self.fail(str(exception))

            # Create a new empty profile
            profile = Profile(value, {}, validate=False)
        else:
            if self._cannot_exist:
                self.fail(str(f'the profile `{value}` already exists'))

        if self._load_profile:
            load_profile(profile.name)

        ctx.obj.profile = profile  # type: ignore[union-attr]

        return profile  # type: ignore[no-any-return]

    def shell_complete(self, ctx: click.Context, param: click.Parameter, incomplete: str) -> list[CompletionItem]:
        """Return possible completions based on an incomplete value

        :returns: list of tuples of valid entry points (matching incomplete) and a description
        """
        from aiida.common.exceptions import MissingConfigurationError
        from aiida.manage.configuration import get_config

        if self._cannot_exist:
            return []

        try:
            config = get_config()
        except MissingConfigurationError:
            return []

        return [CompletionItem(profile.name) for profile in config.profiles if profile.name.startswith(incomplete)]
