# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################

import plum.port as port
import plum.process
import plum.util
from aiida.common.lang import override
from aiida.work.process import Process, DictSchema
from voluptuous import Any



class JobProcess(Process):
    CALC_NODE_LABEL = 'calc_node'
    OPTIONS_INPUT_LABEL = '_options'
    _CALC_CLASS = None

    @classmethod
    def build(cls, calc_class):
        from aiida.orm.data import Data
        from aiida.orm.computer import Computer

        def define(cls_, spec):
            super(JobProcess, cls_).define(spec)

            # Calculation options
            options = {
                "max_wallclock_seconds": int,
                "resources": dict,
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

        class_name = "{}_{}".format(
            JobProcess.__name__, plum.util.fullname(calc_class))
        return type(class_name, (JobProcess,),
                    {
                        Process.define.__name__: classmethod(define),
                        '_CALC_CLASS': calc_class
                    })

    @override
    def _run(self, **kwargs):
        from aiida.work.legacy.wait_on import wait_on_job_calculation

        # Create this wait_on here because there is a check to make sure the
        # callback function is defined correctly which may cause an assertion, in which
        # case we shouldn't submit
        wait_on = wait_on_job_calculation(
            self.calculation_finished, self.calc.pk)
        self.calc.submit()
        return wait_on

    def calculation_finished(self, wait_on):
        """
        The callback function that is called when the remote calculation
        is finished.

        :param wait_on: The original WaitOnJobCalculation object.
        :type wait_on: :class:`aiida.work.legacy.wait_on.WaitOnJobCalculation`
        """
        assert not self.calc._is_running()

        for label, node in self.calc.get_outputs_dict().iteritems():
            self.out(label, node)

    @override
    def create_db_record(self):
        return self._CALC_CLASS()

    @override
    def _on_output_emitted(self, output_port, value, dynamic):
        # Skip over parent _on_output_emitted because it will try to store stuff
        # which is already done for us by the Calculation
        plum.process.Process._on_output_emitted(
            self, output_port, value, dynamic)

    @override
    def _setup_db_record(self):
        """
        Link up all the retrospective provenance for this JobCalculation
        """
        from aiida.common.links import LinkType

        parent_calc = self.get_parent_calc()

        # Set all the attributes using the setter methods
        for name, value in self.inputs.get(self.OPTIONS_INPUT_LABEL, {}).iteritems():
            if value is not None:
                getattr(self._calc, "set_{}".format(name))(value)

        # First get a dictionary of all the inputs to link, this is needed to
        # deal with things like input groups
        to_link = {}
        for name, input in self.get_provenance_inputs_iterator():
            if input is None or name is self.OPTIONS_INPUT_LABEL:
                continue

            # Call the 'use' methods to set up the data-calc links
            if self.spec().has_input(name) and \
                isinstance(self.spec().get_input(name), port.InputGroupPort):
                additional =\
                    self._CALC_CLASS._use_methods[name]['additional_parameter']

                for k, v in input.iteritems():
                    try:
                        getattr(self._calc,
                            'use_{}'.format(name))(v, **{additional: k})
                    except AttributeError as exception:
                        raise AttributeError("You have provided for an input the key '{}' but"
                            "the JobCalculation has no such use_{} method".format(name, name))


            else:
                getattr(self._calc, 'use_{}'.format(name))(input)

        # Get the computer from the code if necessary
        if self._calc.get_computer() is None and 'code' in self.inputs:
            code = self.inputs['code']
            if not code.is_local():
                self._calc.set_computer(code.get_remote_computer())

        if parent_calc:
            self._calc.add_link_from(parent_calc, "CALL", LinkType.CALL)
