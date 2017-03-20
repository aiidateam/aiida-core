# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################

import aiida.common
from aiida.common import aiidalogger
from aiida.orm.workflow import Workflow
from aiida.orm import Code, Computer


logger = aiidalogger.getChild('WorkflowDemo')


class WorkflowDemo(Workflow):
    def __init__(self, **kwargs):
        super(WorkflowDemo, self).__init__(**kwargs)

    def generate_calc(self):
        from aiida.orm import Code, Computer, CalculationFactory
        from aiida.common.datastructures import calc_states

        CustomCalc = CalculationFactory('simpleplugins.templatereplacer')

        computer = Computer.get("localhost")

        calc = CustomCalc(computer=computer, withmpi=True)
        calc.set_resources({"num_machines": 1, "num_mpiprocs_per_machine": 1})
        calc.store()
        calc._set_state(calc_states.FINISHED)

        return calc

    @Workflow.step
    def start(self):
        from aiida.orm.node import Node

        # Testing parameters
        p = self.get_parameters()

        # Testing calculations
        self.attach_calculation(self.generate_calc())
        self.attach_calculation(self.generate_calc())

        # Testing report
        self.append_to_report("Starting workflow with params: {0}".format(p))

        # Testing attachments
        n = Node().store()
        attrs = {"a": [1, 2, 3], "n": n}
        self.add_attributes(attrs)

        # Test process
        self.next(self.second_step)

    @Workflow.step
    def second_step(self):
        # Test retrieval
        calcs = self.get_step_calculations(self.start)
        self.append_to_report("Retrieved calculation 0 (uuid): {0}".format(calcs[0].uuid))

        # Testing report
        a = self.get_attributes()
        self.append_to_report("Execution second_step with attachments: {0}".format(a))

        # Sleeping for some time
        import time
        time.sleep(10)

        # Test results
        self.add_result("scf_converged", calcs[0])

        self.next(self.exit)


class SubWorkflowDemo(Workflow):
    def __init__(self, **kwargs):
        super(SubWorkflowDemo, self).__init__(**kwargs)

    def generate_calc(self):
        from aiida.orm import Code, Computer, CalculationFactory
        from aiida.common.datastructures import calc_states

        CustomCalc = CalculationFactory('simpleplugins.templatereplacer')

        computer = Computer.get("localhost")

        calc = CustomCalc(computer=computer, withmpi=True)
        calc.set_resources({"num_machines": 1, "num_mpiprocs_per_machine": 1})
        calc.store()
        calc._set_state(calc_states.FINISHED)

        return calc

    @Workflow.step
    def start(self):
        self.attach_calculation(self.generate_calc())

        params = {}
        params['nmachine'] = 2

        # Testing subworkflow with input parameters
        w = WorkflowDemo(params=params)
        w.start()
        self.attach_workflow(w)
        self.append_to_report("Workflow attached: {0}".format(w.uuid))

        params['nmachine'] = 4
        w = WorkflowDemo(params=params)
        w.start()
        self.attach_workflow(w)
        self.append_to_report("Workflow attached: {0}".format(w.uuid))

        self.next(self.second)

    @Workflow.step
    def second(self):
        s_wfs = self.get_step(self.start).get_sub_workflows()

        for s_wf in s_wfs:
            self.append_to_report("Workflow {0} has results {1}".format(s_wf.uuid, s_wf.get_result("scf_converged")))

        self.next(self.exit)

