from aiida.engine import calcfunction
from aiida.orm import Int, load_node


@calcfunction
def add(x, y):
    result = load_node(100)
    return result


result = add(Int(value=1), Int(value=2))
