from node_graph.registry import RegistryHub

registry_hub = RegistryHub.from_prefix(
    task_group='aiida_workgraph.task',
    socket_group='aiida_workgraph.socket',
    property_group='aiida_workgraph.property',
    type_mapping_group='aiida_workgraph.type_mapping',
    type_promotion_group='aiida_workgraph.type_promotion',
    identifier_prefix='workgraph',
)

type_mapping = registry_hub.type_mapping
