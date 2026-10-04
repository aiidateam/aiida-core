from aiida.engine import graph_execution as graph
from aiida.engine import rerun_from, run_get_node, tasks
from aiida.engine import task_execution as task


@task(outputs=['total'])
def add(x: int, y: int) -> int:
    return x + y


@graph
def add_twice(x, y):
    return {'total': add(x=add(x=x, y=y).total, y=y).total}


results, node = run_get_node(add_twice, x=1, y=2)

# Every task is a process of its own, reached by the name the graph gave it.
first = tasks(node)['add']
print(first.outputs.total.value, first.pk)

# Run it again, taking what has not changed from the cache. Naming nothing takes
# whatever did not finish well, which is what a graph that stopped is run again for.
rerun_from(node, 'add')
