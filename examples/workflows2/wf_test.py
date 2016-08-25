# -*- coding: utf-8 -*-
from aiida.backends.utils import load_dbenv, is_dbenv_loaded

__copyright__ = u"Copyright (c), This file is part of the AiiDA platform. For further information please visit http://www.aiida.net/. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file."
__authors__ = "The AiiDA team."
__version__ = "0.7.0"

if not is_dbenv_loaded():
    load_dbenv()

from aiida.workflows2.wf import wf
from aiida.orm.data.simple import make_int
from aiida.workflows2.fragmented_wf import FragmentedWorkfunction
from aiida.orm.data.simple import NumericType
from aiida.workflows2.run import run

@wf
def sum(a, b):
    return a + b


@wf
def prod(a, b):
    return a * b


@wf
def add_multiply_wf(a, b, c):
    return prod(sum(a, b), c)


class AddMultiplyWf(FragmentedWorkfunction):
    @classmethod
    def _define(cls, spec):
        super(FragmentedWorkfunction, cls)._define(spec)

        spec.input("a", valid_type=NumericType)
        spec.input("b", valid_type=NumericType)
        spec.input("c", valid_type=NumericType)
        spec.outline(
            cls.sum,
            cls.prod
        )

    def sum(self, ctx):
        ctx.sum = self.inputs.a + self.inputs.b

    def prod(self, ctx):
        self.out(ctx.sum * self.inputs.c)



if __name__ == '__main__':
    two = make_int(2)
    three = make_int(3)
    four = make_int(4)

    print "WORKFUNCTION:"

    simpledata = add_multiply_wf(two, three, four)
    print "output pk:", simpledata.pk
    print "output value:", simpledata.value

    print(run(AddMultiplyWf, a=two, b=three, c=four))
