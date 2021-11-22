# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Module with `OrmEntityLoader` and its sub classes that simplify loading entities through their identifiers."""
from abc import abstractmethod
from enum import Enum
from typing import TYPE_CHECKING

from aiida.common.exceptions import MultipleObjectsError, NotExistent
from aiida.common.lang import classproperty
from aiida.orm.querybuilder import QueryBuilder

if TYPE_CHECKING:
    from aiida.orm import Code, Computer, Group, Node

__all__ = (
    'load_code', 'load_computer', 'load_group', 'load_node', 'load_entity', 'get_loader', 'OrmEntityLoader',
    'CalculationEntityLoader', 'CodeEntityLoader', 'ComputerEntityLoader', 'GroupEntityLoader', 'NodeEntityLoader'
)


def load_entity(
    entity_loader=None, identifier=None, pk=None, uuid=None, label=None, sub_classes=None, query_with_dashes=True
):
    # pylint: disable=too-many-arguments
    """
    Load an entity instance by one of its identifiers: pk, uuid or label

    If the type of the identifier is unknown simply pass it without a keyword and the loader will attempt to
    automatically infer the type.

    :param identifier: pk (integer), uuid (string) or label (string) of a Code
    :param pk: pk of a Code
    :param uuid: uuid of a Code, or the beginning of the uuid
    :param label: label of a Code
    :param sub_classes: an optional tuple of orm classes to narrow the queryset. Each class should be a strict sub class
        of the ORM class of the given entity loader.
    :param bool query_with_dashes: allow to query for a uuid with dashes
    :returns: the Code instance
    :raise ValueError: if none or more than one of the identifiers are supplied
    :raise TypeError: if the provided identifier has the wrong type
    :raise aiida.common.NotExistent: if no matching Code is found
    :raise aiida.common.MultipleObjectsError: if more than one Code was found
    """
    if entity_loader is None or not issubclass(entity_loader, OrmEntityLoader):
        raise TypeError(f'entity_loader should be a sub class of {type(OrmEntityLoader)}')

    inputs_provided = [value is not None for value in (identifier, pk, uuid, label)].count(True)

    if inputs_provided == 0:
        raise ValueError("one of the parameters 'identifier', pk', 'uuid' or 'label' has to be specified")
    elif inputs_provided > 1:
        raise ValueError("only one of parameters 'identifier', pk', 'uuid' or 'label' has to be specified")

    if pk is not None:

        if not isinstance(pk, int):
            raise TypeError('a pk has to be an integer')

        identifier = pk
        identifier_type = IdentifierType.ID

    elif uuid is not None:

        if not isinstance(uuid, str):
            raise TypeError('uuid has to be a string type')

        identifier = uuid
        identifier_type = IdentifierType.UUID

    elif label is not None:

        if not isinstance(label, str):
            raise TypeError('label has to be a string type')

        identifier = label
        identifier_type = IdentifierType.LABEL
    else:
        identifier = str(identifier)
        identifier_type = None

    return entity_loader.load_entity(
        identifier, identifier_type, sub_classes=sub_classes, query_with_dashes=query_with_dashes
    )


def load_code(identifier=None, pk=None, uuid=None, label=None, sub_classes=None, query_with_dashes=True) -> 'Code':
    """
    Load a Code instance by one of its identifiers: pk, uuid or label

    If the type of the identifier is unknown simply pass it without a keyword and the loader will attempt to
    automatically infer the type.

    :param identifier: pk (integer), uuid (string) or label (string) of a Code
    :param pk: pk of a Code
    :param uuid: uuid of a Code, or the beginning of the uuid
    :param label: label of a Code
    :param sub_classes: an optional tuple of orm classes to narrow the queryset. Each class should be a strict sub class
        of the ORM class of the given entity loader.
    :param bool query_with_dashes: allow to query for a uuid with dashes
    :return: the Code instance
    :raise ValueError: if none or more than one of the identifiers are supplied
    :raise TypeError: if the provided identifier has the wrong type
    :raise aiida.common.NotExistent: if no matching Code is found
    :raise aiida.common.MultipleObjectsError: if more than one Code was found
    """
    return load_entity(
        CodeEntityLoader,
        identifier=identifier,
        pk=pk,
        uuid=uuid,
        label=label,
        sub_classes=sub_classes,
        query_with_dashes=query_with_dashes
    )


def load_computer(
    identifier=None, pk=None, uuid=None, label=None, sub_classes=None, query_with_dashes=True
) -> 'Computer':
    """
    Load a Computer instance by one of its identifiers: pk, uuid or label

    If the type of the identifier is unknown simply pass it without a keyword and the loader will attempt to
    automatically infer the type.

    :param identifier: pk (integer), uuid (string) or label (string) of a Computer
    :param pk: pk of a Computer
    :param uuid: uuid of a Computer, or the beginning of the uuid
    :param label: label of a Computer
    :param sub_classes: an optional tuple of orm classes to narrow the queryset. Each class should be a strict sub class
        of the ORM class of the given entity loader.
    :param bool query_with_dashes: allow to query for a uuid with dashes
    :return: the Computer instance
    :raise ValueError: if none or more than one of the identifiers are supplied
    :raise TypeError: if the provided identifier has the wrong type
    :raise aiida.common.NotExistent: if no matching Computer is found
    :raise aiida.common.MultipleObjectsError: if more than one Computer was found
    """
    return load_entity(
        ComputerEntityLoader,
        identifier=identifier,
        pk=pk,
        uuid=uuid,
        label=label,
        sub_classes=sub_classes,
        query_with_dashes=query_with_dashes
    )


def load_group(identifier=None, pk=None, uuid=None, label=None, sub_classes=None, query_with_dashes=True) -> 'Group':
    """
    Load a Group instance by one of its identifiers: pk, uuid or label

    If the type of the identifier is unknown simply pass it without a keyword and the loader will attempt to
    automatically infer the type.

    :param identifier: pk (integer), uuid (string) or label (string) of a Group
    :param pk: pk of a Group
    :param uuid: uuid of a Group, or the beginning of the uuid
    :param label: label of a Group
    :param sub_classes: an optional tuple of orm classes to narrow the queryset. Each class should be a strict sub class
        of the ORM class of the given entity loader.
    :param bool query_with_dashes: allow to query for a uuid with dashes
    :return: the Group instance
    :raise ValueError: if none or more than one of the identifiers are supplied
    :raise TypeError: if the provided identifier has the wrong type
    :raise aiida.common.NotExistent: if no matching Group is found
    :raise aiida.common.MultipleObjectsError: if more than one Group was found
    """
    return load_entity(
        GroupEntityLoader,
        identifier=identifier,
        pk=pk,
        uuid=uuid,
        label=label,
        sub_classes=sub_classes,
        query_with_dashes=query_with_dashes
    )


def load_node(identifier=None, pk=None, uuid=None, label=None, sub_classes=None, query_with_dashes=True) -> 'Node':
    """
    Load a node by one of its identifiers: pk or uuid. If the type of the identifier is unknown
    simply pass it without a keyword and the loader will attempt to infer the type

    :param identifier: pk (integer) or uuid (string)
    :param pk: pk of a node
    :param uuid: uuid of a node, or the beginning of the uuid
    :param label: label of a Node
    :param sub_classes: an optional tuple of orm classes to narrow the queryset. Each class should be a strict sub class
        of the ORM class of the given entity loader.
    :param bool query_with_dashes: allow to query for a uuid with dashes
    :returns: the node instance
    :raise ValueError: if none or more than one of the identifiers are supplied
    :raise TypeError: if the provided identifier has the wrong type
    :raise aiida.common.NotExistent: if no matching Node is found
    :raise aiida.common.MultipleObjectsError: if more than one Node was found
    """
    return load_entity(
        NodeEntityLoader,
        identifier=identifier,
        pk=pk,
        uuid=uuid,
        label=label,
        sub_classes=sub_classes,
        query_with_dashes=query_with_dashes
    )


def get_loader(orm_class):
    """Return the correct OrmEntityLoader for the given orm class.

    :param orm_class: the orm class
    :returns: a subclass of OrmEntityLoader
    :raises ValueError: if no OrmEntityLoader subclass can be found for the given orm class
    """
    from aiida.orm import Code, Computer, Group, Node

    if issubclass(orm_class, Code):
        return CodeEntityLoader

    if issubclass(orm_class, Computer):
        return ComputerEntityLoader

    if issubclass(orm_class, Group):
        return GroupEntityLoader

    if issubclass(orm_class, Node):
        return NodeEntityLoader

    raise ValueError(f'no OrmEntityLoader available for {orm_class}')


class IdentifierType(Enum):
    """
    The enumeration that defines the three types of identifier that can be used to identify an orm entity.
    The ID is always an integer, the UUID a base 16 encoded integer with optional dashes and the LABEL can
    be any string based label or name, the format of which will vary per orm class
    """
    # pylint: disable=invalid-name

    ID = 'ID'
    UUID = 'UUID'
    LABEL = 'LABEL'


class OrmEntityLoader:
    """Base class for entity loaders."""

    label_ambiguity_breaker = '!'

    @classproperty
    def orm_base_class(self):
        """
        Return the orm base class to which loaded entities should be mapped. Actual queries to load an entity
        may further narrow the query set by defining a more specific set of orm classes, as long as each of
        those is a strict sub class of the orm base class.

        :returns: the orm base class
        """
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def _get_query_builder_label_identifier(cls, identifier, classes, operator='==', project='*'):
        """
        Return the query builder instance that attempts to map the identifier onto an entity of the orm class,
        defined for this loader class, interpreting the identifier as a LABEL like identifier

        :param identifier: the LABEL identifier
        :param classes: a tuple of orm classes to which the identifier should be mapped
        :param operator: the operator to use in the query
        :param project: the property or properties to project for entities matching the query
        :returns: the query builder instance
        :raises ValueError: if the identifier is invalid
        :raises aiida.common.NotExistent: if the orm base class does not support a LABEL like identifier
        """
        raise NotImplementedError

    @classmethod
    def _get_query_builder_id_identifier(cls, identifier, classes):
        """
        Return the query builder instance that attempts to map the identifier onto an entity of the orm class,
        defined for this loader class, interpreting the identifier as an ID like identifier

        :param identifier: the ID identifier
        :param classes: a tuple of orm classes to which the identifier should be mapped
        :returns: the query builder instance
        """
        builder = QueryBuilder()
        builder.append(cls=classes, tag='entity', project=['*'])
        builder.add_filter('entity', {'id': identifier})

        return builder

    @classmethod
    def _get_query_builder_uuid_identifier(cls, identifier, classes, query_with_dashes):
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
                    uuid = f'{uuid[:dash_pos]}-{uuid[dash_pos:]}'

        builder = QueryBuilder()
        builder.append(cls=classes, tag='entity', project=['*'])

        # If a UUID can be constructed from the identifier, it is a full UUID and the query can use an equality operator
        try:
            UUID(uuid)
        except ValueError:
            builder.add_filter('entity', {'uuid': {'like': f'{uuid}%'}})
        else:
            builder.add_filter('entity', {'uuid': uuid})

        return builder

    @classmethod
    def get_query_builder(
        cls, identifier, identifier_type=None, sub_classes=None, query_with_dashes=True, operator='==', project='*'
    ):
        """
        Return the query builder instance that attempts to map the identifier onto an entity of the orm class,
        defined for this loader class, inferring the identifier type if it is not defined.

        :param identifier: the identifier
        :param identifier_type: the type of the identifier
        :param sub_classes: an optional tuple of orm classes, that should each be strict sub classes of the
            base orm class of the loader, that will narrow the queryset
        :param operator: the operator to use in the query
        :param project: the property or properties to project for entities matching the query
        :returns: the query builder instance and a dictionary of used query parameters
        """
        # pylint: disable=too-many-arguments
        classes = cls.get_query_classes(sub_classes)

        if identifier_type is None:
            identifier, identifier_type = cls.infer_identifier_type(identifier)

        if identifier_type == IdentifierType.ID:
            builder = cls._get_query_builder_id_identifier(identifier, classes)
        elif identifier_type == IdentifierType.UUID:
            builder = cls._get_query_builder_uuid_identifier(identifier, classes, query_with_dashes)
        elif identifier_type == IdentifierType.LABEL:
            builder = cls._get_query_builder_label_identifier(identifier, classes, operator, project)

        query_parameters = {
            'classes': classes,
            'identifier': identifier,
            'identifier_type': identifier_type,
        }

        return builder, query_parameters

    @classmethod
    def get_options(cls, incomplete, project='*'):
        """Return the list of entities that match the `incomplete` identifier.

        .. note:: For the time being only `LABEL` auto-completion is supported so the identifier type is not inferred
            but hard-coded to be `IdentifierType.LABEL`

        :param incomplete: the incomplete identifier
        :param project: the field(s) to project for each entity that matches the incomplete identifier
        :return: list of entities matching the incomplete identifier
        """
        builder, _ = cls.get_query_builder(incomplete, IdentifierType.LABEL, operator='like', project=project)
        return builder.all()

    @classmethod
    def load_entity(cls, identifier, identifier_type=None, sub_classes=None, query_with_dashes=True):
        """
        Load an entity that uniquely corresponds to the provided identifier of the identifier type.

        :param identifier: the identifier
        :param identifier_type: the type of the identifier
        :param sub_classes: an optional tuple of orm classes, that should each be strict sub classes of the
            base orm class of the loader, that will narrow the queryset
        :returns: the loaded entity
        :raises aiida.common.MultipleObjectsError: if the identifier maps onto multiple entities
        :raises aiida.common.NotExistent: if the identifier maps onto not a single entity
        """
        builder, query_parameters = cls.get_query_builder(identifier, identifier_type, sub_classes, query_with_dashes)
        builder.limit(2)

        classes = ' or '.join([sub_class.__name__ for sub_class in query_parameters['classes']])
        identifier = query_parameters['identifier']
        identifier_type = query_parameters['identifier_type'].value

        try:
            entity = builder.one()[0]
        except MultipleObjectsError:
            error = f'multiple {classes} entries found with {identifier_type}<{identifier}>'
            raise MultipleObjectsError(error)
        except NotExistent as exception:
            error = f'no {classes} found with {identifier_type}<{identifier}>: {exception}'
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
            raise TypeError(f'sub_classes should be a tuple: {sub_classes}')

        for sub_class in sub_classes:
            if not issubclass(sub_class, cls.orm_base_class):
                raise ValueError(f'{sub_class} is not a sub class of the base orm class {cls.orm_base_class}')

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

        if not isinstance(value, str):
            value = str(value)

        # If the final character of the value is the special marker, we enforce LABEL interpretation
        if value[-1] == cls.label_ambiguity_breaker:

            identifier = value.rstrip(cls.label_ambiguity_breaker)
            identifier_type = IdentifierType.LABEL

        else:

            # If the value can be cast into an integer, interpret it as an ID
            try:
                identifier = int(value)
                identifier_type = IdentifierType.ID
            except ValueError:

                # If the value is a valid base sixteen encoded integer, after dashes are removed, interpret it as a UUID
                try:
                    int(value.replace('-', ''), 16)
                    identifier = value
                    identifier_type = IdentifierType.UUID

                # If that fails, interpret it as a LABEL
                except ValueError:
                    identifier = value
                    identifier_type = IdentifierType.LABEL

        return identifier, identifier_type


class ProcessEntityLoader(OrmEntityLoader):
    """Loader for the `Process` entity and sub classes."""

    @classproperty
    def orm_base_class(self):
        """
        Return the orm base class to which loaded entities should be mapped. Actual queries to load an entity
        may further narrow the query set by defining a more specific set of orm classes, as long as each of
        those is a strict sub class of the orm base class.

        :returns: the orm base class
        """
        from aiida.orm import ProcessNode
        return ProcessNode

    @classmethod
    def _get_query_builder_label_identifier(cls, identifier, classes, operator='==', project='*'):
        """
        Return the query builder instance that attempts to map the identifier onto an entity of the orm class,
        defined for this loader class, interpreting the identifier as a LABEL like identifier

        :param identifier: the LABEL identifier
        :param classes: a tuple of orm classes to which the identifier should be mapped
        :param operator: the operator to use in the query
        :param project: the property or properties to project for entities matching the query
        :returns: the query builder instance that should retrieve the entity corresponding to the identifier
        :raises ValueError: if the identifier is invalid
        :raises aiida.common.NotExistent: if the orm base class does not support a LABEL like identifier
        """
        from aiida.common.escaping import escape_for_sql_like

        if operator == 'like':
            identifier = f'{escape_for_sql_like(identifier)}%'

        builder = QueryBuilder()
        builder.append(cls=classes, tag='process', project=project, filters={'label': {operator: identifier}})

        return builder


class CalculationEntityLoader(OrmEntityLoader):
    """Loader for the `Calculation` entity and sub classes."""

    @classproperty
    def orm_base_class(self):
        """
        Return the orm base class to which loaded entities should be mapped. Actual queries to load an entity
        may further narrow the query set by defining a more specific set of orm classes, as long as each of
        those is a strict sub class of the orm base class.

        :returns: the orm base class
        """
        from aiida.orm import CalculationNode
        return CalculationNode

    @classmethod
    def _get_query_builder_label_identifier(cls, identifier, classes, operator='==', project='*'):
        """
        Return the query builder instance that attempts to map the identifier onto an entity of the orm class,
        defined for this loader class, interpreting the identifier as a LABEL like identifier

        :param identifier: the LABEL identifier
        :param classes: a tuple of orm classes to which the identifier should be mapped
        :param operator: the operator to use in the query
        :param project: the property or properties to project for entities matching the query
        :returns: the query builder instance that should retrieve the entity corresponding to the identifier
        :raises ValueError: if the identifier is invalid
        :raises aiida.common.NotExistent: if the orm base class does not support a LABEL like identifier
        """
        from aiida.common.escaping import escape_for_sql_like

        if operator == 'like':
            identifier = f'{escape_for_sql_like(identifier)}%'

        builder = QueryBuilder()
        builder.append(cls=classes, tag='calculation', project=project, filters={'label': {operator: identifier}})

        return builder


class WorkflowEntityLoader(OrmEntityLoader):
    """Loader for the `Workflow` entity and sub classes."""

    @classproperty
    def orm_base_class(self):
        """
        Return the orm base class to which loaded entities should be mapped. Actual queries to load an entity
        may further narrow the query set by defining a more specific set of orm classes, as long as each of
        those is a strict sub class of the orm base class.

        :returns: the orm base class
        """
        from aiida.orm import WorkflowNode
        return WorkflowNode

    @classmethod
    def _get_query_builder_label_identifier(cls, identifier, classes, operator='==', project='*'):
        """
        Return the query builder instance that attempts to map the identifier onto an entity of the orm class,
        defined for this loader class, interpreting the identifier as a LABEL like identifier

        :param identifier: the LABEL identifier
        :param classes: a tuple of orm classes to which the identifier should be mapped
        :param operator: the operator to use in the query
        :param project: the property or properties to project for entities matching the query
        :returns: the query builder instance that should retrieve the entity corresponding to the identifier
        :raises ValueError: if the identifier is invalid
        :raises aiida.common.NotExistent: if the orm base class does not support a LABEL like identifier
        """
        from aiida.common.escaping import escape_for_sql_like

        if operator == 'like':
            identifier = f'{escape_for_sql_like(identifier)}%'

        builder = QueryBuilder()
        builder.append(cls=classes, tag='workflow', project=project, filters={'label': {operator: identifier}})

        return builder


class CodeEntityLoader(OrmEntityLoader):
    """Loader for the `Code` entity and sub classes."""

    @classproperty
    def orm_base_class(self):
        """
        Return the orm base class to which loaded entities should be mapped. Actual queries to load an entity
        may further narrow the query set by defining a more specific set of orm classes, as long as each of
        those is a strict sub class of the orm base class.

        :returns: the orm base class
        """
        from aiida.orm import Code
        return Code

    @classmethod
    def _get_query_builder_label_identifier(cls, identifier, classes, operator='==', project='*'):
        """
        Return the query builder instance that attempts to map the identifier onto an entity of the orm class,
        defined for this loader class, interpreting the identifier as a LABEL like identifier

        :param identifier: the LABEL identifier
        :param classes: a tuple of orm classes to which the identifier should be mapped
        :param operator: the operator to use in the query
        :param project: the property or properties to project for entities matching the query
        :returns: the query builder instance that should retrieve the entity corresponding to the identifier
        :raises ValueError: if the identifier is invalid
        :raises aiida.common.NotExistent: if the orm base class does not support a LABEL like identifier
        """
        from aiida.common.escaping import escape_for_sql_like
        from aiida.orm import Computer

        try:
            identifier, _, machinename = identifier.partition('@')
        except AttributeError:
            raise ValueError('the identifier needs to be a string')

        if operator == 'like':
            identifier = f'{escape_for_sql_like(identifier)}%'

        builder = QueryBuilder()
        builder.append(cls=classes, tag='code', project=project, filters={'label': {operator: identifier}})

        if machinename:
            builder.append(Computer, filters={'label': {'==': machinename}}, with_node='code')

        return builder


class ComputerEntityLoader(OrmEntityLoader):
    """Loader for the `Computer` entity and sub classes."""

    @classproperty
    def orm_base_class(self):
        """
        Return the orm base class to which loaded entities should be mapped. Actual queries to load an entity
        may further narrow the query set by defining a more specific set of orm classes, as long as each of
        those is a strict sub class of the orm base class.

        :returns: the orm base class
        """
        from aiida.orm import Computer
        return Computer

    @classmethod
    def _get_query_builder_label_identifier(cls, identifier, classes, operator='==', project='*'):
        """
        Return the query builder instance that attempts to map the identifier onto an entity of the orm class,
        defined for this loader class, interpreting the identifier as a LABEL like identifier

        :param identifier: the LABEL identifier
        :param classes: a tuple of orm classes to which the identifier should be mapped
        :param operator: the operator to use in the query
        :param project: the property or properties to project for entities matching the query
        :returns: the query builder instance that should retrieve the entity corresponding to the identifier
        :raises ValueError: if the identifier is invalid
        :raises aiida.common.NotExistent: if the orm base class does not support a LABEL like identifier
        """
        from aiida.common.escaping import escape_for_sql_like

        if operator == 'like':
            identifier = f'{escape_for_sql_like(identifier)}%'

        builder = QueryBuilder()
        builder.append(cls=classes, tag='computer', project=project, filters={'label': {operator: identifier}})

        return builder


class DataEntityLoader(OrmEntityLoader):
    """Loader for the `Data` entity and sub classes."""

    @classproperty
    def orm_base_class(self):
        """
        Return the orm base class to which loaded entities should be mapped. Actual queries to load an entity
        may further narrow the query set by defining a more specific set of orm classes, as long as each of
        those is a strict sub class of the orm base class.

        :returns: the orm base class
        """
        from aiida.orm import Data
        return Data

    @classmethod
    def _get_query_builder_label_identifier(cls, identifier, classes, operator='==', project='*'):
        """
        Return the query builder instance that attempts to map the identifier onto an entity of the orm class,
        defined for this loader class, interpreting the identifier as a LABEL like identifier

        :param identifier: the LABEL identifier
        :param classes: a tuple of orm classes to which the identifier should be mapped
        :param operator: the operator to use in the query
        :param project: the property or properties to project for entities matching the query
        :returns: the query builder instance that should retrieve the entity corresponding to the identifier
        :raises ValueError: if the identifier is invalid
        :raises aiida.common.NotExistent: if the orm base class does not support a LABEL like identifier
        """
        from aiida.common.escaping import escape_for_sql_like

        if operator == 'like':
            identifier = f'{escape_for_sql_like(identifier)}%'

        builder = QueryBuilder()
        builder.append(cls=classes, tag='calculation', project=project, filters={'label': {operator: identifier}})

        return builder


class GroupEntityLoader(OrmEntityLoader):
    """Loader for the `Group` entity and sub classes."""

    @classproperty
    def orm_base_class(self):
        """
        Return the orm base class to which loaded entities should be mapped. Actual queries to load an entity
        may further narrow the query set by defining a more specific set of orm classes, as long as each of
        those is a strict sub class of the orm base class.

        :returns: the orm base class
        """
        from aiida.orm.groups import Group
        return Group

    @classmethod
    def _get_query_builder_label_identifier(cls, identifier, classes, operator='==', project='*'):
        """
        Return the query builder instance that attempts to map the identifier onto an entity of the orm class,
        defined for this loader class, interpreting the identifier as a LABEL like identifier

        :param identifier: the LABEL identifier
        :param classes: a tuple of orm classes to which the identifier should be mapped
        :param operator: the operator to use in the query
        :param project: the property or properties to project for entities matching the query
        :returns: the query builder instance that should retrieve the entity corresponding to the identifier
        :raises ValueError: if the identifier is invalid
        :raises aiida.common.NotExistent: if the orm base class does not support a LABEL like identifier
        """
        from aiida.common.escaping import escape_for_sql_like

        if operator == 'like':
            identifier = f'{escape_for_sql_like(identifier)}%'

        builder = QueryBuilder()
        builder.append(cls=classes, tag='group', project=project, filters={'label': {operator: identifier}})

        return builder


class NodeEntityLoader(OrmEntityLoader):
    """Loader for the `Node` entity and sub classes."""

    @classproperty
    def orm_base_class(self):
        """
        Return the orm base class to which loaded entities should be mapped. Actual queries to load an entity
        may further narrow the query set by defining a more specific set of orm classes, as long as each of
        those is a strict sub class of the orm base class.

        :returns: the orm base class
        """
        from aiida.orm import Node
        return Node

    @classmethod
    def _get_query_builder_label_identifier(cls, identifier, classes, operator='==', project='*'):
        """
        Return the query builder instance that attempts to map the identifier onto an entity of the orm class,
        defined for this loader class, interpreting the identifier as a LABEL like identifier

        :param identifier: the LABEL identifier
        :param classes: a tuple of orm classes to which the identifier should be mapped
        :param operator: the operator to use in the query
        :param project: the property or properties to project for entities matching the query
        :returns: the query builder instance that should retrieve the entity corresponding to the identifier
        :raises ValueError: if the identifier is invalid
        :raises aiida.common.NotExistent: if the orm base class does not support a LABEL like identifier
        """
        from aiida.common.escaping import escape_for_sql_like

        if operator == 'like':
            identifier = f'{escape_for_sql_like(identifier)}%'

        builder = QueryBuilder()
        builder.append(cls=classes, tag='node', project=project, filters={'label': {operator: identifier}})

        return builder
