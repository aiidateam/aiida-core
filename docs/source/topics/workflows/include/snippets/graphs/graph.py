from aiida.engine import graph_source, run_get_node, task_source


@task_source
def add(x: int, y: int) -> int:
    return x + y


@task_source
def double(value: int) -> int:
    return value * 2


@graph_source
def add_and_double(x: int, y: int) -> int:
    total = add(x=x, y=y)
    return double(value=total)


results, node = run_get_node(add_and_double, x=2, y=3)
assert results['result'] == 10
