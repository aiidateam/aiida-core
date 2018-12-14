# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from contextlib import contextmanager

from django.db import models, transaction

from aiida.backends.djsite.queries import DjangoQueryManager
from aiida.orm.implementation.sql import SqlBackend

from . import authinfo
from . import comments
from . import computer
from . import convert
from . import groups
from . import logs
from . import querybuilder
from . import users

__all__ = ('DjangoBackend',)


class DjangoBackend(SqlBackend[models.Model]):

    def __init__(self):
        self._authinfos = authinfo.DjangoAuthInfoCollection(self)
        self._comments = comments.DjangoCommentCollection(self)
        self._computers = computer.DjangoComputerCollection(self)
        self._groups = groups.DjangoGroupCollection(self)
        self._logs = logs.DjangoLogCollection(self)
        self._query_manager = DjangoQueryManager(self)
        self._users = users.DjangoUserCollection(self)

    def migrate(self):
        from aiida.backends.djsite.utils import migrate_database
        migrate_database()

    @property
    def authinfos(self):
        return self._authinfos

    @property
    def comments(self):
        return self._comments

    @property
    def computers(self):
        return self._computers

    @property
    def groups(self):
        return self._groups

    @property
    def logs(self):
        return self._logs

    @property
    def query_manager(self):
        return self._query_manager

    def query(self):
        return querybuilder.DjangoQueryBuilder(self)

    @property
    def users(self):
        return self._users

    def get_backend_entity(self, model):
        return convert.get_backend_entity(model, self)

    def get_connection(self):
        """
        Get the Django connection

        :return: the django connection
        """
        # For now we just return the global but if we ever support multiple Django backends
        # being loaded this should be specific to this backend
        from django.db import connection
        return connection

    def execute_raw(self, query):
        with self.cursor() as cursor:
            cursor.execute(query)
            results = cursor.fetchall()

        return results

    @contextmanager
    def cursor(self):
        try:
            yield self.get_connection().cursor()
        finally:
            pass

    def transaction(self):
        return transaction.atomic()
