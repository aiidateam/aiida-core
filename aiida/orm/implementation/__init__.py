# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from aiida.backends.profile import BACKEND_DJANGO, BACKEND_SQLA
from aiida.backends.settings import BACKEND
from aiida.common.exceptions import ConfigurationError

from .authinfos import *
from .backends import *
from .comments import *
from .computers import *
from .groups import *
from .logs import *
from .querybuilder import *
from .users import *

_local = 'Node', 'delete_code',

__all__ = (_local +
           authinfos.__all__ +
           backends.__all__ +
           comments.__all__ +
           computers.__all__ +
           groups.__all__ +
           logs.__all__ +
           querybuilder.__all__ +
           users.__all__)

if BACKEND == BACKEND_SQLA:
    from aiida.orm.implementation.sqlalchemy.node import Node
    from aiida.orm.implementation.sqlalchemy.code import delete_code
elif BACKEND == BACKEND_DJANGO:
    from aiida.orm.implementation.django.node import Node
    from aiida.orm.implementation.django.code import delete_code
elif BACKEND is None:
    raise ConfigurationError("settings.BACKEND has not been set.\n"
                             "Hint: Have you called aiida.load_dbenv?")
else:
    raise ConfigurationError("Unknown settings.BACKEND: {}".format(
        BACKEND))
