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

from aiida.engine.processes.exit_code import ExitCode, ExitCodesNamespace
from aiida.engine.processes.generic import spec
from aiida.engine.processes.generic.ports import UNSPECIFIED
from aiida.engine.processes.port_model import Field, fields_of
from aiida.engine.processes.ports import (
    CalcJobOutputPort,
    InputPort,
    PortNamespace,
    infer_node_types,
    infer_runtime_types,
    is_storable,
)
from aiida.orm import Data, Dict, to_aiida_type

__all__ = ('CalcJobProcessSpec', 'GraphProcessSpec', 'ProcessSpec')


def _require_storable(field: Field) -> None:
    """Reject model fields whose values cannot reach provenance storage."""
    if is_storable(field.annotation):
        return
    name = getattr(field.annotation, '__name__', field.annotation)
    msg = f'model field `{field.name}` with type `{name}` cannot be stored in provenance.'
    raise TypeError(msg)


def _as_a_port(field: Field) -> dict[str, t.Any]:
    """Return how one model field is declared as a port."""
    _require_storable(field)
    declared = infer_runtime_types(field.annotation)
    # Non-nullable fields stay required so no `None` type is added; a default still applies through the port.
    required = field.required or type(None) not in declared
    options: dict[str, t.Any] = {'required': required, 'help': field.help}

    if not field.required:
        options['default'] = _lazily(field.default)

    return {**options, 'valid_type': declared or (Data,)}


def _as_an_output_port(field: Field) -> dict[str, t.Any]:
    """Return how one field of a structured type is declared as an output port.

    An output holds what a process produced, so unlike an input it carries no serializer and no default: the
    value is a node by the time it is attached.
    """
    _require_storable(field)
    declared = infer_node_types(field.annotation)

    return {'required': field.required, 'help': field.help, 'valid_type': declared or (Data,)}


def _with_defaults(fields: tuple[Field, ...], defaults: t.Mapping[str, t.Any] | None) -> tuple[Field, ...]:
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


class ProcessSpec(spec.ProcessSpec):
    """Default process spec for process classes defined in `aiida-core`.

    This sub class defines custom classes for input ports and port namespaces. It also adds support for the definition
    of exit codes and retrieving them subsequently.
    """

    METADATA_KEY: str = 'metadata'
    METADATA_OPTIONS_KEY: str = 'options'
    INPUT_PORT_TYPE = InputPort
    PORT_NAMESPACE_TYPE = PortNamespace

    def __init__(self) -> None:
        super().__init__()
        self._exit_codes = ExitCodesNamespace()
        self._structured_outputs = False

    @property
    def result_port(self) -> str:
        """Return the port representing a call result, or the root for a namespace result."""
        if self._structured_outputs or len(self.outputs) != 1:
            return ''
        return next(iter(self.outputs))

    def input_namespace_from(
        self,
        name: str,
        container: type,
        *,
        defaults: t.Mapping[str, t.Any] | None = None,
        **kwargs: t.Any,
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
        :param defaults: default values for nested model fields, keyed by field name.
        :param kwargs: passed on to the namespace itself, ``required`` and ``help`` among them.
        :raises TypeError: if the structured type is not one this knows how to read.
        """
        fields = fields_of(container)

        if fields is None:
            msg = (
                f'`{getattr(container, "__name__", container)}` is not a structured type, so there is nothing '
                f'to declare `{name}` from. Use a `PortModel`.'
            )
            raise TypeError(msg)

        self.input_namespace(name, **kwargs)

        for field in _with_defaults(fields, defaults):
            self._declare_field(f'{name}{self.namespace_separator}{field.name}', field)

    def _declare_field(self, name: str, field: Field) -> None:
        """Declare one model field as a port or a nested namespace."""
        if fields_of(field.annotation) is not None:
            nested = field.default.as_dict() if isinstance(field.default, field.annotation) else field.default
            self.input_namespace_from(
                name,
                field.annotation,
                required=field.required,
                help=field.help,
                defaults=nested if isinstance(nested, dict) else None,
            )
            return
        self.input(name, **_as_a_port(field))

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

        if not prefix:
            self._structured_outputs = True

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
    """Process spec for graph tasks and graph processes, declaring runtime-typed inputs.

    The ``Field``-based declaration path lives here so plain processes never see it:
    annotations convert to plain Python runtime types, with provenance serialization
    happening after runtime validation.
    """

    def input_from_field(self, name: str, field: Field) -> None:
        """Convert one extracted :class:`Field` to an input port or namespace.

        Structured annotations become a namespace via :meth:`input_namespace_from`; all other
        annotations become a leaf :class:`InputPort`.

        :param name: the port or namespace to declare (dotted for nested fields).
        :param field: the extracted field carrying the stripped annotation, default and help.
        """
        valid_type = infer_runtime_types(field.annotation) or (Data,)

        if self.has_input(name):
            port = self.inputs[name]
            assert isinstance(port, InputPort)
            port.default = field.default
            return

        if field.default is None and type(None) not in valid_type:
            valid_type += (type(None),)

        if fields_of(field.annotation) is not None:
            self.input_namespace_from(
                name,
                field.annotation,
                required=field.required,
                help=field.help,
            )
            return

        self.input(
            name,
            valid_type=valid_type,
            default=_lazily(field.default) if field.default is not UNSPECIFIED else UNSPECIFIED,
            serializer=to_aiida_type,
            help=field.help,
        )


class CalcJobProcessSpec(ProcessSpec):
    """Process spec intended for the `CalcJob` process class."""

    OUTPUT_PORT_TYPE = CalcJobOutputPort

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
