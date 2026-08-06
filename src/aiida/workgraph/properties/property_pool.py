from node_graph.registry import EntryPointPool

# global instance
PropertyPool = EntryPointPool(entry_point_group='aiida_workgraph.property')
PropertyPool['any'] = PropertyPool.workgraph.any
