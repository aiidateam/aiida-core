from aiida import orm, plugins
from aiida.engine import submit

ArithmeticAddCalculation = plugins.CalculationFactory('core.arithmetic.add')
inputs = {'x': orm.Int(value=1), 'y': orm.Int(value=2)}
node = submit(ArithmeticAddCalculation, inputs)
