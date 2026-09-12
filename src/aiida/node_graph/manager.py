"""
Simple global variable approach.
Note pitfalls:
    - lack of concurrency control
    - collisions in library code
    - difficulty testing in isolation
    - etc.
"""
from contextlib import contextmanager
from contextvars import ContextVar
from aiida.node_graph.tasks.task_pool import TaskPool
from aiida.node_graph.socket import TaskSocket

_current_graph: ContextVar["Graph | None"] = ContextVar("current_graph", default=None)


class CurrentGraphManager:
    _instance = None

    def __new__(cls, *args, **kwargs):
        """
        Enforce the singleton pattern. Only one instance of
        CurrentGraphManager is created for the entire process.
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def peek_current_graph(self):
        """Return the active graph or None (do NOT auto-create)."""
        return _current_graph.get()

    def get_current_graph(self):
        """
        Retrieve the current graph, or create a new one if none is set.
        """
        from aiida.node_graph.graph import Graph

        g = _current_graph.get()
        if g is None:
            g = Graph()
            _current_graph.set(g)
        return g

    def set_current_graph(self, graph):
        """
        Set the active graph to the given instance.
        """
        _current_graph.set(graph)

    @contextmanager
    def active_graph(self, graph):
        """
        Context manager that temporarily overrides the current graph
        with `graph`, restoring the old graph when exiting the context.
        """
        token = _current_graph.set(graph)
        try:
            yield graph
        finally:
            _current_graph.reset(token)


# Create a global manager instance
_manager = CurrentGraphManager()


def peek_current_graph():
    return _manager.peek_current_graph()


def get_current_graph():
    return _manager.get_current_graph()


def set_current_graph(graph):
    _manager.set_current_graph(graph)


@contextmanager
def active_graph(graph):
    with _manager.active_graph(graph) as ctx:
        yield ctx


@contextmanager
def Zone():
    """
    Context manager to create a "zone" in the current graph.
    """

    graph = get_current_graph()

    zone_task = graph.add_task(
        TaskPool.node_graph.zone,
    )

    old_zone = getattr(graph, "_active_zone", None)
    if old_zone:
        old_zone.children.add(zone_task)
    graph._active_zone = zone_task

    try:
        yield zone_task
    finally:
        graph._active_zone = old_zone


@contextmanager
def If(condition_socket: TaskSocket, invert_condition: bool = False):
    """
    Context manager to create a "conditional zone" in the current graph.

    :param condition_socket: A TaskSocket or boolean-like object (e.g. sum_ > 0)
    :param invert_condition: Whether to invert the condition (useful for else-zones)
    """

    graph = get_current_graph()

    zone_task = graph.add_task(
        TaskPool.node_graph.if_zone,
        conditions=condition_socket,
        invert_condition=invert_condition,
    )

    old_zone = getattr(graph, "_active_zone", None)
    if old_zone:
        old_zone.children.add(zone_task)
    graph._active_zone = zone_task

    try:
        yield zone_task
    finally:
        graph._active_zone = old_zone


@contextmanager
def While(condition_socket: TaskSocket, max_iterations: int = 10000):
    """
    Context manager to create a "while zone" in the current graph.

    :param condition_socket: A TaskSocket or boolean-like object (e.g. sum_ > 0)
    :param max_iterations: Maximum number of iterations before breaking the loop
    """

    graph = get_current_graph()

    zone_task = graph.add_task(
        TaskPool.node_graph.while_zone,
        conditions=condition_socket,
        max_iterations=max_iterations,
    )

    old_zone = getattr(graph, "_active_zone", None)
    if old_zone:
        old_zone.children.add(zone_task)
    graph._active_zone = zone_task

    try:
        yield zone_task
    finally:
        graph._active_zone = old_zone
