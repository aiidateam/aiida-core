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

import inspect
import math
import typing as t
from collections.abc import Callable, Mapping, Sequence
from functools import partial

from aiida.common.exceptions import MissingInput, MissingRequiredInputsError
from aiida.common.loaders import get_object_loader
from aiida.engine.processes.port_model import (
    UNSPECIFIED,
    _port_help,
    as_dict,
    fields_of,
    without_marks,
)
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


def _default(value: t.Any) -> t.Any:
    """Copy finite JSON defaults, never node identities or executable defaults."""
    held = as_dict(value)
    if held is not None:
        value = held
    if value is None or isinstance(value, (bool, int, str)):
        return value
    if isinstance(value, float) and math.isfinite(value):
        return value
    if isinstance(value, list):
        return [_default(item) for item in value]
    if isinstance(value, Mapping) and all(isinstance(key, str) for key in value):
        return {key: _default(item) for key, item in value.items()}
    msg = f'graph default of type `{type(value).__name__}` is not a finite JSON value.'
    raise TypeError(msg)


def _annotation_port(
    name: str, annotation: t.Any, *, required: bool, default: t.Any = UNSPECIFIED
) -> InputPort | PortNamespace:
    container = without_marks(annotation)
    from aiida.engine.processes.many import _takes_many

    if _takes_many(container):
        from aiida.engine.processes.process_spec import ProcessSpec

        spec = ProcessSpec()
        spec.input_many(name, container, required=required, help=_port_help(annotation))
        namespace = spec.inputs[name]
        assert isinstance(namespace, PortNamespace)
        return namespace
    fields = fields_of(container)
    options: dict[str, t.Any] = {'required': required, 'help': _port_help(annotation)}
    if default is not UNSPECIFIED:
        options['default'] = _default(default)
    if fields is None:
        if 'default' in options:
            options['default'] = partial(_default, options['default'])
        valid_type = infer_valid_type_from_type_annotation(annotation, stored=False) or None
        port = InputPort(name, valid_type=valid_type, **options)
        # Ordinary optional process ports also accept None. A graph declaration
        # distinguishes a defaulted key from a nullable value.
        if default is not None:
            port.valid_type = valid_type
        return port
    namespace = PortNamespace(name, populate_defaults=required, **options)
    for field in fields:
        child_annotation = field.annotation
        child = _annotation_port(field.name, child_annotation, required=field.required, default=field.default)
        child.help = field.help
        namespace[field.name] = child
    return namespace


def namespace_for_annotations(hints: Mapping[str, t.Any], names: Sequence[str]) -> PortNamespace:
    """Construct a source graph boundary, whose parameters are all required."""
    namespace = PortNamespace('inputs')
    for name in names:
        namespace[name] = _annotation_port(name, hints.get(name), required=True)
    return namespace


def namespace_for_function(function: Callable[..., t.Any]) -> PortNamespace:
    """Construct a thin namespace from named function parameters and resolved annotations."""
    hints = t.get_type_hints(function, include_extras=True)
    namespace = PortNamespace('inputs')
    for name, parameter in inspect.signature(function).parameters.items():
        if parameter.kind not in (parameter.POSITIONAL_OR_KEYWORD, parameter.KEYWORD_ONLY):
            continue
        default = UNSPECIFIED if parameter.default is parameter.empty else parameter.default
        try:
            namespace[name] = _annotation_port(name, hints.get(name), required=default is UNSPECIFIED, default=default)
        except TypeError as exception:
            msg = f'cannot declare graph input `{name}`: {exception}'
            raise TypeError(msg) from exception
    return namespace


def namespace_for_outputs(annotation: t.Any) -> PortNamespace | None:
    """Declare structured graph returns with the ordinary process output machinery."""
    from aiida.engine.processes.process_spec import ProcessSpec

    if fields_of(annotation) is None:
        return None
    spec = ProcessSpec()
    spec.outputs_from(annotation)
    return spec.outputs


def dump_port(port: InputPort | OutputPort | PortNamespace, *, defaults: bool = True) -> dict[str, t.Any]:
    """Snapshot declarative port properties, not live serializers or validators.

    Task-specific conversion and custom validation remain on the executor's ports.
    """
    result: dict[str, t.Any] = {'name': port.name, 'required': port.required, 'help': port.help}
    if isinstance(port, PortNamespace):
        result.update(
            dynamic=port.dynamic, ports={name: dump_port(child, defaults=defaults) for name, child in port.items()}
        )
        if port.entry_port is not None:
            result['entry_port'] = dump_port(port.entry_port, defaults=defaults)
    if not isinstance(port, PortNamespace) or port.valid_type:
        valid_types = port.valid_type or ()
        if isinstance(valid_types, type):
            valid_types = (valid_types,)
        result['valid_type'] = [
            None if kind is type(None) else get_object_loader().identify_object(kind)
            for kind in dict.fromkeys(valid_types)
        ]
    if defaults and isinstance(port, (InputPort, PortNamespace)) and port.has_default():
        value = port.default
        if isinstance(value, partial) and value.func in (to_aiida_type, _default):
            value = value.args[0]
        result['default'] = _default(value)
    return result


def load_port(data: Mapping[str, t.Any], *, output: bool = False) -> InputPort | OutputPort | PortNamespace:
    """Reconstruct ordinary AiiDA ports from their declaration snapshot."""
    options = {'required': data['required'], 'help': data.get('help')}
    if not isinstance(options['required'], bool) or (
        options['help'] is not None and not isinstance(options['help'], str)
    ):
        msg = 'port declarations require boolean requiredness and string help.'
        raise TypeError(msg)
    if 'default' in data:
        options['default'] = _default(data['default'])
    if 'ports' not in data:
        if 'default' in options:
            options['default'] = partial(_default, options['default'])
        port_class = OutputPort if output else InputPort
        valid_type = (
            tuple(type(None) if kind is None else get_object_loader().load_object(kind) for kind in data['valid_type'])
            or None
        )
        port = port_class(data['name'], valid_type=valid_type, **options)
        # Restore exactly the snapshot, without optional InputPort's implicit None.
        port.valid_type = valid_type
        return port
    valid_type = (
        tuple(
            type(None) if kind is None else get_object_loader().load_object(kind) for kind in data.get('valid_type', ())
        )
        or None
    )
    namespace = PortNamespace(
        data['name'], dynamic=data['dynamic'], valid_type=valid_type, populate_defaults=data['required'], **options
    )
    if 'entry_port' in data:
        entry = load_port(data['entry_port'], output=output)
        assert isinstance(entry, PortNamespace)
        namespace.entry_port = entry
    for name, child in data['ports'].items():
        namespace[name] = load_port(child, output=output)
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
