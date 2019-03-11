# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Generic backend related objects"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import abc
import typing

from .. import backends

__all__ = ('SqlBackend',)

# The template type for the base ORM model type
ModelType = typing.TypeVar('ModelType')  # pylint: disable=invalid-name


class SqlBackend(typing.Generic[ModelType], backends.Backend):
    """
    A class for SQL based backends.  Assumptions are that:
        * there is an ORM
        * that it is possible to convert from ORM model instances to backend instances
        * that psycopg2 is used as the engine

    if any of these assumptions do not fit then just implement a backend from :class:`aiida.orm.implementation.Backend`
    """

    @abc.abstractmethod
    def get_backend_entity(self, model):
        """
        Return the backend entity that corresponds to the given Model instance

        :param model: the ORM model instance to promote to a backend instance
        :return: the backend entity corresponding to the given model
        :rtype: :class:`aiida.orm.implementation.BackendEntity`
        """

    @abc.abstractmethod
    def cursor(self):
        """
        Return a psycopg cursor.  This method should be used as a context manager i.e.::

            with backend.cursor():
                # Do stuff

        :return: a psycopg cursor
        :rtype: :class:`psycopg2.extensions.cursor`
        """

    @abc.abstractmethod
    def execute_raw(self, query):
        """Execute a raw SQL statement and return the result.

        :param query: a string containing a raw SQL statement
        :return: the result of the query
        """

    def execute_prepared_statement(self, sql, parameters):
        """Execute an SQL statement with optional prepared statements.

        :param sql: the SQL statement string
        :param parameters: dictionary to use to populate the prepared statement
        """
        results = []

        with self.cursor() as cursor:
            cursor.execute(sql, parameters)

            for row in cursor:
                results.append(row)

        return results
