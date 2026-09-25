from aiida.engine import Many, each, graph, run, task


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
