from aiida.engine import task


@task(outputs=['total', 'product'])
def sum_product(x: int, y: int) -> tuple[int, int]:
    return x + y, x * y


results = sum_product(x=2, y=3)
