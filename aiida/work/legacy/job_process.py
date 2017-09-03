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

        class_name = "{}_{}".format(cls.__name__, plum.utils.fullname(calc_class))

        # Dynamically create the type for this Process
        return type(class_name, (cls,),
                    {
                        Process.define.__name__: classmethod(define),
                        '_CALC_CLASS': calc_class
                    })

    def __init__(self, inputs, pid=None, logger=None):
        from aiida.backends.utils import get_authinfo

        super(JobProcess, self).__init__(inputs, pid, logger)

        # Everything below here doesn't need to be saved
        self._authinfo = get_authinfo(self.calc.get_computer(), self.calc.get_user())

    # region Process overrides
    @override
    def load_instance_state(self, loop, saved_state, logger=None):
        from aiida.backends.utils import get_authinfo

        super(JobProcess, self).load_instance_state(loop, saved_state, logger)
        self._authinfo = get_authinfo(self.calc.get_computer(), self.calc.get_user())

    @override
    def on_output_emitted(self, output_port, value, dynamic):
        # Skip over parent on_output_emitted because it will try to store stuff
        # which is already done for us by the Calculation
        plum.process.Process.on_output_emitted(self, output_port, value, dynamic)

    @override
    def get_or_create_db_record(self):
        return self._CALC_CLASS()

    @override
    def _setup_db_record(self):
        """
        Link up all the retrospective provenance for this JobCalculation
        """
        from aiida.common.links import LinkType

        # Set all the attributes using the setter methods
        for name, value in self.inputs.get(self.OPTIONS_INPUT_LABEL, {}).iteritems():
            if value is not None:
                getattr(self._calc, "set_{}".format(name))(value)

        # Use the use_[x] methods to join up the links in this case
        for name, input in self.get_provenance_inputs_iterator():
            if input is None or name is self.OPTIONS_INPUT_LABEL:
                continue

            # Call the 'use' methods to set up the data-calc links
            if isinstance(self.spec().get_input(name), port.InputGroupPort):
                additional = \
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

        parent_calc = self.get_parent_calc()
        if parent_calc:
            self._calc.add_link_from(parent_calc, "CALL", LinkType.CALL)

    @override
    def execute(self):
        # Put the calculation in the TOSUBMIT state
        self.calc.submit()

        # Submit the calculation
        return tasks.Await(
            self._calc_submitted,
            self.loop().create(calc_submitter.SubmitCalc, self.calc, self._authinfo)
        )
    # endregion

    def _calc_submitted(self, submit_result):
        return tasks.Await(
            self._scheduler_event_received,
            self.loop().create(event.GetSchedulerEvent, self.calc, self._authinfo)
        )

    def _scheduler_event_received(self, body):
        """
        :param wait_on: :class:`plum.event.WaitOnEvent`
        """
        if body['job_info'] != None:
            computed = update_job_calc_from_job_info(self.calc, body['job_info'])
            if computed:
                # Computed, so get detailed job information
                detailed_info = body.get('detailed_job_info', None)
                if detailed_info:
                    update_job_calc_from_detailed_job_info(self.calc, detailed_info)
            else:
                # Wait for any event from our job
                return tasks.Await(
                    self._scheduler_event_received,
                    self.loop().create(event.GetSchedulerEvent, self.calc, self._authinfo, body['job_info'].job_state)
                )

        # If the job is computed or not found assume it's done
        self.calc._set_scheduler_state(scheduler_states.DONE)
        self.calc._set_state(calc_states.COMPUTED)

        # Next, retrieve the calculation data
        return tasks.Await(
            self._retrieved,
            self.loop().create(calc_submitter.RetrieveCalc, self.calc, self._authinfo)
        )

    def _retrieved(self, result):
        """
        Parse a retrieved job calculation.
        """
        if self.calc.state != calc_states.PARSING:
            self.calc._set_state(calc_states.PARSING)
        try:
            parse_results(self.calc)
        except BaseException:
            try:
                self.calc._set_state(calc_states.PARSINGFAILED)
            except ModificationNotAllowed:
                pass
            raise

        # Finally link up the outputs and we're done
        for label, node in self.calc.get_outputs_dict().iteritems():
            self.out(label, node)


class ContinueJobCalculation(JobProcess):
    ACTIVE_CALC_STATES = [calc_states.TOSUBMIT, calc_states.SUBMITTING,
                          calc_states.WITHSCHEDULER, calc_states.COMPUTED,
                          calc_states.RETRIEVING, calc_states.PARSING]

    @classmethod
    def define(cls, spec):
        super(ContinueJobCalculation, cls).define(spec)
        spec.input("_calc", valid_type=JobCalculation, required=True, non_db=False)

    def execute(self):
        state = self.calc.get_state()
        if state in [calc_states.TOSUBMIT, calc_states.SUBMITTING]:
            return super(ContinueJobCalculation, self).execute()
        elif state in calc_states.WITHSCHEDULER:
            return tasks.Await(
                self._scheduler_event_received,
                self.loop().create(event.GetSchedulerEvent, self.calc, self._authinfo)
            )
        elif state in [calc_states.COMPUTED, calc_states.RETRIEVING]:
            return tasks.Await(
                self._retrieved,
                self.loop().create(calc_submitter.RetrieveCalc, self.calc, self._authinfo)
            )
        elif state is calc_states.PARSING:
            return self._retrieved(True)

        # Otherwise nothing to do...

    @override
    def get_or_create_db_record(self):
        return self.inputs._calc
