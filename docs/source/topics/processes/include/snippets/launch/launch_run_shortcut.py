# -*- coding: utf-8 -*-
from aiida import orm, plugins
from aiida.engine import run

ArithmeticAddCalculation = plugins.CalculationFactory('core.arithmetic.add')
result = run(ArithmeticAddCalculation, x=orm.Int(1), y=orm.Int(2))
result, node = run.get_node(ArithmeticAddCalculation, x=orm.Int(1), y=orm.Int(2))
result, pk = run.get_pk(ArithmeticAddCalculation, x=orm.Int(1), y=orm.Int(2))
