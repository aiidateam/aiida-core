# -*- coding: utf-8 -*-
from aiida.backends.utils import load_dbenv, is_dbenv_loaded

__copyright__ = u"Copyright (c), This file is part of the AiiDA platform. For further information please visit http://www.aiida.net/. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file."
__authors__ = "The AiiDA team."
__version__ = "0.7.1.1"

if not is_dbenv_loaded():
    load_dbenv()

import aiida.workflows2.wf as wf
from aiida.workflows2.run import async
from aiida.workflows2.db_types import to_db_type
from aiida.workflows2.process import Process
from aiida.workflows2.workflow import Workflow


def add(a, b):
    return a + b


def multiply(a, b):
    return a * b


@wf.wf
def add_wf(a, b):
    return {'value': to_db_type(a.value + b.value)}


@wf.wf
def muliply_wf(a, b):
    return {'value': to_db_type(a.value * b.value)}


@wf.wf
def add_multiply_wf(a, b, c):
    return muliply_wf(add_wf(a, b)['value'], c)


class Add(Process):
    @staticmethod
    def _define(spec):
        spec.input('a', default=0)
        spec.input('b', default=0)
        spec.output('value')

    def _run(self, a, b):
        self._out('value', to_db_type(a.value + b.value))


class Mul(Process):
    @staticmethod
    def _define(spec):
        spec.input('a', default=1)
        spec.input('b', default=1)
        spec.output('value')

    def _run(self, a, b):
        self._out('value', to_db_type(a.value * b.value))


class MulAdd(Workflow):
    @staticmethod
    def _define(spec):
        spec.process(Mul)
        spec.process(Add)

        spec.exposed_inputs('Add')
        spec.exposed_outputs('Mul')
        spec.input('c')

        spec.link(':c', 'Mul:a')
        spec.link('Add:value', 'Mul:b')


if __name__ == '__main__':
    two = to_db_type(2)
    three = to_db_type(3)
    four = to_db_type(4)

    print "WORKFUNCTION:"
    simpledata = async(add_multiply_wf, two, three, four).result()['value']
    print "output pk:", simpledata.pk
    print "output value:", simpledata.value

    print "PROCESS:"
    simpledata = MulAdd.run(inputs={'a': two, 'b': three, 'c': four})['value']
    print "output pk:", simpledata.pk
    print "output value:", simpledata.value
