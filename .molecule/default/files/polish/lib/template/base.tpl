# -*- coding: utf-8 -*-
from numpy import prod
from copy import deepcopy
from aiida.engine import submit, WorkChain, if_, while_, append_, ToContext, calcfunction
from aiida.orm import AbstractCode, Int, Str, Dict
from aiida.plugins import CalculationFactory


ArithmeticAddCalculation = CalculationFactory('core.arithmetic.add')


def get_default_options(num_machines=1, max_wallclock_seconds=1800):
    """
    Return an instance of the options dictionary with the minimally required parameters
    for a CalcJobs and set to default values unless overriden

    :param num_machines: set the number of nodes, default=1
    :param max_wallclock_seconds: set the maximum number of wallclock seconds, default=1800
    """
    return {
        'resources': {
            'num_machines': int(num_machines)
        },
        'max_wallclock_seconds': int(max_wallclock_seconds),
    }


@calcfunction
def add_modulo(x, y, modulo):
    return (x + y) % modulo

@calcfunction
def subtract_modulo(x, y, modulo):
    return (x - y) % modulo
