# -*- coding: utf-8 -*-
from aiida.engine import calcfunction, run, run_get_node, run_get_pk
from aiida.orm import Int

@calcfunction
def add(x, y):
    return x + y

x = Int(1)
y = Int(2)

result = run(add, x, y)
result, node = run_get_node(add, x, y)
result, pk = run_get_pk(add, x, y)
