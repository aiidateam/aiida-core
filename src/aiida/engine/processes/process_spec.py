###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""AiiDA-specific process specifications."""

from __future__ import annotations

import copy
import dataclasses
import typing as t
from collections.abc import Callable, Mapping

from aiida.engine.processes.exit_code import ExitCode, ExitCodesNamespace
from aiida.engine.processes.generic import spec
from aiida.engine.processes.generic.ports import UNSPECIFIED
from aiida.engine.processes.port_model import Field, PortModel, _namespace_value, _reject_optional_structured, fields_of
from aiida.engine.processes.ports import (
    CalcJobOutputPort,
    InputPort,
    PortNamespace,
    _infer_node_types,
    _infer_runtime_types,
    _is_storable,
)
from aiida.orm import Data, Dict, to_aiida_type

__all__ = ('CalcJobProcessSpec', 'GraphProcessSpec', 'ProcessSpec')


def _require_storable(field: Field) -> None:
    """Reject model fields whose values cannot reach provenance storage."""
    if _is_storable(field.annotation):
        return
    name = getattr(field.annotation, '__name__', field.annotation)
    msg = f'model field `{field.name}` with type `{name}` cannot be stored in provenance; use a storable type instead.'
    raise TypeError(msg)


def _as_a_port(field: Field) -> dict[str, t.Any]:
    """Return how one model field is declared as a port."""
    _require_storable(field)
    _reject_optional_structured(field.annotation, name=field.name)
    declared = _infer_runtime_types(field.annotation)
    valid_type = declared or (Data,)
    if field.default is None and type(None) not in valid_type:
        valid_type = (*valid_type, type(None))
    # Non-nullable fields stay required so no `None` type is added; a default still applies through the port.
    required = field.required or type(None) not in valid_type
    options: dict[str, t.Any] = {'required': required, 'help': field.help}

    if not field.required:
        options['default'] = _lazily(field.default)

    return {**options, 'valid_type': valid_type}


def _as_an_output_port(field: Field) -> dict[str, t.Any]:
    """Return how one field of a structured type is declared as an output port.

    An output holds what a process produced, so unlike an input it carries no serializer and no default: the
    value is a node by the time it is attached.
    """
    _require_storable(field)
    _reject_optional_structured(field.annotation, name=field.name)
    declared = _infer_node_types(field.annotation)

    return {'required': field.required, 'help': field.help, 'valid_type': declared or (Data,)}


def _with_defaults(fields: tuple[Field, ...], defaults: Mapping[str, t.Any] | None) -> tuple[Field, ...]:
    """Override field defaults with an enclosing instance's values."""
    if not defaults:
        return fields
    return tuple(
        dataclasses.replace(field, default=defaults[field.name]) if field.name in defaults else field
        for field in fields
    )


def _lazily(default: t.Any) -> t.Any:
    """Copy Python defaults per launch; provenance serialization happens after runtime validation."""
    if default is None or isinstance(default, Data) or callable(default):
        return default

    return lambda: copy.deepcopy(default)


def _declare_namespace(
    spec: ProcessSpec,
    name: str,
    container: type,
    *,
    leaf_options: Callable[[Field], dict[str, t.Any]],
    defaults: Mapping[str, t.Any] | None = None,
    required: bool = True,
    help: str | None = None,
    validator: Callable[[t.Any, t.Any], str | None] | None = None,
) -> None:
    """Declare a model tree with the leaf types appropriate to its process."""
    fields = fields_of(container)
    if fields is None:
        msg = f'`{getattr(container, "__name__", container)}` is not a structured type. Use a `PortModel`.'
        raise TypeError(msg)
    spec.input_namespace(name, required=required, help=help, validator=validator)
    for field in _with_defaults(fields, defaults):
        path = f'{name}{spec.namespace_separator}{field.name}'
        if fields_of(field.annotation) is not None:
            nested = _namespace_defaults(field.default)
            _declare_namespace(
                spec,
                path,
                field.annotation,
                leaf_options=leaf_options,
                defaults=nested,
                required=field.required,
                help=field.help,
            )
        else:
            spec.input(path, **leaf_options(field))


def _namespace_defaults(default: t.Any) -> Mapping[str, t.Any] | None:
    """Return nested namespace defaults, calling a default factory once at declaration."""
    if callable(default) and not isinstance(default, (PortModel, Mapping, type)):
        default = default()
    return _mapping_of(default)


def _mapping_of(default: t.Any) -> Mapping[str, t.Any] | None:
    """Return an instance default as a mapping, for a structured container."""
    if isinstance(default, PortModel):
        return default.as_dict()
    if isinstance(default, Mapping):
        return default
    mapped = _namespace_value(default)
    return mapped if isinstance(mapped, Mapping) else None


class ProcessSpec(spec.ProcessSpec):
    """Default process spec for process classes defined in `aiida-core`.

    This sub class defines custom classes for input ports and port namespaces. It also adds support for the definition
    of exit codes and retrieving them subsequently.
    """

    METADATA_KEY: str = 'metadata'
    METADATA_OPTIONS_KEY: str = 'options'
    INPUT_PORT_TYPE: type[InputPort] = InputPort
    PORT_NAMESPACE_TYPE: type[PortNamespace] = PortNamespace

    def __init__(self) -> None:
        super().__init__()
        self._exit_codes = ExitCodesNamespace()

    def input_namespace_from(
        self,
        name: str,
        container: type,
        *,
        defaults: Mapping[str, t.Any] | None = None,
        required: bool = True,
        help: str | None = None,
        validator: Callable[[t.Any, t.Any], str | None] | None = None,
    ) -> None:
        """Declare a namespace holding one port per field of a structured type.

        A ``PortModel`` declares which names a value has, of
        which types, and which of them have a default. That is what a namespace of ports says, so this is how one
        is written once and said in both places:

        >>> class Relax(PortModel):
        >>>     structure: StructureData
        >>>     steps: int = 10
        >>>
        >>> spec.input_namespace_from('relax', Relax)

        Validation then belongs to the ports, wherever the values come from, so a structured type is a way of saying
        what a namespace holds rather than a second place where types live.

        :param name: the namespace to declare the fields under.
        :param container: the structured type whose fields to declare.
        :param defaults: enclosing instance values overriding nested model defaults.
        :param required: whether the namespace itself is required.
        :param help: help text for the namespace itself.
        :param validator: validator for the namespace itself.
        :raises TypeError: if the structured type is not one this knows how to read.
        """
        _declare_namespace(
            self,
            name,
            container,
            leaf_options=_as_a_port,
            defaults=defaults,
            required=required,
            help=help,
            validator=validator,
        )

    def outputs_from(self, container: type, prefix: str = '') -> None:
        """Declare one output port per field of a structured type.

        The counterpart of :meth:`input_namespace_from`, and it goes as deep: a field that is itself a structured
        type is the namespace its own fields name, so a task producing one and a task taking one declare the same
        shape and a graph can wire the two onto each other.

        >>> class Relaxed(PortModel):
        >>>     structure: StructureData
        >>>     energy: float
        >>>
        >>> spec.outputs_from(Relaxed)

        :param container: the structured type whose fields to declare.
        :param prefix: the namespace to declare them under, empty for the top level.
        :raises TypeError: if the structured type is not one this knows how to read.
        """
        fields = fields_of(container)

        if fields is None:
            msg = (
                f'`{getattr(container, "__name__", container)}` is not a structured type, so there is nothing '
                f'to declare the outputs from. Use a `PortModel`.'
            )
            raise TypeError(msg)

        for field in fields:
            name = f'{prefix}{field.name}'

            if fields_of(field.annotation) is not None:
                self.output_namespace(name, required=field.required, help=field.help)
                self.outputs_from(field.annotation, prefix=f'{name}{self.namespace_separator}')
                continue

            self.output(name, **_as_an_output_port(field))

    @property
    def metadata_key(self) -> str:
        return self.METADATA_KEY

    @property
    def options_key(self) -> str:
        return self.METADATA_OPTIONS_KEY

    @property
    def exit_codes(self) -> ExitCodesNamespace:
        """Return the namespace of exit codes defined for this ProcessSpec

        :returns: ExitCodesNamespace of ExitCode named tuples
        """
        return self._exit_codes

    def exit_code(self, status: int, label: str, message: str, invalidates_cache: bool = False) -> None:
        """Add an exit code to the ProcessSpec

        :param status: the exit status integer
        :param label: a label by which the exit code can be addressed
        :param message: a more detailed description of the exit code
        :param invalidates_cache: when set to `True`, a process exiting
            with this exit code will not be considered for caching
        """
        if not isinstance(status, int):
            msg = f'status should be of integer type and not of {type(status)}'  # type: ignore[unreachable]
            raise TypeError(msg)

        if status < 0:
            msg = f'status should be a positive integer, received {type(status)}'
            raise ValueError(msg)

        if not isinstance(label, str):
            msg = f'label should be of str type and not of {type(label)}'  # type: ignore[unreachable]
            raise TypeError(msg)

        if not isinstance(message, str):
            msg = f'message should be of str type and not of {type(message)}'  # type: ignore[unreachable]
            raise TypeError(msg)

        if not isinstance(invalidates_cache, bool):
            msg = f'invalidates_cache should be of type bool and not of {type(invalidates_cache)}'  # type: ignore[unreachable]
            raise TypeError(msg)

        self._exit_codes[label] = ExitCode(status, message, invalidates_cache=invalidates_cache)

    # override return type to aiida's PortNamespace subclass

    @property
    def ports(self) -> PortNamespace:
        return super().ports  # type: ignore[return-value]

    @property
    def inputs(self) -> PortNamespace:
        return super().inputs  # type: ignore[return-value]

    @property
    def outputs(self) -> PortNamespace:
        return super().outputs  # type: ignore[return-value]


class GraphProcessSpec(ProcessSpec):
    """Process specification for graph and task processes with runtime-typed inputs."""

    def input_from_field(self, name: str, field: Field) -> None:
        """Declare a runtime-typed input port or structured namespace from a field.

        :param name: the input port or namespace name, dotted for nested fields.
        :param field: the extracted annotation, default and help for the input.
        """
        valid_type = _infer_runtime_types(field.annotation) or (Data,)

        if self.has_input(name):
            port = self.inputs[name]
            if not isinstance(port, InputPort):
                msg = f'cannot override namespace input `{name}` with a field default; declare it once instead.'
                raise TypeError(msg)
            if field.default is None:
                current = port.valid_type
                if current is not None:
                    kinds = current if isinstance(current, tuple) else (current,)
                    if type(None) not in kinds:
                        port.valid_type = tuple(kinds) + (type(None),)
            port.default = _lazily(field.default) if field.default is not UNSPECIFIED else UNSPECIFIED
            return

        if field.default is None and type(None) not in valid_type:
            valid_type += (type(None),)

        if fields_of(field.annotation) is not None:
            defaults = _namespace_defaults(field.default)
            self.input_namespace_from(
                name,
                field.annotation,
                defaults=defaults,
                required=field.required,
                help=field.help,
            )
            return
        _reject_optional_structured(field.annotation, name=name)
        self.input(
            name,
            valid_type=valid_type,
            default=_lazily(field.default) if field.default is not UNSPECIFIED else UNSPECIFIED,
            serializer=to_aiida_type,
            help=field.help,
        )


class CalcJobProcessSpec(ProcessSpec):
    """Process spec intended for the `CalcJob` process class."""

    OUTPUT_PORT_TYPE: type[CalcJobOutputPort] = CalcJobOutputPort

    def __init__(self) -> None:
        super().__init__()
        self._default_output_node: str | None = None

    @property
    def default_output_node(self) -> str | None:
        return self._default_output_node

    @default_output_node.setter
    def default_output_node(self, port_name: str) -> None:
        if port_name not in self.outputs:
            msg = f'{port_name} is not a registered output port'
            raise ValueError(msg)

        valid_type_port = self.outputs[port_name].valid_type
        valid_type_required = Dict

        if valid_type_port is not valid_type_required:
            msg = f'the valid type of a default output has to be a {valid_type_required} but it is {valid_type_port}'
            raise ValueError(msg)

        self._default_output_node = port_name
