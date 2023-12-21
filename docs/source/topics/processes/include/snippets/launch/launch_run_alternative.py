# -*- coding: utf-8 -*-
from aiida import orm, plugins
from aiida.engine import run_get_node, run_get_pk

ArithmeticAddCalculation = plugins.CalculationFactory('core.arithmetic.add')
result, node = run_get_node(ArithmeticAddCalculation, x=orm.Int(1), y=orm.Int(2))
result, pk = run_get_pk(ArithmeticAddCalculation, x=orm.Int(1), y=orm.Int(2))
