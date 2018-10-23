#!/usr/bin/env runaiida
# -*- coding: utf-8 -*-
from __future__ import print_function

from aiida.orm.data.bool import Bool
from aiida.orm.data.float import Float
from aiida.orm.data.int import Int
from aiida.work import run
from complex_parent import ComplexParentWorkChain

if __name__ == '__main__':
    result = run(
        ComplexParentWorkChain,
        a=Int(1),
        child_1=dict(b=Float(1.2), c=Bool(True)),
        child_2=dict(b=Float(2.3), c=Bool(False))
    )
    print(result)
    # {
    #     u'e': 1.2,
    #     u'child_1.d': 1, u'child_1.f': True,
    #     u'child_2.d': 1, u'child_2.f': False
    # }
