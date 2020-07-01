# -*- coding: utf-8 -*-
from aiida import orm
from aiida.engine import submit

ArithmeticAddCalculation = CalculationFactory('arithmetic.add')

builder = ArithmeticAddCalculation.get_builder()
builder.x = orm.Int(1)
builder.y = orm.Int(2)

node = submit(builder)
