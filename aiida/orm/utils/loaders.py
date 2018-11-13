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
from abc import ABCMeta
from enum import Enum

import six

from aiida.common.exceptions import MultipleObjectsError, NotExistent
from aiida.common.utils import abstractclassmethod, classproperty
from aiida.orm.querybuilder import QueryBuilder

__all__ = [
    'get_loader', 'OrmEntityLoader', 'CalculationEntityLoader', 'CodeEntityLoader', 'ComputerEntityLoader',
    'GroupEntityLoader', 'NodeEntityLoader'
]


def get_loader(orm_class):
    """
    Get the correct OrmEntityLoader for the given orm class

    :param orm_class: the orm class
    :returns: a subclass of OrmEntityLoader
    :raises ValueError: if no OrmEntityLoader subclass can be found for the given orm class
    """
    from aiida.orm import Code, Computer, Group, Node

    if issubclass(orm_class, Code):
        return CodeEntityLoader
    elif issubclass(orm_class, Computer):
        return ComputerEntityLoader
    elif issubclass(orm_class, Group):
        return GroupEntityLoader
    elif issubclass(orm_class, Node):
        return NodeEntityLoader
    else:
        raise ValueError('no OrmEntityLoader available for {}'.format(orm_class))


class IdentifierType(Enum):
    """
    The enumeration that defines the three types of identifier that can be used to identify an orm entity.
    The ID is always an integer, the UUID a base 16 encoded integer with optional dashes and the LABEL can
    be any string based label or name, the format of which will vary per orm class
    """

    ID = 'ID'
    UUID = 'UUID'
    LABEL = 'LABEL'


@six.add_metaclass(ABCMeta)
class OrmEntityLoader(object):

    LABEL_AMBIGUITY_BREAKER_CHARACTER = '!'

    @classproperty
    def orm_base_class(cls):
        """
        Return the orm base class to which loaded entities should be mapped. Actual queries to load an entity
        may further narrow the query set by defining a more specific set of orm classes, as long as each of
        those is a strict sub class of the orm base class.

        :returns: the orm base class
        """
        raise NotImplementedError

    @abstractclassmethod
    def _get_query_builder_label_identifier(self, identifier, classes):
        """
        Return the query builder instance that attempts to map the identifier onto an entity of the orm class,
        defined for this loader class, interpreting the identifier as a LABEL like identifier

        :param identifier: the LABEL identifier
        :param classes: a tuple of orm classes to which the identifier should be mapped
        :returns: the query builder instance
        :raises ValueError: if the identifier is invalid
        :raises NotExistent: if the orm base class does not support a LABEL like identifier
        """
        raise NotImplementedError

    @classmethod
    def _get_query_builder_id_identifier(self, identifier, classes):
        """
        Return the query builder instance that attempts to map the identifier onto an entity of the orm class,
        defined for this loader class, interpreting the identifier as an ID like identifier

        :param identifier: the ID identifier
        :param classes: a tuple of orm classes to which the identifier should be mapped
        :returns: the query builder instance
        """
        qb = QueryBuilder()
        qb.append(cls=classes, tag='entity', project=['*'])
        qb.add_filter('entity', {'id': identifier})

        return qb

    @classmethod
    def _get_query_builder_uuid_identifier(self, identifier, classes, query_with_dashes):
        """
        Return the query builder instance that attempts to map the identifier onto an entity of the orm class,
        defined for this loader class, interpreting the identifier as a UUID like identifier

        :param identifier: the UUID identifier
        :param classes: a tuple of orm classes to which the identifier should be mapped
        :returns: the query builder instance
        """
        from uuid import UUID

        uuid = identifier.replace('-', '')

        if query_with_dashes:
            for dash_pos in [20, 16, 12, 8]:
                if len(uuid) > dash_pos:
                    uuid = '{}-{}'.format(uuid[:dash_pos], uuid[dash_pos:])

        qb = QueryBuilder()
        qb.append(cls=classes, tag='entity', project=['*'])

        # If a UUID can be constructed from the identifier, it is a full UUID and the query can use an equality operator
        try:
            UUID(uuid)
        except ValueError:
            qb.add_filter('entity', {'uuid': {'like': '{}%'.format(uuid)}})
        else:
            qb.add_filter('entity', {'uuid': uuid})

        return qb

    @classmethod
    def get_query_builder(cls, identifier, identifier_type=None, sub_classes=None, query_with_dashes=True):
        """
        Return the query builder instance that attempts to map the identifier onto an entity of the orm class,
        defined for this loader class, inferring the identifier type if it is not defined.

        :param identifier: the identifier
        :param identifier_type: the type of the identifier
        :param sub_classes: an optional tuple of orm classes, that should each be strict sub classes of the
            base orm class of the loader, that will narrow the queryset
        :returns: the query builder instance and a dictionary of used query parameters
        """
        classes = cls.get_query_classes(sub_classes)

        if identifier_type is None:
            identifier, identifier_type = cls.infer_identifier_type(identifier)

        if identifier_type == IdentifierType.ID:
            qb = cls._get_query_builder_id_identifier(identifier, classes)
        elif identifier_type == IdentifierType.UUID:
            qb = cls._get_query_builder_uuid_identifier(identifier, classes, query_with_dashes)
        elif identifier_type == IdentifierType.LABEL:
            qb = cls._get_query_builder_label_identifier(identifier, classes)

        query_parameters = {
            'classes': classes,
            'identifier': identifier,
            'identifier_type': identifier_type,
        }

        return qb, query_parameters

    @classmethod
    def load_entity(cls, identifier, identifier_type=None, sub_classes=None, query_with_dashes=True):
        """
        Load an entity that uniquely corresponds to the provided identifier of the identifier type.

        :param identifier: the identifier
        :param identifier_type: the type of the identifier
        :param sub_classes: an optional tuple of orm classes, that should each be strict sub classes of the
            base orm class of the loader, that will narrow the queryset
        :returns: the loaded entity
        :raises MultipleObjectsError: if the identifier maps onto multiple entities
        :raises NotExistent: if the identifier maps onto not a single entity
        """
        qb, query_parameters = cls.get_query_builder(identifier, identifier_type, sub_classes, query_with_dashes)
        qb.limit(2)

        classes = ' or '.join([sub_class.__name__ for sub_class in query_parameters['classes']])
        identifier = query_parameters['identifier']
        identifier_type = query_parameters['identifier_type'].value

        try:
            entity = qb.one()[0]
        except MultipleObjectsError:
            error = 'multiple {} entries found with {}<{}>'.format(classes, identifier_type, identifier)
            raise MultipleObjectsError(error)
        except NotExistent:
            error = 'no {} found with {}<{}>'.format(classes, identifier_type, identifier)
            raise NotExistent(error)

        return entity

    @classmethod
    def get_query_classes(cls, sub_classes=None):
        """
        Get the tuple of classes to be used for the entity query. If sub_classes is defined, each class will be
        validated by verifying that it is a sub class of the loader's orm base class.
        Validate a tuple of classes if a user passes in a specific one when attempting to load an entity. Each class
        should be a sub class of the entity loader's orm base class

        :param sub_classes: an optional tuple of orm classes, that should each be strict sub classes of the
            base orm class of the loader, that will narrow the queryset
        :returns: the tuple of orm classes to be used for the entity query
        :raises ValueError: if any of the classes are not a sub class of the entity loader's orm base class
        """
        if sub_classes is None:
            return (cls.orm_base_class,)

        if not isinstance(sub_classes, tuple):
            raise TypeError('sub_classes should be a tuple: {}'.format(sub_classes))

        for sub_class in sub_classes:
            if not issubclass(sub_class, cls.orm_base_class):
                raise ValueError('{} is not a sub class of the base orm class {}'.format(sub_class, cls.orm_base_class))

        return sub_classes

    @classmethod
    def infer_identifier_type(cls, value):
        """
        This method will attempt to automatically distinguish which identifier type is implied for the given value, if
        the value itself has no type from which it can be inferred.

        The strategy is to first attempt to convert the value to an integer. If successful, it is assumed that the value
        represents an ID. If that fails, we attempt to interpret the value as a base 16 encoded integer, after having
        removed any dashes from the string. If that succeeds, it is most likely a UUID. If it seems to be neither an ID
        nor a UUID, it is assumed to be a LABEL like identifier.

        With this approach there is the possibility for ambiguity. Since it is allowed to pass a partial UUID, it is
        possible that the partial UUID is also a valid ID. Likewise, a LABEL identifier might also be a valid ID, or a
        valid (partial) UUID. Fortunately, these ambiguities can be solved though:

         * ID/UUID: can always be solved by passing a partial UUID with at least one dash
         * ID/LABEL: appending an exclamation point ! to the identifier, will force LABEL interpretation
         * UUID/LABEL: appending an exclamation point ! to the identifier, will force LABEL interpretation

        As one can see, the user will always be able to include at least one dash of the UUID identifier to prevent it
        from being interpreted as an ID. For the potential ambiguities in LABEL identifiers, we had to introduce a
        special marker to provide a surefire way of breaking any ambiguity that may arise. Adding an exclamation point
        will break the normal strategy and the identifier will directly be interpreted as a LABEL identifier.

        :param value: the value of the identifier
        :returns: the identifier and identifier type
        :raises ValueError: if the value is an invalid identifier
        """
        if not value:
            raise ValueError('the value for the identifier cannot be empty')

        if not isinstance(value, six.string_types):
            value = str(value)

        # If the final character of the value is the special marker, we enforce LABEL interpretation
        if value[-1] == cls.LABEL_AMBIGUITY_BREAKER_CHARACTER:

            identifier = value.rstrip(cls.LABEL_AMBIGUITY_BREAKER_CHARACTER)
            identifier_type = IdentifierType.LABEL

        else:

            # If the value can be cast into an integer, interpret it as an ID
            try:
                identifier = int(value)
                identifier_type = IdentifierType.ID
            except ValueError:

                # If the value is a valid base sixteen encoded integer, after dashes are removed, interpret it as a UUID
                try:
                    hexadecimal = int(value.replace('-', ''), 16)
                    identifier = value
                    identifier_type = IdentifierType.UUID

                # If that fails, interpret it as a LABEL
                except ValueError:
                    identifier = value
                    identifier_type = IdentifierType.LABEL

        return identifier, identifier_type


class CalculationEntityLoader(OrmEntityLoader):

    @classproperty
    def orm_base_class(cls):
        """
        Return the orm base class to which loaded entities should be mapped. Actual queries to load an entity
        may further narrow the query set by defining a more specific set of orm classes, as long as each of
        those is a strict sub class of the orm base class.

        :returns: the orm base class
        """
        from aiida.orm.calculation import Calculation
        return Calculation

    @classmethod
    def _get_query_builder_label_identifier(cls, identifier, classes):
        """
        Return the query builder instance that attempts to map the identifier onto an entity of the orm class,
        defined for this loader class, interpreting the identifier as a LABEL like identifier

        :param identifier: the LABEL identifier
        :param classes: a tuple of orm classes to which the identifier should be mapped
        :returns: the query builder instance that should retrieve the entity corresponding to the identifier
        :raises ValueError: if the identifier is invalid
        :raises NotExistent: if the orm base class does not support a LABEL like identifier
        """
        qb = QueryBuilder()
        qb.append(cls=classes, tag='calculation', project=['*'], filters={'label': {'==': identifier}})

        return qb


class CodeEntityLoader(OrmEntityLoader):

    @classproperty
    def orm_base_class(cls):
        """
        Return the orm base class to which loaded entities should be mapped. Actual queries to load an entity
        may further narrow the query set by defining a more specific set of orm classes, as long as each of
        those is a strict sub class of the orm base class.

        :returns: the orm base class
        """
        from aiida.orm.code import Code
        return Code

    @classmethod
    def _get_query_builder_label_identifier(cls, identifier, classes):
        """
        Return the query builder instance that attempts to map the identifier onto an entity of the orm class,
        defined for this loader class, interpreting the identifier as a LABEL like identifier

        :param identifier: the LABEL identifier
        :param classes: a tuple of orm classes to which the identifier should be mapped
        :returns: the query builder instance that should retrieve the entity corresponding to the identifier
        :raises ValueError: if the identifier is invalid
        :raises NotExistent: if the orm base class does not support a LABEL like identifier
        """
        from aiida.orm.computers import Computer

        try:
            label, sep, machinename = identifier.partition('@')
        except AttributeError as exception:
            raise ValueError('the identifier needs to be a string')

        qb = QueryBuilder()
        qb.append(cls=classes, tag='code', project=['*'], filters={'label': {'==': label}})

        if machinename:
            qb.append(Computer, filters={'name': {'==': machinename}}, computer_of='code')

        return qb


class ComputerEntityLoader(OrmEntityLoader):

    @classproperty
    def orm_base_class(cls):
        """
        Return the orm base class to which loaded entities should be mapped. Actual queries to load an entity
        may further narrow the query set by defining a more specific set of orm classes, as long as each of
        those is a strict sub class of the orm base class.

        :returns: the orm base class
        """
        from aiida.orm.computers import Computer
        return Computer

    @classmethod
    def _get_query_builder_label_identifier(cls, identifier, classes):
        """
        Return the query builder instance that attempts to map the identifier onto an entity of the orm class,
        defined for this loader class, interpreting the identifier as a LABEL like identifier

        :param identifier: the LABEL identifier
        :param classes: a tuple of orm classes to which the identifier should be mapped
        :returns: the query builder instance that should retrieve the entity corresponding to the identifier
        :raises ValueError: if the identifier is invalid
        :raises NotExistent: if the orm base class does not support a LABEL like identifier
        """
        qb = QueryBuilder()
        qb.append(cls=classes, tag='computer', project=['*'], filters={'name': {'==': identifier}})

        return qb


class DataEntityLoader(OrmEntityLoader):

    @classproperty
    def orm_base_class(cls):
        """
        Return the orm base class to which loaded entities should be mapped. Actual queries to load an entity
        may further narrow the query set by defining a more specific set of orm classes, as long as each of
        those is a strict sub class of the orm base class.

        :returns: the orm base class
        """
        from aiida.orm.data import Data
        return Data

    @classmethod
    def _get_query_builder_label_identifier(cls, identifier, classes):
        """
        Return the query builder instance that attempts to map the identifier onto an entity of the orm class,
        defined for this loader class, interpreting the identifier as a LABEL like identifier

        :param identifier: the LABEL identifier
        :param classes: a tuple of orm classes to which the identifier should be mapped
        :returns: the query builder instance that should retrieve the entity corresponding to the identifier
        :raises ValueError: if the identifier is invalid
        :raises NotExistent: if the orm base class does not support a LABEL like identifier
        """
        qb = QueryBuilder()
        qb.append(cls=classes, tag='calculation', project=['*'], filters={'label': {'==': identifier}})

        return qb


class GroupEntityLoader(OrmEntityLoader):

    @classproperty
    def orm_base_class(cls):
        """
        Return the orm base class to which loaded entities should be mapped. Actual queries to load an entity
        may further narrow the query set by defining a more specific set of orm classes, as long as each of
        those is a strict sub class of the orm base class.

        :returns: the orm base class
        """
        from aiida.orm.group import Group
        return Group

    @classmethod
    def _get_query_builder_label_identifier(cls, identifier, classes):
        """
        Return the query builder instance that attempts to map the identifier onto an entity of the orm class,
        defined for this loader class, interpreting the identifier as a LABEL like identifier

        :param identifier: the LABEL identifier
        :param classes: a tuple of orm classes to which the identifier should be mapped
        :returns: the query builder instance that should retrieve the entity corresponding to the identifier
        :raises ValueError: if the identifier is invalid
        :raises NotExistent: if the orm base class does not support a LABEL like identifier
        """
        qb = QueryBuilder()
        qb.append(cls=classes, tag='group', project=['*'], filters={'name': {'==': identifier}})

        return qb


class NodeEntityLoader(OrmEntityLoader):

    @classproperty
    def orm_base_class(cls):
        """
        Return the orm base class to which loaded entities should be mapped. Actual queries to load an entity
        may further narrow the query set by defining a more specific set of orm classes, as long as each of
        those is a strict sub class of the orm base class.

        :returns: the orm base class
        """
        from aiida.orm.node import Node
        return Node

    @classmethod
    def _get_query_builder_label_identifier(cls, identifier, classes):
        """
        Return the query builder instance that attempts to map the identifier onto an entity of the orm class,
        defined for this loader class, interpreting the identifier as a LABEL like identifier

        :param identifier: the LABEL identifier
        :param classes: a tuple of orm classes to which the identifier should be mapped
        :returns: the query builder instance that should retrieve the entity corresponding to the identifier
        :raises ValueError: if the identifier is invalid
        :raises NotExistent: if the orm base class does not support a LABEL like identifier
        """
        qb = QueryBuilder()
        qb.append(cls=classes, tag='node', project=['*'], filters={'label': {'==': identifier}})

        return qb


class LegacyWorkflowLoader(OrmEntityLoader):

    @classmethod
    def load_entity(cls, identifier, identifier_type=None, sub_classes=None, query_with_dashes=True):
        from aiida.orm import Workflow

        if identifier_type is None:
            identifier, identifier_type = cls.infer_identifier_type(identifier)

        if identifier_type == IdentifierType.ID:
            result = Workflow.query(pk=identifier)
        elif identifier_type == IdentifierType.UUID:
            result = Workflow.query(uuid=identifier)
        elif identifier_type == IdentifierType.LABEL:
            result = Workflow.query(label=identifier)

        result = [workflow for workflow in result]

        if len(result) > 1:
            error = 'multiple legacy workflows found with {} <{}>'.format(identifier_type, identifier)
            raise MultipleObjectsError(error)
        elif not result:
            error = 'no legacy workflow found with {} <{}>'.format(identifier_type, identifier)
            raise NotExistent(error)

        return result[0]
