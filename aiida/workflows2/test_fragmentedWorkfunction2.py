# -*- coding: utf-8 -*-

__copyright__ = u"Copyright (c), This file is part of the AiiDA platform. For further information please visit http://www.aiida.net/.. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file"
__version__ = "0.6.0"
__authors__ = "The AiiDA team."

from aiida.backends.utils import load_dbenv, is_dbenv_loaded

if not is_dbenv_loaded():
    load_dbenv()

import inspect
from unittest import TestCase
from aiida.workflows2.fragmented_wf2 import *
from aiida.workflows2.db_types import to_db_type


class _Wf(FragmentedWorkfunction2):
    @classmethod
    def _define(cls, spec):
        spec.input("value")
        spec.input("n")
        spec.outline(
            cls.s1,
            if_(cls.isA)(
                cls.s2
            ).elif_(cls.isB)(
                cls.s3
            ).else_(
                cls.s4
            ),
            cls.s5,
            while_(cls.ltN)(
                cls.s6
            ),
        )

    def __init__(self, attributes=None):
        super(_Wf, self).__init__(attributes)
        self.finished_steps = {
            k: False for k in
            [self.s1.__name__, self.s2.__name__, self.s3.__name__,
             self.s4.__name__, self.s5.__name__, self.s6.__name__,
             self.isA.__name__, self.isB.__name__, self.ltN.__name__]
        }

    def all_steps_finished(self):
        return all(self.finished_steps.itervalues())

    def s1(self, ctx):
        self._set_finished(inspect.stack()[0][3])

    def s2(self, ctx):
        self._set_finished(inspect.stack()[0][3])

    def s3(self, ctx):
        self._set_finished(inspect.stack()[0][3])

    def s4(self, ctx):
        self._set_finished(inspect.stack()[0][3])

    def s5(self, ctx):
        self._set_finished(inspect.stack()[0][3])

    def s6(self, ctx):
        ctx.counter = ctx.get('counter', 0) + 1
        self._set_finished(inspect.stack()[0][3])

    def isA(self, ctx):
        self._set_finished(inspect.stack()[0][3])
        return self.inputs.value.value == 'A'

    def isB(self, ctx):
        self._set_finished(inspect.stack()[0][3])
        return self.inputs.value.value == 'B'

    def ltN(self, ctx):
        keep_looping = ctx.get('counter') < self.inputs.n.value
        if not keep_looping:
            self._set_finished(inspect.stack()[0][3])
        return keep_looping

    def _set_finished(self, function_name):
        self.finished_steps[function_name] = True


class TestFragmentedWorkfunction2(TestCase):
    def test__run(self):
        wf = _Wf()

        A = to_db_type('A')
        B = to_db_type('B')
        C = to_db_type('C')
        three = to_db_type(3)

        # Try the if(..) part
        wf.run(inputs={'value': A,'n': three})
        # All steps except s3 and s4 should have finished
        for step, finished in wf.finished_steps.iteritems():
            if step not in ['s3', 's4', 'isB']:
                self.assertTrue(
                    finished, "Step {} was not called by workflow".format(step))

        # Try the elif(..) part
        wf.run(inputs={'value': B, 'n': three})
        # All steps except s3 and s4 should have finished
        for step, finished in wf.finished_steps.iteritems():
            if step not in ['isA', 's2', 's4']:
                self.assertTrue(
                    finished, "Step {} was not called by workflow".format(step))

        # Try the else... part
        wf.run(inputs={'value': C, 'n': three})
        # All steps except s3 and s4 should have finished
        for step, finished in wf.finished_steps.iteritems():
            if step not in ['isA', 's2', 'isB', 's3']:
                self.assertTrue(
                    finished, "Step {} was not called by workflow".format(step))
