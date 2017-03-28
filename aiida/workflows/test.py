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
        self.attach_calculation(generate_calc())

        # Test process
        self.next(self.second_step)

    @Workflow.step
    def second_step(self):
        self.next(self.exit)


class WFTestSimpleWithSubWF(Workflow):
    def __init__(self, **kwargs):
        super(WFTestSimpleWithSubWF, self).__init__(**kwargs)

    @Workflow.step
    def start(self):
        self.attach_calculation(generate_calc())

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


def generate_calc():
    from aiida.orm import Code, Computer, CalculationFactory
    from aiida.common.datastructures import calc_states

    CustomCalc = CalculationFactory('simpleplugins.templatereplacer')

    computer = Computer.get("localhost")

    calc = CustomCalc(computer=computer, withmpi=True)
    calc.set_resources(
        {"num_machines": 1, "num_mpiprocs_per_machine": 1})
    calc.store()
    calc._set_state(calc_states.FINISHED)

    return calc