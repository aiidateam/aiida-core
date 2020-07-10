# -*- coding: utf-8 -*-
from aiida.engine import calcfunction
from aiida.orm import Int

@calcfunction
def sum_and_difference(alpha, beta):
    return {'sum': alpha + beta, 'difference': alpha - beta}

result = sum_and_difference(Int(1), Int(2))
