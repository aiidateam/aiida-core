# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################

import apricotpy
import aiida.work.globals
from aiida.backends.testbase import AiidaTestCase
from aiida.orm.data.base import Int
from aiida.work import workfunction, run, async
from aiida.work.interstep import Action, Assign, Append
from aiida.work.run import RunningInfo, RunningType
from aiida.work.workchain import WorkChain, ToContext, return_, assign_, append_
from aiida.work.workchain import ToContext, Outputs


class TestIntersteps(AiidaTestCase):

    def test_insert_interstep_assign(self):
        val = Int(5)

        @workfunction
        def wf():
            return val

        class Workchain(WorkChain):
            @classmethod
            def define(cls, spec):
                super(Workchain, cls).define(spec)
                spec.outline(cls.run, cls.test)

            def run(self):
                self.insert_intersteps(ToContext(result_a=Outputs(async(wf))))
                self.insert_intersteps(ToContext(result_b=assign_(Outputs(async(wf)))))
                return

            def test(self):
                assert self.ctx.result_a['_return'] == val
                assert self.ctx.result_b['_return'] == val
                return

        run(Workchain)

    def test_insert_interstep_append(self):
        val = Int(5)
    
        @workfunction
        def wf():
            return val
    
        class Workchain(WorkChain):
            @classmethod
            def define(cls, spec):
                super(Workchain, cls).define(spec)
                spec.outline(cls.run, cls.test)
    
            def run(self):
                self.insert_intersteps(ToContext(result_a=append_(Outputs(async(wf)))))
                self.insert_intersteps(ToContext(result_a=append_(Outputs(async(wf)))))
                return
    
            def test(self):
                assert self.ctx.result_a[0]['_return'] == val
                assert len(self.ctx.result_a) == 2
                return
    
        run(Workchain)

    def test_insert_interstep_assign_append(self):
        val = Int(5)
    
        @workfunction
        def wf():
            return val
    
        class Workchain(WorkChain):
            @classmethod
            def define(cls, spec):
                super(Workchain, cls).define(spec)
                spec.outline(cls.run, cls.result)
    
            def run(self):
                self.insert_intersteps(ToContext(result_a=assign_(Outputs(async(wf)))))
                self.insert_intersteps(ToContext(result_a=append_(Outputs(async(wf)))))
                return
    
            def result(self):
                return
    
        with self.assertRaises(TypeError):
            run(Workchain)

    def test_save_load_instance_state_assign(self):

        pid = 1000
        key = 'testing'
        function_string = 'test'

        running = RunningInfo(RunningType.PROCESS, pid)
        action = Action(running, 'test')

        state = apricotpy.Bundle()
        assign_instance = assign_(action).build(key)
        assign_instance.save_instance_state(state)
        assign_recreated = Assign.create_from(state)
        self.assertEqual(assign_instance, assign_recreated)

    def test_save_load_instance_state_append(self):

        pid = 1000
        key = 'testing'
        function_string = 'test'

        running = RunningInfo(RunningType.PROCESS, pid)
        action = Action(running, 'test')

        state = apricotpy.Bundle()
        append_instance = append_(action).build(key)
        append_instance.save_instance_state(state)
        append_recreated = Append.create_from(state)
        self.assertEqual(append_instance, append_recreated)