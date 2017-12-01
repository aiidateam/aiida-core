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
from aiida.orm.data.base import Float, Int
from aiida.work.workfunction import workfunction

"""
This example implements exactly the same functionality as seen in the basic WorkChain
example, except in this case it utilizes workfunctions instead of workchains.
"""


@workfunction
def sum(a, b):
    return a + b


@workfunction
def product(a, b):
    return a * b


@workfunction
def sumproduct(a, b, c):
    return product(sum(a, b), c)


def main():
    a = Float(3.14)
    b = Int(4)
    c = Int(6)

    results = sum(a, b)
    print 'Result of sum: {}'.format(results)

    results = product(a, b)
    print 'Result of product: {}'.format(results)

    results = sumproduct(a, b, c)
    print 'Result of sumproduct: {}'.format(results)


if __name__ == '__main__':
    main()