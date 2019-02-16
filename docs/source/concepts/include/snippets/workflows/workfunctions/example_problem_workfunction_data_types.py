# -*- coding: utf-8 -*-
from aiida.orm.nodes.data.int import Int
from aiida.work import calcfunction

a = Int(1)
b = Int(2)
c = Int(3)

@calcfunction
def add(a, b):
    return Int(a + b)

@calcfunction
def multiply(a, b):
    return Int(a * b)

result = multiply(add(a, b), c)