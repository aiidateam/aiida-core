from aiida.engine import calcfunction
from aiida.orm import Int


@calcfunction
def add(x, y):
    return x + y


result, node = add.run_get_node(Int(value=1), Int(value=2))
print(node.function_name)  # add
print(node.function_namespace)  # __main__
print(node.function_starting_line_number)  # 4
