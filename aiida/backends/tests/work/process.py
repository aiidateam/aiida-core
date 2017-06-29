# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################


import uuid
import shutil
import tempfile
import threading
import time

import plum.process_monitor
from aiida.backends.testbase import AiidaTestCase
from aiida.orm import load_node
from aiida.orm.data.base import Int
from aiida.orm.data.frozendict import FrozenDict
from aiida.common.lang import override
import aiida.work.globals as globals
from aiida.work.persistence import Persistence
from aiida.work.process import Process, FunctionProcess
from aiida.work.run import run, submit
from aiida.work.workfunction import workfunction
import aiida.work.util as util
from aiida.work.test_utils import DummyProcess, BadOutput


class ProcessStackTest(Process):
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
        self.assertEquals(len(plum.process_monitor.MONITOR.get_pids()), 0)

    def tearDown(self):
        super(TestProcess, self).tearDown()
        procman = globals.get_thread_executor()
        procman.abort_all(timeout=10.)
        self.assertEqual(procman.get_num_processes(), 0, "Failed to abort all processes")
        self.assertEquals(len(util.ProcessStack.stack()), 0)
        self.assertEquals(len(plum.process_monitor.MONITOR.get_pids()), 0)

    def test_process_stack(self):
        ProcessStackTest.run()

    def test_inputs(self):
        with self.assertRaises(TypeError):
            BadOutput.run()

    def test_pid_is_uuid(self):
        p = DummyProcess.new(inputs={'_store_provenance': False})
        self.assertEqual(uuid.UUID(p._calc.uuid), p.pid)

    def test_input_link_creation(self):
        dummy_inputs = ["1", "2", "3", "4"]

        inputs = {l: Int(l) for l in dummy_inputs}
        inputs['_store_provenance'] = True
        p = DummyProcess.new(inputs)

        for label, value in p._calc.get_inputs_dict().iteritems():
            self.assertTrue(label in inputs)
            self.assertEqual(int(label), int(value.value))
            dummy_inputs.remove(label)

        # Make sure there are no other inputs
        self.assertFalse(dummy_inputs)

    def test_none_input(self):
        # Check that if we pass no input the process runs fine
        DummyProcess.new().play()
        # Check that if we explicitly pass None as the input it also runs fine
        DummyProcess.new(inputs=None).play()

    def test_seal(self):
        rinfo = run(DummyProcess, _return_pid=True)[1]
        # This is annoying but have to wait 'cause the sealed attribute
        # sometimes isn't set yet
        time.sleep(0.2)
        self.assertTrue(load_node(pk=rinfo).is_sealed)

        storedir = tempfile.mkdtemp()
        storage = Persistence.create_from_basedir(storedir)

        rinfo = submit(DummyProcess, _jobs_store=storage)
        n = load_node(pk=rinfo.pid)
        self.assertFalse(n.is_sealed)

        dp = DummyProcess.create_from(storage.load_checkpoint(rinfo.pid))
        dp.play()
        self.assertTrue(n.is_sealed)
        shutil.rmtree(storedir)

    def test_description(self):
        dp = DummyProcess.new(inputs={'_description': 'My description'})
        self.assertEquals(dp.calc.description, 'My description')

        with self.assertRaises(ValueError):
            DummyProcess.new(inputs={'_description': 5})

    def test_label(self):
        dp = DummyProcess.new(inputs={'_label': 'My label'})
        self.assertEquals(dp.calc.label, 'My label')

        with self.assertRaises(ValueError):
            DummyProcess.new(inputs={'_label': 5})

    def test_work_calc_finish(self):
        p = DummyProcess.new()
        self.assertFalse(p.calc.has_finished_ok())
        p.play()
        self.assertTrue(p.calc.has_finished_ok())

    def test_calculation_input(self):
        @workfunction
        def simple_wf():
            return {'a': Int(6), 'b': Int(7)}

        outputs, pid = run(simple_wf, _return_pid=True)
        calc = load_node(pid)
        dp = DummyProcess.new(inputs={'calc': calc})
        dp.play()

        input_calc = dp.calc.get_inputs_dict()['calc']
        self.assertTrue(isinstance(input_calc, FrozenDict))
        self.assertEqual(input_calc['a'], outputs['a'])


class TestFunctionProcess(AiidaTestCase):
    def test_fixed_inputs(self):
        def wf(a, b, c):
            return {'a': a, 'b': b, 'c': c}

        inputs = {'a': Int(4), 'b': Int(5), 'c': Int(6)}
        FP = FunctionProcess.build(wf)
        self.assertEqual(FP.run(**inputs), inputs)

    def test_kwargs(self):
        def wf_with_kwargs(**kwargs):
            return kwargs

        def wf_without_kwargs():
            return Int(4)

        def wf_fixed_args(a):
            return {'a': a}

        a = Int(4)
        inputs = {'a': a}

        FP = FunctionProcess.build(wf_with_kwargs)
        outs = FP.run(**inputs)
        self.assertEqual(outs, inputs)

        FP = FunctionProcess.build(wf_without_kwargs)
        with self.assertRaises(ValueError):
            FP.run(**inputs)

        FP = FunctionProcess.build(wf_fixed_args)
        outs = FP.run(**inputs)
        self.assertEqual(outs, inputs)



