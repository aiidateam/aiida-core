#!/usr/bin/env runaiida

from __future__ import print_function

from aiida.orm.data.base import Int, Float, Bool
from aiida.work import run

from simple_parent import SimpleParentWorkChain

if __name__ == '__main__':
    print(run(
        SimpleParentWorkChain,
        a=Int(1), b=Float(1.2), c=Bool(True)
    ))
    # Result: {u'e': 1.2, u'd': 1, u'f': True}
