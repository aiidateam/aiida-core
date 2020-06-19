# -*- coding: utf-8 -*-
from aiida import orm
from aiida.engine import submit

ArithmeticAddCalculation = CalculationFactory('arithmetic.add')
node = submit(ArithmeticAddCalculation, x=orm.Int(1), y=orm.Int(2))
