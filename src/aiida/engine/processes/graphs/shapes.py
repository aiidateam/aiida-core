###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Native value contracts for graph references, independent of process ports."""

from __future__ import annotations

import inspect
import math
import typing as t
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from types import UnionType

from aiida.common.loaders import get_object_loader
from aiida.engine.processes.many import _takes_many
from aiida.engine.processes.port_model import UNSPECIFIED, _port_help, as_dict, fields_of, without_marks


@dataclass(frozen=True, kw_only=True)
class ValueShape:
    """Requiredness, documentation and defaults shared by graph value contracts."""

    required: bool = True
    help: str | None = None
    default: object = UNSPECIFIED


@dataclass(frozen=True, kw_only=True)
class LeafShape(ValueShape):
    """One value, rather than a collection of individually linked fields."""

    types: tuple[type, ...] | None = None


@dataclass(frozen=True, kw_only=True)
class NamespaceShape(ValueShape):
    """Fixed fields declared by a PortModel, optionally allowing additional entries."""

    fields: tuple[tuple[str, Shape], ...] = ()
    extra: Shape | None = None

    def select(self, name: str) -> Shape:
        """Return a declared field's contract, or reject an unknown field."""
        for field_name, shape in self.fields:
            if name == field_name:
                return shape
        if self.extra is not None:
            return self.extra
        raise KeyError(name)


@dataclass(frozen=True, kw_only=True)
class ManyShape(ValueShape):
    """A runtime-keyed collection with one contract for every entry."""

    entry: Shape


Shape: t.TypeAlias = LeafShape | NamespaceShape | ManyShape


class _Options(t.TypedDict):
    required: bool
    help: str | None
    default: object


def shape_for_annotation(
    annotation: object, *, required: bool = True, default: object = UNSPECIFIED, help: str | None = None
) -> Shape:
    """Capture a Python declaration without constructing engine input or output ports."""
    options: _Options = {'required': required, 'default': default, 'help': help or _port_help(annotation)}
    annotation = without_marks(annotation)
    if _takes_many(annotation):
        args = t.get_args(annotation)
        return ManyShape(entry=shape_for_annotation(args[0] if args else None), **options)
    fields = fields_of(annotation)
    if fields is not None:
        return NamespaceShape(
            fields=tuple(
                (
                    field.name,
                    shape_for_annotation(
                        field.annotation, required=field.required, default=field.default, help=field.help
                    ),
                )
                for field in fields
            ),
            **options,
        )
    origin = t.get_origin(annotation)
    types = None
    if annotation is not t.Any:
        if origin in (t.Union, UnionType):
            args = t.get_args(annotation)
            types = tuple(arg for arg in args if isinstance(arg, type)) or None
        elif origin in (dict, list):
            types = (origin,)
        elif isinstance(annotation, type):
            types = (annotation,)
    return LeafShape(types=types, **options)


def shape_for_annotations(hints: Mapping[str, object], names: tuple[str, ...]) -> NamespaceShape:
    """Capture the named inputs of a source graph."""
    return NamespaceShape(fields=tuple((name, shape_for_annotation(hints.get(name))) for name in names))


def shape_for_function(function: Callable[..., object]) -> NamespaceShape:
    """Capture named function parameters, including defaults and resolved annotations."""
    hints = t.get_type_hints(function, include_extras=True)
    fields = []
    for name, parameter in inspect.signature(function).parameters.items():
        if parameter.kind not in (parameter.POSITIONAL_OR_KEYWORD, parameter.KEYWORD_ONLY):
            continue
        default = UNSPECIFIED if parameter.default is parameter.empty else parameter.default
        try:
            if default is not UNSPECIFIED:
                default = json_default(default)
            shape = shape_for_annotation(hints.get(name), required=default is UNSPECIFIED, default=default)
            dump_shape(shape)
        except TypeError as exception:
            msg = f'cannot declare graph input `{name}`: {exception}'
            raise TypeError(msg) from exception
        fields.append((name, shape))
    return NamespaceShape(fields=tuple(fields))


def json_default(value: object) -> object:
    """Copy finite JSON defaults, rejecting identities and executable values."""
    held = as_dict(value)
    if held is not None:
        value = held
    if value is None or isinstance(value, (bool, int, str)):
        return value
    if isinstance(value, float) and math.isfinite(value):
        return value
    if isinstance(value, list):
        return [json_default(item) for item in value]
    if isinstance(value, Mapping) and all(isinstance(key, str) for key in value):
        return {key: json_default(item) for key, item in value.items()}
    msg = f'graph default of type `{type(value).__name__}` is not a finite JSON value.'
    raise TypeError(msg)


def dump_shape(shape: Shape, *, defaults: bool = True) -> dict[str, t.Any]:
    """Serialize a native value contract; no process-port properties are persisted."""
    result: dict[str, t.Any] = {'required': shape.required, 'help': shape.help}
    if defaults and shape.default is not UNSPECIFIED:
        result['default'] = json_default(shape.default)
    if isinstance(shape, LeafShape):
        result.update(
            kind='leaf',
            types=None
            if shape.types is None
            else [None if kind is type(None) else get_object_loader().identify_object(kind) for kind in shape.types],
        )
    elif isinstance(shape, NamespaceShape):
        result.update(
            kind='namespace', fields={name: dump_shape(field, defaults=defaults) for name, field in shape.fields}
        )
        if shape.extra is not None:
            result['extra'] = dump_shape(shape.extra, defaults=defaults)
    else:
        result.update(kind='many', entry=dump_shape(shape.entry, defaults=defaults))
    return result


def load_shape(data: Mapping[str, t.Any]) -> Shape:
    """Restore a native contract without importing or constructing process ports."""
    required, help = data['required'], data.get('help')
    if not isinstance(required, bool) or (help is not None and not isinstance(help, str)):
        msg = 'shape declarations require boolean requiredness and string help.'
        raise TypeError(msg)
    options: _Options = {
        'required': required,
        'help': help,
        'default': json_default(data['default']) if 'default' in data else UNSPECIFIED,
    }
    if data['kind'] == 'leaf':
        types = data.get('types')
        return LeafShape(
            types=None
            if types is None
            else tuple(type(None) if kind is None else get_object_loader().load_object(kind) for kind in types),
            **options,
        )
    if data['kind'] == 'namespace':
        return NamespaceShape(
            fields=tuple((name, load_shape(field)) for name, field in data['fields'].items()),
            extra=load_shape(data['extra']) if 'extra' in data else None,
            **options,
        )
    if data['kind'] == 'many':
        return ManyShape(entry=load_shape(data['entry']), **options)
    msg = f'Unknown graph value shape `{data["kind"]}`.'
    raise ValueError(msg)
