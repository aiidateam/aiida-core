from aiida.node_graph.socket import TaskSocket


class SocketAny(TaskSocket):
    """Socket that accepts any type of data."""

    _identifier: str = "node_graph.any"
    _socket_property_identifier: str = "node_graph.any"


class SocketAnnotated(TaskSocket):
    """Socket for annotated Python types stored in metadata."""

    _identifier: str = "node_graph.annotated"
    _socket_property_identifier: str = "node_graph.any"


class SocketNamespace(TaskSocket):
    """Socket that holds a namespace."""

    _identifier: str = "node_graph.namespace"
    _socket_property_identifier: str = "node_graph.any"


class SocketFloat(TaskSocket):
    """Socket for float data."""

    _identifier: str = "node_graph.float"
    _socket_property_identifier: str = "node_graph.float"


class SocketInt(TaskSocket):
    """Socket for integer data."""

    _identifier: str = "node_graph.int"
    _socket_property_identifier: str = "node_graph.int"


class SocketString(TaskSocket):
    """Socket for string data."""

    _identifier: str = "node_graph.string"
    _socket_property_identifier: str = "node_graph.string"


class SocketBool(TaskSocket):
    """Socket for boolean data."""

    _identifier: str = "node_graph.bool"
    _socket_property_identifier: str = "node_graph.bool"


class SocketBaseList(TaskSocket):
    """Socket with a BaseList property."""

    _identifier: str = "node_graph.base_list"
    _socket_property_identifier: str = "node_graph.base_list"


class SocketBaseDict(TaskSocket):
    """Socket with a BaseDict property."""

    _identifier: str = "node_graph.base_dict"
    _socket_property_identifier: str = "node_graph.base_dict"


class SocketIntVector(TaskSocket):
    """Socket for integer vector data."""

    _identifier: str = "node_graph.int_vector"
    _socket_property_identifier: str = "node_graph.int_vector"


class SocketFloatVector(TaskSocket):
    """Socket for float vector data."""

    _identifier: str = "node_graph.float_vector"
    _socket_property_identifier: str = "node_graph.float_vector"
