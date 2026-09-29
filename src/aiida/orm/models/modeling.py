from __future__ import annotations

import abc
import dataclasses
import typing as t
from collections.abc import Callable, Iterable

import pydantic as pdt

from aiida.common.lang import classproperty
from aiida.orm import qb_fields

__all__ = (
    'ModelAdapter',
    'ModelProjection',
    'ModelSerializerInfo',
    'ModelValidatorInfo',
    'iter_model_serializers',
    'iter_model_validators',
    'make_model_serializer',
    'make_model_validator',
    'model_serializer',
    'model_validator',
)


_EntityValueT = t.TypeVar('_EntityValueT')
_ModelValueT = t.TypeVar('_ModelValueT')
_QbFieldT = t.TypeVar('_QbFieldT', bound=qb_fields.QbField)


class ModelAdapter(abc.ABC, t.Generic[_EntityValueT, _ModelValueT, _QbFieldT]):
    """Abstract base class for model adapters that convert between orm and model values."""

    _model_type: t.ClassVar[t.Any] = None

    @classproperty
    def model_type(cls: type[ModelAdapter]) -> t.Any:  # noqa: N805
        """Return the model type inferred from `to_model`."""
        if cls._model_type is None:
            try:
                cls._model_type = t.get_type_hints(cls.to_model)['return']
            except KeyError:
                msg = f'`{cls.__name__}.to_model` must have a return annotation'
                raise TypeError(msg) from None

        return cls._model_type

    @abc.abstractmethod
    def to_model(self, value: _EntityValueT, *, context: dict[str, t.Any] | None = None) -> _ModelValueT:
        """Convert an orm value to its model representation."""

    @abc.abstractmethod
    def to_orm(self, value: _ModelValueT) -> _EntityValueT:
        """Convert a model value to its orm representation."""


ModelProjection = t.Literal['read', 'create', 'update']


@dataclasses.dataclass(frozen=True)
class ModelValidatorInfo:
    """Configuration for a generated entity-model validator."""

    mode: t.Literal['before', 'after', 'wrap']
    projections: frozenset[ModelProjection] | None = None


@dataclasses.dataclass(frozen=True)
class ModelSerializerInfo:
    """Configuration for a generated entity-model serializer."""

    mode: t.Literal['plain', 'wrap']
    projections: frozenset[ModelProjection] | None = None


_ModelValidator = tuple[Callable[..., t.Any], ModelValidatorInfo]
_ModelSerializer = tuple[Callable[..., t.Any], ModelSerializerInfo]


def model_validator(
    *,
    mode: t.Literal['before', 'after', 'wrap'],
    projections: Iterable[ModelProjection] | None = None,
) -> Callable[[staticmethod], staticmethod]:
    """Declare a validator for generated entity models.

    The decorated method must be a `staticmethod`. The callback is later
    installed as a real Pydantic model validator on each generated entity-model
    projection to which it applies.
    """
    info = ModelValidatorInfo(
        mode=mode,
        projections=None if projections is None else frozenset(projections),
    )

    def decorator(method: staticmethod) -> staticmethod:
        if not isinstance(method, staticmethod):
            raise TypeError('model_validator must decorate a staticmethod')

        setattr(method.__func__, '__aiida_model_validator__', info)
        return method

    return decorator


def model_serializer(
    *,
    mode: t.Literal['plain', 'wrap'],
    projections: Iterable[ModelProjection] | None = None,
) -> Callable[[staticmethod], staticmethod]:
    """Declare a serializer for generated entity models.

    The decorated method must be a `staticmethod`. The callback is later
    installed as a real Pydantic instance serializer on each generated
    entity-model projection to which it applies.
    """
    info = ModelSerializerInfo(
        mode=mode,
        projections=None if projections is None else frozenset(projections),
    )

    def decorator(method: staticmethod) -> staticmethod:
        if not isinstance(method, staticmethod):
            raise TypeError('model_serializer must decorate a staticmethod')

        setattr(method.__func__, '__aiida_model_serializer__', info)
        return method

    return decorator


def iter_model_validators(entity: type) -> dict[str, _ModelValidator]:
    """Return effective model validators across an entity hierarchy."""
    result: dict[str, _ModelValidator] = {}

    for base in reversed(entity.__mro__):
        for name, value in vars(base).items():
            if isinstance(value, staticmethod):
                function = value.__func__
                info = getattr(function, '__aiida_model_validator__', None)

                if isinstance(info, ModelValidatorInfo):
                    result[name] = (function, info)
                    continue

            result.pop(name, None)

    return result


def iter_model_serializers(entity: type) -> dict[str, _ModelSerializer]:
    """Return effective model serializers across an entity hierarchy."""
    result: dict[str, _ModelSerializer] = {}

    for base in reversed(entity.__mro__):
        for name, value in vars(base).items():
            if isinstance(value, staticmethod):
                function = value.__func__
                info = getattr(function, '__aiida_model_serializer__', None)

                if isinstance(info, ModelSerializerInfo):
                    result[name] = (function, info)
                    continue

            result.pop(name, None)

    return result


def make_model_validator(
    function: Callable[..., t.Any],
    *,
    mode: t.Literal['before', 'after', 'wrap'],
) -> t.Any:
    """Create a real Pydantic model validator delegating to a static callback."""
    if mode == 'before':

        @pdt.model_validator(mode='before')  # type: ignore[misc]
        @classmethod
        def validator(cls: type[pdt.BaseModel], value: t.Any) -> t.Any:
            return function(value)

        return validator

    if mode == 'after':

        @pdt.model_validator(mode='after')
        def validator(self: pdt.BaseModel) -> t.Any:
            return function(self)

        return validator

    if mode == 'wrap':

        @pdt.model_validator(mode='wrap')  # type: ignore[misc]
        @classmethod
        def validator(
            cls: type[pdt.BaseModel],
            value: t.Any,
            handler: pdt.ModelWrapValidatorHandler[t.Any],
        ) -> t.Any:
            return function(value, handler)

        return validator

    t.assert_never(mode)


def make_model_serializer(
    function: Callable[..., t.Any],
    *,
    mode: t.Literal['plain', 'wrap'],
) -> t.Any:
    """Create a real Pydantic model serializer delegating to a static callback."""
    if mode == 'plain':

        @pdt.model_serializer(mode='plain')
        def serializer(self: pdt.BaseModel) -> t.Any:
            return function(self)

        return serializer

    if mode == 'wrap':

        @pdt.model_serializer(mode='wrap')
        def serializer(  # type: ignore[misc]
            self: pdt.BaseModel,
            handler: pdt.SerializerFunctionWrapHandler,
        ) -> t.Any:
            return function(self, handler)

        return serializer

    t.assert_never(mode)
