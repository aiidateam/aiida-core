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

from aiida.common.exceptions import MissingInput, MissingRequiredInputsError
from aiida.engine.processes.graphs.shapes import LeafShape, NamespaceShape, Shape, json_default
from aiida.engine.processes.port_model import UNSPECIFIED, as_dict
from aiida.engine.processes.ports import InputPort, OutputPort, PortNamespace


def at(container: t.Any, path: str) -> t.Any:
    """Read a value inside a namespace, or the whole namespace for an empty path."""
    for name in path.split('.') if path else ():
        container = container[name]
    return container


def shape_from_port(port: InputPort | OutputPort | PortNamespace, *, defaults: bool = True) -> Shape:
    """Capture only the graph-relevant static contract of a process port."""
    options: dict[str, t.Any] = {'required': port.required, 'help': port.help}
    if defaults and isinstance(port, (InputPort, PortNamespace)) and port.has_default():
        default = port.default
        if isinstance(default, partial) and default.func is json_default:
            default = default.args[0]
        options['default'] = json_default(default)
    if not isinstance(port, PortNamespace):
        kinds = port.valid_type
        return LeafShape(types=(kinds,) if isinstance(kinds, type) else kinds, **options)
    return NamespaceShape(
        fields=tuple(
            (name, shape_from_port(child, defaults=defaults))
            for name, child in port.items()
            if not getattr(child, 'is_metadata', False)
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


def prepare_inputs(namespace: PortNamespace, given: Mapping[str, t.Any], identifier: str | None) -> dict[str, t.Any]:
    """Apply defaults and aggregate missing graph input fields without mutating callers."""
    missing: list[MissingInput] = []

    def visit(port: InputPort | PortNamespace, value: t.Any, path: str) -> t.Any:
        absent_namespace = False
        missing_before = len(missing)
        if value is UNSPECIFIED:
            if port.has_default():
                default = port.default
                if isinstance(default, partial) and default.func is json_default:
                    default = default.args[0]
                value = json_default(default)
            elif not port.required:
                return UNSPECIFIED
            elif not isinstance(port, PortNamespace) or not port:
                missing.append(MissingInput(identifier, path, port.help, True))
                return UNSPECIFIED
            else:
                absent_namespace = True
                value = {}
        if not isinstance(port, PortNamespace):
            return value
        held = as_dict(value)
        value = value if held is None else held
        if not isinstance(value, Mapping):
            msg = f'graph input `{path}` must be a namespace mapping, not `{type(value).__name__}`.'
            raise TypeError(msg)
        unknown = value.keys() - port.keys()
        if unknown:
            msg = f'unexpected graph inputs under `{path}`: {sorted(unknown)}.'
            raise TypeError(msg)
        result = dict(value)
        for name, child in sorted(port.items()):
            child_path = f'{path}.{name}' if path else name
            prepared = visit(child, value.get(name, UNSPECIFIED), child_path)
            if prepared is not UNSPECIFIED:
                result[name] = prepared
        if absent_namespace and len(missing) == missing_before:
            missing.append(MissingInput(identifier, path, port.help, True))
        return result

    prepared = visit(namespace, given, '')
    if missing:
        raise MissingRequiredInputsError(tuple(missing))
    return t.cast(dict[str, t.Any], prepared)
