# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Abstract `QueryBuilder` definition.

Note that this abstract class actually contains parts of the implementation, which are tightly coupled to SqlAlchemy.
This is done because currently, both database backend implementations, both Django and SqlAlchemy, directly use the
SqlAlchemy library to implement the query builder. If there ever is another database backend to be implemented that does
not go through SqlAlchemy, this class will have to be refactored. The SqlAlchemy specific implementations should most
likely be moved to a `SqlAlchemyBasedQueryBuilder` class and restore this abstract class to being a pure agnostic one.
"""
import abc
import uuid

# pylint: disable=no-name-in-module, import-error
from sqlalchemy_utils.types.choice import Choice
from sqlalchemy.types import Integer, Float, Boolean, DateTime
from sqlalchemy.dialects.postgresql import JSONB

from aiida.common import exceptions
from aiida.common.lang import abstractclassmethod, type_check
from aiida.common.exceptions import InputValidationError

__all__ = ('BackendQueryBuilder',)


class BackendQueryBuilder:
    """Backend query builder interface"""

    # pylint: disable=invalid-name,too-many-public-methods

    outer_to_inner_schema = None
    inner_to_outer_schema = None

    def __init__(self, backend):
        """
        :param backend: the backend
        """
        from . import backends
        type_check(backend, backends.Backend)
        self._backend = backend
        self.inner_to_outer_schema = dict()
        self.outer_to_inner_schema = dict()

    @abc.abstractproperty
    def Node(self):
        """
        Decorated as a property, returns the implementation for DbNode.
        It needs to return a subclass of sqlalchemy.Base, which means that for different ORM's
        a corresponding dummy-model  must be written.
        """

    @abc.abstractproperty
    def Link(self):
        """
        A property, decorated with @property. Returns the implementation for the DbLink
        """

    @abc.abstractproperty
    def Computer(self):
        """
        A property, decorated with @property. Returns the implementation for the Computer
        """

    @abc.abstractproperty
    def User(self):
        """
        A property, decorated with @property. Returns the implementation for the User
        """

    @abc.abstractproperty
    def Group(self):
        """
        A property, decorated with @property. Returns the implementation for the Group
        """

    @abc.abstractproperty
    def AuthInfo(self):
        """
        A property, decorated with @property. Returns the implementation for the AuthInfo
        """

    @abc.abstractproperty
    def Comment(self):
        """
        A property, decorated with @property. Returns the implementation for the Comment
        """

    @abc.abstractproperty
    def Log(self):
        """
        A property, decorated with @property. Returns the implementation for the Log
        """

    @abc.abstractproperty
    def table_groups_nodes(self):
        """
        A property, decorated with @property. Returns the implementation for the many-to-many
        relationship between group and nodes.
        """

    @property
    def AiidaNode(self):
        """
        A property, decorated with @property. Returns the implementation for the AiiDA-class for Node
        """
        from aiida.orm import Node
        return Node

    def get_session(self):
        """
        :returns: a valid session, an instance of :class:`sqlalchemy.orm.session.Session`
        """
        return self._backend.get_session()

    @abc.abstractmethod
    def modify_expansions(self, alias, expansions):
        """
        Modify names of projections if ** was specified.
        This is important for the schema having attributes in a different table.
        """

    @abstractclassmethod
    def get_filter_expr_from_attributes(cls, operator, value, attr_key, column=None, column_name=None, alias=None):  # pylint: disable=too-many-arguments
        """
        Returns an valid SQLAlchemy expression.

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

    @classmethod
    def get_corresponding_properties(cls, entity_table, given_properties, mapper):
        """
        This method returns a list of updated properties for a given list of properties.
        If there is no update for the property, the given property is returned in the list.
        """
        if entity_table in mapper.keys():
            res = list()
            for given_property in given_properties:
                res.append(cls.get_corresponding_property(entity_table, given_property, mapper))
            return res

        return given_properties

    @classmethod
    def get_corresponding_property(cls, entity_table, given_property, mapper):
        """
        This method returns an updated property for a given a property.
        If there is no update for the property, the given property is returned.
        """
        try:
            # Get the mapping for the specific entity_table
            property_mapping = mapper[entity_table]
            try:
                # Get the mapping for the specific property
                return property_mapping[given_property]
            except KeyError:
                # If there is no mapping, the property remains unchanged
                return given_property
        except KeyError:
            # If it doesn't exist, it means that the given_property remains v
            return given_property

    @classmethod
    def get_filter_expr_from_column(cls, operator, value, column):
        """
        A method that returns an valid SQLAlchemy expression.

        :param operator: The operator provided by the user ('==',  '>', ...)
        :param value: The value to compare with, e.g. (5.0, 'foo', ['a','b'])
        :param column: an instance of sqlalchemy.orm.attributes.InstrumentedAttribute or

        :returns: An instance of sqlalchemy.sql.elements.BinaryExpression
        """
        # Label is used because it is what is returned for the
        # 'state' column by the hybrid_column construct

        # Remove when https://github.com/PyCQA/pylint/issues/1931 is fixed
        # pylint: disable=no-name-in-module,import-error
        from sqlalchemy.sql.elements import Cast, Label
        from sqlalchemy.orm.attributes import InstrumentedAttribute, QueryableAttribute
        from sqlalchemy.sql.expression import ColumnClause
        from sqlalchemy.types import String

        if not isinstance(column, (Cast, InstrumentedAttribute, QueryableAttribute, Label, ColumnClause)):
            raise TypeError('column ({}) {} is not a valid column'.format(type(column), column))
        database_entity = column
        if operator == '==':
            expr = database_entity == value
        elif operator == '>':
            expr = database_entity > value
        elif operator == '<':
            expr = database_entity < value
        elif operator == '>=':
            expr = database_entity >= value
        elif operator == '<=':
            expr = database_entity <= value
        elif operator == 'like':
            # the like operator expects a string, so we cast to avoid problems
            # with fields like UUID, which don't support the like operator
            expr = database_entity.cast(String).like(value)
        elif operator == 'ilike':
            expr = database_entity.ilike(value)
        elif operator == 'in':
            expr = database_entity.in_(value)
        else:
            raise InputValidationError('Unknown operator {} for filters on columns'.format(operator))
        return expr

    def get_projectable_attribute(self, alias, column_name, attrpath, cast=None, **kwargs):
        """
        :returns: An attribute store in a JSON field of the give column
        """
        # pylint: disable=unused-argument
        entity = self.get_column(column_name, alias)[attrpath]
        if cast is None:
            pass
        elif cast == 'f':
            entity = entity.astext.cast(Float)
        elif cast == 'i':
            entity = entity.astext.cast(Integer)
        elif cast == 'b':
            entity = entity.astext.cast(Boolean)
        elif cast == 't':
            entity = entity.astext
        elif cast == 'j':
            entity = entity.astext.cast(JSONB)
        elif cast == 'd':
            entity = entity.astext.cast(DateTime)
        else:
            raise InputValidationError('Unkown casting key {}'.format(cast))
        return entity

    def get_aiida_res(self, res):
        """
        Some instance returned by ORM (django or SA) need to be converted
        to AiiDA instances (eg nodes). Choice (sqlalchemy_utils)
        will return their value

        :param res: the result returned by the query

        :returns: an aiida-compatible instance
        """
        if isinstance(res, Choice):
            return res.value

        if isinstance(res, uuid.UUID):
            return str(res)

        try:
            return self._backend.get_backend_entity(res)
        except TypeError:
            return res

    def yield_per(self, query, batch_size):
        """
        :param int batch_size: Number of rows to yield per step

        Yields *count* rows at a time

        :returns: a generator
        """
        try:
            return query.yield_per(batch_size)
        except Exception:
            self.get_session().close()
            raise

    def count(self, query):
        """
        :returns: the number of results
        """
        try:
            return query.count()
        except Exception:
            self.get_session().close()
            raise

    def first(self, query):
        """
        Executes query in the backend asking for one instance.

        :returns: One row of aiida results
        """
        try:
            return query.first()
        except Exception:
            self.get_session().close()
            raise

    def iterall(self, query, batch_size, tag_to_index_dict):
        """
        :return: An iterator over all the results of a list of lists.
        """
        try:
            if not tag_to_index_dict:
                raise Exception('Got an empty dictionary: {}'.format(tag_to_index_dict))

            results = query.yield_per(batch_size)

            if len(tag_to_index_dict) == 1:
                # Sqlalchemy, for some strange reason, does not return a list of lsits
                # if you have provided an ormclass

                if list(tag_to_index_dict.values()) == ['*']:
                    for rowitem in results:
                        yield [self.get_aiida_res(rowitem)]
                else:
                    for rowitem, in results:
                        yield [self.get_aiida_res(rowitem)]
            elif len(tag_to_index_dict) > 1:
                for resultrow in results:
                    yield [self.get_aiida_res(rowitem) for colindex, rowitem in enumerate(resultrow)]
            else:
                raise ValueError('Got an empty dictionary')
        except Exception:
            self.get_session().close()
            raise

    def iterdict(self, query, batch_size, tag_to_projected_properties_dict, tag_to_alias_map):
        """
        :returns: An iterator over all the results of a list of dictionaries.
        """
        try:
            nr_items = sum(len(v) for v in tag_to_projected_properties_dict.values())

            if not nr_items:
                raise ValueError('Got an empty dictionary')

            results = query.yield_per(batch_size)
            if nr_items > 1:
                for this_result in results:
                    yield {
                        tag: {
                            self.get_corresponding_property(
                                self.get_table_name(tag_to_alias_map[tag]), attrkey, self.inner_to_outer_schema
                            ): self.get_aiida_res(this_result[index_in_sql_result])
                            for attrkey, index_in_sql_result in projected_entities_dict.items()
                        } for tag, projected_entities_dict in tag_to_projected_properties_dict.items()
                    }
            elif nr_items == 1:
                # I this case, sql returns a  list, where each listitem is the result
                # for one row. Here I am converting it to a list of lists (of length 1)
                if [v for entityd in tag_to_projected_properties_dict.values() for v in entityd.keys()] == ['*']:
                    for this_result in results:
                        yield {
                            tag: {
                                self.get_corresponding_property(
                                    self.get_table_name(tag_to_alias_map[tag]), attrkey, self.inner_to_outer_schema
                                ): self.get_aiida_res(this_result)
                                for attrkey, position in projected_entities_dict.items()
                            } for tag, projected_entities_dict in tag_to_projected_properties_dict.items()
                        }
                else:
                    for this_result, in results:
                        yield {
                            tag: {
                                self.get_corresponding_property(
                                    self.get_table_name(tag_to_alias_map[tag]), attrkey, self.inner_to_outer_schema
                                ): self.get_aiida_res(this_result)
                                for attrkey, position in projected_entities_dict.items()
                            } for tag, projected_entities_dict in tag_to_projected_properties_dict.items()
                        }
            else:
                raise ValueError('Got an empty dictionary')
        except Exception:
            self.get_session().close()
            raise

    @staticmethod
    @abstractclassmethod
    def get_table_name(aliased_class):
        """Returns the table name given an Aliased class."""

    @abc.abstractmethod
    def get_column_names(self, alias):
        """
        Return the column names of the given table (alias).
        """

    def get_column(self, colname, alias):  # pylint: disable=no-self-use
        """
        Return the column for a given projection.
        """
        try:
            return getattr(alias, colname)
        except AttributeError:
            raise exceptions.InputValidationError(
                '{} is not a column of {}\n'
                'Valid columns are:\n'
                '{}'.format(
                    colname,
                    alias,
                    '\n'.join(alias._sa_class_manager.mapper.c.keys())  # pylint: disable=protected-access
                )
            )
