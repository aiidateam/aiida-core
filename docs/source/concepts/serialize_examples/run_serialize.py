#!/usr/bin/env runaiida
# -*- coding: utf-8 -*-

from __future__ import print_function

from aiida.engine import run

from serialize_workchain import SerializeWorkChain

if __name__ == '__main__':
    print(run(
        SerializeWorkChain,
        a=1, b=1.2, c=True
    ))
    # Result: {'a': 1, 'b': 1.2, 'c': True}
