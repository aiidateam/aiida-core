from __future__ import annotations

import dataclasses
import datetime
import typing as t
from collections.abc import Callable, Mapping, Sequence

import pydantic as pdt
from typing_extensions import Self

from aiida.orm import qb_fields
from aiida.orm.decorators.base import (
    BaseField,
    BaseFieldConfig,
    BaseFieldDecorator,
    BaseFieldSpec,
    Storable,
)

if t.TYPE_CHECKING:
    from aiida.orm.cli import CliAdapter, CliFieldInfo
    from aiida.orm.models.modeling import ModelAdapter, ModelMetadata

__all__ = (
    'Column',
    'ColumnConfig',
    'ColumnSpec',
    'column',
    'iter_columns',
)


@dataclasses.dataclass(frozen=True)
class ColumnConfig(BaseFieldConfig):
    """Unresolved configuration supplied to the `column` decorator."""

    backend_key: str | None = None
    updatable: bool = False
    may_be_large: bool = False


@dataclasses.dataclass(frozen=True)
class ColumnSpec(BaseFieldSpec):
    """Canonical semantic description of a top-level entity column."""

    backend_key: str
    updatable: bool
    may_be_large: bool = False

    @property
    def immutable(self) -> bool:
        """Return whether the column is immutable after storage."""
        return not self.updatable


_EntityT = t.TypeVar('_EntityT', bound=Storable)
_ValueT = t.TypeVar('_ValueT')
_QbFieldT = t.TypeVar('_QbFieldT', bound=qb_fields.QbField)


class Column(
    BaseField[
        _EntityT,
        _ValueT,
        _QbFieldT,
        ColumnSpec,
        ColumnConfig,
    ],
):
    """Descriptor declaring a top-level ORM entity column."""

    config_type = ColumnConfig
    spec_type = ColumnSpec

    @t.overload
    def __get__(self, instance: None, owner: type[_EntityT]) -> _QbFieldT: ...

    @t.overload
    def __get__(self, instance: _EntityT, owner: type[_EntityT] | None = None) -> _ValueT: ...

    def __get__(
        self,
        instance: _EntityT | None,
        owner: type[_EntityT] | None = None,
    ) -> _ValueT | _QbFieldT:
        if instance is None:
            if owner is None:
                raise AttributeError('ORM column must be accessed through an entity class')

            return self._get_column_qb_field(owner)

        return self.fget(instance)

    def _immutable_once_stored(self, instance: _EntityT) -> bool:
        return instance.is_stored and self.spec.immutable

    def _build_spec(self, **kwargs: t.Any) -> ColumnSpec:
        """Resolve descriptor structure into the canonical column specification."""
        if self._name is None:
            raise RuntimeError('column has not been assigned to an entity')

        spec = super()._build_spec(
            backend_key=self._config.backend_key or self._name,
            updatable=self._config.updatable,
            may_be_large=self._config.may_be_large,
        )

        if spec.updatable and self.fset is None:
            raise TypeError(f'{spec.name!r} is declared updatable but defines no setter')

        if spec.readonly and spec.updatable:
            raise TypeError(f'{spec.name!r} cannot be both read-only and updatable')

        return spec

    def _get_column_qb_field(self, owner: type[_EntityT]) -> _QbFieldT:
        """Return the lazily constructed QueryBuilder column."""
        return self._get_qb_field(self.spec.backend_key, is_attribute=False)


_ConfiguredQbFieldT = t.TypeVar('_ConfiguredQbFieldT', bound=qb_fields.QbField)


class ConfiguredColumnDecorator(t.Protocol[_ConfiguredQbFieldT]):
    """Configured column decorator with a known QueryBuilder field type."""

    def __call__(
        self,
        fget: Callable[[_EntityT], _ValueT],
        /,
    ) -> Column[_EntityT, _ValueT, _ConfiguredQbFieldT]: ...


_AdaptedEntityT = t.TypeVar('_AdaptedEntityT')
_AdaptedModelT = t.TypeVar('_AdaptedModelT')


class ColumnDecorator(
    BaseFieldDecorator[
        _EntityT,
        _ValueT,
        ColumnConfig,
        Column[t.Any, t.Any, qb_fields.QbField],
    ],
):
    """Decorator for top-level entity columns."""

    config_type = ColumnConfig
    field_type = Column

    @t.overload
    def __call__(
        self,
        fget: Callable[[_EntityT], int],
        /,
    ) -> Column[_EntityT, int, qb_fields.QbNumericField]: ...

    @t.overload
    def __call__(
        self,
        fget: Callable[[_EntityT], int | None],
        /,
    ) -> Column[_EntityT, int | None, qb_fields.QbNumericField]: ...

    @t.overload
    def __call__(
        self,
        fget: Callable[[_EntityT], float],
        /,
    ) -> Column[_EntityT, float, qb_fields.QbNumericField]: ...

    @t.overload
    def __call__(
        self,
        fget: Callable[[_EntityT], float | None],
        /,
    ) -> Column[_EntityT, float | None, qb_fields.QbNumericField]: ...

    @t.overload
    def __call__(
        self,
        fget: Callable[[_EntityT], datetime.datetime],
        /,
    ) -> Column[_EntityT, datetime.datetime, qb_fields.QbNumericField]: ...

    @t.overload
    def __call__(
        self,
        fget: Callable[[_EntityT], datetime.datetime | None],
        /,
    ) -> Column[_EntityT, datetime.datetime | None, qb_fields.QbNumericField]: ...

    @t.overload
    def __call__(
        self,
        fget: Callable[[_EntityT], str],
        /,
    ) -> Column[_EntityT, str, qb_fields.QbStrField]: ...

    @t.overload
    def __call__(
        self,
        fget: Callable[[_EntityT], str | None],
        /,
    ) -> Column[_EntityT, str | None, qb_fields.QbStrField]: ...

    @t.overload
    def __call__(
        self,
        fget: Callable[[_EntityT], list[_ValueT]],
        /,
    ) -> Column[_EntityT, list[_ValueT], qb_fields.QbArrayField]: ...

    @t.overload
    def __call__(
        self,
        fget: Callable[[_EntityT], list[_ValueT] | None],
        /,
    ) -> Column[_EntityT, list[_ValueT] | None, qb_fields.QbArrayField]: ...

    @t.overload
    def __call__(
        self,
        fget: Callable[[_EntityT], tuple[_ValueT, ...]],
        /,
    ) -> Column[_EntityT, tuple[_ValueT, ...], qb_fields.QbArrayField]: ...

    @t.overload
    def __call__(
        self,
        fget: Callable[[_EntityT], tuple[_ValueT, ...] | None],
        /,
    ) -> Column[_EntityT, tuple[_ValueT, ...] | None, qb_fields.QbArrayField]: ...

    @t.overload
    def __call__(
        self,
        fget: Callable[[_EntityT], Sequence[_ValueT]],
        /,
    ) -> Column[_EntityT, Sequence[_ValueT], qb_fields.QbArrayField]: ...

    @t.overload
    def __call__(
        self,
        fget: Callable[[_EntityT], Sequence[_ValueT] | None],
        /,
    ) -> Column[_EntityT, Sequence[_ValueT] | None, qb_fields.QbArrayField]: ...

    @t.overload
    def __call__(
        self,
        fget: Callable[[_EntityT], dict[str, _ValueT]],
        /,
    ) -> Column[_EntityT, dict[str, _ValueT], qb_fields.QbDictField]: ...

    @t.overload
    def __call__(
        self,
        fget: Callable[[_EntityT], dict[str, _ValueT] | None],
        /,
    ) -> Column[_EntityT, dict[str, _ValueT] | None, qb_fields.QbDictField]: ...

    @t.overload
    def __call__(
        self,
        fget: Callable[[_EntityT], Mapping[str, _ValueT]],
        /,
    ) -> Column[_EntityT, Mapping[str, _ValueT], qb_fields.QbDictField]: ...

    @t.overload
    def __call__(
        self,
        fget: Callable[[_EntityT], Mapping[str, _ValueT] | None],
        /,
    ) -> Column[_EntityT, Mapping[str, _ValueT] | None, qb_fields.QbDictField]: ...

    @t.overload
    def __call__(
        self,
        fget: Callable[[_EntityT], object],
        /,
    ) -> Column[_EntityT, object, qb_fields.QbAnyField]: ...

    @t.overload
    def __call__(
        self,
        fget: Callable[[_EntityT], _ValueT],
        /,
    ) -> Column[_EntityT, _ValueT, qb_fields.QbAnyField]: ...

    @t.overload
    def __call__(
        self,
        *,
        backend_key: str | None = None,
        readonly: bool = False,
        updatable: bool = False,
        required_once_stored: bool = False,
        may_be_large: bool = False,
        model_field_info: pdt.fields.FieldInfo | None = None,
        model_metadata: tuple[ModelMetadata, ...] = (),
        model_adapter: ModelAdapter[_AdaptedEntityT, _AdaptedModelT, _QbFieldT],
        cli_exclude: bool = False,
        cli_field_info: CliFieldInfo | None = None,
        cli_adapter: CliAdapter[t.Any, t.Any] | None = None,
    ) -> ConfiguredColumnDecorator[_QbFieldT]: ...

    @t.overload
    def __call__(
        self,
        *,
        backend_key: str | None = None,
        readonly: bool = False,
        updatable: bool = False,
        required_once_stored: bool = False,
        may_be_large: bool = False,
        model_field_info: pdt.fields.FieldInfo | None = None,
        model_metadata: tuple[ModelMetadata, ...] = (),
        model_adapter: None = None,
        cli_exclude: bool = False,
        cli_field_info: CliFieldInfo | None = None,
        cli_adapter: CliAdapter[t.Any, t.Any] | None = None,
    ) -> Self: ...

    def __call__(self, *args: t.Any, **kwargs: t.Any) -> t.Any:
        return self._call(*args, **kwargs)


column: ColumnDecorator = ColumnDecorator()


def iter_columns(entity: type) -> dict[str, Column]:
    """Return all effective ORM columns on an entity hierarchy."""
    result: dict[str, Column] = {}

    for base in reversed(entity.__mro__):
        for name, value in vars(base).items():
            if isinstance(value, Column):
                result[name] = value
            elif name in result:
                del result[name]

    return result
