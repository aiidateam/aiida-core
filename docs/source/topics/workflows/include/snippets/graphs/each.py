from aiida.engine import Many, each, run
from aiida.engine import graph_execution as graph
from aiida.engine import task_execution as task


@task(outputs=['shifted'])
def shift(value: int, by: int) -> int:
    return value + by


@task(outputs=['total'])
def total_of(parts: Many[int]) -> int:
    return sum(parts.values())


@graph
def shift_all(values, by):
    shifted = shift(value=each(values), by=by)
    return {'total': total_of(parts=shifted.shifted).total}


results = run(shift_all, values=[1, 2, 3], by=10)
