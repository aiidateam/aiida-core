from pydantic import BaseModel

from aiida.calculations.arithmetic.add import ArithmeticAddCalculation
from aiida.workgraph import Task, task


class BlobModel(BaseModel):
    model_config = {'leaf': True}  # always a leaf blob

    a: int
    b: int


class AnotherModel(BaseModel):
    a: int
    b: int


@task
def add(x, y):
    """Add two numbers."""
    return x + y


@task
def multiply(x, y):
    """Multiply two numbers."""
    return x * y


def handle_negative_sum(task: Task):
    """Handle negative sum by resetting the task and changing the inputs.
    self is the WorkGraph instance, thus we can access the tasks and the context.
    """
    from aiida import orm

    # modify task inputs
    task.set_inputs(
        {
            'x': orm.Int(abs(task.inputs.x.value)),
            'y': orm.Int(abs(task.inputs.y.value)),
        }
    )
    msg = 'Run error handler: handle_negative_sum.'
    return msg


BaseAddTask = task(
    error_handlers={
        'handle_negative_sum': {
            'executor': handle_negative_sum,
            'exit_codes': [
                ArithmeticAddCalculation.exit_codes.ERROR_NEGATIVE_NUMBER.status,
            ],
            'max_retries': 5,
            'kwargs': {},
        }
    }
)(ArithmeticAddCalculation)
