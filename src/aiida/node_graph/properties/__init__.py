from aiida.node_graph.registry import EntryPointPool

# global instance
PropertyPool = EntryPointPool(entry_point_group="node_graph.property")
PropertyPool["any"] = PropertyPool.node_graph.any
