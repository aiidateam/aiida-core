from aiida.engine import calcfunction
from aiida.orm import Int


@calcfunction
def add(**kwargs):
    return sum(kwargs.values())


result = add(alpha=Int(value=1), beta=Int(value=2), gamma=Int(value=3))
