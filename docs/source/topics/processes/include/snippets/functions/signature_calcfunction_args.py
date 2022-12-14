# -*- coding: utf-8 -*-
from aiida.engine import calcfunction
from aiida.orm import Int


@calcfunction
def average(*args):
    return sum(args) / len(args)

result = average(*(Int(1), Int(2), Int(3)))
