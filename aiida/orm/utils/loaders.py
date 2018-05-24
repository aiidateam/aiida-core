# -*- coding: utf-8 -*-
from abc import abstractmethod
from enum import Enum

__all__ = ['IdentifierType', 'OrmEntityLoader', 'CodeEntityLoader', 'ComputerEntityLoader', 'GroupEntityLoader']


class IdentifierType(Enum):

    ID = 'ID'
    UUID = 'UUID'
    LABEL = 'LABEL'


class OrmEntityLoader(object):

    def __init__(self, orm_class):
        self._orm_class = orm_class

    @abstractmethod
    def get_label_query_builder(orm_class, identifier):
        pass

    def load_entity(self, identifier, identifier_type=IdentifierType.ID):
        """
        """
        from aiida.common.exceptions import MultipleObjectsError, NotExistent
        from aiida.orm.querybuilder import QueryBuilder

        qb = QueryBuilder()
        qb.append(self._orm_class, tag='entity')
        qb.add_projection('entity', '*')

        if identifier_type == IdentifierType.ID:
            qb.add_filter('entity', {'id': identifier})
        elif identifier_type == IdentifierType.UUID:
            qb.add_filter('entity', {'uuid': {'like': '{}%'.format(identifier)}})
        elif identifier_type == IdentifierType.LABEL:
            qb = self.get_label_query_builder(self._orm_class, identifier)

        qb.limit(2)

        try:
            return qb.one()[0]
        except MultipleObjectsError:
            raise MultipleObjectsError('More than one entity found')
        except NotExistent:
            raise NotExistent('No entity found')


class CodeEntityLoader(OrmEntityLoader):

    def get_label_query_builder(self, orm_class, identifier):
        """
        """
        from aiida.orm.computer import Computer
        from aiida.orm.querybuilder import QueryBuilder

        try:
            label, sep, machinename = identifier.partition('@')
        except AttributeError as exception:
            raise ValueError('the identifier needs to be a string')

        qb = QueryBuilder()
        qb.append(orm_class, tag='code', project=['*'], filters={'label': {'==': label}})

        if machinename:
            qb.append(Computer, filters={'name': {'==': machinename}}, computer_of='code')

        return qb


class ComputerEntityLoader(OrmEntityLoader):

    def get_label_query_builder(self, orm_class, identifier):
        """
        """
        from aiida.orm.querybuilder import QueryBuilder

        qb = QueryBuilder()
        qb.append(orm_class, tag='code', project=['*'], filters={'name': {'==': identifier}})

        return qb


class GroupEntityLoader(OrmEntityLoader):

    def get_label_query_builder(self, orm_class, identifier):
        """
        """
        from aiida.orm.querybuilder import QueryBuilder

        qb = QueryBuilder()
        qb.append(orm_class, tag='code', project=['*'], filters={'name': {'==': identifier}})

        return qb
