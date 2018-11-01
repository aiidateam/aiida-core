# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Methods to create, get and set global components for communication with RabbitMQ."""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from .communicators import create_communicator, get_communicator, set_communicator
from .controllers import create_controller, get_controller, set_controller

__all__ = [
    'create_communicator', 'get_communicator', 'set_communicator', 'create_controller', 'get_controller',
    'set_controller'
]
