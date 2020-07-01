# -*- coding: utf-8 -*-
from aiida.engine import calcfunction
from aiida.orm import Int

@calcfunction
def add(x, y):
    result = Int(x + y).store()
    return result

result = add(Int(1), Int(2))
