###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""AiiDA Group entities"""

from __future__ import annotations

import datetime
import typing as t
import warnings
from collections.abc import Sequence
from functools import cached_property
from pathlib import Path

import pydantic as pdt
from typing_extensions import Self

from aiida.common import exceptions
from aiida.common.lang import classproperty, type_check
from aiida.manage import get_manager
from aiida.orm import convert, entities, extras, users
from aiida.orm.decorators import column
from aiida.orm.models.adapters import EntityPkAdapter, StrUuidAdapter
from aiida.orm.users import User

if t.TYPE_CHECKING:
    from importlib_metadata import EntryPoint

    from aiida.orm import Node
    from aiida.orm.implementation import StorageBackend
    from aiida.orm.implementation.groups import BackendGroup

__all__ = ('AutoGroup', 'Group', 'ImportGroup', 'UpfFamily')


def load_group_class(type_string: str) -> type[Group]:
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


class GroupCollection(entities.EntityCollection['Group']):
    """Collection of Groups"""

    collection_type: t.ClassVar[str] = 'groups'

    def get_or_create(self, label: str | None = None, **kwargs) -> tuple[Group, bool]:
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

    def get_one_by_identifier(self, identifier: object) -> Group:
        """Get a single group by its identifier.

        :param identifier: the primary key or label of the group to get
        :return: the group instance
        """
        if isinstance(identifier, int):
            return self.get(pk=identifier)
        if isinstance(identifier, str):
            return self.get(label=identifier)
        raise TypeError('Identifier must be an int or str')

    def delete(self, pk: int) -> None:
        """Delete a group

        :param pk: the id of the group to delete
        """
        self._backend.groups.delete(pk)

    @staticmethod
    def _entity_base_cls() -> type[Group]:
        return Group


class GroupBase:
    """A namespace for group related functionality, that is not directly related to its user-facing properties."""

    def __init__(self, group: Group) -> None:
        """Construct a new instance of the base namespace."""
        self._group: Group = group

    @cached_property
    def extras(self) -> extras.EntityExtras:
        """Return the extras of this group."""
        return extras.EntityExtras(self._group)


class Group(entities.Entity['BackendGroup', GroupCollection]):
    """ORM representation of an AiiDA group."""

    identity_field = 'uuid'

    __type_string: t.ClassVar[str | None]

    _CLS_COLLECTION = GroupCollection

    def __init__(
        self,
        label: str | None = None,
        user: User | None = None,
        description: str = '',
        time: datetime.datetime | None = None,
        extras: dict[str, t.Any] | None = None,
        backend: StorageBackend | None = None,
    ):
        """Create a new group. Either pass a dbgroup parameter, to reload
        a group from the DB (and then, no further parameters are allowed),
        or pass the parameters for the Group creation.

        :param label: The group label, required on creation
        :param description: The group description (by default, an empty string)
        :param user: The owner of the group (by default, the automatic user)
        """
        if not label:
            raise ValueError('Group label must be provided')

        backend = backend or get_manager().get_profile_storage()
        user = t.cast(users.User, user or backend.default_user)
        type_check(user, users.User)

        self._backend_entity = backend.groups.create(
            label=label,
            user=user.backend_entity,
            description=description,
            type_string=self._type_string,
            time=time,
        )

        if extras is not None:
            self.base.extras.set_many(extras)

        self.finalize()

    def __repr__(self) -> str:
        return (
            f'<{self.__class__.__name__}: {self.label!r} '
            f'[{"type " + self.type_string if self.type_string else "user-defined"}], of user {self.user.email}>'
        )

    def __str__(self) -> str:
        return f'{self.__class__.__name__}<{self.label}>'

    @column(updatable=True)
    def label(self) -> str:
        """The label of the group."""
        return self._backend_entity.label

    @label.setter
    def label(self, value: str) -> None:
        self._backend_entity.label = value

    @column(updatable=True)
    def description(self) -> str:
        """The description of the group."""
        return self._backend_entity.description

    @description.setter
    def description(self, value: str) -> None:
        self._backend_entity.description = value

    @column(readonly=True)
    def type_string(self) -> str:
        """The string defining the type of the group"""
        return self._backend_entity.type_string

    @column(
        readonly=True,
        model_adapter=StrUuidAdapter(),
    )
    def uuid(self) -> str:
        """The UUID of the group."""
        return self._backend_entity.uuid

    @column(readonly=True)
    def time(self) -> datetime.datetime:
        """The creation time of the group."""
        return self._backend_entity.time

    @column(
        readonly=True,
        model_adapter=EntityPkAdapter(users.User),
    )
    def user(self) -> User:
        """The user of the group."""
        return User.from_backend_entity(self._backend_entity.user)

    @column(
        updatable=True,
        may_be_large=True,
        model_field_info=pdt.fields.FieldInfo(default_factory=dict),
    )
    def extras(self) -> dict[str, t.Any]:
        """The extras of the group."""
        return self.base.extras.all

    @extras.setter
    def extras(self, value: dict[str, t.Any]) -> None:
        self.base.extras.reset(value)

    @cached_property
    def base(self) -> GroupBase:
        """Return the group base namespace."""
        return GroupBase(self)

    @classproperty
    def entry_point(cls: type[Group]) -> EntryPoint | None:  # noqa: N805
        """Return the entry point associated this group type.

        :return: the associated entry point or ``None`` if it isn't known.
        """
        from aiida.plugins.entry_point import get_entry_point_from_class

        return get_entry_point_from_class(cls.__module__, cls.__name__)[1]

    @property
    def nodes(self) -> convert.ConvertIterator:
        """Return a generator/iterator that iterates over all nodes and returns
        the respective AiiDA subclasses of Node, and also allows to ask for
        the number of nodes in the group using len().
        """
        return convert.ConvertIterator(self._backend_entity.nodes)

    @property
    def is_empty(self) -> bool:
        """Return whether the group is empty, i.e. it does not contain any nodes."""
        try:
            self.nodes[0]
        except IndexError:
            return True
        return False

    def store(self) -> Self:
        """Verify that the group is allowed to be stored, which is the case along as `type_string` is set."""
        if self._type_string is None:
            raise exceptions.StoringNotAllowed('`type_string` is `None` so the group cannot be stored.')

        return super().store()

    def count(self) -> int:
        """Return the number of entities in this group.

        :return: integer number of entities contained within the group
        """
        return self._backend_entity.count()

    def clear(self) -> None:
        """Remove all the nodes from this group."""
        return self._backend_entity.clear()

    def add_nodes(self, nodes: Node | Sequence[Node]) -> None:
        """Add a node or a set of nodes to the group.

        :note: all the nodes *and* the group itself have to be stored.

        :param nodes: a single `Node` or a list of `Nodes`
        """
        from aiida.orm.nodes import Node

        if not self.is_stored:
            raise exceptions.ModificationNotAllowed('cannot add nodes to an unstored group')

        # Cannot use `collections.Iterable` here, because that would also match iterable `Node` sub classes like `List`
        if not isinstance(nodes, (list, tuple)):
            nodes = [nodes]  # type: ignore[list-item]

        for node in nodes:
            type_check(node, Node)

        self._backend_entity.add_nodes([node.backend_entity for node in nodes])

    def remove_nodes(self, nodes: Node | Sequence[Node]) -> None:
        """Remove a node or a set of nodes to the group.

        :note: all the nodes *and* the group itself have to be stored.

        :param nodes: a single `Node` or a list of `Nodes`
        """
        from aiida.orm.nodes import Node

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
        output_path: str | Path | None = None,
        # Dump mode options
        dry_run: bool = False,
        overwrite: bool = False,
        # Time filtering options
        past_days: int | None = None,
        start_date: datetime.datetime | None = None,
        end_date: datetime.datetime | None = None,
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

    @classproperty
    def _type_string(cls: type[Group]) -> str | None:  # noqa: N805
        from aiida.plugins.entry_point import get_entry_point_from_class

        if hasattr(cls, '__type_string'):
            return cls.__type_string

        mod, name = cls.__module__, cls.__name__
        entry_point_group, entry_point = get_entry_point_from_class(mod, name)

        if entry_point_group is None or entry_point_group != 'aiida.groups':
            cls.__type_string = None
            message = f'no registered entry point for `{mod}:{name}` so its instances will not be storable.'
            warnings.warn(message)
        else:
            assert entry_point is not None
            cls.__type_string = entry_point.name
        return cls.__type_string


class AutoGroup(Group):
    """Group to be used to contain selected nodes generated, whilst autogrouping is enabled."""


class ImportGroup(Group):
    """Group to be used to contain all nodes from an export archive that has been imported."""


class UpfFamily(Group):
    """Group that represents a pseudo potential family containing `UpfData` nodes."""
