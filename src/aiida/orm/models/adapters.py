from __future__ import annotations

import enum
import pathlib
import typing as t
from uuid import UUID

import numpy as np

from aiida.common import exceptions
from aiida.orm import qb_fields
from aiida.orm.cli import CliAdapter
from aiida.orm.entities import Entity
from aiida.orm.implementation import BackendEntity
from aiida.orm.models.modeling import ModelAdapter

_EntityT_co = t.TypeVar('_EntityT_co', covariant=True)


class EntityFetcher(t.Protocol[_EntityT_co]):
    def get_one_by_identifier(self, identifier: object) -> _EntityT_co: ...


_EntityT = t.TypeVar('_EntityT', bound=Entity[t.Any, t.Any])


class EntityPkAdapter(ModelAdapter[_EntityT, int, qb_fields.QbNumericField]):
    """Represent an ORM entity by its primary key in models."""

    def __init__(self, entity_type: type[_EntityT]) -> None:
        self._entity_type = entity_type

    @property
    def collection(self) -> EntityFetcher[_EntityT]:
        return self._entity_type.collection

    def to_model(self, value: _EntityT, *, context: dict[str, t.Any] | None = None) -> int:
        if value.pk is None:
            raise ValueError('entity must be stored to be represented by PK')
        return value.pk

    def to_orm(self, value: int) -> _EntityT:
        try:
            return self.collection.get_one_by_identifier(value)
        except exceptions.NotExistent:
            msg = f'entity with PK {value} does not exist'
            raise ValueError(msg) from None


class BackendEntityPkAdapter(
    ModelAdapter[BackendEntity, int, qb_fields.QbNumericField],
    t.Generic[_EntityT],
):
    """Represent an ORM backend entity by its primary key in models."""

    def __init__(self, backend_entity_type: type[BackendEntity], entity_type: type[_EntityT]) -> None:
        self._backend_entity_type = backend_entity_type
        self._entity_type = entity_type

    @property
    def collection(self) -> EntityFetcher[_EntityT]:
        return self._entity_type.collection

    def to_model(self, value: BackendEntity, *, context: dict[str, t.Any] | None = None) -> int:
        if value.pk is None:
            raise ValueError('backend entity must be stored to be represented by PK')
        return value.pk

    def to_orm(self, value: int) -> BackendEntity:
        try:
            entity = self.collection.get_one_by_identifier(value)
        except exceptions.NotExistent:
            msg = f'entity with PK {value} does not exist'
            raise ValueError(msg) from None

        backend_entity = entity.backend_entity

        if not isinstance(backend_entity, self._backend_entity_type):
            msg = (
                f'expected backend entity of type {self._backend_entity_type.__name__}, '
                f'got {type(backend_entity).__name__}'
            )
            raise TypeError(msg)

        return entity.backend_entity


class StrUuidAdapter(ModelAdapter[str, UUID, qb_fields.QbStrField]):
    """Represent a UUID string in models."""

    def to_model(self, value: str, *, context: dict[str, t.Any] | None = None) -> UUID:
        return UUID(value)

    def to_orm(self, value: UUID) -> str:
        return str(value)


class PathStrAdapter(ModelAdapter[pathlib.PurePath, str, qb_fields.QbStrField]):
    """Represent a `pathlib.PurePath` object as a string in models."""

    def to_model(self, value: pathlib.PurePath, *, context: dict[str, t.Any] | None = None) -> str:
        return str(value)

    def to_orm(self, value: str) -> pathlib.PurePath:
        return pathlib.PurePath(value)


class EnumStrAdapter(ModelAdapter[enum.Enum, str, qb_fields.QbStrField]):
    """Represent an Enum as a string in models."""

    def __init__(self, enum_type: type[enum.Enum]) -> None:
        self._enum_type = enum_type

    def to_model(self, value: enum.Enum, *, context: dict[str, t.Any] | None = None) -> str:
        return value.value

    def to_orm(self, value: str) -> enum.Enum:
        return self._enum_type(value)


class NumpyArrayListAdapter(ModelAdapter[np.ndarray, list, qb_fields.QbArrayField]):
    """Represent a NumPy array as a list in models."""

    def to_model(self, value: np.ndarray, *, context: dict[str, t.Any] | None = None) -> list:
        return value.tolist()

    def to_orm(self, value: list) -> np.ndarray:
        return np.array(value)


@t.runtime_checkable
class HasLabel(t.Protocol):
    @property
    def label(self) -> str: ...


class LabelPkAdapter(CliAdapter[str, int]):
    """Represent a label as a primary key in CLI values."""

    def __init__(self, entity_type: type[Entity[t.Any, t.Any]]) -> None:
        self._entity_type = entity_type

    @property
    def collection(self) -> EntityFetcher[Entity[t.Any, t.Any]]:
        return self._entity_type.collection

    def to_model(self, value: str) -> int:
        entity = self.collection.get_one_by_identifier(value)

        if entity.pk is None:
            msg = f'{self._entity_type.__name__} with label {value!r} is not stored'
            raise ValueError(msg)

        return entity.pk

    def to_cli(self, value: int) -> str:
        entity = self.collection.get_one_by_identifier(value)

        if not isinstance(entity, HasLabel):
            msg = f'{self._entity_type.__name__} with PK {value} does not have a label'
            raise ValueError(msg)

        return entity.label
