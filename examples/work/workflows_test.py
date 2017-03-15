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
from aiida.work.db_types import to_db_type
from aiida.work.process import Process
from aiida.work.workflow import Workflow


def add(a, b):
    return a + b


def multiply(a, b):
    return a * b


@workfunction
def sum(a, b):
    return to_db_type(a.value + b.value)


@workfunction
def prod(a, b):
    return to_db_type(a.value * b.value)


@workfunction
def add_multiply_wf(a, b, c):
    return prod(sum(a, b), c)


class Add(Process):
    @classmethod
    def define(cls, spec):
        spec.input('a', default=0)
        spec.input('b', default=0)
        spec.output('value')

    def _run(self, a, b):
        self.out('value', to_db_type(a.value + b.value))


class Mul(Process):
    @classmethod
    def define(cls, spec):
        spec.input('a', default=1)
        spec.input('b', default=1)
        spec.output('value')

    def _run(self, a, b):
        self.out('value', to_db_type(a.value * b.value))


class MulAdd(Workflow):
    @classmethod
    def define(cls, spec):
        spec.process(Mul)
        spec.process(Add)

        spec.exposed_inputs('Add')
        spec.exposed_outputs('Mul')
        spec.input('c')

        spec.link(':c', 'Mul:a')
        spec.link('Add:value', 'Mul:b')


if __name__ == '__main__':
    two = Int(2)
    three = Int(3)
    four = Int(4)

    print "WORKFUNCTION:"

    simpledata = add_multiply_wf(two, three, four)
    print "output pk:", simpledata.pk
    print "output value:", simpledata.value

    print "PROCESS:"
    outs = MulAdd.run(inputs={'a': two, 'b': three, 'c': four})
    simpledata = outs['value']
    print "output pk:", simpledata.pk
    print "output value:", simpledata.value
