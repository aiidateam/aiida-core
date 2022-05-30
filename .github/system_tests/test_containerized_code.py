import os
from aiida import orm
from aiida.engine import run_get_node
from aiida.plugins import CalculationFactory

ArithmeticAddCalculation = CalculationFactory('core.arithmetic.add') 

inputs = {
    'code': orm.load_code('add-docker@localhost'),
    'x': orm.Int(4),
    'y': orm.Int(6),
    'metadata': {
        'options': {
            'resources': {
                'num_machines': 1,
                'num_mpiprocs_per_machine': 1
            }
        }
    }
}

res, node = run_get_node(ArithmeticAddCalculation, **inputs)
assert 'sum' in res
assert 'remote_folder' in res
assert 'retrieved' in res
assert res['sum'].value == 10
