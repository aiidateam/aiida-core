#!/usr/bin/env runaiida
# -*- coding: utf-8 -*-
from __future__ import print_function

from aiida.orm.data.bool import Bool
from aiida.orm.data.float import Float
from aiida.orm.data.int import Int
from aiida.work import run
from simple_parent import SimpleParentWorkChain

if __name__ == '__main__':
    result = run(SimpleParentWorkChain, a=Int(1), b=Float(1.2), c=Bool(True))
    print(result)
    # {u'e': 1.2, u'd': 1, u'f': True}
