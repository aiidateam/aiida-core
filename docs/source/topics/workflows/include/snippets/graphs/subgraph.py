from aiida.engine import graph_execution as graph
from aiida.engine import run, subgraph
from aiida.engine import task_execution as task


@task(outputs=['total'])
def add(x: int, y: int) -> int:
    return x + y


@graph
def add_twice_then_double(x, y):
    with subgraph() as added:
        once = add(x=x, y=y)
        added.returns(total=add(x=once.total, y=y).total)

    return {'total': add(x=added.total, y=added.total).total}


results = run(add_twice_then_double, x=1, y=2)
