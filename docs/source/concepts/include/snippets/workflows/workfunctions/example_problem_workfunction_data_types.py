# -*- coding: utf-8 -*-
from aiida.orm.data.int import Int
from aiida.work.workfunctions import workfunction

a = Int(1)
b = Int(2)
c = Int(3)

@workfunction
def add(a, b):
    return Int(a + b)

@workfunction
def multiply(a, b):
    return Int(a * b)

result = multiply(add(a, b), c)