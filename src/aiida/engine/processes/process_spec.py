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

import typing as t
from collections.abc import Mapping

from aiida.engine.processes.containers import UNSPECIFIED, Field, build, fields_of, is_a_container
from aiida.engine.processes.exit_code import ExitCode, ExitCodesNamespace
from aiida.engine.processes.generic import spec
from aiida.engine.processes.ports import (
    CalcJobOutputPort,
    InputPort,
    PortNamespace,
    infer_valid_type_from_type_annotation,
    serializer_for,
)
from aiida.orm import Data, Dict, JsonableData, to_aiida_type

__all__ = ('CalcJobProcessSpec', 'ProcessSpec')


def _as_a_port(field: Field) -> dict[str, t.Any]:
    """Return how one field of a container is declared as a port.

    A field kept whole is one node holding the object, which is what :class:`~aiida.orm.JsonableData` is for,
    unless what it holds is a node already.
    """
    declared = infer_valid_type_from_type_annotation(field.annotation)
    options: dict[str, t.Any] = {'required': field.required}

    if not field.required:
        options['default'] = _lazily(field.default)

    if field.whole and not declared:
        return {**options, 'valid_type': (JsonableData,), 'serializer': _as_one_node(field)}

    return {**options, 'valid_type': declared or (Data,), 'serializer': serializer_for(field.annotation)}


def _as_one_node(field: Field) -> t.Callable[[t.Any], JsonableData]:
    """Return what stores a field kept whole, which is one node holding the whole of it."""

    def store(value: t.Any) -> JsonableData:
        # A namespace takes the fields written as a mapping, so a port holding the whole container takes one
        # too, and the container is what says whether those fields are acceptable.
        if isinstance(value, Mapping) and is_a_container(field.annotation):
            value = build(field.annotation, dict(value))

        try:
            return JsonableData(value)
        except Exception as exception:
            msg = (
                f'`{field.name}` is kept whole, so it is stored as one node holding it as JSON, and '
                f'`{type(value).__name__}` holds something that cannot be written that way. Either say how that '
                f'value is rendered, or drop the mark so that each field is stored as the node it is.'
            )
            raise ValueError(msg) from exception

    return store


def _lazily(default: t.Any) -> t.Any:
    """Return the default as a port takes it, which for a value to be stored is something that makes it.

    A port default is called where one is needed, so that a node is made at that moment rather than when the
    class was defined, which is too early for anything to be stored.
    """
    if default is None or isinstance(default, Data) or callable(default):
        return default

    return lambda: to_aiida_type(default)


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

    def input_whole(self, name: str, container: type, default: t.Any = UNSPECIFIED, **kwargs: t.Any) -> None:
        """Declare one port holding the whole of a structured container.

        This is what :class:`~aiida.engine.processes.containers.Whole` asks for: the container is stored as one
        node holding it as JSON, so nothing wires into a field of it and the provenance carries one value:

        >>> spec.input_whole('config', SomeConfig)

        :param name: the port to declare.
        :param container: the structured container the port holds.
        :param default: what the port holds when nothing is given, or ``UNSPECIFIED`` to make it required.
        :param kwargs: passed on to the port, ``help`` among them.
        """
        field = Field(name=name, annotation=container, default=default, whole=True)
        self.input(name, **{**_as_a_port(field), **kwargs})

    def input_namespace_from(self, name: str, container: type, **kwargs: t.Any) -> None:
        """Declare a namespace holding one port per field of a structured container.

        A ``TypedDict``, a dataclass, a ``NamedTuple`` and a pydantic model each say which names a value has, of
        which types, and which of them have a default. That is what a namespace of ports says, so this is how one
        is written once and said in both places:

        >>> class Relax(BaseModel):
        >>>     structure: StructureData
        >>>     steps: int = 10
        >>>
        >>> spec.input_namespace_from('relax', Relax)

        Validation then belongs to the ports, wherever the values come from, so a container is a way of saying
        what a namespace holds rather than a second place where types live.

        :param name: the namespace to declare the fields under.
        :param container: the structured container whose fields to declare.
        :param kwargs: passed on to the namespace itself, ``required`` and ``help`` among them.
        :raises TypeError: if the container is not one this knows how to read.
        """
        fields = fields_of(container)

        if fields is None:
            raise TypeError(
                f'`{getattr(container, "__name__", container)}` is not a structured container, so there is nothing '
                f'to declare `{name}` from. Use a `TypedDict`, a dataclass, a `NamedTuple` or a pydantic model.'
            )

        self.input_namespace(name, **kwargs)

        for field in fields:
            under = f'{name}{self.namespace_separator}{field.name}'

            if fields_of(field.annotation) is not None and not field.whole:
                self.input_namespace_from(under, field.annotation, required=field.required)
                continue

            self.input(
                under,
                **_as_a_port(field),
            )

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
            raise TypeError(f'status should be of integer type and not of {type(status)}')

        if status < 0:
            raise ValueError(f'status should be a positive integer, received {type(status)}')

        if not isinstance(label, str):
            raise TypeError(f'label should be of str type and not of {type(label)}')

        if not isinstance(message, str):
            raise TypeError(f'message should be of str type and not of {type(message)}')

        if not isinstance(invalidates_cache, bool):
            raise TypeError(f'invalidates_cache should be of type bool and not of {type(invalidates_cache)}')

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
            raise ValueError(f'{port_name} is not a registered output port')

        valid_type_port = self.outputs[port_name].valid_type
        valid_type_required = Dict

        if valid_type_port is not valid_type_required:
            raise ValueError(
                f'the valid type of a default output has to be a {valid_type_required} but it is {valid_type_port}'
            )

        self._default_output_node = port_name
