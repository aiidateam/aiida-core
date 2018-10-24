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
from aiida.orm.backend import Backend

from aiida.backends.djsite.queries import DjangoQueryManager
from . import authinfo
from . import computer
from . import log
from . import user


class DjangoBackend(Backend):

    def __init__(self):
        self._logs = log.DjangoLogCollection(self)
        self._users = user.DjangoUserCollection(self)
        self._authinfos = authinfo.DjangoAuthInfoCollection(self)
        self._computers = computer.DjangoComputerCollection(self)
        self._query_manager = DjangoQueryManager(self)

    @property
    def logs(self):
        return self._logs

    @property
    def users(self):
        return self._users

    @property
    def authinfos(self):
        return self._authinfos

    @property
    def computers(self):
        return self._computers

    @property
    def query_manager(self):
        return self._query_manager

    def query_builder(self):
        # For now this doesn't select the Django one because that's
        # done in the constructor of QueryBuilder but ideally this
        # should be reworked so the Django version subclasses QueryBuilder
        from aiida.orm.querybuilder import QueryBuilder
        return QueryBuilder()
