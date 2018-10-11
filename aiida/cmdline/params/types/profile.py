# -*- coding: utf-8 -*-
"""Profile param type for click."""
from __future__ import absolute_import
import click


class ProfileParamType(click.ParamType):
    """The profile parameter type for click."""

    name = 'profile'

    def convert(self, value, param, ctx):
        """Attempt to match the given value to a valid profile."""
        from aiida.common.exceptions import MissingConfigurationError
        from aiida.common.profile import Profile
        from aiida.common.setup import get_config

        try:
            profiles = get_config()
        except MissingConfigurationError:
            self.fail('could not load the configuration file')

        try:
            profile = profiles['profiles'][value]
        except KeyError:
            self.fail('invalid profile name {}'.format(value))

        return Profile(name=value, **profile)

    def complete(self, ctx, incomplete):  # pylint: disable=unused-argument,no-self-use
        """
        Return possible completions based on an incomplete value

        :returns: list of tuples of valid entry points (matching incomplete) and a description
        """
        from aiida.common.exceptions import MissingConfigurationError
        from aiida.common.setup import get_config

        try:
            profiles = get_config()
        except MissingConfigurationError:
            return []

        try:
            profiles = profiles['profiles']
        except KeyError:
            return []

        return [(profile, '') for profile in profiles.keys() if profile.startswith(incomplete)]
