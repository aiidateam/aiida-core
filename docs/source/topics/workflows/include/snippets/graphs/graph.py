from aiida.engine import graph, run, task


@task(outputs=['total'])
def add(x: int, y: int) -> int:
    return x + y


@task(outputs=['doubled'])
def double(value: int) -> int:
    return value * 2


@graph
def add_and_double(x, y):
    return {'doubled': double(value=add(x=x, y=y).total).doubled}


results = run(add_and_double, x=2, y=3)
