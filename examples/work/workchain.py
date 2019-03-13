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
This example illustrates in a very minimal way how a WorkChain can be defined and how it can be run. This mostly
illustrates how the spec of the WorkChain is defined and how functions in the outline of the spec have to be defined.
"""
from __future__ import division
from __future__ import absolute_import
from __future__ import print_function

from aiida.engine import WorkChain, run
from aiida.orm import NumericType, Float, Int


class SumWorkChain(WorkChain):

    @classmethod
    def define(cls, spec):
        super(SumWorkChain, cls).define(spec)
        spec.input('a', valid_type=NumericType)
        spec.input('b', valid_type=NumericType)
        spec.outline(
            cls.sum
        )
        spec.output('sum', valid_type=NumericType)

    def sum(self):
        self.out('sum', self.inputs.a + self.inputs.b)


class ProductWorkChain(WorkChain):

    @classmethod
    def define(cls, spec):
        super(ProductWorkChain, cls).define(spec)
        spec.input('a', valid_type=NumericType)
        spec.input('b', valid_type=NumericType)
        spec.outline(
            cls.product
        )
        spec.output('product', valid_type=NumericType)

    def product(self):
        self.out('product', self.inputs.a * self.inputs.b)


class SumProductWorkChain(WorkChain):

    @classmethod
    def define(cls, spec):
        super(SumProductWorkChain, cls).define(spec)
        spec.input('a', valid_type=NumericType)
        spec.input('b', valid_type=NumericType)
        spec.input('c', valid_type=NumericType)
        spec.outline(
            cls.sum,
            cls.product
        )
        spec.output('sumproduct', valid_type=NumericType)

    def sum(self):
        self.ctx.sum = self.inputs.a + self.inputs.b

    def product(self):
        self.out('sumproduct', self.ctx.sum * self.inputs.c)


def main():
    inputs = {
        'a': Float(3.14),
        'b': Int(4),
        'c': Int(6)
    }

    results = run(SumWorkChain, **inputs)
    print('Result of SumWorkChain: {}'.format(results))

    results = run(ProductWorkChain, **inputs)
    print('Result of ProductWorkChain: {}'.format(results))

    results = run(SumProductWorkChain, **inputs)
    print('Result of SumProductWorkChain: {}'.format(results))


if __name__ == '__main__':
    main()
