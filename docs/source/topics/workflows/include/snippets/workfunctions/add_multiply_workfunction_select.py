# -*- coding: utf-8 -*-
from aiida.engine import workfunction
from aiida.orm import Int

@workfunction
def maximum(x, y, z):
    return sorted([x, y, z])[-1]

result = maximum(Int(1), Int(2), Int(3))
