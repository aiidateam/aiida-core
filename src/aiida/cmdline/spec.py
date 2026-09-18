from __future__ import annotations

import dataclasses
import typing as t

import pydantic as pdt
from pydantic_core import PydanticUndefined

from aiida.common.utils import make_required

__all__ = (
    'CliCreateSpec',
    'CliParameter',
    'PydanticCliCreateSpec',
)


@dataclasses.dataclass(frozen=True)
class CliParameter:
    """Resolved description of a CLI creation parameter."""

    name: str
    annotation: t.Any
    required: bool
    default: t.Any
    prompt: bool | str
    help: str
    priority: int = 0
    short_name: str = ''
    option_cls: t.Any = None

    @property
    def is_flag(self) -> bool:
        """Return whether the parameter should be rendered as a boolean flag."""
        return self.annotation is bool

    def as_option_spec(self) -> dict[str, t.Any]:
        """Return the Click option specification for this parameter."""
        spec: dict[str, t.Any] = {
            'required': self.required,
            'type': self.annotation,
            'is_flag': self.is_flag,
            'prompt': self.prompt,
            'default': self.default,
            'help': self.help,
            'priority': self.priority,
        }

        if self.short_name:
            spec['short_name'] = self.short_name

        if self.option_cls is not None:
            spec['option_cls'] = self.option_cls

        return spec


class CliCreateSpec(t.Protocol):
    """Specification for dynamically exposing creation through the CLI."""

    def parameters(self) -> list[CliParameter]:
        """Return the resolved CLI parameters."""

    def validate(self, values: dict[str, t.Any]) -> pdt.BaseModel:
        """Validate CLI values and return the corresponding creation model."""


class PydanticCliCreateSpec:
    """CLI creation specification backed directly by a Pydantic model."""

    def __init__(self, model: type[pdt.BaseModel]) -> None:
        self.model = model

    def parameters(self) -> list[CliParameter]:
        """Return CLI parameters derived from the Pydantic model."""
        parameters: list[CliParameter] = []

        for name, field_info in self.model.model_fields.items():
            if field_info.default is not PydanticUndefined:
                default = field_info.default
            elif field_info.default_factory is not None:
                default = field_info.default_factory
            else:
                default = None

            metadata: dict[str, t.Any] = {}

            for item in field_info.metadata:
                if isinstance(item, dict):
                    metadata.update(item)

            parameters.append(
                CliParameter(
                    name=name,
                    annotation=make_required(field_info.annotation),
                    required=field_info.is_required(),
                    default=default,
                    prompt=field_info.title or True,
                    help=field_info.description or '',
                    priority=metadata.get('priority', 0),
                    short_name=metadata.get('short_name', ''),
                    option_cls=metadata.get('option_cls'),
                )
            )

        return parameters

    def validate(self, values: dict[str, t.Any]) -> pdt.BaseModel:
        """Validate values against the underlying Pydantic model."""
        return self.model(**values)
