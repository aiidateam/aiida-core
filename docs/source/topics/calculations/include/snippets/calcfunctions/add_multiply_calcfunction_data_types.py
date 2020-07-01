# -*- coding: utf-8 -*-
from aiida.engine import calcfunction
from aiida.orm import Int

@calcfunction
def add(x, y):
    return x + y

@calcfunction
def multiply(x, y):
    return x * y

result = multiply(add(Int(1), Int(2)), Int(3))
