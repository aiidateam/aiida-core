from aiida import orm
import time
#
# # Configuration
# # total_nodes = 100_000
# num_nodes = 100_000
#
# # Create the group first
# group = orm.Group(label=f'{num_nodes}-nodes').store()
#
# print(f"Creating and adding {num_nodes} nodes")
#
# # Process nodes in batches
# start_time = time.perf_counter()
#
# all_nodes = [orm.Int(i).store() for i in range(num_nodes)]
#
# node_creation_done = time.perf_counter()
#
# # Add the batch to the group
# group.add_nodes(all_nodes)
#
# end_time = time.perf_counter()
#
# print(f"Successfully added all {num_nodes} nodes to group '{group.label}'")
#
# print(f"Node creation: {node_creation_done-start_time:.1f}")
# print(f"Group addition: {end_time-node_creation_done:.1f}")
# print(f"Total time: {end_time-start_time:.1f}")
# print(f"Time per node: {(end_time-start_time) / num_nodes * 1000:.1f}ms")

nodes = orm.QueryBuilder().append(orm.Int).all(flat=True)
group = orm.load_group(label='mygroup')
breakpoint()
group.add_nodes(nodes)
