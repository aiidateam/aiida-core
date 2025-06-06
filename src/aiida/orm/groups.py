###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""AiiDA Group entites"""

import datetime
import warnings
from functools import cached_property
from pathlib import Path
from typing import TYPE_CHECKING, Any, ClassVar, Dict, Optional, Sequence, Tuple, Type, TypeVar, Union, cast

from aiida.common import exceptions
from aiida.common.lang import classproperty, type_check
from aiida.common.pydantic import MetadataField
from aiida.common.warnings import warn_deprecation
from aiida.manage import get_manager

from . import convert, entities, extras, users

if TYPE_CHECKING:
    from importlib_metadata import EntryPoint

    from aiida.orm import Node, User
    from aiida.orm.implementation import StorageBackend
    from aiida.orm.implementation.groups import BackendGroup  # noqa: F401

__all__ = ('AutoGroup', 'Group', 'ImportGroup', 'UpfFamily')

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
        warnings.warn(message)
        group_class = Group

    return group_class


class GroupCollection(entities.Collection['Group']):
    """Collection of Groups"""

    @staticmethod
    def _entity_base_cls() -> Type['Group']:
        return Group

    def get_or_create(self, label: Optional[str] = None, **kwargs) -> Tuple['Group', bool]:
        """Try to retrieve a group from the DB with the given arguments;
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
        """Delete a group

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


class Group(entities.Entity['BackendGroup', GroupCollection]):
    """An AiiDA ORM implementation of group of nodes."""

    __type_string: ClassVar[Optional[str]]

    class Model(entities.Entity.Model):
        uuid: str = MetadataField(description='The UUID of the group', is_attribute=False, exclude_to_orm=True)
        type_string: str = MetadataField(description='The type of the group', is_attribute=False, exclude_to_orm=True)
        user: int = MetadataField(
            description='The group owner',
            is_attribute=False,
            orm_class='core.user',
            orm_to_model=lambda group, _: group.user.pk,  # type: ignore[attr-defined]
        )
        time: Optional[datetime.datetime] = MetadataField(
            description='The creation time of the node', is_attribute=False
        )
        label: str = MetadataField(description='The group label', is_attribute=False)
        description: Optional[str] = MetadataField(description='The group description', is_attribute=False)
        extras: Optional[Dict[str, Any]] = MetadataField(
            description='The group extras',
            is_attribute=False,
            is_subscriptable=True,
            orm_to_model=lambda group, _: group.base.extras.all,  # type: ignore[attr-defined]
        )

    _CLS_COLLECTION = GroupCollection

    def __init__(
        self,
        label: Optional[str] = None,
        user: Optional['User'] = None,
        description: str = '',
        type_string: Optional[str] = None,
        time: Optional[datetime.datetime] = None,
        extras: Optional[Dict[str, Any]] = None,
        backend: Optional['StorageBackend'] = None,
    ):
        """Create a new group. Either pass a dbgroup parameter, to reload
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

        if type_string:
            warn_deprecation('Passing the `type_string` is deprecated, it is determined automatically', version=3)

        backend = backend or get_manager().get_profile_storage()
        user = cast(users.User, user or backend.default_user)
        type_check(user, users.User)

        model = backend.groups.create(
            label=label, user=user.backend_entity, description=description, type_string=self._type_string, time=time
        )
        super().__init__(model)
        if extras is not None:
            self.base.extras.set_many(extras)

    @classproperty
    def _type_string(cls) -> Optional[str]:  # noqa: N805
        from aiida.plugins.entry_point import get_entry_point_from_class

        if hasattr(cls, '__type_string'):
            return cls.__type_string

        mod, name = cls.__module__, cls.__name__
        entry_point_group, entry_point = get_entry_point_from_class(mod, name)

        if entry_point_group is None or entry_point_group != 'aiida.groups':
            cls.__type_string = None  # type: ignore[misc]
            message = f'no registered entry point for `{mod}:{name}` so its instances will not be storable.'
            warnings.warn(message)
        else:
            assert entry_point is not None
            cls.__type_string = entry_point.name  # type: ignore[misc]
        return cls.__type_string

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
    def entry_point(cls) -> Optional['EntryPoint']:  # noqa: N805
        """Return the entry point associated this group type.

        :return: the associated entry point or ``None`` if it isn't known.
        """
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
        """:return: the label of the group as a string"""
        return self._backend_entity.label

    @label.setter
    def label(self, label: str) -> None:
        """Attempt to change the label of the group instance. If the group is already stored
        and the another group of the same type already exists with the desired label, a
        UniquenessError will be raised

        :param label: the new group label
        :type label: str

        :raises aiida.common.UniquenessError: if another group of same type and label already exists
        """
        self._backend_entity.label = label

    @property
    def description(self) -> str:
        """:return: the description of the group as a string"""
        return self._backend_entity.description or ''

    @description.setter
    def description(self, description: str) -> None:
        """:param description: the description of the group as a string"""
        self._backend_entity.description = description

    @property
    def type_string(self) -> str:
        """:return: the string defining the type of the group"""
        return self._backend_entity.type_string

    @property
    def time(self) -> datetime.datetime:
        """:return: the creation time"""
        return self._backend_entity.time

    @property
    def user(self) -> 'User':
        """:return: the user associated with this group"""
        return entities.from_backend_entity(users.User, self._backend_entity.user)

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
        """Return a generator/iterator that iterates over all nodes and returns
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
            nodes = [nodes]  # type: ignore[list-item]

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
            nodes = [nodes]  # type: ignore[list-item]

        for node in nodes:
            type_check(node, Node)

        self._backend_entity.remove_nodes([node.backend_entity for node in nodes])

    def is_user_defined(self) -> bool:
        """:return: True if the group is user defined, False otherwise"""
        return not self.type_string

    def dump(
        self,
        output_path: Optional[Union[str, Path]] = None,
        # Dump mode options
        dry_run: bool = False,
        overwrite: bool = False,
        # Time filtering options
        past_days: Optional[int] = None,
        start_date: Optional[datetime.datetime] = None,
        end_date: Optional[datetime.datetime] = None,
        filter_by_last_dump_time: bool = True,
        # Node collection options
        only_top_level_calcs: bool = True,
        only_top_level_workflows: bool = True,
        # Process dump options
        include_inputs: bool = True,
        include_outputs: bool = False,
        include_attributes: bool = True,
        include_extras: bool = False,
        flat: bool = False,
        dump_unsealed: bool = False,
        symlink_calcs: bool = False,
    ) -> Path:
        """Dump the group and its associated nodes to disk.

        :param output_path: Target directory for the dump, defaults to None
        :param dry_run: Show what would be dumped without actually dumping, defaults to False
        :param overwrite: Overwrite existing dump directories, defaults to False
        :param past_days: Only include nodes modified in the past N days, defaults to None
        :param start_date: Only include nodes modified after this date, defaults to None
        :param end_date: Only include nodes modified before this date, defaults to None
        :param filter_by_last_dump_time: Filter nodes by last dump time, defaults to True
        :param only_top_level_calcs: Only dump top-level calculations, defaults to True
        :param only_top_level_workflows: Only dump top-level workflows, defaults to True
        :param include_inputs: Include input files in the dump, defaults to True
        :param include_outputs: Include output files in the dump, defaults to False
        :param include_attributes: Include node attributes in metadata, defaults to True
        :param include_extras: Include node extras in metadata, defaults to False
        :param flat: Use flat directory structure, defaults to False
        :param dump_unsealed: Allow dumping of unsealed nodes, defaults to False
        :param symlink_calcs: Create symlinks for calculation nodes, defaults to False
        :return: Path where the group was dumped
        """
        from aiida.tools._dumping.config import GroupDumpConfig
        from aiida.tools._dumping.engine import DumpEngine
        from aiida.tools._dumping.utils import DumpPaths

        # Construct GroupDumpConfig from kwargs
        config_data = {
            'groups': [self],  # Set this specific group
            'dry_run': dry_run,
            'overwrite': overwrite,
            'past_days': past_days,
            'start_date': start_date,
            'end_date': end_date,
            'filter_by_last_dump_time': filter_by_last_dump_time,
            'only_top_level_calcs': only_top_level_calcs,
            'only_top_level_workflows': only_top_level_workflows,
            'include_inputs': include_inputs,
            'include_outputs': include_outputs,
            'include_attributes': include_attributes,
            'include_extras': include_extras,
            'flat': flat,
            'dump_unsealed': dump_unsealed,
            'symlink_calcs': symlink_calcs,
        }

        config = GroupDumpConfig.model_validate(config_data)

        if output_path:
            target_path: Path = Path(output_path).resolve()
        else:
            target_path = DumpPaths.get_default_dump_path(entity=self)

        engine = DumpEngine(base_output_path=target_path, config=config, dump_target_entity=self)
        engine.dump()

        return target_path

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
        """This method is called when an extras is not found in the instance.

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
