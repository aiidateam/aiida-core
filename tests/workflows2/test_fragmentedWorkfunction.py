# -*- coding: utf-8 -*-

__copyright__ = u"Copyright (c), This file is part of the AiiDA platform. For further information please visit http://www.aiida.net/. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file."
__version__ = "0.7.1.1"
__authors__ = "The AiiDA team."

from aiida.backends.utils import load_dbenv, is_dbenv_loaded

if not is_dbenv_loaded():
    load_dbenv()

import inspect
from unittest import TestCase
from aiida.workflows2.fragmented_wf import *
from aiida.workflows2.fragmented_wf import _FragmentedWorkfunctionSpec
from aiida.workflows2.db_types import to_db_type
from aiida.workflows2.wf import wf
from aiida.workflows2.run import async
from aiida.orm.data.simple import Str

# This is nasty, use a global variable to track the finishing of steps but in a
# test it's kind of OK.
finished_steps = {}


class Wf(FragmentedWorkfunction):
    finished_steps = {}

    @classmethod
    def _define(cls, spec):
        spec.input("value")
        spec.input("n")
        spec.dynamic_output()
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

    def __init__(self, store_provenance=False):
        super(Wf, self).__init__(store_provenance)
        # Reset the finished step
        self.finished_steps = {
            k: False for k in
            [self.s1.__name__, self.s2.__name__, self.s3.__name__,
             self.s4.__name__, self.s5.__name__, self.s6.__name__,
             self.isA.__name__, self.isB.__name__, self.ltN.__name__]
        }

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


class TestFragmentedWorkfunction(TestCase):
    def test_run(self):
        A = to_db_type('A')
        B = to_db_type('B')
        C = to_db_type('C')
        three = to_db_type(3)

        # Try the if(..) part
        Wf.run(inputs={'value': A, 'n': three})
        # Check the steps that should have been run
        for step, finished in Wf.finished_steps.iteritems():
            if step not in ['s3', 's4', 'isB']:
                self.assertTrue(
                    finished, "Step {} was not called by workflow".format(step))

        # Try the elif(..) part
        finished_steps = Wf.run(inputs={'value': B, 'n': three})
        # Check the steps that should have been run
        for step, finished in finished_steps.iteritems():
            if step not in ['isA', 's2', 's4']:
                self.assertTrue(
                    finished, "Step {} was not called by workflow".format(step))

        # Try the else... part
        finished_steps = Wf.run(inputs={'value': C, 'n': three})
        # Check the steps that should have been run
        for step, finished in finished_steps.iteritems():
            if step not in ['isA', 's2', 'isB', 's3']:
                self.assertTrue(
                    finished, "Step {} was not called by workflow".format(step))

    def test_incorrect_outline(self):
        class Wf(FragmentedWorkfunction):
            @classmethod
            def _define(cls, spec):
                # Try defining an invalid outline
                spec.outline(5)

        with self.assertRaises(ValueError):
            Wf.spec()

    def test_context(self):
        A = Str("a")
        B = Str("b")

        @wf
        def a():
            return A

        @wf
        def b():
            return B

        class Wf(FragmentedWorkfunction):
            @classmethod
            def _define(cls, spec):
                spec.outline(cls.s1, cls.s2, cls.s3)

            def s1(self, ctx):
                fa = async(a)
                fb = async(b)
                return ResultToContext(r1=fa, r2=fb)

            def s2(self, ctx):
                assert ctx.r1['_return'] == A
                assert ctx.r2['_return'] == B
                fb = async(b)
                # Try overwriting r1
                return ResultToContext(r1=fb)

            def s3(self, ctx):
                assert ctx.r1['_return'] == B
                assert ctx.r2['_return'] == B

        Wf.run()

    def test_str(self):
        self.assertIsInstance(str(Wf.spec()), basestring)

    def test_malformed_outline(self):
        spec = _FragmentedWorkfunctionSpec()

        with self.assertRaises(ValueError):
            spec.outline(5)

        with self.assertRaises(ValueError):
            spec.outline(type)
