# -*- coding: utf-8 -*-
from aiida import orm, plugins
from aiida.engine import submit

ArithmeticAddCalculation = plugins.CalculationFactory('core.arithmetic.add')
node = submit(ArithmeticAddCalculation, x=orm.Int(1), y=orm.Int(2))
