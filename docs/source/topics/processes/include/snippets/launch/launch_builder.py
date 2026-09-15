from aiida import orm, plugins
from aiida.engine import submit

ArithmeticAddCalculation = plugins.CalculationFactory('core.arithmetic.add')

builder = ArithmeticAddCalculation.get_builder()
builder.x = orm.Int(value=1)
builder.y = orm.Int(value=2)

node = submit(builder)
