from typing import Any


class SerializationAdapter:
    id: str = "null"
    name: str = "null"

    def validate(self, value: Any, socket: Any, *, mode: str = "assign") -> Any:
        return value

    def serialize(self, value: Any, socket: Any, *, store: bool) -> Any:
        return value

    def deserialize(self, value: Any, socket: Any) -> Any:
        return value

    def serialize_ports(
        self, python_data: Any, port_schema: Any, *, store: bool
    ) -> Any:
        return python_data


class NullSerializationAdapter(SerializationAdapter):
    id: str = "null"
    name: str = "null"
