#!/usr/bin/env runaiida
# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""
This example implements exactly the same functionality as seen in the basic WorkChain example, except in this case it
utilizes calcfunctions instead of workchains.
"""
from __future__ import division
from __future__ import absolute_import
from __future__ import print_function

from aiida.engine import calcfunction
from aiida.orm import Float, Int


@calcfunction
def sum(a, b):
    return a + b


@calcfunction
def product(a, b):
    return a * b


@calcfunction
def sumproduct(a, b, c):
    return product(sum(a, b), c)


def main():
    a = Float(3.14)
    b = Int(4)
    c = Int(6)

    results = sum(a, b)
    print('Result of sum: {}'.format(results))

    results = product(a, b)
    print('Result of product: {}'.format(results))

    results = sumproduct(a, b, c)
    print('Result of sumproduct: {}'.format(results))


if __name__ == '__main__':
    main()
