from aiida.engine import calcfunction, run
from aiida.orm import Int


@calcfunction
def add(x, y):
    return x + y


inputs = {
    'x': Int(value=1),
    'y': Int(value=2),
    'metadata': {
        'label': 'Some label',
        'description': 'Some description',
    },
}

result = run(add, **inputs)
