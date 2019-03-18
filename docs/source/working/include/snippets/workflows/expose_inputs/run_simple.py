#!/usr/bin/env runaiida
# -*- coding: utf-8 -*-
from __future__ import print_function

from aiida.orm import Bool, Float, Int
from aiida.engine import run
from simple_parent import SimpleParentWorkChain

if __name__ == '__main__':
    result = run(SimpleParentWorkChain, a=Int(1), b=Float(1.2), c=Bool(True))
    print(result)
    # {u'e': 1.2, u'd': 1, u'f': True}
