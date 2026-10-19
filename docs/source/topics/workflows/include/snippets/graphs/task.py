from aiida.engine import task_source


@task_source
def add(x: int, y: int) -> int:
    return x + y


result = add(x=2, y=3)
assert result == 5
