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
from aiida.common.datastructures import calc_states
from aiida.scheduler.datastructures import job_states as scheduler_states
from aiida.common.lang import override
from aiida.common.exceptions import ModificationNotAllowed
from aiida.daemon.execmanager import submit_calc, retrieve_all, parse_results, \
    update_job_calc_from_job_info, update_job_calc_from_detailed_job_info
from aiida.orm.calculation.job import JobCalculation
from aiida.work.globals import get_event_emitter
from aiida.work.event import SchedulerEmitter
from aiida.work.process import Process, DictSchema
from aiida.work.wait_ons import WaitForTransport
from aiida.work.util import WithHeartbeat
from plum.event import WaitOnEvent
from plum.persistence import Bundle
from voluptuous import Any



class JobProcess(Process, WithHeartbeat):
    CALC_NODE_LABEL = 'calc_node'
    OPTIONS_INPUT_LABEL = '_options'
    WAITING_ON = 'waiting_on'
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
            cls.__name__, plum.util.fullname(calc_class))
        return type(class_name, (cls,),
                    {
                        Process.define.__name__: classmethod(define),
                        '_CALC_CLASS': calc_class
                    })

    def __init__(self, inputs, pid, logger=None):
        super(JobProcess, self).__init__(inputs, pid, logger)
        # Everything below here doesn't need to be saved
        self.__waiting_on = None
        self._authinfo = None

    # region Process overrides
    @override
    def on_create(self, saved_instance_state):
        from aiida.backends.utils import get_authinfo
        super(JobProcess, self).on_create(saved_instance_state)

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
    def save_wait_on_state(self):
        return Bundle({'waiting_on': self.__waiting_on})

    @override
    def create_wait_on(self, bundle):
        return self._create_wait_on(bundle['waiting_on'])

    @override
    def _run(self, **kwargs):
        self.calc.submit()
        # We need the transport to be able to submit
        return self._create_wait_on('transport'), self._submit_job

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
                    getattr(self._calc,
                            'use_{}'.format(name))(v, **{additional: k})

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

    # endregion

    def _submit_job(self, wait_on):
        """
        :param wait_on: The WaitOnTransport we need to proceed
        :type wait_on: :class:`WaitOnTransport`
        """
        try:
            submit_calc(self.calc, self._authinfo, wait_on.transport)
        finally:
            wait_on.release_transport()

        # Wait for any event from our job
        return self._create_wait_on('scheduler_event'), self._scheduler_event_received

    def _scheduler_event_received(self, wait_on):
        """
        :param wait_on: :class:`plum.event.WaitOnEvent`
        """
        if not wait_on.get_event().endswith(SchedulerEmitter.JOB_NOT_FOUND):
            body = wait_on.get_body()
            computed = update_job_calc_from_job_info(self.calc, body['job_info'])
            if computed:
                # Computed, so get detailed job information
                detailed_info = body.get('detailed_job_info', None)
                if detailed_info:
                    update_job_calc_from_detailed_job_info(self.calc, detailed_info)
            else:
                # Wait for any event from our job
                return self._create_wait_on('scheduler_event'), self._scheduler_event_received

        # If the job is computed or not found assume it's done
        self.calc._set_scheduler_state(scheduler_states.DONE)
        self.calc._set_state(calc_states.COMPUTED)

        # Now we need the transport to be able to retrieve
        return self._create_wait_on('transport'), self._retrieve_and_parse

    def _retrieve_and_parse(self, wait_on):
        """
        Process a computed job.
        """
        try:
            try:
                retrieve_all(self.calc, wait_on.transport)
            except BaseException:
                self.calc._set_state(calc_states.RETRIEVALFAILED)
                raise
        finally:
            # Make sure to always release the transport
            wait_on.release_transport()

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

    def _create_wait_on(self, what):
        if what == 'transport':
            self.__waiting_on = what
            return WaitForTransport(self._authinfo)
        elif what == 'scheduler_event':
            self.__waiting_on = what
            all_events = "job.{}.*".format(self.calc.pk)
            return WaitOnEvent(get_event_emitter(), all_events)
        else:
            raise ValueError("Don't know how to wait on '{}'".format(what))


class ContinueJobCalculation(JobProcess):
    ACTIVE_CALC_STATES = [calc_states.TOSUBMIT, calc_states.SUBMITTING,
                          calc_states.WITHSCHEDULER, calc_states.COMPUTED,
                          calc_states.RETRIEVING, calc_states.PARSING]

    @classmethod
    def define(cls, spec):
        super(ContinueJobCalculation, cls).define(spec)
        spec.input("_calc", valid_type=JobCalculation, required=True)

    def _run(self, **kwargs):
        state = self.calc.get_state()
        if state in [calc_states.TOSUBMIT, calc_states.SUBMITTING]:
            return self._create_wait_on('transport'), self._submit_job
        elif state in calc_states.WITHSCHEDULER:
            return self._create_wait_on('scheduler_event'), self._scheduler_event_received
        elif state in [calc_states.COMPUTED, calc_states.RETRIEVING, calc_states.PARSING]:
            return self._create_wait_on('transport'), self._retrieve_and_parse
            # Otherwise nothing to do...

    @override
    def get_or_create_db_record(self):
        return self.inputs._calc
