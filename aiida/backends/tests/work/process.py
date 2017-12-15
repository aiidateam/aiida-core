# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################


import threading

import aiida.work.utils as util
from aiida.backends.testbase import AiidaTestCase
from aiida.common.lang import override
from aiida.orm import load_node
from aiida.orm.data.base import Int
from aiida.orm.data.frozendict import FrozenDict
from aiida.work.test_utils import DummyProcess, BadOutput
from aiida import work


class ProcessStackTest(work.Process):
    @override
    def _run(self):
        pass

    @override
    def on_create(self):
        super(ProcessStackTest, self).on_create()
        self._thread_id = threading.current_thread().ident

    @override
    def on_stop(self):
        # The therad must match the one used in on_create because process
        # stack is using thread local storage to keep track of who called who
        super(ProcessStackTest, self).on_stop()
        assert self._thread_id is threading.current_thread().ident


class TestProcess(AiidaTestCase):
    def setUp(self):
        super(TestProcess, self).setUp()

        self.assertEquals(len(util.ProcessStack.stack()), 0)

    def tearDown(self):
        super(TestProcess, self).tearDown()

        self.assertEquals(len(util.ProcessStack.stack()), 0)

    def test_process_stack(self):
        work.run(ProcessStackTest)

    def test_inputs(self):
        with self.assertRaises(TypeError):
            work.run(BadOutput)

    def test_input_link_creation(self):
        dummy_inputs = ["1", "2", "3", "4"]

        inputs = {l: Int(l) for l in dummy_inputs}
        inputs['_store_provenance'] = True
        p = DummyProcess(inputs)

        for label, value in p._calc.get_inputs_dict().iteritems():
            self.assertTrue(label in inputs)
            self.assertEqual(int(label), int(value.value))
            dummy_inputs.remove(label)

        # Make sure there are no other inputs
        self.assertFalse(dummy_inputs)

    def test_none_input(self):
        # Check that if we pass no input the process runs fine
        work.run(DummyProcess)

    def test_seal(self):
        pid = work.run_get_pid(DummyProcess).pid
        self.assertTrue(load_node(pk=pid).is_sealed)

    def test_description(self):
        dp = DummyProcess(inputs={'_description': "Rockin' process"})
        self.assertEquals(dp.calc.description, "Rockin' process")

        with self.assertRaises(ValueError):
            DummyProcess(inputs={'_description': 5})

    def test_label(self):
        dp = DummyProcess(inputs={'_label': 'My label'})
        self.assertEquals(dp.calc.label, 'My label')

        with self.assertRaises(ValueError):
            DummyProcess(inputs={'_label': 5})

    def test_work_calc_finish(self):
        p = DummyProcess()
        self.assertFalse(p.calc.has_finished_ok())
        work.run(p)
        self.assertTrue(p.calc.has_finished_ok())

    def test_calculation_input(self):
        @work.workfunction
        def simple_wf():
            return {'a': Int(6), 'b': Int(7)}

        outputs, pid = work.run_get_pid(simple_wf)
        calc = load_node(pid)

        dp = DummyProcess(inputs={'calc': calc})
        work.run(dp)

        input_calc = dp.calc.get_inputs_dict()['calc']
        self.assertTrue(isinstance(input_calc, FrozenDict))
        self.assertEqual(input_calc['a'], outputs['a'])


class TestFunctionProcess(AiidaTestCase):
    def test_fixed_inputs(self):
        def wf(a, b, c):
            return {'a': a, 'b': b, 'c': c}

        inputs = {'a': Int(4), 'b': Int(5), 'c': Int(6)}
        function_process_class = work.FunctionProcess.build(wf)
        self.assertEqual(work.run(function_process_class, **inputs), inputs)

    def test_kwargs(self):
        def wf_with_kwargs(**kwargs):
            return kwargs

        def wf_without_kwargs():
            return Int(4)

        def wf_fixed_args(a):
            return {'a': a}

        a = Int(4)
        inputs = {'a': a}

        function_process_class = work.FunctionProcess.build(wf_with_kwargs)
        outs = work.run(function_process_class, **inputs)
        self.assertEqual(outs, inputs)

        function_process_class = work.FunctionProcess.build(wf_without_kwargs)
        with self.assertRaises(ValueError):
            work.run(function_process_class, **inputs)

        function_process_class = work.FunctionProcess.build(wf_fixed_args)
        outs = work.run(function_process_class, **inputs)
        self.assertEqual(outs, inputs)
