from aiida.workgraph.socket import TaskSocket


class SocketAny(TaskSocket):
    """Any socket."""

    _identifier: str = 'workgraph.any'
    _socket_property_identifier: str = 'workgraph.any'


class SocketAnnotated(TaskSocket):
    """Socket for annotated Python types stored in metadata."""

    _identifier: str = 'workgraph.annotated'
    _socket_property_identifier: str = 'workgraph.any'


class SocketFloat(TaskSocket):
    """Float socket."""

    _identifier: str = 'workgraph.float'
    _socket_property_identifier: str = 'workgraph.float'


class SocketInt(TaskSocket):
    """Int socket."""

    _identifier: str = 'workgraph.int'
    _socket_property_identifier: str = 'workgraph.int'


class SocketString(TaskSocket):
    """String socket."""

    _identifier: str = 'workgraph.string'
    _socket_property_identifier: str = 'workgraph.string'


class SocketBool(TaskSocket):
    """Bool socket."""

    _identifier: str = 'workgraph.bool'
    _socket_property_identifier: str = 'workgraph.bool'


class SocketList(TaskSocket):
    """List socket."""

    _identifier: str = 'workgraph.list'
    _socket_property_identifier: str = 'workgraph.list'


class SocketDict(TaskSocket):
    """Dict socket."""

    _identifier: str = 'workgraph.dict'
    _socket_property_identifier: str = 'workgraph.dict'


class SocketAiiDAIntVector(TaskSocket):
    """Socket with a AiiDAIntVector property."""

    _identifier: str = 'workgraph.aiida_int_vector'
    _socket_property_identifier: str = 'workgraph.aiida_int_vector'


class SocketAiiDAFloatVector(TaskSocket):
    """Socket with a FloatVector property."""

    _identifier: str = 'workgraph.aiida_float_vector'
    _socket_property_identifier: str = 'workgraph.aiida_float_vector'


class SocketStructureData(TaskSocket):
    """Any socket."""

    _identifier: str = 'workgraph.aiida_structuredata'
    _socket_property_identifier: str = 'workgraph.aiida_structuredata'
