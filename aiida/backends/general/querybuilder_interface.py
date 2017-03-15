# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
from abc import abstractmethod, ABCMeta


class QueryBuilderInterface():
    __metaclass__ = ABCMeta
    @abstractmethod
    def __init__(self, *args, **kwargs):
        pass

    @abstractmethod
    def Node(self):
        """
        Decorated as a property, returns the implementation for DbNode.
        It needs to return a subclass of sqlalchemy.Base, which means that for different ORM's 
        a corresponding dummy-model  must be written.
        """
        pass

    @abstractmethod
    def Link(self):
        """
        A property, decorated with @property. Returns the implementation for the DbLink
        """
        pass

    @abstractmethod
    def Computer(self):
        """
        A property, decorated with @property. Returns the implementation for the Computer
        """
        pass

    @abstractmethod
    def User(self):
        """
        A property, decorated with @property. Returns the implementation for the User
        """
        pass

    @abstractmethod
    def Group(self):
        """
        A property, decorated with @property. Returns the implementation for the Group
        """
        pass

    @abstractmethod
    def table_groups_nodes(self):
        """
        A property, decorated with @property. Returns the implementation for the many-to-many
        relationship between group and nodes.
        """
        pass

    @abstractmethod
    def AiidaNode(self):
        """
        A property, decorated with @property. Returns the implementation for the AiiDA-class for Node
        """
        pass

    @abstractmethod
    def AiidaGroup(self):
        """
        A property, decorated with @property. Returns the implementation for the AiiDA-class for Group
        """
        pass

    @abstractmethod
    def AiidaUser(self):
        """
        A property, decorated with @property. Returns the implementation for the AiiDA-class for User
        """
        pass

    @abstractmethod
    def AiidaComputer(self):
        """
        A property, decorated with @property. Returns the implementation for the AiiDA-class for Computer
        """
        pass

    @abstractmethod
    def prepare_with_dbpath(self):
        """
        A method to use the DbPath, if this is supported, or throw an
        exception if not.
        The overrider must fill add the DbPath-ORM as an attribute to self::

            from aiida.backends.implementation.model import DbPath
            self.path = DbPath

        """
        pass
    @abstractmethod
    def get_session(self):
        """
        :returns: a valid session, an instance of sqlalchemy.orm.session.Session
        """
        pass

    @abstractmethod
    def modify_expansions(self, alias, expansions):
        """
        Modify names of projections if ** was specified.
        This is important for the schema having attributes in a different table.
        """
        pass

    @abstractmethod
    def get_filter_expr_from_attributes(
            cls, operator, value, attr_key,
            column=None, column_name=None, alias=None):
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
    @abstractmethod
    def get_projectable_attribute(
            self, alias, column_name, attrpath,
            cast=None, **kwargs):
        pass
    @abstractmethod
    def get_aiida_res(self, key, res):
        """
        Some instance returned by ORM (django or SA) need to be converted
        to Aiida instances (eg nodes)

        :param key: the key that this entry would be returned with
        :param res: the result returned by the query

        :returns: an aiida-compatible instance
        """
        pass

    @abstractmethod
    def get_ormclass(self,  cls, ormclasstype):
        pass


    @abstractmethod
    def yield_per(self, batch_size):
        """
        :param int batch_size: Number of rows to yield per step

        Yields *count* rows at a time

        :returns: a generator
        """
        pass

    @abstractmethod
    def count(self):
        """
        :returns: the number of results
        """
        pass

    @abstractmethod
    def first(self):
        """
        Executes query in the backend asking for one instance.

        :returns: One row of aiida results
        """

        pass
    @abstractmethod
    def iterall(self, batch_size=100):
        """
        :returns: An iterator over all the results of a list of lists.
        """
        pass

    @abstractmethod
    def iterdict(self, batch_size=100):
        """
        :returns: An iterator over all the results of a list of dictionaries.
        """
        pass


