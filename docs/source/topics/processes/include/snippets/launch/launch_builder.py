from aiida import orm, plugins
from aiida.engine import submit

ArithmeticAddCalculation = plugins.CalculationFactory('core.arithmetic.add')

builder = ArithmeticAddCalculation.get_builder()
builder.x = orm.Int(1)
builder.y = orm.Int(2)

node = submit(builder)
