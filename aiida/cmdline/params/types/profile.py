# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Profile param type for click."""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import
import click


class ProfileParamType(click.ParamType):
    """The profile parameter type for click."""

    name = 'profile'

    def convert(self, value, param, ctx):
        """Attempt to match the given value to a valid profile."""
        from aiida.common.exceptions import MissingConfigurationError, ProfileConfigurationError
        from aiida.manage.configuration import get_config

        try:
            config = get_config()
            profile = config.get_profile(value)
        except (MissingConfigurationError, ProfileConfigurationError) as exception:
            self.fail(str(exception))

        return profile

    def complete(self, ctx, incomplete):  # pylint: disable=unused-argument,no-self-use
        """
        Return possible completions based on an incomplete value

        :returns: list of tuples of valid entry points (matching incomplete) and a description
        """
        from aiida.common.exceptions import MissingConfigurationError
        from aiida.manage.configuration import get_config

        try:
            config = get_config()
        except MissingConfigurationError:
            return []

        return [(profile.name, '') for profile in config.profiles if profile.name.startswith(incomplete)]
