from __future__ import annotations

import abc
import dataclasses
import typing as t
from collections.abc import Callable

from pydantic.fields import FieldInfo as ModelFieldInfo
from typing_extensions import Self

from aiida.common import exceptions
from aiida.common.utils import is_nullable
from aiida.orm import qb_fields
from aiida.orm.cli.utils import CliFieldInfo

__all__ = (
    'BaseField',
    'BaseFieldConfig',
    'BaseFieldDecorator',
    'BaseFieldSpec',
    'Storable',
)

if t.TYPE_CHECKING:
    from aiida.orm.cli.utils import CliAdapter
    from aiida.orm.models.modeling import ModelAdapter


@dataclasses.dataclass(frozen=True)
class BaseFieldConfig:
    """Base unresolved configuration for an ORM field."""

    readonly: bool = False
    required_once_stored: bool = False

    model_field_info: ModelFieldInfo = dataclasses.field(default_factory=ModelFieldInfo)
    model_metadata: tuple[t.Any, ...] = ()
    model_adapter: ModelAdapter[t.Any, t.Any, t.Any] | None = None

    cli_exclude: bool = False
    cli_field_info: CliFieldInfo = dataclasses.field(default_factory=CliFieldInfo)
    cli_adapter: CliAdapter[t.Any, t.Any] | None = None


@dataclasses.dataclass(frozen=True)
class BaseFieldSpec:
    """Base semantic description of an ORM field."""

    name: str
    value_type: t.Any
    description: str
    readonly: bool
    required_once_stored: bool


class Storable(t.Protocol):
    """Protocol for ORM objects with storage lifecycle semantics."""

    @property
    def is_stored(self) -> bool: ...


_OwnerT = t.TypeVar('_OwnerT', bound=Storable)
_ValueT = t.TypeVar('_ValueT')
_QbFieldT = t.TypeVar('_QbFieldT', bound=qb_fields.QbField)
_SpecT = t.TypeVar('_SpecT', bound=BaseFieldSpec)
_ConfigT = t.TypeVar('_ConfigT', bound=BaseFieldConfig)


class BaseField(
    abc.ABC,
    t.Generic[
        _OwnerT,
        _ValueT,
        _QbFieldT,
        _SpecT,
        _ConfigT,
    ],
):
    """Common infrastructure for typed ORM field declarations."""

    config_type: t.ClassVar[type[_ConfigT]]
    spec_type: t.ClassVar[type[_SpecT]]

    def __init__(
        self,
        fget: Callable[[_OwnerT], _ValueT],
        fset: Callable[[_OwnerT, _ValueT], None] | None = None,
        fdel: Callable[[_OwnerT], None] | None = None,
        *,
        config: _ConfigT,
    ) -> None:
        self.fget = fget
        self.fset = fset
        self.fdel = fdel

        self.__doc__ = getattr(fget, '__doc__', None)

        self._name: str | None = None
        self._owner: type[_OwnerT] | None = None
        self._config = config
        self._spec: _SpecT | None = None
        self._qb_field: _QbFieldT | None = None

    def __set_name__(self, owner: type[_OwnerT], name: str) -> None:
        self._name = name
        self._owner = owner

    def __set__(self, instance: _OwnerT, value: _ValueT) -> None:
        func = self._get_valid_mutability_function(instance, self.fset)
        func(instance, value)

    def __delete__(self, instance: _OwnerT) -> None:
        func = self._get_valid_mutability_function(instance, self.fdel)
        func(instance)

    @property
    def spec(self) -> _SpecT:
        """Return the lazily resolved field specification."""
        if self._spec is None:
            self._spec = self._build_spec()

        return self._spec

    @property
    def model_field_info(self) -> ModelFieldInfo:
        """Return optional Pydantic-specific field configuration."""
        return self._config.model_field_info

    @property
    def model_metadata(self) -> tuple[t.Any, ...]:
        """Return additional Pydantic `Annotated` metadata."""
        return self._config.model_metadata

    @property
    def model_adapter(self) -> ModelAdapter[t.Any, t.Any, t.Any] | None:
        """Return the entity/model representation adapter."""
        return self._config.model_adapter

    @property
    def adapted_type(self) -> t.Any:
        """Return the model-adapted representation type."""
        if self.model_adapter is not None:
            return self.model_adapter.model_type

        return self.spec.value_type

    @property
    def cli_exclude(self) -> bool:
        """Return whether the field should be excluded from the CLI."""
        return self._config.cli_exclude

    @property
    def cli_field_info(self) -> CliFieldInfo:
        """Return optional CLI-specific field configuration."""
        return self._config.cli_field_info

    @property
    def cli_adapter(self) -> CliAdapter[t.Any, t.Any] | None:
        """Return the model/CLI representation adapter."""
        return self._config.cli_adapter

    @property
    def title(self) -> str:
        """Return the human-readable title."""
        if self.model_field_info.title is not None:
            return self.model_field_info.title

        return self.spec.name.replace('_', ' ').title()

    def getter(self, fget: Callable[[_OwnerT], _ValueT], /) -> Self:
        """Set the getter and return this descriptor."""
        self.fget = fget
        self.__doc__ = getattr(fget, '__doc__', None)
        self._spec = None
        self._qb_field = None
        return self

    def setter(self, fset: Callable[[_OwnerT, _ValueT], None], /) -> Self:
        """Set the setter and return this descriptor."""
        if self._config.readonly:
            raise TypeError('cannot define a setter for a read-only ORM field')

        self.fset = fset
        self._spec = None
        return self

    def deleter(self, fdel: Callable[[_OwnerT], None], /) -> Self:
        """Set the deleter and return this descriptor."""
        if self._config.readonly:
            raise TypeError('cannot define a deleter for a read-only ORM field')

        self.fdel = fdel
        return self

    def _get_valid_mutability_function(
        self,
        instance: _OwnerT,
        func: Callable[..., t.Any] | None,
    ) -> Callable[..., t.Any]:
        """Return mutability function if field is mutable."""
        if self._owner is None or self._name is None:
            raise RuntimeError('column has not been assigned to an entity')

        if func is None:
            func_name = 'setter' if func is self.fset else 'deleter'
            msg = f'{self._owner.__name__}.{self._name} has no {func_name}'
            raise AttributeError(msg)

        if self.spec.readonly:
            msg = f'{self._owner.__name__}.{self._name} is read-only'
            raise AttributeError(msg)

        if self._immutable_once_stored(instance):
            msg = f'{self._owner.__name__}.{self._name} is immutable once stored'
            raise exceptions.ModificationNotAllowed(msg)

        return func

    @abc.abstractmethod
    def _immutable_once_stored(self, instance: _OwnerT) -> bool:
        """Check whether the field is immutable once stored."""

    def _build_spec(self, **kwargs: t.Any) -> _SpecT:
        """Resolve the declaration into the canonical specification."""
        spec = self.spec_type(
            **self._base_spec_values(),
            readonly=self._config.readonly,
            required_once_stored=self._config.required_once_stored,
            **kwargs,
        )

        if spec.readonly and self.fset is not None:
            msg = f'{spec.name!r} is declared read-only but defines a setter'
            raise TypeError(msg)

        if spec.required_once_stored and not is_nullable(spec.value_type):
            msg = f'{spec.name!r} cannot be required_once_stored because its declared type is not nullable'
            raise TypeError(msg)

        return spec

    def _base_spec_values(self) -> dict[str, t.Any]:
        """Return values shared by all field specifications."""
        if self._owner is None or self._name is None:
            raise RuntimeError('field has not been assigned to a class')

        value_type = t.get_type_hints(self.fget).get('return')

        field = f'{self._owner.__name__}.{self._name}'

        if value_type is None:
            msg = f'{field!r} is missing a return type annotation'
            raise TypeError(msg)

        if value_type is t.Any:
            msg = (
                f"{field!r} has return type 'Any'. Use 'object' instead to express an unconstrained type, "
                "as 'Any' is too permissive for reliable ORM field typing."
            )
            raise TypeError(msg)

        # We only take the first line of the docstring as the description,
        description = (self.__doc__ or '').strip().split('\n')[0].strip()

        return {
            'name': self._name,
            'value_type': value_type,
            'description': description,
        }

    def _build_qb_field(self, key: str, *, is_attribute: bool) -> _QbFieldT:
        """Build the QueryBuilder representation of this field."""
        return t.cast(
            _QbFieldT,
            qb_fields.add_field(
                key,
                dtype=self.adapted_type,
                doc=self.spec.description,
                is_attribute=is_attribute,
            ),
        )

    def _get_qb_field(self, key: str, *, is_attribute: bool) -> _QbFieldT:
        """Return the lazily constructed QueryBuilder field."""
        if self._qb_field is None:
            self._qb_field = self._build_qb_field(key, is_attribute=is_attribute)

        return self._qb_field


_FieldT = t.TypeVar('_FieldT', bound=BaseField)


class BaseFieldDecorator(
    t.Generic[
        _OwnerT,
        _ValueT,
        _ConfigT,
        _FieldT,
    ]
):
    """Common decorator-factory mechanics for typed field declarations."""

    config_type: Callable[..., _ConfigT]
    field_type: Callable[..., _FieldT]

    def __init__(self, config: _ConfigT | None = None) -> None:
        self._config = config or self.config_type()

    def _call(
        self,
        fget: Callable[..., t.Any] | None = None,
        /,
        **kwargs: t.Any,
    ) -> _FieldT | Self:
        if fget is None:
            return type(self)(self.config_type(**kwargs))

        return self.field_type(fget, config=self._config)
