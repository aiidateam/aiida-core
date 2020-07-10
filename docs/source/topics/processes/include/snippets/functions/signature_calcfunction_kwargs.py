# -*- coding: utf-8 -*-
from aiida.engine import calcfunction
from aiida.orm import Int

@calcfunction
def add(**kwargs):
    return sum(kwargs.values())

result = add(alpha=Int(1), beta=Int(2), gamma=Int(3))
