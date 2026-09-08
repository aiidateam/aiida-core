from aiida.node_graph.registry import EntryPointPool

# global instance
TaskPool = EntryPointPool(entry_point_group="node_graph.task")
TaskPool["any"] = TaskPool.node_graph.task
TaskPool["graph_level"] = TaskPool.node_graph.graph_level
