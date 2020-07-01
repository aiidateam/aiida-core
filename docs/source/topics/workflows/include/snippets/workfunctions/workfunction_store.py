# -*- coding: utf-8 -*-
from aiida.engine import workfunction
from aiida.orm import Int

@workfunction
def illegal_workfunction(x, y):
    return Int(x + y)

result = illegal_workfunction(Int(1), Int(2))
