# -*- coding: utf-8 -*-
from aiida.engine import calcfunction

@calcfunction
def add(x, y):
    return x + y

@calcfunction
def multiply(x, y):
    return x * y

result = multiply(add(1, 2), 3)
