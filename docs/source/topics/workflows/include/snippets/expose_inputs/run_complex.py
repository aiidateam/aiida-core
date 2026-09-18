#!/usr/bin/env runaiida

from complex_parent import ComplexParentWorkChain

from aiida.engine import run
from aiida.orm import Bool, Float, Int

if __name__ == '__main__':
    result = run(
        ComplexParentWorkChain,
        a=Int(value=1),
        child_1=dict(b=Float(value=1.2), c=Bool(value=True)),
        child_2=dict(b=Float(value=2.3), c=Bool(value=False)),
    )
    print(result)
    # {
    #     'e': 1.2,
    #     'child_1.d': 1, 'child_1.f': True,
    #     'child_2.d': 1, 'child_2.f': False
    # }
