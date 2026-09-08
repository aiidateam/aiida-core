from __future__ import annotations
from uuid import uuid4
from aiida.node_graph.collection import DependencyCollection
from aiida.node_graph.property import TaskProperty
from typing import Any, Dict, List, Optional, TYPE_CHECKING, Union
from aiida.node_graph.collection import get_item_class
from dataclasses import MISSING, replace
from aiida.node_graph.orm.mapping import type_mapping
from aiida.node_graph.socket_meta import SocketMeta, UPDATABLE_SOCKET_META_FIELDS
from aiida.node_graph.registry import EntryPointPool
from aiida.node_graph.utils.struct_utils import is_structured_instance, structured_to_dict
from aiida.node_graph.utils import resolve_tagged_values
import wrapt

if TYPE_CHECKING:
    from aiida.node_graph.task import Task
    from aiida.node_graph.link import TaskLink
    from aiida.node_graph.graph import Graph


def has_socket(data: dict):
    """Check if the data contains a socket."""
    for value in data.values():
        if isinstance(value, BaseSocket):
            return True
        elif isinstance(value, dict):
            return has_socket(value)

    return False


def op_add(x, y):
    return x + y


def op_sub(x, y):
    return x - y


def op_mul(x, y):
    return x * y


def op_truediv(x, y):
    return x / y


def op_pow(x, y):
    return x**y


def op_mod(x, y):
    return x % y


def op_floordiv(x, y):
    return x // y


# comparison operations
def op_lt(x, y):
    return x < y


def op_gt(x, y):
    return x > y


def op_le(x, y):
    return x <= y


def op_ge(x, y):
    return x >= y


def op_eq(x, y):
    return x == y


def op_ne(x, y):
    return x != y


def _raise_illegal(sock, what: str, tips: list[str]):
    from .errors import GraphDeferredIllegalOperationError

    task = getattr(sock, "_task", None)
    task_name = getattr(task, "name", None) or "<unknown-task>"
    socket_name = (
        getattr(sock, "_name", None) or getattr(sock, "name", None) or "<socket>"
    )

    common = [
        "General guidance:",
        "  • Wrap logic in a nested @task.graph.",
        "  • Or use the Graph If zone for branching on predicates.",
        "  • Or for loops, use the While zone or Map zone.",
    ]

    msg = (
        f"Illegal operation on a future value (Socket): {what}\n"
        f"Socket: {socket_name} of task '{task_name}'"
    )
    msg += "\n\nFix:\n" + "\n".join(tips + [""] + common)
    raise GraphDeferredIllegalOperationError(msg)


def _tip_cast(kind):  # numeric/bytes/path-like casts
    return [
        f"Avoid {kind} on futures. Compute the value inside the graph, then cast afterwards.",
        "If you need a cast during execution, use a dedicated cast task.",
    ]


def _tip_iter():  # iteration/len/container-ish
    return [
        "You tried to iterate or take len()/index a future.",
        "Use @task.graph to build logic that needs to iterate over values.",
    ]


def _tip_bool():
    return [
        "You used a future in a boolean context (if/while/assert/and/or).",
        "Wrap logic in a nested @task.graph.",
    ]


def _tip_numpy():
    return [
        "NumPy tried to coerce or operate on a future.",
        "Use built-in operator sockets (+, -, *, <, …) to build predicates/expressions,",
        "or use a dedicated numpy/ufunc task.",
    ]


def _tip_ctxmgr():
    return [
        "You tried to use a future as a context manager.",
        "Wrap side effects in a graph task or zone instead.",
    ]


def _tip_indexing():
    return [
        "You tried to subscript a future (obj[idx]).",
        "Index inside the graph (task/zone) where the value is concrete.",
    ]


class OperatorSocketMixin:
    @property
    def _decorator(self):
        from aiida.node_graph.decorator import task

        return task

    def _create_operator_task(self, op_func, x, y):
        """Create a "hidden" operator Task in the Graph,
        hooking `self` up as 'x' and `other` as 'y'.
        Return the output socket from that new Task.
        """

        graph = self._task.graph
        if not graph:
            raise ValueError("Socket does not belong to a Graph.")

        new_node = graph.tasks._new(
            self._decorator()(op_func),
            x=x,
            y=y,
        )
        active_zone = getattr(graph, "_active_zone", None)
        if active_zone:
            active_zone.children.add(new_node)
        return new_node.outputs.result

    # Arithmetic Operations
    def __add__(self, other):
        return self._create_operator_task(op_add, self, other)

    def __sub__(self, other):
        return self._create_operator_task(op_sub, self, other)

    def __mul__(self, other):
        return self._create_operator_task(op_mul, self, other)

    def __truediv__(self, other):
        return self._create_operator_task(op_truediv, self, other)

    def __floordiv__(self, other):
        return self._create_operator_task(op_floordiv, self, other)

    def __mod__(self, other):
        return self._create_operator_task(op_mod, self, other)

    def __pow__(self, other):
        return self._create_operator_task(op_pow, self, other)

    # Reverse Arithmetic Operations
    def __radd__(self, other):
        return self._create_operator_task(op_add, other, self)

    def __rsub__(self, other):
        return self._create_operator_task(op_sub, other, self)

    def __rmul__(self, other):
        return self._create_operator_task(op_mul, other, self)

    def __rtruediv__(self, other):
        return self._create_operator_task(op_truediv, other, self)

    def __rfloordiv__(self, other):
        return self._create_operator_task(op_floordiv, other, self)

    def __rmod__(self, other):
        return self._create_operator_task(op_mod, other, self)

    def __rpow__(self, other):
        return self._create_operator_task(op_pow, other, self)

    # Comparison Operations
    def __lt__(self, other):
        return self._create_operator_task(op_lt, self, other)

    def __le__(self, other):
        return self._create_operator_task(op_le, self, other)

    def __gt__(self, other):
        return self._create_operator_task(op_gt, self, other)

    def __ge__(self, other):
        return self._create_operator_task(op_ge, self, other)

    def __eq__(self, other):
        return self._create_operator_task(op_eq, self, other)

    def __ne__(self, other):
        return self._create_operator_task(op_ne, self, other)

    def __rshift__(self, other: BaseSocket | Task | DependencyCollection):
        """
        Called when we do: self >> other
        So we link them or mark that 'other' must wait for 'self'.
        """
        if isinstance(other, DependencyCollection):
            for item in other.items:
                self >> item
        else:
            other._waiting_on.add(self)
        return other

    def __lshift__(self, other: BaseSocket | Task | DependencyCollection):
        """
        Called when we do: self << other
        Means the same as: other >> self
        """
        if isinstance(other, DependencyCollection):
            for item in other.items:
                self << item
        else:
            self._waiting_on.add(other)
        return other

    # Truthiness / boolean contexts
    def __bool__(self):
        _raise_illegal(self, "boolean evaluation", _tip_bool())

    # Numeric casts & indices
    def __int__(self):
        _raise_illegal(self, "int() cast", _tip_cast("int()"))

    def __float__(self):
        _raise_illegal(self, "float() cast", _tip_cast("float()"))

    def __complex__(self):
        _raise_illegal(self, "complex() cast", _tip_cast("complex()"))

    def __index__(self):
        _raise_illegal(self, "use as an index (__index__)", _tip_cast("indexing"))

    def __round__(self, *a, **k):
        _raise_illegal(self, "round()", _tip_cast("round()"))

    def __trunc__(self):
        _raise_illegal(self, "trunc()", _tip_cast("trunc()"))

    def __floor__(self):
        _raise_illegal(self, "math.floor()", _tip_cast("floor()"))

    def __ceil__(self):
        _raise_illegal(self, "math.ceil()", _tip_cast("ceil()"))

    # Sequence / mapping / container protocols
    def __len__(self):
        _raise_illegal(self, "len()", _tip_iter())

    def __iter__(self):
        _raise_illegal(self, "iteration", _tip_iter())

    def __reversed__(self):
        _raise_illegal(self, "reversed()", _tip_iter())

    def __contains__(self, _):
        _raise_illegal(self, "membership test (x in socket)", _tip_iter())

    def __getitem__(self, _):
        _raise_illegal(self, "subscript access (socket[idx])", _tip_indexing())

    def __setitem__(self, *_):
        _raise_illegal(self, "item assignment (socket[idx] = ...)", _tip_indexing())

    def __delitem__(self, *_):
        _raise_illegal(self, "item deletion (del socket[idx])", _tip_indexing())

    # Bitwise / logical operators that people misuse for predicates
    def __and__(self, _):
        _raise_illegal(self, "bitwise and (&) on futures", _tip_bool())

    def __or__(self, _):
        _raise_illegal(self, "bitwise or (|) on futures", _tip_bool())

    def __xor__(self, _):
        _raise_illegal(self, "bitwise xor (^) on futures", _tip_bool())

    def __invert__(self):
        _raise_illegal(self, "bitwise not (~) on futures", _tip_bool())

    def __matmul__(self, _):
        _raise_illegal(self, "matrix multiply (@)", _tip_numpy())

    # Hashing / dict keys / set members
    def __hash__(self):
        _raise_illegal(
            self,
            "hashing (use as dict/set key)",
            ["Futures are not stable keys. Resolve to a concrete value first."],
        )

    # Function-like / context-manager / async
    def __enter__(self):
        _raise_illegal(
            self,
            "context-manager enter (__enter__)",
            ["Use Socket as a context manager is not supported."],
        )

    def __exit__(self, *a):
        _raise_illegal(
            self,
            "context-manager exit (__exit__)",
            ["Use Socket as a context manager is not supported."],
        )

    def __await__(self):
        _raise_illegal(
            self,
            "await on a future (__await__)",
            ["Awaiting is not supported; use @task.graph to build logic instead."],
        )

    def __aiter__(self):
        _raise_illegal(
            self,
            "async iteration (__aiter__)",
            [
                "Async iteration is not supported; use @task.graph to build logic instead."
            ],
        )

    def __anext__(self):
        _raise_illegal(
            self,
            "async next (__anext__)",
            [
                "Async iteration is not supported; use @task.graph to build logic instead."
            ],
        )

    # NumPy interoperability guards
    # Prevent silent coercion to ndarray
    def __array__(self, *a, **k):
        _raise_illegal(self, "NumPy array coercion (__array__)", _tip_numpy())

    # Intercept ufuncs like np.add, np.sin, etc.
    def __array_ufunc__(self, *a, **k):
        _raise_illegal(self, "NumPy ufunc on future (__array_ufunc__)", _tip_numpy())

    # Intercept high-level NumPy functions
    def __array_function__(self, *a, **k):
        _raise_illegal(self, "NumPy high-level op (__array_function__)", _tip_numpy())


class WaitingOn:
    """
    A small helper class that manages 'waiting on' dependencies for a Socket.
    """

    def __init__(self, task: "BaseSocket", graph: "Graph") -> None:
        self.task = task
        self.graph = graph

    def add(self, other: "BaseSocket" | "Task") -> None:
        """Add a socket to the waiting list."""
        from aiida.node_graph.task import Task

        if isinstance(other, BaseSocket):
            task = other._task
        elif isinstance(other, Task):
            task = other
        else:
            raise TypeError(f"Expected BaseSocket or Task, got {type(other).__name__}.")
        link_name = f"{task.name}._wait -> {self.task.name}._wait"
        if link_name not in self.graph.links:
            self.graph.add_link(task.outputs._wait, self.task.inputs._wait)
        else:
            print(f"Link {link_name} already exists, skipping creation.")


def _normalize_meta(raw: Union[SocketMeta, Dict[str, Any], None]) -> SocketMeta:
    if raw is None:
        return SocketMeta()
    if isinstance(raw, SocketMeta):
        return SocketMeta.from_dict(raw.to_dict())
    if isinstance(raw, dict):
        meta = SocketMeta.from_dict(raw)
        if meta.required is None:
            meta.required = False
        if meta.socket_type is None:
            meta.socket_type = "INPUT"
        if meta.arg_type is None:
            meta.arg_type = "kwargs"
        return meta
    raise TypeError(f"metadata must be dict | SocketMeta | None – got {type(raw)!r}")


_RUNTIME_EXTRA_KEYS = {
    "identifier",
    "sockets",
    "dynamic",
    "item",
    "builtin_socket",
    "function_socket",
}


class TaggedValue(wrapt.ObjectProxy):
    def __init__(self, wrapped, socket=None):
        super().__init__(wrapped)

        self._self_socket = socket
        self._self_uuid = str(uuid4())

    # Provide clean access via `proxy._socket` instead of `proxy._self_socket`
    @property
    def _socket(self):
        return self._self_socket

    @property
    def _uuid(self):
        return self._self_uuid

    @_socket.setter
    def _socket(self, value):
        self._self_socket = value

    def __copy__(self):
        # shallow-copy the wrapped value, preserve the tag
        from copy import copy as _copy

        w = _copy(self.__wrapped__)
        return type(self)(w, socket=self._socket)

    def __deepcopy__(self, memo):
        from copy import deepcopy as _deepcopy

        # required by wrapt.ObjectProxy
        oid = id(self)
        if oid in memo:
            return memo[oid]
        w = _deepcopy(self.__wrapped__, memo)
        clone = type(self)(w, socket=self._socket)
        memo[oid] = clone
        return clone

    def __reduce_ex__(self, protocol):
        """
        This is the magic method for serialization.

        Instead of returning instructions to rebuild the TaggedValue proxy,
        only the underlying value (self.__wrapped__) gets saved.
        """
        return self.__wrapped__.__reduce_ex__(protocol)

    def __repr__(self):
        return f"TaggedValue({self.__wrapped__!r}, socket={self._socket!r}, uuid={self._uuid})"


class BaseSocket:
    """Socket object for input and output sockets of a Task.

    Attributes:
        name (str): Socket name.
        task (Task): Task this socket belongs to.
        type (str): Socket type, either "INPUT" or "OUTPUT".
        links (List[Link]): Connected links.
        property (Optional[TaskProperty]): Associated property.
        link_limit (int): Maximum number of links.
    """

    _identifier: str = "BaseSocket"

    def __init__(
        self,
        name: str,
        task: Optional["Task"] = None,
        parent: Optional["TaskSocketNamespace"] = None,
        graph: Optional["Graph"] = None,
        link_limit: int = 1,
        metadata: Union[SocketMeta, Dict[str, Any], None] = None,
        **kwargs: Any,
    ) -> None:
        """Initialize an instance of TaskSocket.

        Args:
            name (str): Name of the socket.
            parent (Optional[Task]): Parent task. Defaults to None.
            type (str, optional): Socket type. Defaults to "INPUT".
            link_limit (int, optional): Maximum number of links. Defaults to 1.
        """
        from aiida.node_graph.utils import valid_name_string

        valid_name_string(name)
        self._name = name
        self._task = task
        self._parent = parent
        self._graph = graph
        self._links = []
        self._link_limit = link_limit
        self._metadata: SocketMeta = _normalize_meta(metadata)
        self._waiting_on = WaitingOn(task=self._task, graph=self._graph)

    @property
    def _full_name(self) -> str:
        """Full hierarchical name, including all parent namespaces."""
        if self._parent is not None:
            return f"{self._parent._full_name}.{self._name}"
        return self._name

    @property
    def _scoped_name(self) -> str:
        """The name relative to its immediate parent, excluding the root namespace."""
        return self._full_name.split(".", 1)[-1]

    @property
    def _full_name_with_task(self) -> str:
        """Full hierarchical name, including task name and all parent namespaces."""
        if self._task is not None:
            return f"{self._task.name}.{self._full_name}"
        return self._full_name

    def _to_dict(self) -> Dict[str, Any]:
        """Export the socket to a dictionary for database storage."""
        data: Dict[str, Any] = {
            "name": self._name,
            "identifier": self._identifier,
            "link_limit": self._link_limit,
            "links": [],
            "metadata": self._metadata.to_dict(),
        }
        for link in self._links:
            if self._metadata.socket_type.upper() == "INPUT":
                data["links"].append(
                    {
                        "from_task": link.from_task.name,
                        "from_socket": link.from_socket._name,
                    }
                )
            else:
                data["links"].append(
                    {
                        "to_task": link.to_task.name,
                        "to_socket": link.to_socket._name,
                    }
                )

        return data

    def _update_updatable_meta(self, payload: Dict[str, Any]) -> None:
        """Update whitelisted metadata extras on the socket."""
        extras = self._metadata.extras
        for key, value in payload.items():
            if key not in UPDATABLE_SOCKET_META_FIELDS:
                continue
            if value is None or (key == "value_source" and value == "link"):
                extras.pop(key, None)
            else:
                extras[key] = value


class TaskSocket(BaseSocket, OperatorSocketMixin):
    _identifier: str = "TaskSocket"

    _socket_property_class = TaskProperty

    _socket_property_identifier: Optional[str] = None

    def __init__(
        self,
        name: str,
        task: Optional["Task"] = None,
        parent: Optional["TaskSocketNamespace"] = None,
        graph: Optional["Graph"] = None,
        link_limit: int = 1,
        metadata: Optional[dict] = None,
        property: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        """Initialize an instance of TaskSocket.

        Args:
            name (str): Name of the socket.
            parent (Optional[Task]): Parent task. Defaults to None.
            type (str, optional): Socket type. Defaults to "INPUT".
            link_limit (int, optional): Maximum number of links. Defaults to 1.
        """
        BaseSocket.__init__(
            self,
            name=name,
            task=task,
            parent=parent,
            graph=graph,
            link_limit=link_limit,
            metadata=metadata,
            **kwargs,
        )
        # Conditionally add a property if property_identifier is provided
        self.property: Optional[TaskProperty] = None
        if self._socket_property_identifier:
            property = property or {}
            property["identifier"] = self._socket_property_identifier
            property["name"] = name
            self.add_property(**(property or {}))

    def add_property(
        self, identifier: str, name: Optional[str] = None, **kwargs: Any
    ) -> None:
        """Add a property to this socket."""
        if name is None:
            name = self._name
        self.property = self._socket_property_class.new(identifier, name=name, **kwargs)

    @property
    def _value(self) -> Any:
        """Get the value of the socket."""
        if self.property:
            return self.property.value
        return None

    @property
    def value(self) -> Any:
        if (
            self._task is not None
            and self._task._input_resolver is not None
            and self._full_name.split(".")[0] == "inputs"
            and self._metadata.extras.get("value_source") != "property"
        ):
            return self._task._input_resolver(self)
        return self._value

    @value.setter
    def value(self, value: Any) -> None:
        self._set_socket_value(value)

    def _set_socket_value(self, value: Any, *, value_source: str = "link") -> None:
        if isinstance(value, BaseSocket):
            if (
                isinstance(value, TaskSocketNamespace)
                and value._parent is None
                and "_outputs" in value
            ):
                value = value._outputs
            self._update_updatable_meta({"value_source": "link"})
            self._task.graph.add_link(value, self)
        elif isinstance(value, TaggedValue) and value._socket is not None:
            self._update_updatable_meta({"value_source": "link"})
            self._task.graph.add_link(value._socket, self)
        elif self.property:
            is_input = self._full_name.split(".")[0] == "inputs"
            has_link = any(
                [
                    link.to_socket._full_name_with_task == self._full_name_with_task
                    for link in self._links
                ]
            )
            if is_input and has_link:
                override = (
                    value_source == "property"
                    or self._metadata.extras.get("value_source") == "property"
                )
                if not override:
                    raise ValueError(
                        f"Input {self._full_name_with_task} has already been set via a "
                        f"link. Please update the linked value in {self._links}"
                    )
                self._update_updatable_meta({"value_source": "property"})
            elif is_input and value_source != "property":
                self._update_updatable_meta({"value_source": "link"})

            graph = getattr(self._task, "graph", None)
            if graph is not None:
                policy = getattr(graph, "serialization_policy", "off")
                if policy in {"validate", "eager"}:
                    serialized = graph.serialization.serialize(value, self, store=False)
                    if policy == "eager":
                        self._serialized_preview = serialized

            self.property.value = value
        else:
            raise AttributeError(
                f"Socket '{self._name}' has no property to set a value."
            )

    def _serialize_value(self, store: bool = False) -> Any:
        """Serialize the socket value unless it's metadata (stored as raw)."""
        value = resolve_tagged_values(self._value)
        if value is None:
            return None
        if self._metadata.is_metadata:
            return value
        graph = getattr(self, "_graph", None)
        if graph is None and getattr(self, "_task", None) is not None:
            graph = getattr(self._task, "graph", None)
        serializer = getattr(graph, "serialization", None) if graph else None
        if serializer is not None and hasattr(serializer, "serialize"):
            return serializer.serialize(value, self, store=store)
        return value

    def set_serializer(self, func) -> None:
        """Override socket-level serialization with a callable."""
        import types

        self._serialize_value = types.MethodType(func, self)

    def _to_dict(self):
        data = super()._to_dict()
        # data from property
        if self.property is not None:
            data["property"] = self.property.to_dict()
        else:
            data["property"] = None
        return data

    def _to_spec(self) -> "SocketSpec":
        """
        Create a SocketSpec describing the current runtime state of this socket.
        """
        from copy import deepcopy
        from aiida.node_graph.socket_spec import SocketSpec, SocketMeta

        runtime_meta = self._metadata
        extras = {
            k: v
            for k, v in (runtime_meta.extras or {}).items()
            if k not in _RUNTIME_EXTRA_KEYS
        }

        meta = SocketMeta(
            help=runtime_meta.help,
            required=runtime_meta.required,
            call_role=runtime_meta.call_role,
            is_metadata=runtime_meta.is_metadata,
            dynamic=False,
            child_default_link_limit=runtime_meta.child_default_link_limit,
            extras=extras,
        )
        spec_kwargs: Dict[str, Any] = {
            "identifier": self._identifier,
            "item": None,
            "fields": {},
            "link_limit": self._link_limit,
            "meta": meta,
        }

        if "default" in extras:
            spec_kwargs["default"] = deepcopy(extras["default"])

        return SocketSpec(**spec_kwargs)

    @classmethod
    def _from_dict(cls, data: Dict[str, Any]) -> None:
        # Create a new instance of this class
        socket = cls(
            name=data["name"],
            link_limit=data.get("link_limit", 1),
            metadata=data.get("metadata", {}),
        )
        # Add property
        if data.get("property"):
            socket.add_property(**data["property"])
        return socket

    def _copy(
        self,
        task: Optional["Task"] = None,
        parent: Optional["Task"] = None,
        **kwargs: Any,
    ) -> "TaskSocket":
        """Copy this socket.

        Args:
            parent (Task, optional): Task that this socket will belong to. Defaults to None.

        Returns:
            TaskSocket: The copied socket.
        """
        task = self._task if task is None else task
        parent = self._parent if parent is None else parent
        socket_copy = self.__class__(
            name=self._name,
            task=task,
            parent=parent,
            link_limit=self._link_limit,
        )
        if self.property:
            socket_copy.property = self.property.copy()
        return socket_copy

    def __repr__(self) -> str:
        value = self.property.value if self.property else None
        return f"{self.__class__.__name__}(name='{self._name}', value={value})"


def check_identifier_name(identifier: str, pool: dict) -> None:
    import difflib

    if isinstance(identifier, str) and identifier.lower() not in pool:
        items = difflib.get_close_matches(identifier.lower(), pool._keys())
        if len(items) == 0:
            msg = f"Identifier: {identifier} is not defined."
        else:
            msg = f"Identifier: {identifier} is not defined. Did you mean {', '.join(item.lower() for item in items)}?"
        raise ValueError(msg)


def _raise_namespace_assignment_error(
    *,
    target_ns: "TaskSocketNamespace",
    incoming_desc: str,
    reason: str,
    fixes: list[str],
) -> None:
    """Raise a ValueError guiding users when setting/linking values into a namespace."""
    where = getattr(target_ns, "_full_name_with_task", "<namespace>")
    msg = [
        f"Invalid assignment into namespace socket: {where}",
        "",
        "What happened:",
        f"  • {reason}",
        f"  • Incoming value: {incoming_desc}",
        "",
        "Why this matters:",
        "  • Without a namespace-typed graph input, the whole dict is treated as *one value*,",
        "    so its inner keys are NOT wired to the child sockets. You'd end up with missing links.",
        "",
        "How to fix:",
        *[f"  • {line}" for line in fixes],
    ]
    raise ValueError("\n".join(msg))


class TaskSocketNamespace(BaseSocket, OperatorSocketMixin):
    """A TaskSocket that also acts as a namespace (collection) of other sockets."""

    _identifier: str = "node_graph.namespace"
    _type_mapping: dict = type_mapping

    _RESERVED_NAMES = {
        "_RESERVED_NAMES",
        "_IDENTIFIER",
        "_VALUE",
        "_NAME",
        "_TASK",
        "_PARENT",
        "_LINKS",
        "_LINK_LIMIT",
        "_METADATA",
    }

    def __init__(
        self,
        name: str,
        task: Optional["Task"] = None,
        parent: Optional["TaskSocket"] = None,
        link_limit: int = 1000000,
        metadata: Union[SocketMeta, Dict[str, Any], None] = None,
        sockets: Optional[Dict[str, object]] = None,
        pool: Optional[object] = None,
        entry_point: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        # Initialize TaskSocket first
        BaseSocket.__init__(
            self,
            name=name,
            task=task,
            parent=parent,
            link_limit=link_limit,
            metadata=metadata,
            **kwargs,
        )
        #
        self._sockets: Dict[str, object] = {}
        self._parent = parent
        self._SocketPool = None
        # one can specify the pool or entry_point to get the pool
        if pool is not None:
            self._SocketPool = pool
        elif entry_point is not None and self._SocketPool is None:
            self._SocketPool = EntryPointPool(entry_point_group=entry_point)
        else:
            from aiida.node_graph.sockets import SocketPool

            self._SocketPool = SocketPool

        if self._metadata.dynamic:
            self._link_limit = 1000000
        if sockets is not None:
            for key, socket in sockets.items():
                kwargs = {}
                if "property" in socket:
                    kwargs["property"] = socket["property"]
                if "sockets" in socket:
                    kwargs["sockets"] = socket["sockets"]
                self._new(
                    socket["identifier"],
                    name=key,
                    metadata=socket.get("metadata", {}),
                    **kwargs,
                )

    def __getattr__(self, name: str) -> Any:
        """
        We check if it is in our _sockets. If so, return that sub-socket.
        Otherwise, raise AttributeError.
        """
        # By explicitly raising an AttributeError, Python will continue its normal flow
        # We still hardcoded the built-in sockets: _wait and outputs
        if name.startswith("_") and name not in ["_wait", "_outputs"]:
            raise AttributeError(f"{self.__class__.__name__} has no attribute '{name}'")
        try:
            return self._sockets[name]
        except KeyError:
            avail = ", ".join(self._sockets.keys()) or "<none>"
            raise AttributeError(
                f"{self.__class__.__name__}: '{self._full_name_with_task}' has no sub-socket '{name}'.\n"
                f"Available: {avail}\n"
                f"Tip: If '{name}' should exist, add it to the SocketSpec (or make this namespace dynamic)."
            )

    def __setattr__(self, name: str, value: Any) -> None:
        """
        Override __setattr__ so that doing `namespace_socket.some_name = x`
        either sets the property or links to another socket, rather than
        replacing the entire sub-socket object.
        """
        # If the attribute name is "private" or reserved, do normal attribute setting
        if name.startswith("_"):
            object.__setattr__(self, name, value)
            return

        self._set_socket_value({name: value})

    def __setitem__(self, key: str | int, value: Any) -> None:
        """
        Override __setitem__ so that doing `namespace_socket[key] = x`
        either sets the property or links to another socket, rather than
        replacing the entire sub-socket object.
        """
        if isinstance(key, int):
            key = list(self._sockets.keys())[key]
        self.__setattr__(key, value)

    def __dir__(self) -> list[str]:
        """
        Make tab-completion more friendly:
        """
        # Get the list of default attributes from the parent class
        default_attrs = super().__dir__()

        # Get the custom attributes from the _sockets dictionary
        socket_attrs = self._sockets.keys()

        # Combine the default and custom attributes, remove duplicates, and sort
        return sorted(list(set(default_attrs) | set(socket_attrs)))

    def _new(
        self,
        identifier: Union[str, type] = None,
        name: Optional[str] = None,
        metadata: Optional[dict] = None,
        **kwargs: Any,
    ) -> object:
        identifier = identifier or self._SocketPool["any"]
        check_identifier_name(identifier, self._SocketPool)

        meta_payload = dict(metadata or {})
        if "socket_type" not in meta_payload and self._metadata.socket_type:
            meta_payload["socket_type"] = self._metadata.socket_type

        _names = name.split(".", 1)
        if len(_names) > 1:
            namespace = _names[0]
            if namespace not in self:
                # if the namespace is dynamic, create sub-sockets if it does not exist
                if self._metadata.dynamic:
                    # the sub-socket should also be dynamic
                    self._new(
                        self._SocketPool["namespace"],
                        namespace,
                        metadata={
                            "dynamic": True,
                            "child_default_link_limit": self._metadata.child_default_link_limit,
                        },
                    )
                else:
                    raise ValueError(
                        f"Namespace {namespace} does not exist in the socket collection."
                    )
            return self[namespace]._new(
                identifier,
                _names[1],
                link_limit=self._metadata.child_default_link_limit,
                metadata=meta_payload,
            )
        else:
            ItemClass = get_item_class(identifier, self._SocketPool)
            kwargs.pop("graph", None)
            kwargs.setdefault("link_limit", self._metadata.child_default_link_limit)
            item = ItemClass(
                name,
                task=self._task,
                parent=self,
                graph=self._graph,
                metadata=meta_payload,
                pool=self._SocketPool,
                **kwargs,
            )
            self._append(item)
            return item

    @property
    def _value(self) -> Dict[str, Any]:
        return self._collect_values()

    def _collect_values(
        self, unwrap: bool = True, resolve: bool = False, serialize: bool = False
    ) -> Dict[str, Any]:
        data = {}
        for name, item in self._sockets.items():
            if isinstance(item, TaskSocketNamespace):
                value = item._collect_values(
                    unwrap=unwrap, resolve=resolve, serialize=serialize
                )
                if value:
                    data[name] = value
            else:
                value = item.value if resolve else item._value
                if serialize:
                    value = item._serialize_value(store=False)
                if value is not None:
                    if unwrap and isinstance(value, TaggedValue):
                        data[name] = value.__wrapped__
                    else:
                        data[name] = value
        return data

    def _to_spec(self) -> "SocketSpec":
        """
        Materialize the current namespace into a SocketSpec snapshot.
        """
        from aiida.node_graph.socket_spec import SocketSpec, SocketMeta
        from copy import deepcopy

        runtime_meta = self._metadata
        extras = {
            k: v
            for k, v in (runtime_meta.extras or {}).items()
            if k not in _RUNTIME_EXTRA_KEYS
        }

        meta = SocketMeta(
            help=runtime_meta.help,
            required=runtime_meta.required,
            call_role=runtime_meta.call_role,
            is_metadata=runtime_meta.is_metadata,
            dynamic=self._metadata.dynamic,
            child_default_link_limit=runtime_meta.child_default_link_limit,
            extras=extras,
        )

        fields: Dict[str, "SocketSpec"] = {}
        for name, child in self._sockets.items():
            if child._metadata.extras.get("builtin_socket"):
                continue
            if hasattr(child, "_to_spec"):
                fields[name] = child._to_spec()

        item_spec = None
        if "item" in extras:
            item_snapshot = extras["item"]
            if isinstance(item_snapshot, dict):
                item_spec = self._spec_from_shape_snapshot(item_snapshot)
            else:
                item_spec = None

        spec = SocketSpec(
            identifier=self._identifier,
            item=item_spec,
            fields=fields,
            link_limit=self._link_limit,
            meta=meta,
        )

        if "default" in extras:
            spec = replace(spec, default=deepcopy(extras["default"]))

        return spec

    @staticmethod
    def _spec_from_shape_snapshot(snapshot: Dict[str, Any]) -> "SocketSpec":
        """
        Rebuild a SocketSpec from a minimal shape snapshot stored in metadata extras.
        """
        from copy import deepcopy
        from aiida.node_graph.socket_spec import SocketSpec, SocketMeta

        identifier = snapshot.get("identifier", "node_graph.any")

        fields = {
            name: TaskSocketNamespace._spec_from_shape_snapshot(child_snapshot)
            for name, child_snapshot in snapshot.get("sockets", {}).items()
        }

        item_snapshot = snapshot.get("item")
        item_spec = (
            TaskSocketNamespace._spec_from_shape_snapshot(item_snapshot)
            if isinstance(item_snapshot, dict)
            else None
        )

        meta = SocketMeta(dynamic=bool(snapshot.get("dynamic", False)))

        spec_kwargs: Dict[str, Any] = {
            "identifier": identifier,
            "fields": fields,
            "item": item_spec,
            "meta": meta,
        }

        if "default" in snapshot:
            spec_kwargs["default"] = deepcopy(snapshot["default"])
        if "link_limit" in snapshot:
            spec_kwargs["link_limit"] = snapshot["link_limit"]

        return SocketSpec(**spec_kwargs)

    @_value.setter
    def _value(self, value: Dict[str, Any]) -> None:
        self._set_socket_value(value)

    def _link_namespace_socket(self, value: BaseSocket) -> None:
        """Link a socket directly to this namespace."""
        self._clear_updatable_meta()
        self._task.graph.add_link(value, self)

    def _append_dynamic_child(self, key: str, val: Any) -> None:
        from aiida.node_graph.socket_spec import SocketSpec

        extras = self._metadata.extras or {}
        item_snapshot = extras.get("item") if isinstance(extras, dict) else None
        if item_snapshot is None:
            if isinstance(val, (dict, TaskSocketNamespace)):
                item_snapshot = {
                    "identifier": self._type_mapping["namespace"],
                    "dynamic": True,
                }
            else:
                item_snapshot = {"identifier": self._type_mapping["default"]}
        item_spec = (
            SocketSpec.from_dict(item_snapshot)
            if isinstance(item_snapshot, dict)
            else None
        )
        self._append_from_spec(
            self,
            key,
            item_spec,
            task=self._task,
            graph=self._graph,
            role="input",
        )

    def _get_or_create_child(self, key: str, val: Any) -> object:
        if key in self._sockets:
            return self._sockets[key]
        if key.startswith("_"):
            _raise_namespace_assignment_error(
                target_ns=self,
                incoming_desc=f"key '{key}'",
                reason=f"Field '{key}' is a reserved builtin socket.",
                fixes=[
                    "Remove the builtin key from the assignment; or",
                    "link to an explicit leaf socket instead of the namespace.",
                ],
            )
        if not self._metadata.dynamic:
            _raise_namespace_assignment_error(
                target_ns=self,
                incoming_desc=f"key '{key}'",
                reason=f"Field '{key}' is not defined and this namespace is not dynamic.",
                fixes=[
                    "Add the field to the namespace spec; or",
                    "make the namespace dynamic if it should grow automatically.",
                ],
            )
        self._append_dynamic_child(key, val)
        return self._sockets[key]

    def _assign_key_value(self, key: str, val: Any, *, value_source: str) -> None:
        if "." in key:
            head, tail = key.split(".", 1)
            if head not in self._sockets:
                if head.startswith("_"):
                    _raise_namespace_assignment_error(
                        target_ns=self,
                        incoming_desc=f"key '{head}'",
                        reason=f"Field '{head}' is a reserved builtin socket.",
                        fixes=[
                            "Remove the builtin key from the assignment; or",
                            "link to an explicit leaf socket instead of the namespace.",
                        ],
                    )
                if not self._metadata.dynamic:
                    _raise_namespace_assignment_error(
                        target_ns=self,
                        incoming_desc=f"key '{head}'",
                        reason=f"Field '{head}' is not defined and this namespace is not dynamic.",
                        fixes=[
                            "Define the field in the socket spec (preferred); or",
                            "mark this namespace dynamic if it must accept arbitrary keys;",
                            "or correct the key path being assigned.",
                        ],
                    )
                self._new(
                    self._SocketPool["namespace"],
                    head,
                    metadata={
                        "dynamic": True,
                        "child_default_link_limit": self._metadata.child_default_link_limit,
                    },
                )
            child = self._sockets[head]
            if not isinstance(child, TaskSocketNamespace):
                _raise_namespace_assignment_error(
                    target_ns=self,
                    incoming_desc=f"nested key '{key}' under leaf '{head}'",
                    reason=f"'{head}' is a leaf socket, but you attempted to assign nested data below it.",
                    fixes=[
                        "Use a namespace socket for hierarchical data; update your SocketSpec accordingly; or",
                        "flatten your assignment to target a leaf socket directly.",
                    ],
                )
            child._set_socket_value({tail: val}, value_source=value_source)
            return

        target = self._get_or_create_child(key, val)
        if isinstance(target, TaskSocketNamespace):
            if is_structured_instance(val):
                val = structured_to_dict(val)
            if isinstance(val, TaskSocketNamespace):
                target._set_socket_value(val, value_source=value_source)
                return
            if isinstance(val, BaseSocket):
                if target._metadata.dynamic:
                    target._set_socket_value(val, value_source=value_source)
                    return
                if getattr(val, "_scoped_name", None) == "_outputs":
                    target._set_socket_value(val, value_source=value_source)
                    return
                _raise_namespace_assignment_error(
                    target_ns=target,
                    incoming_desc=type(val).__name__,
                    reason="A non-dynamic namespace cannot accept a direct socket link.",
                    fixes=[
                        "Link a specific leaf socket instead of the namespace; or",
                        "make the namespace dynamic if it should accept multiple links.",
                    ],
                )
            if isinstance(val, (dict, TaskSocketNamespace)):
                target._set_socket_value(val, value_source=value_source)
                return
            _raise_namespace_assignment_error(
                target_ns=target,
                incoming_desc=type(val).__name__,
                reason="A namespace expects a mapping of fields, but a non-dict value was provided.",
                fixes=[
                    "Provide a dict like {'x': 1, 'y': 2} that matches the namespace shape.",
                ],
            )
        else:
            target._set_socket_value(val, value_source=value_source)

    def _set_socket_value(
        self, value: Dict[str, Any] | TaskSocket, *, value_source: str = "link"
    ) -> None:
        """Set value(s) into this namespace.

        Supports:
        - linking another socket (BaseSocket)
        - nested dicts
        - dotted keys like "data.x" or "nested.data.x"

        Creation rules:
        - Missing immediate children can be created only if *this* namespace is dynamic.
        - Intermediate dotted segments are created as namespaces (dynamic=True) when needed.
        """
        if value is None:
            return
        if is_structured_instance(value):
            value = structured_to_dict(value)

        # Link another socket directly to this namespace
        if isinstance(value, BaseSocket):
            self._link_namespace_socket(value)
            return

        if isinstance(value, TaggedValue):
            src = getattr(
                getattr(value, "_socket", None),
                "_full_name_with_task",
                "<unknown-socket>",
            )
            _raise_namespace_assignment_error(
                target_ns=self,
                incoming_desc=f"TaggedValue(dict) from {src}",
                reason="A TaggedValue wrapping a dict is being assigned to a *namespace*.",
                fixes=[
                    "Annotate the graph-level parameter as a namespace, e.g.:",
                    f"    def your_graph({self._name}: Annotated[dict, namespace({list(self._sockets.keys())[0]}=, ...)]):",
                    "",
                    "Or reuse the task’s own input spec, e.g.:",
                    f"    def your_graph({self._name}: Annotated[dict, add_multiply.inputs.data]):",
                    "        add_multiply(data=data)",
                    "",
                ],
            )

        if not isinstance(value, dict):
            _raise_namespace_assignment_error(
                target_ns=self,
                incoming_desc=type(value).__name__,
                reason="This is a namespace socket and expects a dict (or a Socket link).",
                fixes=[
                    "Provide a dict with keys matching the namespace fields;",
                    "or link another socket/namespace; or declare the graph input as a namespace.",
                ],
            )

        for key, val in value.items():
            self._assign_key_value(key, val, value_source=value_source)

    def _export_updatable_meta_map(self) -> Dict[str, Dict[str, Any]]:
        """Export whitelisted metadata extras keyed by scoped socket path."""
        meta_map: Dict[str, Dict[str, Any]] = {}
        for name, child in self._sockets.items():
            child_payload = {
                key: child._metadata.extras.get(key)
                for key in UPDATABLE_SOCKET_META_FIELDS
                if key in child._metadata.extras
            }
            if child_payload:
                meta_map[name] = child_payload
            if isinstance(child, TaskSocketNamespace):
                nested = child._export_updatable_meta_map()
                for nested_name, payload in nested.items():
                    meta_map[f"{name}.{nested_name}"] = payload
        return meta_map

    def _apply_updatable_meta_map(self, meta_map: Dict[str, Dict[str, Any]]) -> None:
        """Apply whitelisted metadata extras from a scoped map."""
        for path, payload in meta_map.items():
            try:
                target = self[path]
            except Exception:
                continue
            if hasattr(target, "_update_updatable_meta"):
                target._update_updatable_meta(payload)

    def _clear_updatable_meta(self) -> None:
        """Clear all whitelisted metadata extras in this namespace subtree."""
        self._update_updatable_meta({key: None for key in UPDATABLE_SOCKET_META_FIELDS})
        for child in self._sockets.values():
            if hasattr(child, "_clear_updatable_meta"):
                child._clear_updatable_meta()
            elif hasattr(child, "_update_updatable_meta"):
                child._update_updatable_meta(
                    {key: None for key in UPDATABLE_SOCKET_META_FIELDS}
                )

    @property
    def _all_links(self) -> List["TaskLink"]:
        links = []
        for item in self._sockets.values():
            links.extend(item._links)
            if isinstance(item, TaskSocketNamespace):
                links.extend(item._all_links)
        return links

    def _to_dict(self) -> Dict[str, Any]:
        data = super()._to_dict()
        data["sockets"] = {}
        # Add nested sockets information
        for item in self._sockets.values():
            data["sockets"][item._name] = item._to_dict()
        return data

    @classmethod
    def _from_dict(
        cls,
        data: Dict[str, Any],
        task: Optional["Task"] = None,
        parent: Optional["TaskSocket"] = None,
        pool: Optional[object] = None,
        **kwargs: Any,
    ) -> None:
        # Create a new instance of this class
        ns = cls(
            name=data["name"],
            link_limit=data.get("link_limit", 1),
            metadata=data.get("metadata", {}),
            task=task,
            parent=parent,
            graph=kwargs.pop("graph", None),
            pool=pool,
            **kwargs,
        )
        # Add nested sockets
        for name, item_data in data.get("sockets", {}).items():
            item_data["name"] = name
            ns._new(**item_data)
        return ns

    @classmethod
    def _from_spec(
        cls,
        name: str,
        spec: "SocketSpec",
        *,
        task: Optional["Task"],
        graph: Optional["Graph"],
        parent: Optional["TaskSocket"] = None,
        pool: Optional[object] = None,
        role: str = "input",
    ) -> "TaskSocketNamespace":
        """
        Materialize a runtime namespace (and children) from a SocketSpec.
        The *spec* must be a namespace.
        """
        from aiida.node_graph.materialize import runtime_meta_from_spec

        if spec.identifier != cls._type_mapping["namespace"]:
            raise ValueError(
                f"The socket spec identifier must be a namespace, got: {spec.identifier}"
            )

        ns_meta = runtime_meta_from_spec(
            spec, role=role, function_generated=True, type_mapping=cls._type_mapping
        )
        ns = cls(
            name=name,
            task=task,
            parent=parent,
            graph=graph,
            link_limit=spec.link_limit or 1,
            metadata=ns_meta,
            pool=pool or (task._REGISTRY.socket_pool if task else None),
        )

        # materialize fixed fields
        for fname, f_spec in (spec.fields or {}).items():
            cls._append_from_spec(ns, fname, f_spec, task=task, graph=graph, role=role)
        return ns

    @classmethod
    def _append_from_spec(
        cls,
        parent_ns: "TaskSocketNamespace",
        name: str,
        spec: "SocketSpec",
        *,
        task,
        graph,
        role: str,
    ) -> None:
        if "." in name:
            head, tail = name.split(".", 1)
            existing = parent_ns._sockets.get(head)

            if existing is None:
                raise ValueError(
                    f"Cannot assign nested field '{tail}' under missing socket '{head}'."
                )

            if not isinstance(existing, TaskSocketNamespace):
                raise TypeError(
                    f"Cannot assign nested field '{tail}' under non-namespace socket '{head}'."
                )

            cls._append_from_spec(
                existing,
                tail,
                spec,
                task=task,
                graph=graph,
                role=role,
            )
            return

        from copy import deepcopy
        from aiida.node_graph.materialize import runtime_meta_from_spec

        if spec.identifier == cls._type_mapping["namespace"]:
            child_meta = runtime_meta_from_spec(
                spec, role=role, function_generated=True, type_mapping=cls._type_mapping
            )
            child = cls(
                name=name,
                task=task,
                parent=parent_ns,
                graph=graph,
                metadata=child_meta,
                pool=parent_ns._SocketPool,
            )
            parent_ns._append(child)

            for fname, f_spec in (spec.fields or {}).items():
                cls._append_from_spec(
                    child,
                    fname,
                    f_spec,
                    task=task,
                    graph=graph,
                    role=role,
                )
        else:
            # leaf
            leaf_meta = runtime_meta_from_spec(
                spec, role=role, function_generated=True, type_mapping=cls._type_mapping
            )

            prop = {"identifier": spec.identifier}
            if not isinstance(spec.default, type(MISSING)):
                prop["default"] = deepcopy(spec.default)

            ItemClass = get_item_class(spec.identifier, parent_ns._SocketPool)
            sock = ItemClass(
                name=name,
                task=task,
                parent=parent_ns,
                graph=graph,
                metadata=leaf_meta,
                property=prop,
                link_limit=parent_ns._metadata.child_default_link_limit,
            )
            parent_ns._append(sock)

    def _copy(
        self,
        task: Optional[Task] = None,
        parent: Optional[TaskSocket] = None,
        skip_linked: bool = False,
        skip_builtin: bool = False,
    ) -> "TaskSocketNamespace":
        # Copy as parentSocket
        parent = self._parent if parent is None else parent
        ns_copy = self.__class__(
            self._name,
            task=task,
            parent=parent,
            link_limit=self._link_limit,
            metadata=self._metadata,
        )
        # Copy nested sockets
        for item in self._sockets.values():
            if len(item._links) > 0 and skip_linked:
                continue
            if skip_builtin and item._name in ["_wait", "_outputs"]:
                continue
            ns_copy._append(
                item._copy(task=task, parent=ns_copy, skip_linked=skip_linked)
            )
        return ns_copy

    def __iter__(self) -> object:
        # Iterate over items in insertion order
        return iter(self._sockets.values())

    def __getitem__(self, key: Union[int, str]) -> object:
        if isinstance(key, int):
            # If indexing by int, convert dict keys to a list and index it
            return self._sockets[list(self._sockets.keys())[key]]
        elif isinstance(key, str):
            keys = key.split(".", 1)
            if keys[0] in self._sockets:
                item = self._sockets[keys[0]]
                if len(keys) > 1:
                    return item[keys[1]]
                return item
            raise AttributeError(
                f""""{key}" is not in this namespace: {self._full_name_with_task}. Acceptable names are {self._get_keys()}."""
            )

    def __contains__(self, name: str) -> bool:
        """Check if an item with the given name exists in the collection.

        Args:
            name (str): The name of the item to check.

        Returns:
            bool: True if the item exists, False otherwise.
        """
        keys = name.split(".", 1)
        if keys[0] in self._sockets:
            if len(keys) > 1:
                child = self._sockets[keys[0]]
                if isinstance(child, TaskSocketNamespace):
                    return keys[1] in child
                return False  # cannot have nested under a non-namespace
            return True
        return False

    def _append(self, item: object) -> None:
        """Append item into this collection."""
        if item._name in self._sockets:
            raise ValueError(f"Name '{item._name}' already exists in the namespace.")
        if item._name.upper() in self._RESERVED_NAMES:
            raise ValueError(f"Name '{item._name}' is reserved by the namespace.")
        self._sockets[item._name] = item

    def _get(self, name: str) -> object:
        """Find item by name

        Args:
            name (str): _description_

        Returns:
            object: _description_
        """

    def _get_all_keys(self) -> List[str]:
        # keys in the collection, with the option to include nested keys
        keys = [item._scoped_name for item in self._sockets.values()]
        for item in self._sockets.values():
            if isinstance(item, TaskSocketNamespace):
                keys.extend(item._get_all_keys())
        return keys

    def _get_keys(self) -> List[str]:
        # keys in the collection, with the option to include nested keys
        return list(self._sockets.keys())

    def _clear(self) -> None:
        """Remove all items from this collection."""
        self._sockets = {}

    def __delitem__(self, index: Union[int, List[int], str]) -> None:
        # If index is int, convert _items to a list and remove by index
        if isinstance(index, str):
            self._sockets.pop(index)
        elif isinstance(index, int):
            key = list(self._sockets.keys())[index]
            self._sockets.pop(key)
        elif isinstance(index, list):
            keys = list(self._sockets.keys())
            for i in sorted(index, reverse=True):
                key = keys[i]
                self._sockets.pop(key)
        else:
            raise ValueError(
                f"Invalid index type for __delitem__: {index}, expected int or str, or list of int."
            )

    def __len__(self) -> int:
        return len(self._sockets)

    def __repr__(self) -> str:
        nested = list(self._sockets.keys())
        return f"{self.__class__.__name__}(name='{self._name}', sockets={nested})"

    def _iter_children(
        self, *, include_builtins: bool = False
    ) -> list[tuple[str, object]]:
        """Iterate namespace children, optionally including builtin sockets."""
        items = []
        for name, child in self._sockets.items():
            if not include_builtins and name.startswith("_"):
                continue
            items.append((name, child))
        return items

    def _relative_keys(self, *, include_builtins: bool = False) -> set[str]:
        """Return leaf socket paths relative to this namespace."""
        keys: set[str] = set()

        def _walk(namespace: "TaskSocketNamespace", prefix: str = "") -> None:
            for name, child in namespace._iter_children(
                include_builtins=include_builtins
            ):
                path = f"{prefix}{name}" if prefix else name
                if isinstance(child, TaskSocketNamespace):
                    _walk(child, f"{path}.")
                else:
                    keys.add(path)

        _walk(self)
        return keys
