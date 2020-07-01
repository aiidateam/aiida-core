# -*- coding: utf-8 -*-
from aiida.engine import calcfunction
from aiida.orm import Int

@calcfunction
def divide(x, y):
    return x / y

result = divide(Int(1), Int(0))
