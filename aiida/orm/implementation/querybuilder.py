# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Backend query implementation classes"""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import
import abc
import six

from aiida.common.utils import abstractclassmethod

__all__ = ('BackendQueryBuilder',)


@six.add_metaclass(abc.ABCMeta)
class BackendQueryBuilder(object):
    """Backend query builder interface"""

    # pylint: disable=invalid-name

    @abc.abstractmethod
    def Node(self):
        """
        Decorated as a property, returns the implementation for DbNode.
        It needs to return a subclass of sqlalchemy.Base, which means that for different ORM's
        a corresponding dummy-model  must be written.
        """
        pass

    @abc.abstractmethod
    def Link(self):
        """
        A property, decorated with @property. Returns the implementation for the DbLink
        """
        pass

    @abc.abstractmethod
    def Computer(self):
        """
        A property, decorated with @property. Returns the implementation for the Computer
        """
        pass

    @abc.abstractmethod
    def User(self):
        """
        A property, decorated with @property. Returns the implementation for the User
        """
        pass

    @abc.abstractmethod
    def Group(self):
        """
        A property, decorated with @property. Returns the implementation for the Group
        """
        pass

    @abc.abstractmethod
    def AuthInfo(self):
        """
        A property, decorated with @property. Returns the implementation for the Group
        """
        pass

    @abc.abstractmethod
    def table_groups_nodes(self):
        """
        A property, decorated with @property. Returns the implementation for the many-to-many
        relationship between group and nodes.
        """
        pass

    @abc.abstractmethod
    def AiidaNode(self):
        """
        A property, decorated with @property. Returns the implementation for the AiiDA-class for Node
        """
        pass

    @abc.abstractmethod
    def AiidaGroup(self):
        """
        A property, decorated with @property. Returns the implementation for the AiiDA-class for Group
        """
        pass

    @abc.abstractmethod
    def get_session(self):
        """
        :returns: a valid session, an instance of sqlalchemy.orm.session.Session
        """
        pass

    @abc.abstractmethod
    def modify_expansions(self, alias, expansions):
        """
        Modify names of projections if ** was specified.
        This is important for the schema having attributes in a different table.
        """
        pass

    @abstractclassmethod
    def get_filter_expr_from_attributes(cls, operator, value, attr_key, column=None, column_name=None, alias=None):  # pylint: disable=too-many-arguments
        """
        A classmethod that returns an valid SQLAlchemy expression.

        :param operator: The operator provided by the user ('==',  '>', ...)
        :param value: The value to compare with, e.g. (5.0, 'foo', ['a','b'])
        :param str attr_key:
            The path to that attribute as a tuple of values.
            I.e. if that attribute I want to filter by is the 2nd element in a list stored under the
            key 'mylist', this is ('mylist', '2').
        :param column: Optional, an instance of sqlalchemy.orm.attributes.InstrumentedAttribute or
        :param str column_name: The name of the column, and the backend should get the InstrumentedAttribute.
        :param alias: The aliased class.


        :returns: An instance of sqlalchemy.sql.elements.BinaryExpression
        """
        pass

    @abc.abstractmethod
    def get_projectable_attribute(self, alias, column_name, attrpath, cast=None, **kwargs):
        pass

    @abc.abstractmethod
    def get_aiida_res(self, key, res):
        """
        Some instance returned by ORM (django or SA) need to be converted
        to Aiida instances (eg nodes)

        :param key: the key that this entry would be returned with
        :param res: the result returned by the query

        :returns: an aiida-compatible instance
        """
        pass

    @abc.abstractmethod
    def yield_per(self, query, batch_size):
        """
        :param int batch_size: Number of rows to yield per step

        Yields *count* rows at a time

        :returns: a generator
        """
        pass

    @abc.abstractmethod
    def count(self, query):
        """
        :returns: the number of results
        """
        pass

    @abc.abstractmethod
    def first(self, query):
        """
        Executes query in the backend asking for one instance.

        :returns: One row of aiida results
        """

        pass

    @abc.abstractmethod
    def iterall(self, query, batch_size, tag_to_index_dict):
        """
        :returns: An iterator over all the results of a list of lists.
        """
        pass

    @abc.abstractmethod
    def iterdict(self, query, batch_size, tag_to_projected_entity_dict):
        """
        :returns: An iterator over all the results of a list of dictionaries.
        """
        pass
