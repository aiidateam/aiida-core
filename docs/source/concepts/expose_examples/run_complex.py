#!/usr/bin/env runaiida

from __future__ import print_function

from aiida.orm.data.base import Int, Float, Bool
from aiida.work import run

from complex_parent import ComplexParentWorkChain

if __name__ == '__main__':
    print('complex parent:',
        run(
            ComplexParentWorkChain,
            a=Int(1),
            child_1=dict(b=Float(1.2), c=Bool(True)),
            child_2=dict(b=Float(2.3), c=Bool(False))
        )
    )
