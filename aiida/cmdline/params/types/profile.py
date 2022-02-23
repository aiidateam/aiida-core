# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Profile param type for click."""
from click.shell_completion import CompletionItem

from .strings import LabelStringType

__all__ = ('ProfileParamType',)


class ProfileParamType(LabelStringType):
    """The profile parameter type for click."""

    name = 'profile'

    def __init__(self, *args, **kwargs):
        self._cannot_exist = kwargs.pop('cannot_exist', False)
        self._load_profile = kwargs.pop('load_profile', False)  # If True, will load the profile converted from value
        super().__init__(*args, **kwargs)

    @staticmethod
    def deconvert_default(value):
        return value.name

    def convert(self, value, param, ctx):
        """Attempt to match the given value to a valid profile."""
        from aiida.common import extendeddicts
        from aiida.common.exceptions import MissingConfigurationError, ProfileConfigurationError
        from aiida.manage.configuration import Profile, get_config, load_profile

        # If the value is already of the expected return type, simply return it. This behavior is new in `click==8.0`:
        # https://click.palletsprojects.com/en/8.0.x/parameters/#implementing-custom-types
        if isinstance(value, Profile):
            return value

        value = super().convert(value, param, ctx)

        try:
            config = get_config(create=True)
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

        if ctx.obj is None:
            ctx.obj = extendeddicts.AttributeDict()

        ctx.obj.config = config
        ctx.obj.profile = profile

        return profile

    def shell_complete(self, ctx, param, incomplete):  # pylint: disable=unused-argument,no-self-use
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
