# -*- coding: utf-8 -*-
from aiida.engine import calcfunction
from aiida.orm import Int

@calcfunction
def add(x, y):
    result = load_node(100)
    return result

result = add(Int(1), Int(2))
