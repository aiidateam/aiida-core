from aiida import orm, plugins
from aiida.engine import submit

ArithmeticAddCalculation = plugins.CalculationFactory('core.arithmetic.add')
inputs = {'x': orm.Int(1), 'y': orm.Int(2)}
node = submit(ArithmeticAddCalculation, inputs)
