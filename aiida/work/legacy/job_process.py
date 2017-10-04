# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
from functools import partial
import plum
import plum.port as port
from voluptuous import Any

from aiida.backends.utils import get_authinfo
from aiida.common.datastructures import calc_states
from aiida.common.lang import override
from aiida.common import exceptions
from aiida.daemon import execmanager
from aiida.orm.calculation.job import JobCalculation
from aiida.scheduler.datastructures import job_states
from aiida.work import process
from aiida.work import utils


class JobProcess(process.Process):
    TRANSPORT_OPERATION = 'TRANSPORT_OPERATION'
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
            spec.input(cls.OPTIONS_INPUT_LABEL, validator=process.DictSchema(options))

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

        class_name = "{}_{}".format(cls.__name__, utils.class_name(calc_class))

        # Dynamically create the type for this Process
        return type(class_name, (cls,),
                    {
                        plum.Process.define.__name__: classmethod(define),
                        '_CALC_CLASS': calc_class
                    })

    def __init__(self, inputs, pid=None, logger=None):
        super(JobProcess, self).__init__(inputs, pid, logger)

        self._transport_operation = None

        # Everything below here doesn't need to be saved
        self._authinfo = None

    # region Process overrides
    @override
    def save_instance_state(self, out_state):
        super(JobProcess, self).save_instance_state(out_state)

        if self._transport_operation is not None:
            out_state[self.TRANSPORT_OPERATION] = self._transport_operation

    @override
    def load_instance_state(self, saved_state):
        super(JobProcess, self).load_instance_state(saved_state)

        try:
            self._transport_operation = saved_state[self.TRANSPORT_OPERATION]
            self._relaunch_transport_operation()
        except KeyError:
            self._transport_operation = None

        self._authinfo = None

    @override
    def on_output_emitted(self, output_port, value, dynamic):
        # Skip over parent on_output_emitted because it will try to store stuff
        # which is already done for us by the Calculation
        plum.Process.on_output_emitted(self, output_port, value, dynamic)

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
                        getattr(self._calc, 'use_{}'.format(name))(v, **{additional: k})
                    except AttributeError:
                        raise AttributeError(
                            "You have provided for an input the key '{}' but"
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

        self._add_description_and_label()

    @override
    def _run(self, **kwargs):
        # Put the calculation in the TOSUBMIT state
        self.calc.submit()
        # Launch the submit operation
        return self._submit()

    # endregion

    def _get_authinfo(self):
        if self._authinfo is None:
            self._authinfo = get_authinfo(self.calc.get_computer(), self.calc.get_user())

        return self._authinfo

    # region Functions that require transport

    def _launch_transport_operation(self, operation):
        """
        Schedule a callback to a function that requires transport
        
        :param operation: 
        :return: A future corresponding to the operation 
        """
        self._transport_operation = self.loop().create_future()

        fn = partial(self._do_transport_operation, operation)
        self._callback_handle = self.runner.transport.call_me_with_transport(
            self._get_authinfo(), fn)

        return self._transport_operation

    def _relaunch_transport_operation(self):
        assert self._transport_operation is not None, \
            "Not currently performing transport operation"

        state = self.calc.get_state()
        if state in (calc_states.TOSUBMIT, calc_states.SUBMITTING):
            op = self._submit_with_transport
        elif state == calc_states.WITHSCHEDULER:
            op = self._update_scheduler_state_with_transport
        elif state == calc_states.COMPUTED:
            op = self._retrieve_with_transport
        else:
            raise RuntimeError("Job calculation is not in a state that requires transport")

        fn = partial(self._do_transport_operation, op)
        self._callback_handle = self.runner.transport.call_me_with_transport(
            self._get_authinfo(), fn)

    def _do_transport_operation(self, operation, authinfo, transp):
        self._callback_handle = None

        try:
            result = operation(authinfo, transp)
            self._transport_operation.set_result(result)
        except BaseException as e:
            self._transport_operation.set_exception(e)

    def _submit_with_transport(self, authinfo, transp):
        execmanager.submit_calc(self.calc, authinfo, transp)
        return True

    def _update_scheduler_state_with_transport(self, authinfo, trans):
        """
        Given a transport this method updates the calculation scheduler state.
        
        :param authinfo: The authentication info
        :param trans: The (opened) transport
        :return: True if the job is done, False otherwise 
        """
        scheduler = self.calc.get_computer().get_scheduler()
        scheduler.set_transport(trans)

        job_id = self.calc.get_job_id()

        kwargs = {'jobs': [job_id], 'as_dict': True}
        if scheduler.get_feature('can_query_by_user'):
            kwargs['user'] = "$USER"
        found_jobs = scheduler.getJobs(**kwargs)

        info = found_jobs.get(job_id, None)
        if info is None:
            # If the job is computed or not found assume it's done
            job_done = True
            self.calc._set_scheduler_state(job_states.DONE)
        else:
            # Has the state changed?
            last_jobinfo = self.calc._get_last_jobinfo()

            if info.job_state != last_jobinfo.job_state:
                execmanager.update_job_calc_from_job_info(self.calc, info)

            job_done = info.job_state == job_states.DONE

        if job_done:
            # If the job is done, also get detailed job info
            try:
                detailed_job_info = scheduler.get_detailed_jobinfo(job_id)
            except NotImplementedError:
                detailed_job_info = (
                    u"AiiDA MESSAGE: This scheduler does not implement "
                    u"the routine get_detailed_jobinfo to retrieve "
                    u"the information on "
                    u"a job after it has finished.")

            execmanager.update_job_calc_from_detailed_job_info(self.calc, detailed_job_info)

            self.calc._set_state(calc_states.COMPUTED)

        return job_done

    def _retrieve_with_transport(self, authinfo, transp):
        execmanager.retrieve_all(self.calc, transp)
        return True

    # endregion

    def _submit(self):
        # Submit the calculation
        future = self._launch_transport_operation(self._submit_with_transport)
        return future, self._update_scheduler_state

    def _update_scheduler_state(self, job_done):
        if job_done:
            future = self._launch_transport_operation(self._retrieve_with_transport)
            return future, self._retrieved
        else:
            future = self._launch_transport_operation(self._update_scheduler_state_with_transport)
            return future, self._update_scheduler_state

    def _retrieved(self, result):
        """
        Parse a retrieved job calculation.
        """
        try:
            execmanager.parse_results(self.calc)
        except BaseException:
            try:
                self.calc._set_state(calc_states.PARSINGFAILED)
            except exceptions.ModificationNotAllowed:
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

    def _run(self):
        state = self.calc.get_state()

        if state == calc_states.NEW:
            return super(ContinueJobCalculation, self)._run()

        if state in [calc_states.TOSUBMIT, calc_states.SUBMITTING]:
            return self._submit()

        elif state in calc_states.WITHSCHEDULER:
            return self._update_scheduler_state(job_done=False)

        elif state in [calc_states.COMPUTED, calc_states.RETRIEVING]:
            return self._update_scheduler_state(job_done=True)

        elif state == calc_states.PARSING:
            return self._retrieved(True)

            # Otherwise nothing to do...

    @override
    def get_or_create_db_record(self):
        return self.inputs._calc
