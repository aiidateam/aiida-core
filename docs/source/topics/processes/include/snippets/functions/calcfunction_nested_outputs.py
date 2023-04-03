# -*- coding: utf-8 -*-
from aiida.engine import calcfunction
from aiida.orm import Int


@calcfunction
def add(alpha, beta):
    return {'nested.sum': alpha + beta}

result = add(Int(1), Int(2))
assert result['nested']['sum'] == 3
