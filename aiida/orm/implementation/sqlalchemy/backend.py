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
from aiida.orm.implementation.backends import Backend

from aiida.backends.sqlalchemy.queries import SqlaQueryManager
from aiida.backends.sqlalchemy.querybuilder_sqla import QueryBuilderImplSQLA
from . import authinfo
from . import computer
from . import log
from . import user


class SqlaBackend(Backend):

    def __init__(self):
        self._logs = log.SqlaLogCollection(self, log.SqlaLog)
        self._users = user.SqlaUserCollection(self, user.SqlaUser)
        self._authinfos = authinfo.SqlaAuthInfoCollection(self, authinfo.SqlaAuthInfo)
        self._computers = computer.SqlaComputerCollection(self)
        self._query_manager = SqlaQueryManager(self)

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

    def query(self):
        return QueryBuilderImplSQLA()
