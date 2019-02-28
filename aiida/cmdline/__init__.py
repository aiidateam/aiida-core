# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# pylint: disable=wildcard-import,undefined-variable
"""The command line interface of AiiDA."""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from .params.arguments import *
from .params.options import *
from .params.types import *
from .utils.decorators import *
from .utils.echo import *

__all__ = (params.arguments.__all__ + params.options.__all__ + params.types.__all__ + utils.decorators.__all__ +
           utils.echo.__all__)
