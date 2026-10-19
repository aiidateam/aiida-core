###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Graph boundaries use ordinary input ports; namespaces are not stored data nodes."""

from __future__ import annotations

import typing as t
from collections.abc import Mapping, Sequence
from functools import partial

from aiida.common.exceptions import MissingInput, MissingRequiredInputsError
from aiida.engine.processes.graphs.shapes import LeafShape, ManyShape, NamespaceShape, Shape
from aiida.engine.processes.graphs.shapes import json_default as _default
from aiida.engine.processes.port_model import UNSPECIFIED, as_dict
from aiida.engine.processes.ports import InputPort, OutputPort, PortNamespace, infer_valid_type_from_type_annotation
from aiida.orm import Data, to_aiida_type


def at(container: t.Any, path: str) -> t.Any:
    """Return what sits at a path in something nested, which may name an output inside a namespace.

    :param path: name of a port, or names separated by dots for one inside a nested namespace.
    """
    if not path:
        return container
    value = container

    for name in path.split('.'):
        value = value[name]

    return value


def shape_from_port(port: InputPort | OutputPort | PortNamespace, *, defaults: bool = True) -> Shape:
    """Adapt executor ports to the graph's native declaration vocabulary."""
    options: dict[str, t.Any] = {'required': port.required, 'help': port.help}
    if defaults and isinstance(port, (InputPort, PortNamespace)) and port.has_default():
        default = port.default
        if isinstance(default, partial) and default.func in (to_aiida_type, _default):
            default = default.args[0]
        options['default'] = _default(default)
    if not isinstance(port, PortNamespace):
        types = port.valid_type
        return LeafShape(types=(types,) if isinstance(types, type) else types, **options)
    extra = None
    if port.dynamic:
        extra = (
            shape_from_port(port.entry_port, defaults=defaults)
            if port.entry_port is not None
            else LeafShape(types=(port.valid_type,) if isinstance(port.valid_type, type) else port.valid_type)
        )
        if not port:
            return ManyShape(entry=extra, **options)
    return NamespaceShape(
        fields=tuple((name, shape_from_port(child, defaults=defaults)) for name, child in port.items()),
        extra=extra,
        **options,
    )


def port_for_shape(name: str, shape: Shape, *, output: bool = False) -> InputPort | OutputPort | PortNamespace:
    """Adapt a native graph contract to engine ports at the process boundary."""
    options: dict[str, t.Any] = {'required': shape.required, 'help': shape.help}
    if not output and shape.default is not UNSPECIFIED:
        default = _default(shape.default)
        options['default'] = partial(_default, default) if isinstance(shape, LeafShape) else default
    if isinstance(shape, LeafShape):
        types = shape.types
        if output and types:
            types = (
                tuple(
                    dict.fromkeys(
                        kind for declared in types for kind in infer_valid_type_from_type_annotation(declared)
                    )
                )
                or None
            )
        port = (OutputPort if output else InputPort)(name, valid_type=types, **options)
        port.valid_type = types
        return port
    extra = shape.entry if isinstance(shape, ManyShape) else shape.extra
    namespace = PortNamespace(name, dynamic=extra is not None, populate_defaults=shape.required, **options)
    if isinstance(extra, LeafShape):
        leaf = port_for_shape('entry', extra, output=output)
        namespace.valid_type = leaf.valid_type
    elif extra is not None:
        entry = port_for_shape('entry', extra, output=output)
        assert isinstance(entry, PortNamespace)
        namespace.entry_port = entry
    if isinstance(shape, NamespaceShape):
        for field, child in shape.fields:
            namespace[field] = port_for_shape(field, child, output=output)
    return namespace


def merge_ports(name: str, ports: Sequence[InputPort | PortNamespace]) -> InputPort | PortNamespace:
    """Infer a boundary accepted by every consumer, without lifting task defaults."""
    if not ports:
        return InputPort(name, valid_type=Data)
    namespaces = [isinstance(port, PortNamespace) for port in ports]
    if any(namespaces) and not all(namespaces):
        msg = f'graph input `{name}` feeds incompatible value and namespace ports.'
        raise ValueError(msg)
    helps = sorted({port.help for port in ports if port.help})
    options: dict[str, t.Any] = {'required': any(port.required for port in ports), 'help': helps[0] if helps else None}
    if not all(namespaces):
        # Each consumer is validated separately; the inferred port must not select
        # one consumer's valid types and thereby reject another's more specific type.
        return InputPort(name, valid_type=Data, **options)
    consumers = t.cast(Sequence[PortNamespace], ports)
    namespace = PortNamespace(name, dynamic=all(port.dynamic for port in consumers), **options)
    entries = [port.entry_port for port in consumers if port.entry_port is not None]
    if entries:
        if len(entries) != len(consumers):
            msg = f'graph input `{name}` feeds incompatible keyed namespace contracts.'
            raise ValueError(msg)
        entry = merge_ports('entry', entries)
        assert isinstance(entry, PortNamespace)
        namespace.entry_port = entry
    names = sorted({key for port in consumers for key in port})
    for key in names:
        children = [t.cast(InputPort | PortNamespace, port[key]) for port in consumers if key in port]
        if not all(key in port or port.dynamic for port in consumers):
            if any(child.required for child in children):
                msg = f'graph input `{name}.{key}` is required by one consumer but rejected by another.'
                raise ValueError(msg)
            continue
        namespace[key] = merge_ports(key, children)
    return namespace


def prepare_inputs(namespace: PortNamespace, given: Mapping[str, t.Any], identifier: str | None) -> dict[str, t.Any]:
    """Normalize defaults and aggregate missing fields without mutating inputs."""
    missing: list[MissingInput] = []

    def visit(port: InputPort | PortNamespace, value: t.Any, path: str) -> t.Any:
        absent_namespace = False
        missing_before = len(missing)
        if value is UNSPECIFIED:
            if port.has_default():
                default = port.default
                if isinstance(default, partial) and default.func in (to_aiida_type, _default):
                    default = default.args[0]
                value = _default(default)
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
        if unknown and not port.dynamic:
            msg = f'unexpected graph inputs under `{path}`: {sorted(unknown)}.'
            raise TypeError(msg)
        result = dict(value)
        if port.entry_port is not None:
            result = {name: visit(port.entry_port, item, f'{path}.{name}') for name, item in value.items()}
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
