# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
from aiida.orm.backend import Backend
from aiida.orm.implementation.django.log import DjangoLog


class DjangoBackend(Backend):
    def __init__(self):
        self._log = DjangoLog()

    @property
    def log(self):
        return self._log
