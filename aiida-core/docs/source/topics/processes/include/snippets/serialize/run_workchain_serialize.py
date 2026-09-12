#!/usr/bin/env runaiida
from serialize_workchain import SerializeWorkChain

from aiida.engine import run

if __name__ == '__main__':
    print(run(SerializeWorkChain, a=1, b=1.2, c=True))
    # Result: {'a': 1, 'b': 1.2, 'c': True}
