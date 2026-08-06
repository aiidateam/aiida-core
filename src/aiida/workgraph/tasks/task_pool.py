from node_graph.registry import EntryPointPool

# global instance
TaskPool = EntryPointPool(entry_point_group='aiida_workgraph.task')
TaskPool['any'] = TaskPool.workgraph.any
TaskPool['graph_level'] = TaskPool.workgraph.graph_level
