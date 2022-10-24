# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Module with utilities to interact with RabbitMQ."""

# AUTO-GENERATED

# yapf: disable
# pylint: disable=wildcard-import

from .client import *
from .defaults import *
from .launcher import *
from .utils import *

__all__ = (
    'BROKER_DEFAULTS',
    'ManagementApiConnectionError',
    'ProcessLauncher',
    'RabbitmqManagementClient',
    'get_launch_queue_name',
    'get_message_exchange_name',
    'get_rmq_url',
    'get_task_exchange_name',
)

# yapf: enable
