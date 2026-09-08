from aiida.node_graph.registry import EntryPointPool

# global instance
SocketPool = EntryPointPool(entry_point_group="node_graph.socket")
SocketPool["any"] = SocketPool.node_graph.any
SocketPool["namespace"] = SocketPool.node_graph.namespace
