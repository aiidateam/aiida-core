# -*- coding: utf-8 -*-
from abc import ABCMeta, abstractmethod, abstractproperty
from enum import Enum

from aiida.common.exceptions import MultipleObjectsError, NotExistent
from aiida.orm.querybuilder import QueryBuilder

__all__ = [
    'IdentifierType', 'OrmEntityLoader', 'CodeEntityLoader', 'ComputerEntityLoader', 'GroupEntityLoader',
    'NodeEntityLoader'
]


class IdentifierType(Enum):
    """
    The enumeration that defines the three types of identifier that can be used to identify an ORM entity.
    The ID is always an integer, the UUID a base 16 encoded integer with optional dashes and the STRING can
    be any string based label or name, the format of which will vary per ORM class
    """

    ID = 'ID'
    UUID = 'UUID'
    STRING = 'STRING'


class OrmEntityLoader(object):

    __metaclass__ = ABCMeta

    @abstractproperty
    def orm_class(self):
        """
        Return the ORM class to which loaded entities should be mapped

        :return: the ORM class
        """
        raise NotImplementedError

    @abstractmethod
    def get_label_query_builder(self, identifier):
        """
        Return the query builder instance that attempts to map the identifier onto an entity of the ORM class,
        defined for this loader class, interpreting the identifier as a STRING like identifier

        :param identifier: the STRING identifier
        :return: the query builder instance that should retrieve the entity corresponding to the identifier
        :raises ValueError: if the identifier is invalid
        :raises NotExistent: if the ORM class does not support a STRING like identifier
        """
        raise NotImplementedError

    def load_entity(self, identifier, identifier_type=IdentifierType.ID):
        """
        Load an entity that uniquely corresponds to the provided identifier of the identifier type.

        :param identifier: the identifier
        :param identifier_type: the type of the identifier
        :return: the loaded entity
        :raises MultipleObjectsError: if the identifier maps onto multiple entities
        :raises NotExistent: if the identifier maps onto not a single entity
        :raises ValueError: if the `get_label_query_builder` method has not been implemented
        """
        qb = QueryBuilder()
        qb.append(self.orm_class, tag='entity')
        qb.add_projection('entity', '*')

        if identifier_type == IdentifierType.ID:
            qb.add_filter('entity', {'id': identifier})
        elif identifier_type == IdentifierType.UUID:
            qb.add_filter('entity', {'uuid': {'like': '{}%'.format(identifier)}})
        elif identifier_type == IdentifierType.STRING:
            qb = self.get_label_query_builder(identifier)

        qb.limit(2)

        try:
            entity = qb.one()[0]
        except MultipleObjectsError:
            raise MultipleObjectsError('more than one entity found')
        except NotExistent:
            raise NotExistent('no entity found')

        return entity


class CodeEntityLoader(OrmEntityLoader):

    @property
    def orm_class(self):
        """
        Return the ORM class to which loaded entities should be mapped

        :return: the ORM class
        """
        from aiida.orm.code import Code
        return Code

    def get_label_query_builder(self, identifier):
        """
        Return the query builder instance that attempts to map the identifier onto an entity of the ORM class,
        defined for this loader class, interpreting the identifier as a STRING like identifier

        :param identifier: the STRING identifier
        :return: the query builder instance that should retrieve the entity corresponding to the identifier
        :raises ValueError: if the identifier is invalid
        :raises NotExistent: if the ORM class does not support a STRING like identifier
        """
        from aiida.orm.computer import Computer

        try:
            label, sep, machinename = identifier.partition('@')
        except AttributeError as exception:
            raise ValueError('the identifier needs to be a string')

        qb = QueryBuilder()
        qb.append(self.orm_class, tag='code', project=['*'], filters={'label': {'==': label}})

        if machinename:
            qb.append(Computer, filters={'name': {'==': machinename}}, computer_of='code')

        return qb


class ComputerEntityLoader(OrmEntityLoader):

    @property
    def orm_class(self):
        """
        Return the ORM class to which loaded entities should be mapped

        :return: the ORM class
        """
        from aiida.orm.computer import Computer
        return Computer

    def get_label_query_builder(self, identifier):
        """
        Return the query builder instance that attempts to map the identifier onto an entity of the ORM class,
        defined for this loader class, interpreting the identifier as a STRING like identifier

        :param identifier: the STRING identifier
        :return: the query builder instance that should retrieve the entity corresponding to the identifier
        :raises ValueError: if the identifier is invalid
        :raises NotExistent: if the ORM class does not support a STRING like identifier
        """
        qb = QueryBuilder()
        qb.append(self.orm_class, tag='code', project=['*'], filters={'name': {'==': identifier}})

        return qb


class GroupEntityLoader(OrmEntityLoader):

    @property
    def orm_class(self):
        """
        Return the ORM class to which loaded entities should be mapped

        :return: the ORM class
        """
        from aiida.orm.group import Group
        return Group

    def get_label_query_builder(self, identifier):
        """
        Return the query builder instance that attempts to map the identifier onto an entity of the ORM class,
        defined for this loader class, interpreting the identifier as a STRING like identifier

        :param identifier: the STRING identifier
        :return: the query builder instance that should retrieve the entity corresponding to the identifier
        :raises ValueError: if the identifier is invalid
        :raises NotExistent: if the ORM class does not support a STRING like identifier
        """
        qb = QueryBuilder()
        qb.append(self.orm_class, tag='code', project=['*'], filters={'name': {'==': identifier}})

        return qb


class NodeEntityLoader(OrmEntityLoader):

    @property
    def orm_class(self):
        """
        Return the ORM class to which loaded entities should be mapped

        :return: the ORM class
        """
        from aiida.orm.node import Node
        return Node

    def get_label_query_builder(self, identifier):
        """
        Return the query builder instance that attempts to map the identifier onto an entity of the ORM class,
        defined for this loader class, interpreting the identifier as a STRING like identifier

        :param identifier: the STRING identifier
        :return: the query builder instance that should retrieve the entity corresponding to the identifier
        :raises ValueError: if the identifier is invalid
        :raises NotExistent: if the ORM class does not support a STRING like identifier
        """
        raise NotExistent
