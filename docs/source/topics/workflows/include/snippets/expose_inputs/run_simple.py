#!/usr/bin/env runaiida

from simple_parent import SimpleParentWorkChain

from aiida.engine import run
from aiida.orm import Bool, Float, Int

if __name__ == '__main__':
    result = run(SimpleParentWorkChain, a=Int(1), b=Float(1.2), c=Bool(True))
    print(result)
    # {'e': 1.2, 'd': 1, 'f': True}
