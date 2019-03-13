# -*- coding: utf-8 -*-
from aiida.engine import calcfunction

a = 1
b = 2
c = 3

@calcfunction
def add(a, b):
    return a + b

@calcfunction
def multiply(a, b):
    return a * b

result = multiply(add(a, b), c)