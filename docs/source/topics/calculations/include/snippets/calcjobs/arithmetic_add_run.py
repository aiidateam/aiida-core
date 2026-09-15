from aiida.engine import run
from aiida.orm import Int, load_code
from aiida.plugins import CalculationFactory

ArithmeticAddCalculation = CalculationFactory('core.arithmetic.add')

inputs = {
    'code': load_code('add@localhost'),
    'x': Int(value=1),
    'y': Int(value=2),
}

run(ArithmeticAddCalculation, **inputs)
