from __future__ import annotations

import abc
import typing as t
from dataclasses import asdict, dataclass
from datetime import datetime, timezone

from aiida import load_profile
from aiida.common.lang import classproperty
from aiida.manage import get_manager
from aiida.orm import qb_fields

REGISTRY: dict[str, type[EntityInterface]] = {}


def register(entity_type: str):
    def decorator(cls: type[EntityInterface]):
        REGISTRY[entity_type] = cls
        return cls

    return decorator


class EntityQuery:
    """The query interface for entities."""

    pk: qb_fields.QbNumericField


@dataclass(kw_only=True)
class Entity:
    """The mostly-immutable backend interface.

    - It is NOT the DB Node itself.
    - It is an abstraction over the database row, providing a higher-level interface.
    - It is what `orm.load(pk=...)` yields.
    - It is an immutable representation of a database row.
    - It can yield a mutable frontend interface instance via `.get_interface()`, fetched from a registry and
      instantiated with the database row data.
    """

    pk: int | None = None

    @property
    def _entity_type(self) -> str:
        raise NotImplementedError

    def get_interface(self) -> EntityInterface:
        """Return the mutable frontend interface for this entity."""
        interface_cls = REGISTRY.get(self._entity_type)
        if interface_cls is None:
            msg = f"No interface registered for entity type '{self._entity_type}'"
            raise ValueError(msg)
        interface_kwargs = self._get_interface_kwargs()
        return interface_cls(**interface_kwargs)

    def _get_interface_class(self) -> type[EntityInterface]:
        """Return the interface class for this entity."""
        interface_cls = REGISTRY.get(self._entity_type)
        if interface_cls is None:
            msg = f"No interface registered for entity type '{self._entity_type}'"
            raise ValueError(msg)
        return interface_cls

    def _get_interface_kwargs(self) -> dict[str, t.Any]:
        """Return the keyword arguments to instantiate the interface class."""
        return asdict(self)


E = t.TypeVar('E', bound=Entity)
EQ = t.TypeVar('EQ', bound=EntityQuery)


class EntityInterface(t.Generic[E, EQ], metaclass=abc.ABCMeta):
    """The mutable frontend interface.

    - It is a mutable frontend interface.
    - It can be converted into an `Entity` instance via a `store` method or passed to a `store` function.
    - It carries pre-stored data.
    - It provides domain-specific methods and logic for interacting with the underlying entity type.
    """

    _entity_cls: type[E]
    _query_cls: type[EQ]

    @classproperty
    def q(cls) -> EQ:  # noqa: N805
        """Return the query interface for the entity class."""
        raise NotImplementedError

    @abc.abstractmethod
    def store(self) -> E:
        """Store the given interface as an immutable backend entity."""
        raise NotImplementedError


class NodeQuery(EntityQuery):
    """The query interface for node entities."""

    label: qb_fields.QbStrField
    description: qb_fields.QbStrField
    node_type: qb_fields.QbStrField
    process_type: qb_fields.QbStrField
    extras: qb_fields.QbDictField
    attributes: qb_fields.QbAttributesField
    repository_metadata: qb_fields.QbDictField
    ctime: qb_fields.QbNumericField
    mtime: qb_fields.QbNumericField
    computer: qb_fields.QbNumericField
    user: qb_fields.QbNumericField


@dataclass(kw_only=True)
class Node(Entity):
    """The mostly-immutable backend interface for a node entity."""

    label: str
    description: str
    node_type: str
    process_type: str
    extras: dict[str, t.Any]
    attributes: dict[str, t.Any]
    repository_metadata: dict[str, t.Any]
    ctime: datetime
    mtime: datetime
    computer: int | None
    user: int

    @property
    def _entity_type(self) -> str:
        if not self.node_type:
            raise ValueError('Node type is not set.')
        return f'node:{self.node_type}'

    def _get_interface_kwargs(self) -> dict[str, t.Any]:
        data = asdict(self)
        return data.get('attributes', {})


@dataclass(kw_only=True)
class NodeAttributes:
    """A representation of the node's JSONB attributes column."""


N = t.TypeVar('N', bound=Node)
NA = t.TypeVar('NA', bound=NodeAttributes)


class NodeInterface(EntityInterface[N, EQ], t.Generic[N, EQ, NA], metaclass=abc.ABCMeta):
    """The mutable frontend interface for a node entity."""

    _attributes: NA
    _node_type: str

    def store(
        self,
        *,
        label: str = '',
        description: str = '',
        extras: dict[str, t.Any] | None = None,
        node_type: str | None = None,
        process_type: str | None = None,
        ctime: datetime | None = None,
        mtime: datetime | None = None,
        computer_id: int | None = None,
        user_id: int | None = None,
        repository_metadata: dict[str, t.Any] | None = None,
    ) -> N:
        backend = get_manager().get_profile_storage()

        default_user = backend.default_user
        if default_user is None or not default_user.pk:
            raise ValueError('No default user found in the backend.')

        return self._entity_cls(
            label=label,
            description=description,
            node_type=node_type or self._node_type,
            process_type=process_type or '',
            extras=extras or {},
            attributes=asdict(self._attributes),
            repository_metadata=repository_metadata or {},
            ctime=ctime or datetime.now(tz=timezone.utc),
            mtime=mtime or datetime.now(tz=timezone.utc),
            computer=computer_id,
            user=user_id or default_user.pk,
        )


class DataQuery(NodeQuery):
    """The query interface for data node entities."""


@dataclass(kw_only=True)
class DataNodeAttributes(NodeAttributes):
    """A representation of the data node's JSONB attributes column."""


@dataclass(kw_only=True)
class DataNode(Node):
    """A data node."""

    @property
    def _entity_type(self) -> str:
        if not self.node_type:
            raise ValueError('Node type is not set.')
        return f'data:{self.node_type}'


class Data(NodeInterface[DataNode, EQ, NA], t.Generic[EQ, NA], metaclass=abc.ABCMeta):
    """The mutable frontend interface for a data nodes.

    - This is what plugin developers implement for their new data types.
    """

    _entity_cls = DataNode


class IntQuery(DataQuery):
    """The query interface for integer data node entities."""

    value: qb_fields.QbNumericField


@dataclass(kw_only=True)
class IntAttributes(NodeAttributes):
    value: int = 0


@register('data:core.int')
class Int(Data[IntQuery, IntAttributes]):
    """The mutable frontend interface for an integer data node."""

    _query_cls = IntQuery

    _node_type = 'core.int'

    def __init__(self, value: int | None) -> None:
        """Instantiate the interface with data populated by the given value."""
        self._attributes = IntAttributes(value=value or 0)

    @property
    def value(self) -> int:
        return self._attributes.value

    @value.setter
    def value(self, value: int) -> None:
        self._attributes.value = value


if __name__ == '__main__':
    load_profile()
    integer = Int(42)
    data = integer.store()
    interface = data.get_interface()
