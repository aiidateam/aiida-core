from aiida import orm, load_profile
from tqdm import tqdm
import math

load_profile()

# Configuration
total_nodes = 40000  # 1 to 32767 inclusive
batch_size = 1000

# Calculate number of batches
num_batches = math.ceil(total_nodes / batch_size)

# Create the group first
group = orm.Group(label='test_adding_many_nodes').store()

print(f"Creating and adding {total_nodes} nodes in batches of {batch_size}...")

# Process nodes in batches
for batch_num in tqdm(range(num_batches), desc="Processing batches"):
    # Calculate start and end indices for this batch
    start_idx = batch_num * batch_size + 1
    end_idx = min((batch_num + 1) * batch_size + 1, total_nodes + 1)
    
    # Create nodes for this batch
    batch_nodes = [orm.Int(i).store() for i in range(start_idx, end_idx)]
    
    # Add the batch to the group
    group.add_nodes(batch_nodes)
    
    # Optional: print batch info
    nodes_in_batch = len(batch_nodes)
    tqdm.write(f"Batch {batch_num + 1}/{num_batches}: Added {nodes_in_batch} nodes "
               f"(nodes {start_idx} to {end_idx - 1})")

print(f"Successfully added all {total_nodes} nodes to group '{group.label}'")
