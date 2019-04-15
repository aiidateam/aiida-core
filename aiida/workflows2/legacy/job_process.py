# -*- coding: utf-8 -*-

import plum.port as port
import plum.process
from aiida.common.lang import override
from aiida.workflows2.process import Process, DictSchema
from voluptuous import Any

__copyright__ = u"Copyright (c), This file is part of the AiiDA platform. For further information please visit http://www.aiida.net/. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file."
__version__ = "0.7.0.1"
__authors__ = "The AiiDA team."


class JobProcess(Process):
    CALC_NODE_LABEL = 'calc_node'
    OPTIONS_INPUT_LABEL = '_options'
    _CALC_CLASS = None

    @classmethod
    def build(cls, calc_class):
        from aiida.orm.data import Data
        from aiida.orm.computer import Computer

        def _define(spec):
            # Calculation options
            options = {
                "max_wallclock_seconds": int,
                "resources": {
                    "num_machines": int,
                    "num_mpiprocs_per_machine": int
                },
                "custom_scheduler_commands": unicode,
                "queue_name": basestring,
                "computer": Computer,
                "withmpi": bool,
                "mpirun_extra_params": Any(list, tuple),
                "import_sys_environment": bool,
                "environment_variables": dict,
                "priority": unicode,
                "max_memory_kb": int,
                "prepend_text": unicode,
                "append_text": unicode,
            }
            spec.input(cls.OPTIONS_INPUT_LABEL, validator=DictSchema(options))

            # Inputs from use methods
            for k, v in calc_class._use_methods.iteritems():
                if v.get('additional_parameter'):
                    spec.input_group(k, help=v.get('docstring', None),
                                     valid_type=v['valid_types'], required=False)
                else:
                    spec.input(k, help=v.get('docstring', None),
                               valid_type=v['valid_types'], required=False)

            # Outputs
            spec.dynamic_output(valid_type=Data)

        return type(calc_class.__name__, (JobProcess,),
                    {'_define': staticmethod(_define),
                     '_CALC_CLASS': calc_class})

    def __init__(self, store_provenance=True):
        # Need to tell Process to not create output links as these are
        # created internally by the execution manager
        super(JobProcess, self).__init__(store_provenance)

    def _run(self, **kwargs):
        from aiida.workflows2.legacy.wait_on import wait_on_job_calculation

        # I create this wait_on here because there is a check to make sure the
        # callback function is defined correctly which may cause an assertion, in which
        # case we shouldn't submit
        wait_on = wait_on_job_calculation(
            self.calculation_finished, self.calc.pk)
        self.calc.submit()
        return wait_on

    def calculation_finished(self, wait_on):
        assert not self.calc._is_running()

        for label, node in self.calc.get_outputs_dict().iteritems():
            self.out(label, node)

        if self.calc.has_failed():
            raise RuntimeError(
                "Calculation (pk={}) failed with state '{}'".
                    format(self.calc.pk, self.calc.get_state()))

    @override
    def _on_output_emitted(self, output_port, value, dynamic):
        # Skip over parent _on_output_emitted because it will try to store stuff
        # which is already done for us by the Calculation
        plum.process.Process._on_output_emitted(
            self, output_port, value, dynamic)

    @override
    def create_db_record(self):
        return self._CALC_CLASS()

    @override
    def _setup_db_record(self):
        from aiida.common.links import LinkType

        parent_calc = self.get_parent_calc()

        # Link and store the retrospective provenance for this process
        calc = self.create_db_record()  # (unstored)
        assert (not calc.is_stored)

        # Set all the attributes using the setter methods
        for name, value in self.inputs.get(self.OPTIONS_INPUT_LABEL, {}).iteritems():
            if value is not None:
                getattr(calc, "set_{}".format(name))(value)

        # First get a dictionary of all the inputs to link, this is needed to
        # deal with things like input groups
        to_link = {}
        for name, input in self.inputs.iteritems():
            if input is None or name is self.OPTIONS_INPUT_LABEL:
                continue

            # Call the 'use' methods to set up the data-calc links
            if isinstance(self.spec().get_input(name), port.InputGroupPort):
                additional =\
                    self._CALC_CLASS._use_methods[name]['additional_parameter']

                for k, v in input.iteritems():
                    getattr(calc, 'use_{}'.format(name))(v, **{additional: k})

            else:
                getattr(calc, 'use_{}'.format(name))(input)

        # Get the computer from the code if necessary
        if calc.get_computer() is None and 'code' in self.inputs:
            code = self.inputs['code']
            if not code.is_local():
                calc.set_computer(code.get_remote_computer())

        if parent_calc:
            calc.add_link_from(parent_calc, "CALL", LinkType.CALL)

        self._calc = calc
