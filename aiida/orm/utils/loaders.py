# -*- coding: utf-8 -*-
from abc import ABCMeta
from enum import Enum

from aiida.common.exceptions import MultipleObjectsError, NotExistent
from aiida.common.utils import abstractclassmethod, classproperty
from aiida.orm.querybuilder import QueryBuilder

__all__ = [
    'get_loader', 'OrmEntityLoader', 'CodeEntityLoader', 'ComputerEntityLoader', 'GroupEntityLoader', 'NodeEntityLoader'
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


class OrmEntityLoader(object):

    __metaclass__ = ABCMeta

    LABEL_AMBIGUITY_BREAKER_CHARACTER = '!'

    @classproperty
    def orm_class(self):
        """
        Return the orm class to which loaded entities should be mapped

        :returns: the orm class
        """
        raise NotImplementedError

    @abstractclassmethod
    def _get_query_builder_label_identifier(self, identifier, orm_class):
        """
        Return the query builder instance that attempts to map the identifier onto an entity of the orm class,
        defined for this loader class, interpreting the identifier as a LABEL like identifier

        :param identifier: the LABEL identifier
        :param orm_class: the class of the entity to query for
        :returns: the query builder instance
        :raises ValueError: if the identifier is invalid
        :raises NotExistent: if the orm class does not support a LABEL like identifier
        """
        raise NotImplementedError

    @classmethod
    def _get_query_builder_id_identifier(self, identifier, orm_class):
        """
        Return the query builder instance that attempts to map the identifier onto an entity of the orm class,
        defined for this loader class, interpreting the identifier as an ID like identifier

        :param identifier: the ID identifier
        :param orm_class: the class of the entity to query for
        :returns: the query builder instance
        """
        qb = QueryBuilder()
        qb.append(orm_class, tag='entity', project=['*'])
        qb.add_filter('entity', {'id': identifier})

        return qb

    @classmethod
    def _get_query_builder_uuid_identifier(self, identifier, orm_class, query_with_dashes):
        """
        Return the query builder instance that attempts to map the identifier onto an entity of the orm class,
        defined for this loader class, interpreting the identifier as a UUID like identifier

        :param identifier: the UUID identifier
        :param orm_class: the class of the entity to query for
        :returns: the query builder instance
        """
        uuid = identifier.replace('-', '')

        if query_with_dashes:
            for dash_pos in [20, 16, 12, 8]:
                if len(uuid) > dash_pos:
                    uuid = '{}-{}'.format(uuid[:dash_pos], uuid[dash_pos:])

        qb = QueryBuilder()
        qb.append(orm_class, tag='entity', project=['*'])
        qb.add_filter('entity', {'uuid': {'like': '{}%'.format(uuid)}})

        return qb

    @classmethod
    def get_query_builder(cls, identifier, identifier_type=None, orm_class=None, query_with_dashes=True):
        """
        Return the query builder instance that attempts to map the identifier onto an entity of the orm class,
        defined for this loader class, inferring the identifier type if it is not defined.

        :param identifier: the identifier
        :param identifier_type: the type of the identifier
        :param orm_class: an optional subclass of the base orm class to make the query more specific
        :returns: the query builder instance
        """
        orm_class = cls.validate_orm_class(orm_class)

        if identifier_type is None:
            identifier, identifier_type = cls.infer_identifier_type(identifier)

        if identifier_type == IdentifierType.ID:
            qb = cls._get_query_builder_id_identifier(identifier, orm_class)
        elif identifier_type == IdentifierType.UUID:
            qb = cls._get_query_builder_uuid_identifier(identifier, orm_class, query_with_dashes)
        elif identifier_type == IdentifierType.LABEL:
            qb = cls._get_query_builder_label_identifier(identifier, orm_class)

        return qb

    @classmethod
    def load_entity(cls, identifier, identifier_type=None, orm_class=None, query_with_dashes=True):
        """
        Load an entity that uniquely corresponds to the provided identifier of the identifier type.

        :param identifier: the identifier
        :param identifier_type: the type of the identifier
        :param orm_class: an optional subclass of the base orm class make the query more specific
        :returns: the loaded entity
        :raises MultipleObjectsError: if the identifier maps onto multiple entities
        :raises NotExistent: if the identifier maps onto not a single entity
        """
        orm_class = cls.validate_orm_class(orm_class)

        if identifier_type is None:
            identifier, identifier_type = cls.infer_identifier_type(identifier)

        qb = cls.get_query_builder(identifier, identifier_type, orm_class, query_with_dashes)
        qb.limit(2)

        try:
            entity = qb.one()[0]
        except MultipleObjectsError:
            error = 'multiple {} entries found with {}<{}>'.format(orm_class.__name__, identifier_type.value, identifier)
            raise MultipleObjectsError(error)
        except NotExistent:
            error = 'no {} found with {}<{}>'.format(orm_class.__name__, identifier_type.value, identifier)
            raise NotExistent(error)

        return entity

    @classmethod
    def validate_orm_class(cls, orm_class=None):
        """
        Validate the orm_class if a user passes in a specifc one when attempting to load an entity. The orm class
        should be a subclass of the entity loader's base class

        :returns: the base orm class or the specific orm class if it is valid
        :raises ValueError: if the defined orm_class is not a subclass of the entity loader's base class
        """
        if orm_class is not None and not issubclass(orm_class, cls.orm_class):
            raise ValueError('the specified orm_class is not a proper sub class of the base orm class')

        if orm_class is None:
            orm_class = cls.orm_class

        return orm_class

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

        if not isinstance(value, basestring):
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


class CodeEntityLoader(OrmEntityLoader):

    @classproperty
    def orm_class(cls):
        """
        Return the orm class to which loaded entities should be mapped

        :returns: the orm class
        """
        from aiida.orm.code import Code
        return Code

    @classmethod
    def _get_query_builder_label_identifier(cls, identifier, orm_class):
        """
        Return the query builder instance that attempts to map the identifier onto an entity of the orm class,
        defined for this loader class, interpreting the identifier as a LABEL like identifier

        :param identifier: the LABEL identifier
        :param orm_class: the class of the entity to query for
        :returns: the query builder instance that should retrieve the entity corresponding to the identifier
        :raises ValueError: if the identifier is invalid
        :raises NotExistent: if the orm class does not support a LABEL like identifier
        """
        from aiida.orm.computer import Computer

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

    @classproperty
    def orm_class(cls):
        """
        Return the orm class to which loaded entities should be mapped

        :returns: the orm class
        """
        from aiida.orm.computer import Computer
        return Computer

    @classmethod
    def _get_query_builder_label_identifier(cls, identifier, orm_class):
        """
        Return the query builder instance that attempts to map the identifier onto an entity of the orm class,
        defined for this loader class, interpreting the identifier as a LABEL like identifier

        :param identifier: the LABEL identifier
        :param orm_class: the class of the entity to query for
        :returns: the query builder instance that should retrieve the entity corresponding to the identifier
        :raises ValueError: if the identifier is invalid
        :raises NotExistent: if the orm class does not support a LABEL like identifier
        """
        qb = QueryBuilder()
        qb.append(orm_class, tag='computer', project=['*'], filters={'name': {'==': identifier}})

        return qb


class GroupEntityLoader(OrmEntityLoader):

    @classproperty
    def orm_class(cls):
        """
        Return the orm class to which loaded entities should be mapped

        :returns: the orm class
        """
        from aiida.orm.group import Group
        return Group

    @classmethod
    def _get_query_builder_label_identifier(cls, identifier, orm_class):
        """
        Return the query builder instance that attempts to map the identifier onto an entity of the orm class,
        defined for this loader class, interpreting the identifier as a LABEL like identifier

        :param identifier: the LABEL identifier
        :param orm_class: the class of the entity to query for
        :returns: the query builder instance that should retrieve the entity corresponding to the identifier
        :raises ValueError: if the identifier is invalid
        :raises NotExistent: if the orm class does not support a LABEL like identifier
        """
        qb = QueryBuilder()
        qb.append(orm_class, tag='group', project=['*'], filters={'name': {'==': identifier}})

        return qb


class NodeEntityLoader(OrmEntityLoader):

    @classproperty
    def orm_class(cls):
        """
        Return the orm class to which loaded entities should be mapped

        :returns: the orm class
        """
        from aiida.orm.node import Node
        return Node

    @classmethod
    def _get_query_builder_label_identifier(cls, identifier, orm_class):
        """
        Return the query builder instance that attempts to map the identifier onto an entity of the orm class,
        defined for this loader class, interpreting the identifier as a LABEL like identifier

        :param identifier: the LABEL identifier
        :param orm_class: the class of the entity to query for
        :returns: the query builder instance that should retrieve the entity corresponding to the identifier
        :raises ValueError: if the identifier is invalid
        :raises NotExistent: if the orm class does not support a LABEL like identifier
        """
        raise NotExistent
