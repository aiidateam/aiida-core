# -*- coding: utf-8 -*-
from aiida.engine import ExitCode, calcfunction
from aiida.orm import Int


@calcfunction
def divide(x, y):
    if y == 0:
        return ExitCode(300, 'cannot divide by 0')

    return x / y


result = divide(Int(1), Int(0))
