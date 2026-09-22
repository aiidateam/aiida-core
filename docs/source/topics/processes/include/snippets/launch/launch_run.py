from aiida import orm, plugins
from aiida.engine import run

ArithmeticAddCalculation = plugins.CalculationFactory('core.arithmetic.add')
result = run(ArithmeticAddCalculation, x=orm.Int(value=1), y=orm.Int(value=2))
