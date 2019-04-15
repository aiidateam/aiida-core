# -*- coding: utf-8 -*-
from aiida.backends.utils import load_dbenv, is_dbenv_loaded

__copyright__ = u"Copyright (c), This file is part of the AiiDA platform. For further information please visit http://www.aiida.net/. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file."
__authors__ = "The AiiDA team."
__version__ = "0.7.0.1"

if not is_dbenv_loaded():
    load_dbenv()

from aiida.workflows2.wf import wf
from aiida.orm.data.simple import Int
from aiida.workflows2.db_types import to_db_type, SimpleData
from aiida.workflows2.process import Process
from aiida.workflows2.workflow import Workflow


def add(a, b):
    return a + b


def multiply(a, b):
    return a * b


@wf
def sum(a, b):
    return to_db_type(a.value + b.value)


@wf
def prod(a, b):
    return to_db_type(a.value * b.value)


@wf
def add_multiply_wf(a, b, c):
    return prod(sum(a, b), c)


class Add(Process):
    @classmethod
    def _define(cls, spec):
        spec.input('a', default=0)
        spec.input('b', default=0)
        spec.output('value')

    def _run(self, a, b):
        self.out('value', to_db_type(a.value + b.value))


class Mul(Process):
    @classmethod
    def _define(cls, spec):
        spec.input('a', default=1)
        spec.input('b', default=1)
        spec.output('value')

    def _run(self, a, b):
        self.out('value', to_db_type(a.value * b.value))


class MulAdd(Workflow):
    @classmethod
    def _define(cls, spec):
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
