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
from typing import TYPE_CHECKING
import uuid

# pylint: disable=no-name-in-module,import-error
from sqlalchemy_utils.types.choice import Choice
from sqlalchemy.types import Integer, Float, Boolean, DateTime
from sqlalchemy.dialects.postgresql import JSONB

from aiida.common.lang import type_check

if TYPE_CHECKING:
    from sqlalchemy.orm.session import Session  # pylint: disable=ungrouped-imports

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

    @property
    @abc.abstractmethod
    def Node(self):
        """
        Decorated as a property, returns the implementation for DbNode.
        It needs to return a subclass of sqlalchemy.Base, which means that for different ORM's
        a corresponding dummy-model must be written.
        """

    @property
    @abc.abstractmethod
    def Link(self):
        """Returns the implementation for the DbLink"""

    @property
    @abc.abstractmethod
    def Computer(self):
        """Returns the implementation for the Computer"""

    @property
    @abc.abstractmethod
    def User(self):
        """Returns the implementation for the User"""

    @property
    @abc.abstractmethod
    def Group(self):
        """Returns the implementation for the Group"""

    @property
    @abc.abstractmethod
    def AuthInfo(self):
        """Returns the implementation for the AuthInfo"""

    @property
    @abc.abstractmethod
    def Comment(self):
        """Returns the implementation for the Comment"""

    @property
    @abc.abstractmethod
    def Log(self):
        """Returns the implementation for the Log"""

    @property
    @abc.abstractmethod
    def table_groups_nodes(self):
        """Returns the implementation for the many-to-many relationship between group and nodes."""

    def get_session(self) -> 'Session':
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

    @abc.abstractmethod
    def get_filter_expr(self, operator, value, attr_key, is_attribute, alias=None, column=None, column_name=None):
        """
        Applies a filter on the alias given.
        Expects the alias of the ORM-class on which to filter, and filter_spec.
        Filter_spec contains the specification on the filter.
        Expects:

        :param operator: The operator to apply, see below for further details
        :param value:
            The value for the right side of the expression,
            the value you want to compare with.

        :param path: The path leading to the value

        :param attr_key: Boolean, whether the value is in a json-column,
            or in an attribute like table.


        Implemented and valid operators:

        *   for any type:
            *   ==  (compare single value, eg: '==':5.0)
            *   in    (compare whether in list, eg: 'in':[5, 6, 34]
        *  for floats and integers:
            *   >
            *   <
            *   <=
            *   >=
        *  for strings:
            *   like  (case - sensitive), for example
                'like':'node.calc.%'  will match node.calc.relax and
                node.calc.RELAX and node.calc. but
                not node.CALC.relax
            *   ilike (case - unsensitive)
                will also match node.CaLc.relax in the above example

            .. note::
                The character % is a reserved special character in SQL,
                and acts as a wildcard. If you specifically
                want to capture a ``%`` in the string, use: ``_%``

        *   for arrays and dictionaries (only for the
            SQLAlchemy implementation):

            *   contains: pass a list with all the items that
                the array should contain, or that should be among
                the keys, eg: 'contains': ['N', 'H'])
            *   has_key: pass an element that the list has to contain
                or that has to be a key, eg: 'has_key':'N')

        *  for arrays only (SQLAlchemy version):
            *   of_length
            *   longer
            *   shorter

        All the above filters invoke a negation of the
        expression if preceded by **~**::

            # first example:
            filter_spec = {
                'name' : {
                    '~in':[
                        'halle',
                        'lujah'
                    ]
                } # Name not 'halle' or 'lujah'
            }

            # second example:
            filter_spec =  {
                'id' : {
                    '~==': 2
                }
            } # id is not 2
        """

    @classmethod
    @abc.abstractmethod
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
            raise ValueError(f'Unknown casting key {cast}')
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
                raise Exception(f'Got an empty dictionary: {tag_to_index_dict}')

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

    def iterdict(self, query, batch_size, tag_to_projected_properties_dict, tags):
        """
        :returns: An iterator over all the results of a list of dictionaries.
        """
        # pylint: disable=protected-access
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
                                self.get_table_name(tags._get_alias(self, tag)), attrkey, self.inner_to_outer_schema
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
                                    self.get_table_name(tags._get_alias(self, tag)), attrkey, self.inner_to_outer_schema
                                ): self.get_aiida_res(this_result)
                                for attrkey, position in projected_entities_dict.items()
                            } for tag, projected_entities_dict in tag_to_projected_properties_dict.items()
                        }
                else:
                    for this_result, in results:
                        yield {
                            tag: {
                                self.get_corresponding_property(
                                    self.get_table_name(tags._get_alias(self, tag)), attrkey, self.inner_to_outer_schema
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
    @abc.abstractmethod
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
        except AttributeError as exc:
            raise ValueError(
                '{} is not a column of {}\n'
                'Valid columns are:\n'
                '{}'.format(colname, alias, '\n'.join(alias._sa_class_manager.mapper.c.keys()))  # pylint: disable=protected-access
            ) from exc
