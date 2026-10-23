###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Adapters between fixed graph shapes and process ports."""

from __future__ import annotations

import typing as t
from collections.abc import Mapping
from functools import partial

from aiida.common.exceptions import GraphValidationError, MissingGraphInput, MissingRequiredInputsError
from aiida.engine.processes.generic.ports import UNSPECIFIED
from aiida.engine.processes.graphs.shapes import LeafShape, NamespaceShape, Shape, json_default
from aiida.engine.processes.port_model import _namespace_value
from aiida.engine.processes.ports import InputPort, OutputPort, PortNamespace


def at(container: t.Any, path: str) -> t.Any:
    """Read a value inside a namespace, or the whole namespace for an empty path."""
    for name in path.split('.') if path else ():
        container = container[name]
    return container


def place(inputs: dict[str, t.Any], path: str, value: t.Any) -> None:
    """Place a leaf or namespace reference without flattening dictionary-valued leaves."""
    *namespaces, name = path.split('.')
    target = inputs
    for namespace in namespaces:
        target = target.setdefault(namespace, {})
        if not isinstance(target, dict):
            msg = f'`{path}` puts an input inside a value rather than a namespace; rename one of them instead.'
            raise GraphValidationError(msg)
    target[name] = value


def shape_from_port(port: InputPort | OutputPort | PortNamespace) -> Shape:
    """Capture only the graph-relevant static contract of a process port."""
    options: dict[str, t.Any] = {'required': port.required, 'help': port.help}
    if not isinstance(port, PortNamespace):
        kinds = port.valid_type
        return LeafShape(types=(kinds,) if isinstance(kinds, type) else kinds, **options)
    return NamespaceShape(
        fields=tuple(
            (name, shape_from_port(child)) for name, child in port.items() if not getattr(child, 'is_metadata', False)
        ),
        **options,
    )


def port_for_shape(name: str, shape: Shape) -> InputPort | PortNamespace:
    """Rebuild a fixed boundary without mutating any shared process specification."""
    options: dict[str, t.Any] = {'required': shape.required, 'help': shape.help}
    if shape.default is not UNSPECIFIED:
        value = json_default(shape.default)
        options['default'] = partial(json_default, value) if isinstance(shape, LeafShape) else value
    if isinstance(shape, LeafShape):
        port = InputPort(name, valid_type=shape.types, **options)
        port.valid_type = shape.types
        return port
    namespace = PortNamespace(name, populate_defaults=shape.required, **options)
    for field, child in shape.fields:
        namespace[field] = port_for_shape(field, child)
    return namespace


class _InputResolver:
    """Apply defaults and aggregate missing graph input fields without mutating callers."""

    def __init__(self, identifier: str | None) -> None:
        self.identifier = identifier
        self.missing: list[MissingGraphInput] = []

    def fill(self, namespace: PortNamespace, given: Mapping[str, t.Any]) -> dict[str, t.Any]:
        """Return filled inputs, raising together all missing required fields.

        Filling applies defaults and checks shape only; converting filled
        inputs to runtime values belongs to `PortNamespace.prepare`.
        """
        prepared = self.visit(namespace, given, '')
        if self.missing:
            raise MissingRequiredInputsError(tuple(self.missing))
        return t.cast(dict[str, t.Any], prepared)

    def visit(self, port: InputPort | PortNamespace, value: t.Any, path: str) -> t.Any:
        """Fill one port, recording rather than raising missing required fields."""
        absent_namespace = False
        missing_before = len(self.missing)
        if value is UNSPECIFIED:
            value, absent_namespace = self._fill_default(port, path)
            if value is UNSPECIFIED:
                return UNSPECIFIED
        if not isinstance(port, PortNamespace):
            return value
        value = self._checked_mapping(port, value, path)
        result = dict(value)
        for name, child in sorted(port.items()):
            child_path = f'{path}.{name}' if path else name
            prepared = self.visit(child, value.get(name, UNSPECIFIED), child_path)
            if prepared is not UNSPECIFIED:
                result[name] = prepared
        if absent_namespace and len(self.missing) == missing_before:
            self.missing.append(MissingGraphInput(self.identifier, path, port.help, True))
        return result

    def _fill_default(self, port: InputPort | PortNamespace, path: str) -> tuple[t.Any, bool]:
        """Return a default value and whether an absent namespace was opened."""
        if port.has_default():
            default = port.default
            if callable(default):
                default = default()
            return json_default(default), False
        if not port.required:
            return UNSPECIFIED, False
        if not isinstance(port, PortNamespace) or not port:
            self.missing.append(MissingGraphInput(self.identifier, path, port.help, True))
            return UNSPECIFIED, False
        return {}, True

    def _checked_mapping(self, port: PortNamespace, value: t.Any, path: str) -> Mapping[str, t.Any]:
        """Return namespace values as a mapping, rejecting mistyped and unknown inputs."""
        value = _namespace_value(value)
        if not isinstance(value, Mapping):
            msg = f'graph input `{path}` must be a namespace mapping, not `{type(value).__name__}`.'
            raise GraphValidationError(msg)
        unknown = value.keys() - port.keys()
        if unknown:
            msg = f'unexpected graph inputs under `{path}`: {sorted(unknown)}.'
            raise GraphValidationError(msg)
        return value


def prepare_inputs(namespace: PortNamespace, given: Mapping[str, t.Any], identifier: str | None) -> dict[str, t.Any]:
    """Fill graph inputs with defaults, aggregating missing fields without mutating callers."""
    return _InputResolver(identifier).fill(namespace, given)
