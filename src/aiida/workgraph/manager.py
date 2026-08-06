"""
Simple global variable approach.
Note pitfalls:
    - lack of concurrency control
    - collisions in library code
    - difficulty testing in isolation
    - etc.
"""

from contextlib import contextmanager

from aiida.workgraph.socket import TaskSocket
from aiida.workgraph.tasks.task_pool import TaskPool

DEFAULT_MAP_PLACEHOLDER = 'map_input'


class CurrentGraphManager:
    _instance = None

    def __new__(cls, *args, **kwargs):
        """
        Enforce the singleton pattern. Only one instance of
        CurrentGraphManager is created for the entire process.
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._graph = None  # Storage for the active graph
        return cls._instance

    def get_current_graph(self):
        """
        Retrieve the current graph, or create a new one if none is set.
        """
        from aiida.workgraph import WorkGraph

        if self._graph is None:
            self._graph = WorkGraph()
        return self._graph

    def set_current_graph(self, graph):
        """
        Set the active graph to the given instance.
        """
        self._graph = graph

    @contextmanager
    def active_graph(self, graph):
        """
        Context manager that temporarily overrides the current graph
        with `graph`, restoring the old graph when exiting the context.
        """
        old_graph = self._graph
        self._graph = graph
        try:
            yield graph
        finally:
            self._graph = old_graph


# Create a global manager instance
_manager = CurrentGraphManager()


def get_current_graph():
    """
    Helper function to retrieve the graph
    through the global manager instance.
    """
    return _manager.get_current_graph()


def set_current_graph(graph):
    """
    Helper function to set the graph through the
    global manager instance.
    """
    _manager.set_current_graph(graph)


@contextmanager
def active_graph(graph):
    """
    Top-level context manager that defers to
    the manager's `active_graph` method.
    """
    with _manager.active_graph(graph) as g:
        yield g


@contextmanager
def Zone():
    """
    Context manager to create a "zone" in the current graph.
    """

    wg = get_current_graph()

    zone_task = wg.add_task(
        TaskPool.workgraph.zone,
    )

    old_zone = getattr(wg, '_active_zone', None)
    if old_zone:
        old_zone.children.add(zone_task)
    wg._active_zone = zone_task

    try:
        yield zone_task
    finally:
        wg._active_zone = old_zone


@contextmanager
def If(condition_socket: TaskSocket, invert_condition: bool = False):
    """
    Context manager to create a "conditional zone" in the current graph.

    :param condition_socket: A TaskSocket or boolean-like object (e.g. sum_ > 0)
    :param invert_condition: Whether to invert the condition (useful for else-zones)
    """

    wg = get_current_graph()

    zone_task = wg.add_task(
        TaskPool.workgraph.if_zone,
        conditions=condition_socket,
        invert_condition=invert_condition,
    )

    old_zone = getattr(wg, '_active_zone', None)
    if old_zone:
        old_zone.children.add(zone_task)
    wg._active_zone = zone_task

    try:
        yield zone_task
    finally:
        wg._active_zone = old_zone


@contextmanager
def While(condition_socket: TaskSocket, max_iterations: int = 10000):
    """
    Context manager to create a "while zone" in the current graph.

    :param condition_socket: A TaskSocket or boolean-like object (e.g. sum_ > 0)
    :param max_iterations: Maximum number of iterations before breaking the loop
    """

    wg = get_current_graph()

    zone_task = wg.add_task(
        TaskPool.workgraph.while_zone,
        conditions=condition_socket,
        max_iterations=max_iterations,
    )

    old_zone = getattr(wg, '_active_zone', None)
    if old_zone:
        old_zone.children.add(zone_task)
    wg._active_zone = zone_task

    try:
        yield zone_task
    finally:
        wg._active_zone = old_zone


@contextmanager
def Map(source_socket: TaskSocket, placeholder: str = DEFAULT_MAP_PLACEHOLDER):
    """
    Context manager to create a "map zone" in the current graph.

    :param source_socket: A TaskSocket or boolean-like object (e.g. sum_ > 0)
    :param placeholder: The placeholder string to use as the input for the mapped tasks
    """

    wg = get_current_graph()

    zone_task = wg.add_task(
        TaskPool.workgraph.map_zone,
        source=source_socket,
    )

    old_zone = getattr(wg, '_active_zone', None)
    if old_zone:
        old_zone.children.add(zone_task)
    wg._active_zone = zone_task

    try:
        yield zone_task
    finally:
        wg._active_zone = old_zone
