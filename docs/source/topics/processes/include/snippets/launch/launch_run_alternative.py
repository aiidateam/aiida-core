# -*- coding: utf-8 -*-
from aiida import orm
from aiida.engine import run_get_node, run_get_pk

ArithmeticAddCalculation = CalculationFactory('arithmetic.add')
result, node = run_get_node(ArithmeticAddCalculation, x=orm.Int(1), y=orm.Int(2))
result, pk = run_get_pk(ArithmeticAddCalculation, x=orm.Int(1), y=orm.Int(2))
