# -*- coding: utf-8 -*-
from aiida import orm
from aiida.engine import submit

ArithmeticAddCalculation = CalculationFactory('core.arithmetic.add')
inputs = {
    'x': orm.Int(1),
    'y': orm.Int(2)
}
node = submit(ArithmeticAddCalculation, inputs)
