import time

from aiida.calculations.arithmetic.add import ArithmeticAddCalculation
from aiida.orm import Int
from aiida.workgraph import task
from aiida.workgraph.socket_spec import namespace

ArithmeticAddTask = task(ArithmeticAddCalculation)


@task
def add(x: Int = 0, y: Int = 0, t: Int = 1) -> Int:
    """Add node."""
    time.sleep(t)
    return x + y


@task
def sum_diff(x: Int = 0, y: Int = 0, t: Int = 1) -> namespace(sum=Int, diff=Int):
    """Add node."""
    time.sleep(t)
    return {'sum': x + y, 'diff': x - y}


@task.pythonjob()
def add_pythonjob(x: int, y: int) -> int:
    return x + y


@task.graph
def Fibonacci(n, a=0, b=1):
    """Fibonacci sequence."""
    if n == 0:
        return a
    if n == 1:
        return b
    return Fibonacci(n=n - 1, a=b, b=add(x=a, y=b).result)
