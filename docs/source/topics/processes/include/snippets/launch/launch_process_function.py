from aiida.engine import calcfunction
from aiida.orm import Int


@calcfunction
def add(x, y):
    return x + y


x = Int(value=1)
y = Int(value=2)

result = add(x, y)
result, node = add.run_get_node(x, y)
result, pk = add.run_get_pk(x, y)
