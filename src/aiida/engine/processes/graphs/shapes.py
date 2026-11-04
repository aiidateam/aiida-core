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

import functools
import math
import operator
import typing as t
from collections.abc import Mapping
from dataclasses import dataclass

from aiida.common.exceptions import GraphLanguageError, GraphTypeCheckError
from aiida.common.loaders import get_object_loader
from aiida.engine.processes.generic.ports import UNSPECIFIED
from aiida.engine.processes.port_model import _fields_of, _namespace_value, _port_help, _without_marks
from aiida.engine.processes.ports import _infer_runtime_types

if t.TYPE_CHECKING:
    from aiida.engine.processes.graphs.lowering import GraphHandle
    from aiida.engine.processes.graphs.tasks import CalcJobTaskHandle, FunctionTaskHandle, WorkChainTaskHandle

__all__ = (
    'Forward',
    'LeafShape',
    'NamespaceShape',
    'dump_shape',
    'load_shape',
    'namespace_shape_for',
    'shape_for_annotation',
)


@dataclass(frozen=True, kw_only=True)
class _ValueShape:
    """Requiredness, documentation and defaults shared by graph value contracts."""

    required: bool = True
    help: str | None = None
    default: object = UNSPECIFIED


@dataclass(frozen=True, kw_only=True)
class LeafShape(_ValueShape):
    """One value with optional valid types."""

    types: tuple[type, ...] | None = None


@dataclass(frozen=True, kw_only=True)
class NamespaceShape(_ValueShape):
    """Fixed fields declared by a PortModel or a flat set of named output ports."""

    fields: tuple[tuple[str, Shape], ...] = ()

    def select(self, name: str) -> Shape:
        """Return a declared field's contract, or reject an unknown field."""
        for field_name, shape in self.fields:
            if name == field_name:
                return shape
        raise KeyError(name)


Shape: t.TypeAlias = LeafShape | NamespaceShape


def _is_type_var(annotation: object) -> bool:
    """Return whether an annotation is a `TypeVar`, on any supported Python version."""
    return type(annotation).__name__ == 'TypeVar' and hasattr(annotation, '__constraints__')


def _contains_typevar(annotation: t.Any) -> bool:
    """Return whether a `TypeVar` hides inside a generic annotation."""
    return any(_is_type_var(arg) or _contains_typevar(arg) for arg in t.get_args(_without_marks(annotation)))


def _expand_typevar(annotation: t.Any) -> t.Any:
    """Return the union a bare `TypeVar` declares: constraints, bound, or open."""
    constraints = annotation.__constraints__
    if constraints:
        return functools.reduce(operator.or_, constraints)
    if isinstance(annotation.__bound__, type):
        return annotation.__bound__
    return t.Any


def _expanded_annotation(annotation: t.Any) -> t.Any:
    """Expand a bare `TypeVar`, rejecting nested generics."""
    bare = _without_marks(annotation)
    if _is_type_var(bare):
        return _expand_typevar(bare)
    if _contains_typevar(bare):
        msg = 'type variables declare whole ports, not nested generics; declare concrete types instead.'
        raise GraphTypeCheckError(msg)
    return annotation


class Forward:
    """Mirror a task's input contract: `bundle: Annotated[Any, Forward(task, exclude=...)]`."""

    def __init__(
        self,
        task: FunctionTaskHandle[t.Any, t.Any] | CalcJobTaskHandle | WorkChainTaskHandle | GraphHandle,
        *,
        exclude: tuple[str, ...] | list[str] | str = (),
    ) -> None:
        self.task = task
        self.exclude = _checked_excludes(exclude)


def _checked_excludes(exclude: t.Any) -> tuple[str, ...]:
    """Normalize exclusions to a tuple, accepting a single string as one path."""
    names = (exclude,) if isinstance(exclude, str) else tuple(exclude)
    for name in names:
        if not isinstance(name, str):
            msg = (
                'forward exclusions name input paths, so exclusions must be strings; '
                + f'{name!r} is not excludable; pass dotted input paths instead'
            )
            raise GraphLanguageError(msg)
    return tuple(names)


def _forward_marker(annotation: t.Any) -> Forward | None:
    """Return the `Forward` marker of an annotated declaration, if present."""
    if t.get_origin(annotation) is t.Annotated:
        for mark in t.get_args(annotation)[1:]:
            if isinstance(mark, Forward):
                return mark
    return None


def _shape_paths(shape: NamespaceShape, *, path: str = '') -> set[str]:
    """Return every input path of a namespace shape."""
    paths = set()
    for name, child in shape.fields:
        location = f'{path}.{name}' if path else name
        paths.add(location)
        if isinstance(child, NamespaceShape):
            paths |= _shape_paths(child, path=location)
    return paths


def _without_excluded(shape: NamespaceShape, excludes: tuple[str, ...], *, path: str = '') -> NamespaceShape:
    """Drop excluded input paths from a namespace shape."""
    fields: list[tuple[str, Shape]] = []
    for name, child in shape.fields:
        location = f'{path}.{name}' if path else name
        if location in excludes:
            continue
        if isinstance(child, NamespaceShape):
            pruned = _without_excluded(child, excludes, path=location)
            fields.append((name, pruned))
            continue
        fields.append((name, child))
    return NamespaceShape(fields=tuple(fields), required=shape.required, help=shape.help, default=shape.default)


def _forwarded_shape(
    task: FunctionTaskHandle[t.Any, t.Any] | CalcJobTaskHandle | WorkChainTaskHandle | GraphHandle,
    exclude: tuple[str, ...],
) -> NamespaceShape:
    """Return a task's input contract, minus exclusions, for one graph input namespace."""
    from aiida.engine.processes.graphs.lowering import GraphHandle

    if isinstance(task, GraphHandle):
        shape = task.build().input_shape
    else:
        spec = getattr(task, '_task_spec', None)
        if spec is None:
            msg = (
                'forward declarations mirror task inputs, so only tasks and graphs forward; '
                + f'{task!r} is neither; pass a task handle instead'
            )
            raise GraphLanguageError(msg)
        shape = spec.input_shape
    paths = _shape_paths(shape)
    for excluded in exclude:
        if excluded not in paths and not any(path.startswith(excluded + '.') for path in paths):
            msg = (
                'exclusions drop declared inputs, so exclusions name declared input paths; '
                + f'`{excluded}` matches no input here; exclude a declared input path instead'
            )
            raise GraphLanguageError(msg)
    return _without_excluded(shape, exclude)


def shape_for_annotation(
    annotation: object, *, required: bool = True, default: object = UNSPECIFIED, help: str | None = None
) -> Shape:
    """Capture a Python declaration without constructing engine input or output ports."""
    if default is not UNSPECIFIED:
        if callable(default):
            try:
                default = default()
            except Exception as exception:
                msg = 'a default factory failed; declare a plain value or a working factory instead.'
                raise GraphTypeCheckError(msg) from exception
        default = json_default(default)
    resolved_help = help or _port_help(annotation)
    marker = _forward_marker(annotation)
    if marker is not None:
        return _forwarded_shape(marker.task, marker.exclude)
    annotation = _without_marks(annotation)
    annotation = _expanded_annotation(annotation)
    fields = _fields_of(annotation)
    if fields is None:
        return LeafShape(
            types=_infer_runtime_types(annotation) or None, required=required, default=default, help=resolved_help
        )
    return NamespaceShape(
        fields=tuple(
            (
                field.name,
                shape_for_annotation(field.annotation, required=field.required, default=field.default, help=field.help),
            )
            for field in fields
        ),
        required=required,
        default=default,
        help=resolved_help,
    )


def namespace_shape_for(
    hints: Mapping[str, object], names: tuple[str, ...], defaults: Mapping[str, object] | None = None
) -> NamespaceShape:
    """Capture the named inputs of a source graph."""
    given = defaults or {}
    return NamespaceShape(
        fields=tuple(
            (
                name,
                shape_for_annotation(hints.get(name), required=name not in given, default=given.get(name, UNSPECIFIED)),
            )
            for name in names
        )
    )


def json_default(value: object) -> object:
    """Copy finite JSON defaults, rejecting identities and executable values."""
    value = _namespace_value(value)
    if value is None or isinstance(value, (bool, int, str)):
        return value
    if isinstance(value, float) and math.isfinite(value):
        return value
    if isinstance(value, list):
        return [json_default(item) for item in value]
    if isinstance(value, Mapping) and all(isinstance(key, str) for key in value):
        return {key: json_default(item) for key, item in value.items()}
    msg = f'graph default of type `{type(value).__name__}` is not a finite JSON value.'
    raise GraphTypeCheckError(msg)


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
    return result


def load_shape(data: Mapping[str, t.Any]) -> Shape:
    """Restore a native contract without importing or constructing process ports."""
    for key in ('required', 'kind'):
        if key not in data:
            msg = f'malformed shape declaration; missing key {key!r}.'
            raise GraphTypeCheckError(msg)
    required, help = data['required'], data.get('help')
    if not isinstance(required, bool) or (help is not None and not isinstance(help, str)):
        msg = 'shape declarations require boolean requiredness and string help.'
        raise GraphTypeCheckError(msg)
    default = json_default(data['default']) if 'default' in data else UNSPECIFIED
    if data['kind'] == 'leaf':
        types = data.get('types')
        return LeafShape(
            types=None
            if types is None
            else tuple(type(None) if kind is None else get_object_loader().load_object(kind) for kind in types),
            required=required,
            help=help,
            default=default,
        )
    if data['kind'] == 'namespace':
        if 'extra' in data:
            msg = 'dynamic graph namespaces are not supported.'
            raise GraphTypeCheckError(msg)
        if 'fields' not in data:
            msg = "malformed shape declaration; missing key 'fields'."
            raise GraphTypeCheckError(msg)
        return NamespaceShape(
            fields=tuple((name, load_shape(field)) for name, field in data['fields'].items()),
            required=required,
            help=help,
            default=default,
        )
    msg = f'Unknown graph value shape `{data["kind"]}`.'
    raise GraphTypeCheckError(msg)
