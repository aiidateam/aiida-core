from aiida.engine import branch, run
from aiida.engine import graph_execution as graph
from aiida.engine import task_execution as task


@task(outputs=['total'])
def add(x: int, y: int) -> int:
    return x + y


@graph
def refine_or_not(value, refine_it) -> int:
    with branch(refine_it) as refined:
        refined.returns(total=add(x=value, y=100).total)

    with refined.otherwise:
        refined.returns(total=add(x=value, y=1).total)

    return refined.total


results = run(refine_or_not, value=2, refine_it=True)
