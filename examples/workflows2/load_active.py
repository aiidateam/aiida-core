# -*- coding: utf-8 -*-
from aiida.backends.utils import load_dbenv, is_dbenv_loaded

__copyright__ = u"Copyright (c), This file is part of the AiiDA platform. For further information please visit http://www.aiida.net/. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file."
__authors__ = "The AiiDA team."
__version__ = "0.7.1.1"

if not is_dbenv_loaded():
    load_dbenv()

from aiida.workflows2.persistance.active_factory import load_all_process_records
from aiida.workflows2.process import Process
from aiida.workflows2.workflow import Workflow
from aiida.workflows2.util import load_class
from aiida.workflows2.db_types import to_db_type


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
    # ee = TrackingExecutionEngine()
    #
    # two = to_db_type(2)
    # three = to_db_type(3)
    # four = to_db_type(4)
    #
    # mul_add = MulAdd.create()
    # mul_add.bind('a', two)
    # mul_add.bind('b', three)
    # mul_add.bind('c', four)
    # ee.run(mul_add)

    active = load_all_process_records()
    record = active[0]
    proc = load_class(record.process_class).create()
    proc.continue_from(record)

    simpledata = proc.get_last_outputs()['value']
    print "output pk:", simpledata.pk
    print "output value:", simpledata.value
