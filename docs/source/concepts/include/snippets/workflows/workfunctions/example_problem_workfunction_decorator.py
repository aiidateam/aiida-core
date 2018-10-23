# -*- coding: utf-8 -*-
from aiida.work.workfunctions import workfunction

a = 1
b = 2
c = 3

@workfunction
def add(a, b):
    return a + b

@workfunction
def multiply(a, b):
    return a * b

result = multiply(add(a, b), c)