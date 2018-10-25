# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""
This file provides very simple workflows for testing purposes.
Do not delete, otherwise 'verdi developertest' will stop to work.
"""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import
import plumpy
from aiida.orm.workflow import Workflow


class WFTestEmpty(Workflow):
    """
    Empty workflow, just for testing
    """

    def __init__(self, **kwargs):
        super(WFTestEmpty, self).__init__(**kwargs)


class WFTestSimple(Workflow):
    def __init__(self, **kwargs):
        super(WFTestSimple, self).__init__(**kwargs)

    @Workflow.step
    def start(self):
        # Testing calculations
        self.attach_calculation(generate_calc(self))

        # Test process
        self.next(self.second_step)

    @Workflow.step
    def second_step(self):
        self.next(self.exit)


class FailingWFTestSimple(WFTestSimple):
    @Workflow.step
    def start(self):
        # Testing calculations
        self.attach_calculation(self.generate_calc(self))

        # Test process
        self.next(self.second_step)

    @Workflow.step
    def second_step(self):
        # Testing calculations
        self.attach_calculation(generate_calc(self))
        # Raise a test exception that should make the workflow to stop
        raise Exception('Test exception')

        # Test process
        self.next(self.third_step)

    @Workflow.step
    def third_step(self):
        self.next(self.exit)


class FailingWFTestSimpleWithSubWF(Workflow):
    def __init__(self, **kwargs):
        super(FailingWFTestSimpleWithSubWF, self).__init__(**kwargs)

    @Workflow.step
    def start(self):
        self.attach_calculation(generate_calc(self))

        # Create two subworkflows
        w = FailingWFTestSimple()
        w.start()
        self.attach_workflow(w)

        w = FailingWFTestSimple()
        w.start()
        self.attach_workflow(w)

        self.next(self.second)

    @Workflow.step
    def second(self):
        self.next(self.exit)


class WFTestSimpleWithSubWF(Workflow):
    def __init__(self, **kwargs):
        super(WFTestSimpleWithSubWF, self).__init__(**kwargs)

    @Workflow.step
    def start(self):
        self.attach_calculation(generate_calc(self))

        # Create two subworkflows
        w = WFTestSimple()
        w.start()
        self.attach_workflow(w)

        w = WFTestSimple()
        w.start()
        self.attach_workflow(w)

        self.next(self.second)

    @Workflow.step
    def second(self):
        self.next(self.exit)


def generate_calc(workflow):
    from aiida.orm import CalculationFactory
    from aiida.common.datastructures import calc_states

    CustomCalc = CalculationFactory('simpleplugins.templatereplacer')

    computer = workflow.backend.computers.get(name='localhost')

    calc = CustomCalc(computer=computer, withmpi=True)
    calc.set_option('resources',
        {"num_machines": 1, "num_mpiprocs_per_machine": 1})
    calc.store()
    calc._set_state(calc_states.FINISHED)
    calc._set_process_state(plumpy.ProcessState.FINISHED)

    return calc
