# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Module defining the properties of additional metadata to be stored in the authinfo."""


def validate_positive_number(ctx, param, value):  # pylint: disable=unused-argument
    """Validate that the number passed to this parameter is a positive number.

    :param ctx: the `click.Context`
    :param param: the parameter
    :param value: the value passed for the parameter
    :raises `click.BadParameter`: if the value is not a positive number
    """
    if not isinstance(value, (int, float)) or value < 0:
        from click import BadParameter
        raise BadParameter('{} is not a valid positive number'.format(value))


PROPERTY_SCHEDULER_POLL_INTERVAL = 'scheduler_poll_interval'  # pylint: disable=invalid-name
PROPERTY_SAFE_OPEN_INTERVAL = 'safe_open_interval'  # pylint: disable=invalid-name

# These are directly piped to Click
# These are defined hee so that these can be imported also without importing
# aiida.orm, needed for Click.
# Note that if you add a new COMMON_AUTHINFO_OPTION, its default MUST BE defined
# in the `get_default_for_metadata_field` inside the AuthInfo class
# (it is there because it can use information from the instance, e.g. to use
# transport-dependent defaults)
COMMON_AUTHINFO_OPTIONS = [
    (
        PROPERTY_SAFE_OPEN_INTERVAL, {
            'type': float,
            'prompt': 'Connection safe interval (s)',
            'help': 'Minimum time interval in seconds between consecutive connection openings',
            'callback': validate_positive_number,
            'non_interactive_default': True
        }
    ),
    (
        PROPERTY_SCHEDULER_POLL_INTERVAL, {
            'type': float,
            'prompt': 'Queue poll interval (s)',
            'help': 'Minimum time interval in seconds between consecutive pollings of the job scheduler queue status',
            'callback': validate_positive_number,
            'non_interactive_default': True
        }
    ),
]
