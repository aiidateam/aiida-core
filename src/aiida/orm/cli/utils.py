from __future__ import annotations

import abc
import dataclasses
import functools
import typing as t

import pydantic as pdt

from aiida.common.lang import classproperty

if t.TYPE_CHECKING:
    from aiida.cmdline.params.options.interactive import TemplateInteractiveOption
    from aiida.orm.decorators.base import BaseField

__all__ = (
    'CliAdapter',
    'CliField',
    'CliFieldInfo',
)


@dataclasses.dataclass(frozen=True)
class CliFieldInfo:
    """Optional Click-specific configuration for an ORM field."""

    prompt: str | bool | None = None
    help: str = ''
    priority: int = 0
    short_name: str = ''
    option_cls: functools.partial[TemplateInteractiveOption] | None = None


@dataclasses.dataclass(frozen=True)
class CliField:
    """Resolved ORM field participating in CLI creation."""

    name: str
    field: BaseField
    model_field: pdt.fields.FieldInfo


_CliValueT = t.TypeVar('_CliValueT')
_ModelValueT = t.TypeVar('_ModelValueT')


class CliAdapter(abc.ABC, t.Generic[_CliValueT, _ModelValueT]):
    """Abstract base class for adapters between CLI/external and model-side representations."""

    _cli_type: t.ClassVar[t.Any] = None

    @classproperty
    def cli_type(cls: type[CliAdapter]) -> t.Any:  # noqa: N805
        """Return the CLI-side type inferred from the `to_model` value annotation."""
        if cls._cli_type is None:
            try:
                cls._cli_type = t.get_type_hints(cls.to_model)['value']
            except KeyError:
                msg = f'{cls.__name__}.to_model must annotate its `value` parameter'
                raise TypeError(msg) from None

        return cls._cli_type

    @abc.abstractmethod
    def to_model(self, value: _CliValueT) -> _ModelValueT:
        """Convert a CLI/external value to its model-side representation."""

    @abc.abstractmethod
    def to_cli(self, value: _ModelValueT) -> _CliValueT:
        """Convert a model-side value to its CLI/external representation."""
