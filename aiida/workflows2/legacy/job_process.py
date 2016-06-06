# -*- coding: utf-8 -*-

import plum.port as port
from aiida.workflows2.process import Process, DictSchema
from aiida.workflows2.legacy.wait_on import WaitOnJobCalculation
from aiida.orm.computer import Computer
from voluptuous import Any

__copyright__ = u"Copyright (c), This file is part of the AiiDA platform. For further information please visit http://www.aiida.net/.. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file"
__version__ = "0.6.0"
__authors__ = "The AiiDA team."


class JobProcess(Process):
    CALC_NODE_LABEL = 'calc_node'
    OPTIONS_INPUT_LABEL = '_options'
    _CALC_CLASS = None

    @classmethod
    def build(cls, calc_class):

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
            spec.dynamic_output()

        return type(calc_class.__name__, (JobProcess,),
                    {'_define': staticmethod(_define),
                     '_CALC_CLASS': calc_class})

    def __init__(self):
        # Need to tell Process to not create output links as these are
        # created internally by the execution manager
        super(JobProcess, self).__init__(create_output_links=False)

    def _run(self, **kwargs):
        self._current_calc.submit()
        return WaitOnJobCalculation(
            self.calculation_finished.__name__, self._current_calc.pk)

    def calculation_finished(self):
        assert not self._current_calc._is_running()

        for label, node in self._current_calc.get_outputs_dict():
            self.out(label, node)

    def _create_db_record(self):
        return self._CALC_CLASS()

    def _setup_db_record(self, inputs):
        from aiida.common.links import LinkType

        # Link and store the retrospective provenance for this process
        calc = self._create_db_record()  # (unstored)
        assert (not calc.is_stored)

        # Set all the attributes using the setter methods
        for name, value in inputs.get(self.OPTIONS_INPUT_LABEL, {}).iteritems():
            if value is not None:
                getattr(calc, "set_{}".format(name))(value)

        # First get a dictionary of all the inputs to link, this is needed to
        # deal with things like input groups
        to_link = {}
        for name, input in inputs.iteritems():
            if input is None or name is self.OPTIONS_INPUT_LABEL:
                continue

            if isinstance(self.spec().get_input(name), port.InputGroupPort):
                additional =\
                    self._CALC_CLASS._use_methods[name]['additional_parameter']

                for k, v in input.iteritems():
                    getattr(calc, 'use_{}'.format(name))(v, **{additional: k})

            else:
                getattr(calc, 'use_{}'.format(name))(input)

        if calc.get_computer() is None and 'code' in inputs:
            code = inputs['code']
            if not code.is_local():
                calc.set_computer(code.get_remote_computer())

        if self._parent:
            calc.add_link_from(self._parent._current_calc, "CALL", LinkType.CALL)

        self._current_calc = calc
        self._current_calc.store_all()
