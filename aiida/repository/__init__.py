# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Module with resources dealing with the file repository."""
# pylint: disable=undefined-variable
from .backend import *
from .file_system import *

__all__ = (backend.__all__ + file_system.__all__)  # type: ignore[name-defined]
