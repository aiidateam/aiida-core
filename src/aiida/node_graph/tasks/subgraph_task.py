from __future__ import annotations
from aiida.node_graph.task import Task
from aiida.node_graph.task_spec import TaskSpec


class SubGraphTask(Task):
    """Wrap a Graph instance so it can be used as a Task in a parent graph.

    - Inputs mirror the child graph's *graph_inputs* namespace
    - Outputs mirror the child graph's *graph_outputs* namespace
    - We embed the child graph's serialized dict in metadata for persistence
    """

    identifier = "node_graph.subgraph"
    name = "SubGraphTask"
    task_type = "Normal"
    catalog = "Builtins"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._subgraph = None

    @property
    def subgraph(self):
        from aiida.node_graph import Graph
        from copy import deepcopy

        if not self._subgraph:
            graph_data = deepcopy(self.get_executor().graph_data)
            self._subgraph = Graph.from_dict(graph_data)
        return self._subgraph

    @property
    def tasks(self):
        return self.subgraph.tasks

    @property
    def links(self):
        return self.subgraph.links


def _build_subgraph_task_taskspec(
    graph: "Graph",
    name: str | None = None,
) -> TaskSpec:
    from aiida.node_graph.executor import RuntimeExecutor

    meta = {
        "task_type": "Graph",
    }

    return TaskSpec(
        identifier=graph.name,
        inputs=graph.spec.inputs,
        outputs=graph.spec.outputs,
        executor=RuntimeExecutor.from_graph(graph),
        base_class=SubGraphTask,
        metadata=meta,
    )
