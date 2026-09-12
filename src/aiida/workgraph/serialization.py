from __future__ import annotations

from typing import Any, Dict, Optional

from aiida.pythonjob.data.serializer import all_serializers
from aiida.pythonjob.utils import serialize_ports
from aiida.node_graph.serializer import SerializationAdapter
from aiida.node_graph.utils import resolve_tagged_values


class AiidaSerializationAdapter(SerializationAdapter):
    id: str = 'aiida'
    name: str = 'AiiDA'

    def __init__(self, serializers: Optional[Dict[str, str]] = None, user: Any = None) -> None:
        self.serializers = serializers or all_serializers
        self.user = user

    def serialize(self, value: Any, socket: Any, *, store: bool) -> Any:
        if socket is None:
            return value
        spec = socket._to_spec()
        resolve_tagged_values(value)
        return serialize_ports(
            python_data=value,
            port_schema=spec,
            serializers=self.serializers,
            user=self.user,
        )

    def serialize_ports(self, python_data: Any, port_schema: Any, *, store: bool) -> Any:
        resolve_tagged_values(python_data)
        return serialize_ports(
            python_data=python_data,
            port_schema=port_schema,
            serializers=self.serializers,
            user=self.user,
        )
