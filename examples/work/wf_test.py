# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
from aiida.backends.utils import load_dbenv, is_dbenv_loaded


if not is_dbenv_loaded():
    load_dbenv()

from aiida.work.workfunction import workfunction
from aiida.orm.data.base import Int
from aiida.work.workchain import WorkChain
from aiida.orm.data.base import NumericType
from aiida.work.run import run


@workfunction
def sum(a, b):
    return a + b


@workfunction
def prod(a, b):
    return a * b


@workfunction
def add_multiply_wf(a, b, c):
    return prod(sum(a, b), c)


class AddMultiplyWf(WorkChain):
    @classmethod
    def define(cls, spec):
        super(WorkChain, cls).define(spec)

        spec.input("a", valid_type=NumericType)
        spec.input("b", valid_type=NumericType)
        spec.input("c", valid_type=NumericType)
        spec.outline(
            cls.sum,
            cls.prod
        )

    def sum(self):
        self.ctx.sum = self.inputs.a + self.inputs.b

    def prod(self):
        self.out(self.ctx.sum * self.inputs.c)


if __name__ == '__main__':
    two = Int(2)
    three = Int(3)
    four = Int(4)

    print "WORKFUNCTION:"

    simpledata = add_multiply_wf(two, three, four)
    print "output pk:", simpledata.pk
    print "output value:", simpledata.value

    print(run(AddMultiplyWf, a=two, b=three, c=four))
