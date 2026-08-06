from __future__ import annotations

from dataclasses import replace
from typing import Any

from node_graph.socket_spec import (
    Leaf,
    SocketMeta,
    SocketSpec,
    SocketSpecSelect,
    meta,
    select,
)
from node_graph.socket_spec import (
    SocketSpecAPI as _SocketSpecAPI,
)
from plumpy.ports import Port, PortNamespace

from aiida.engine import Process
from aiida.engine.processes.process_spec import ProcessSpec
from aiida.workgraph.registry import type_mapping

from .socket import TaskSocketNamespace

__all__ = [
    'Leaf',
    'SocketSpecAPI',
    'SocketSpecSelect',
    'dynamic',
    'from_aiida_process',
    'infer_specs_from_callable',
    'meta',
    'namespace',
    'select',
    'socket',
    'validate_socket_data',
]


class SocketSpecAPI(_SocketSpecAPI):
    MAP: dict[Any, str] = type_mapping
    NAMESPACE: str = 'workgraph.namespace'
    DEFAULT: str = 'workgraph.any'
    ANNOTATED: str = 'workgraph.annotated'

    SocketNamespace = TaskSocketNamespace

    @classmethod
    def _identifier_from_valid_type(cls, valid_type: Any) -> str:
        """Map AiiDA Port.valid_type -> identifier with our mapping.
        - tuple of types: if len==1 map that; else -> any/default
        - None/empty: any/default
        - single type: mapped identifier
        """
        if isinstance(valid_type, tuple):
            if len(valid_type) == 1:
                return cls._map_identifier(valid_type[0])
            return cls.DEFAULT
        if valid_type in (None, Ellipsis):
            return cls.DEFAULT
        return cls._map_identifier(valid_type)

    @classmethod
    def _from_port(cls, port: Port | PortNamespace, *, parent_required: bool, role: str) -> SocketSpec:
        """Recursively convert an AiiDA Port/PortNamespace to a SocketSpec.
        `role` is "input" or "output" (affects call_role metadata).
        """
        if isinstance(port, PortNamespace):
            required_here = bool(getattr(port, 'required', True)) and bool(parent_required)

            # Build child fields by iterating explicit .ports mapping
            fields: dict[str, SocketSpec] = {}
            for name, child in port.ports.items():
                fields[name] = cls._from_port(child, parent_required=required_here, role=role)

            ns = SocketSpec(
                identifier=cls.NAMESPACE,
                fields=fields,
                meta=SocketMeta(
                    required=required_here,
                    is_metadata=getattr(port, 'is_metadata', False),
                    call_role=('kwargs' if role == 'input' else None),
                ),
            )

            # Dynamic namespace? (DynamicPortNamespace derives from PortNamespace)
            is_dyn = bool(getattr(port, 'dynamic', False))
            if is_dyn:
                valid_type = getattr(port, 'valid_type', None)
                if valid_type:
                    item_ident = cls._identifier_from_valid_type(valid_type)
                    ns = replace(ns, meta=replace(ns.meta, dynamic=True), item=SocketSpec(identifier=item_ident))
                else:
                    ns = replace(ns, meta=replace(ns.meta, dynamic=True), item=None)
            return ns

        # Leaf Port (InputPort/OutputPort)
        required_here = bool(getattr(port, 'required', True)) and bool(parent_required)
        valid_type = getattr(port, 'valid_type', None)
        ident = cls._identifier_from_valid_type(valid_type)
        return SocketSpec(
            identifier=ident,
            meta=SocketMeta(
                required=required_here,
                is_metadata=getattr(port, 'is_metadata', False),
                call_role=('kwargs' if role == 'input' else None),
            ),
        )

    @classmethod
    def from_aiida_process(
        cls, process_or_spec: type[Process] | Process | ProcessSpec
    ) -> tuple[SocketSpec, SocketSpec]:
        """Return (inputs_spec, outputs_spec) for an AiiDA Process or its ProcessSpec.

        Accepts:
          - AiiDA Process subclass (e.g. CalcJob, WorkChain)
          - AiiDA Process instance
          - ProcessSpec object (as returned by `.spec()`)
        """
        # Normalize to a ProcessSpec
        if isinstance(process_or_spec, ProcessSpec):
            spec = process_or_spec
        elif isinstance(process_or_spec, type) and issubclass(process_or_spec, Process):
            spec = process_or_spec.spec()
        elif isinstance(process_or_spec, Process):
            spec = process_or_spec.spec()
        else:
            raise TypeError(
                'from_aiida_process expects an AiiDA Process class/instance or a ProcessSpec; '
                f'got {type(process_or_spec)!r}'
            )

        # Validate spec structure
        if not isinstance(spec, ProcessSpec):
            raise TypeError(f'.spec() did not return a ProcessSpec; got {type(spec)!r}')

        inputs_ns = getattr(spec, 'inputs', None)
        outputs_ns = getattr(spec, 'outputs', None)
        if not isinstance(inputs_ns, PortNamespace) or not isinstance(outputs_ns, PortNamespace):
            raise TypeError('Spec does not expose PortNamespace for inputs/outputs')

        in_spec = cls._from_port(inputs_ns, parent_required=True, role='input')
        out_spec = cls._from_port(outputs_ns, parent_required=True, role='output')
        # tag top-level outputs with 'return'
        out_spec = replace(out_spec, meta=replace(out_spec.meta, call_role='return'))
        return in_spec, out_spec


socket = SocketSpecAPI.socket
namespace = SocketSpecAPI.namespace
dynamic = SocketSpecAPI.dynamic
validate_socket_data = SocketSpecAPI.validate_socket_data
infer_specs_from_callable = SocketSpecAPI.infer_specs_from_callable
from_aiida_process = SocketSpecAPI.from_aiida_process
