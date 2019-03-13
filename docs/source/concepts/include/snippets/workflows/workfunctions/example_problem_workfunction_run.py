# -*- coding: utf-8 -*-
from aiida.engine import run_get_node, run_get_pid
from aiida.engine import calcfunction

a = 1
b = 2

@calcfunction
def add(a, b):
    return a + b

# Passing inputs as arguments
result, node = run_get_node(add, a, b)
result, pid = run_get_pid(add, a, b)

# Passing inputs as keyword arguments
result, node = run_get_node(add, a=a, b=b)
result, pid = run_get_pid(add, a=a, b=b)