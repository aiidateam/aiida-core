# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# pylint: disable=undefined-variable,wildcard-import
"""
A module to bring together the different parts of AiiDA:

  * configuration file
  * profile
  * daemon runners
  * process controllers
  * RabbitMQ communicators

"""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from .configuration import *
from .manager import *

__all__ = (configuration.__all__ + manager.__all__)
