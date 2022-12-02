# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""AiiDA Group entites"""
from abc import ABCMeta
from functools import cached_property
from typing import TYPE_CHECKING, Any, ClassVar, Optional, Sequence, Tuple, Type, TypeVar, Union, cast
import warnings

from aiida.common import exceptions
from aiida.common.lang import classproperty, type_check
from aiida.common.warnings import warn_deprecation
from aiida.manage import get_manager

from . import convert, entities, extras, users

if TYPE_CHECKING:
    from aiida.orm import Node, User
    from aiida.orm.implementation import BackendGroup, StorageBackend
    from aiida.plugins.entry_point import EntryPoint  # type: ignore

__all__ = ('Group', 'AutoGroup', 'ImportGroup', 'UpfFamily')

SelfType = TypeVar('SelfType', bound='Group')


def load_group_class(type_string: str) -> Type['Group']:
    """Load the sub class of `Group` that corresponds to the given `type_string`.

    .. note:: will fall back on `aiida.orm.groups.Group` if `type_string` cannot be resolved to loadable entry point.

    :param type_string: the entry point name of the `Group` sub class
    :return: sub class of `Group` registered through an entry point
    """
    from aiida.common.exceptions import EntryPointError
    from aiida.plugins.entry_point import load_entry_point

    try:
        group_class = load_entry_point('aiida.groups', type_string)
    except EntryPointError:
        message = f'could not load entry point `{type_string}`, falling back onto `Group` base class.'
        warnings.warn(message)  # pylint: disable=no-member
        group_class = Group

    return group_class


class GroupMeta(ABCMeta):
    """Meta class for `aiida.orm.groups.Group` to automatically set the `type_string` attribute."""

    def __new__(cls, name, bases, namespace, **kwargs):
        from aiida.plugins.entry_point import get_entry_point_from_class

        newcls = ABCMeta.__new__(cls, name, bases, namespace, **kwargs)  # pylint: disable=too-many-function-args

        mod = namespace['__module__']
        entry_point_group, entry_point = get_entry_point_from_class(mod, name)

        if entry_point_group is None or entry_point_group != 'aiida.groups':
            newcls._type_string = None  # type: ignore[attr-defined]
            message = f'no registered entry point for `{mod}:{name}` so its instances will not be storable.'
            warnings.warn(message)  # pylint: disable=no-member
        else:
            assert entry_point is not None
            newcls._type_string = cast(str, entry_point.name)  # type: ignore[attr-defined]  # pylint: disable=protected-access

        return newcls


class GroupCollection(entities.Collection['Group']):
    """Collection of Groups"""

    @staticmethod
    def _entity_base_cls() -> Type['Group']:
        return Group

    def get_or_create(self, label: Optional[str] = None, **kwargs) -> Tuple['Group', bool]:
        """
        Try to retrieve a group from the DB with the given arguments;
        create (and store) a new group if such a group was not present yet.

        :param label: group label

        :return: (group, created) where group is the group (new or existing,
            in any case already stored) and created is a boolean saying
        """
        if not label:
            raise ValueError('Group label must be provided')

        res = self.find(filters={'label': label})

        if not res:
            return self.entity_type(label, backend=self.backend, **kwargs).store(), True

        if len(res) > 1:
            raise exceptions.MultipleObjectsError('More than one groups found in the database')

        return res[0], False

    def delete(self, pk: int) -> None:
        """
        Delete a group

        :param pk: the id of the group to delete
        """
        self._backend.groups.delete(pk)


class GroupBase:
    """A namespace for group related functionality, that is not directly related to its user-facing properties."""

    def __init__(self, group: 'Group') -> None:
        """Construct a new instance of the base namespace."""
        self._group: 'Group' = group

    @cached_property
    def extras(self) -> extras.EntityExtras:
        """Return the extras of this group."""
        return extras.EntityExtras(self._group)


class Group(entities.Entity['BackendGroup', GroupCollection], metaclass=GroupMeta):
    """An AiiDA ORM implementation of group of nodes."""

    # added by metaclass
    _type_string: ClassVar[Optional[str]]

    _CLS_COLLECTION = GroupCollection

    def __init__(
        self,
        label: Optional[str] = None,
        user: Optional['User'] = None,
        description: str = '',
        type_string: Optional[str] = None,
        backend: Optional['StorageBackend'] = None
    ):
        """
        Create a new group. Either pass a dbgroup parameter, to reload
        a group from the DB (and then, no further parameters are allowed),
        or pass the parameters for the Group creation.

        :param label: The group label, required on creation
        :param description: The group description (by default, an empty string)
        :param user: The owner of the group (by default, the automatic user)
        :param type_string: a string identifying the type of group (by default,
            an empty string, indicating an user-defined group.
        """
        if not label:
            raise ValueError('Group label must be provided')

        backend = backend or get_manager().get_profile_storage()
        user = cast(users.User, user or backend.default_user)
        type_check(user, users.User)
        type_string = self._type_string

        model = backend.groups.create(
            label=label, user=user.backend_entity, description=description, type_string=type_string
        )
        super().__init__(model)

    @cached_property
    def base(self) -> GroupBase:
        """Return the group base namespace."""
        return GroupBase(self)

    def __repr__(self) -> str:
        return (
            f'<{self.__class__.__name__}: {self.label!r} '
            f'[{"type " + self.type_string if self.type_string else "user-defined"}], of user {self.user.email}>'
        )

    def __str__(self) -> str:
        return f'{self.__class__.__name__}<{self.label}>'

    def store(self: SelfType) -> SelfType:
        """Verify that the group is allowed to be stored, which is the case along as `type_string` is set."""
        if self._type_string is None:
            raise exceptions.StoringNotAllowed('`type_string` is `None` so the group cannot be stored.')

        return super().store()

    @classproperty
    def entry_point(cls) -> Optional['EntryPoint']:
        """Return the entry point associated this group type.

        :return: the associated entry point or ``None`` if it isn't known.
        """
        # pylint: disable=no-self-use
        from aiida.plugins.entry_point import get_entry_point_from_class
        return get_entry_point_from_class(cls.__module__, cls.__name__)[1]

    @property
    def uuid(self) -> str:
        """Return the UUID for this group.

        This identifier is unique across all entities types and backend instances.

        :return: the entity uuid
        """
        return self._backend_entity.uuid

    @property
    def label(self) -> str:
        """
        :return: the label of the group as a string
        """
        return self._backend_entity.label

    @label.setter
    def label(self, label: str) -> None:
        """
        Attempt to change the label of the group instance. If the group is already stored
        and the another group of the same type already exists with the desired label, a
        UniquenessError will be raised

        :param label: the new group label
        :type label: str

        :raises aiida.common.UniquenessError: if another group of same type and label already exists
        """
        self._backend_entity.label = label

    @property
    def description(self) -> str:
        """
        :return: the description of the group as a string
        """
        return self._backend_entity.description or ''

    @description.setter
    def description(self, description: str) -> None:
        """
        :param description: the description of the group as a string
        """
        self._backend_entity.description = description

    @property
    def type_string(self) -> str:
        """
        :return: the string defining the type of the group
        """
        return self._backend_entity.type_string

    @property
    def user(self) -> 'User':
        """
        :return: the user associated with this group
        """
        return users.User.from_backend_entity(self._backend_entity.user)

    @user.setter
    def user(self, user: 'User') -> None:
        """Set the user.

        :param user: the user
        """
        type_check(user, users.User)
        self._backend_entity.user = user.backend_entity

    def count(self) -> int:
        """Return the number of entities in this group.

        :return: integer number of entities contained within the group
        """
        return self._backend_entity.count()

    @property
    def nodes(self) -> convert.ConvertIterator:
        """
        Return a generator/iterator that iterates over all nodes and returns
        the respective AiiDA subclasses of Node, and also allows to ask for
        the number of nodes in the group using len().
        """
        return convert.ConvertIterator(self._backend_entity.nodes)

    @property
    def is_empty(self) -> bool:
        """Return whether the group is empty, i.e. it does not contain any nodes.

        :return: True if it contains no nodes, False otherwise
        """
        try:
            self.nodes[0]
        except IndexError:
            return True
        else:
            return False

    def clear(self) -> None:
        """Remove all the nodes from this group."""
        return self._backend_entity.clear()

    def add_nodes(self, nodes: Union['Node', Sequence['Node']]) -> None:
        """Add a node or a set of nodes to the group.

        :note: all the nodes *and* the group itself have to be stored.

        :param nodes: a single `Node` or a list of `Nodes`
        """
        from .nodes import Node

        if not self.is_stored:
            raise exceptions.ModificationNotAllowed('cannot add nodes to an unstored group')

        # Cannot use `collections.Iterable` here, because that would also match iterable `Node` sub classes like `List`
        if not isinstance(nodes, (list, tuple)):
            nodes = [nodes]  # type: ignore

        for node in nodes:
            type_check(node, Node)

        self._backend_entity.add_nodes([node.backend_entity for node in nodes])

    def remove_nodes(self, nodes: Union['Node', Sequence['Node']]) -> None:
        """Remove a node or a set of nodes to the group.

        :note: all the nodes *and* the group itself have to be stored.

        :param nodes: a single `Node` or a list of `Nodes`
        """
        from .nodes import Node

        if not self.is_stored:
            raise exceptions.ModificationNotAllowed('cannot add nodes to an unstored group')

        # Cannot use `collections.Iterable` here, because that would also match iterable `Node` sub classes like `List`
        if not isinstance(nodes, (list, tuple)):
            nodes = [nodes]  # type: ignore

        for node in nodes:
            type_check(node, Node)

        self._backend_entity.remove_nodes([node.backend_entity for node in nodes])

    def is_user_defined(self) -> bool:
        """
        :return: True if the group is user defined, False otherwise
        """
        return not self.type_string

    _deprecated_extra_methods = {
        'extras': 'all',
        'get_extra': 'get',
        'get_extra_many': 'get_many',
        'set_extra': 'set',
        'set_extra_many': 'set_many',
        'reset_extras': 'reset',
        'delete_extra': 'delete',
        'delete_extra_many': 'delete_many',
        'clear_extras': 'clear',
        'extras_items': 'items',
        'extras_keys': 'keys',
    }

    def __getattr__(self, name: str) -> Any:
        """
        This method is called when an extras is not found in the instance.

        It allows for the handling of deprecated mixin methods.
        """
        if name in self._deprecated_extra_methods:
            new_name = self._deprecated_extra_methods[name]
            kls = self.__class__.__name__
            warn_deprecation(
                f'`{kls}.{name}` is deprecated, use `{kls}.base.extras.{new_name}` instead.', version=3, stacklevel=3
            )
            return getattr(self.base.extras, new_name)

        raise AttributeError(name)


class AutoGroup(Group):
    """Group to be used to contain selected nodes generated, whilst autogrouping is enabled."""


class ImportGroup(Group):
    """Group to be used to contain all nodes from an export archive that has been imported."""


class UpfFamily(Group):
    """Group that represents a pseudo potential family containing `UpfData` nodes."""
