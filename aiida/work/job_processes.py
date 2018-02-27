# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
import shutil
import sys
import tempfile
import tornado.gen
from voluptuous import Any
from functools import partial

import plumpy
from plumpy.ports import PortNamespace
from aiida.common.datastructures import calc_states
from aiida.common import exceptions
from aiida.common.lang import override
from aiida.daemon import execmanager
from aiida.orm.authinfo import AuthInfo
from aiida.orm.calculation.job import JobCalculation
from aiida.orm.calculation.job import JobCalculationFinishStatus
from aiida.scheduler.datastructures import job_states
from aiida.work.process_spec import DictSchema

from . import processes
from . import utils

__all__ = ['JobProcess']

SUBMIT_COMMAND = 'submit'
UPDATE_SCHEDULER_COMMAND = 'update_scheduler'
RETRIEVE_COMMAND = 'retrieve'


class TransportTaskException(Exception):

    def __init__(self, calc_state):
        self.calc_state = calc_state


class TransportTask(plumpy.Future):
    """ A general task that requires transport """
    def __init__(self, calc_node, transport_queue):
        from aiida.orm.authinfo import AuthInfo

        super(TransportTask, self).__init__()
        self._calc = calc_node
        self._authinfo = AuthInfo.get(
            computer=calc_node.get_computer(),
            user=calc_node.get_user())
        transport_queue.call_me_with_transport(self._authinfo, self._execute)

    def execute(self, transport):
        pass

    def _execute(self, authinfo, transport):
        if not self.cancelled():
            try:
                self.set_result(self.execute(transport))
            except Exception:
                self.set_exc_info(sys.exc_info())


class SubmitJob(TransportTask):
    """ A task to submit a job calculation """

    def execute(self, transport):
        try:
            execmanager.submit_calc(self._calc, self._authinfo, transport)
        except Exception as exception:
            raise TransportTaskException(calc_states.SUBMISSIONFAILED)


class UpdateSchedulerState(TransportTask):
    """ A task to update the scheduler state of a job calculation """

    def execute(self, transport):
        scheduler = self._calc.get_computer().get_scheduler()
        scheduler.set_transport(transport)

        job_id = self._calc.get_job_id()

        kwargs = {'jobs': [job_id], 'as_dict': True}
        if scheduler.get_feature('can_query_by_user'):
            kwargs['user'] = "$USER"
        found_jobs = scheduler.getJobs(**kwargs)

        info = found_jobs.get(job_id, None)
        if info is None:
            # If the job is computed or not found assume it's done
            job_done = True
            self._calc._set_scheduler_state(job_states.DONE)
        else:
            # Has the state changed?
            last_jobinfo = self._calc._get_last_jobinfo()

            execmanager.update_job_calc_from_job_info(self._calc, info)

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

            execmanager.update_job_calc_from_detailed_job_info(self._calc, detailed_job_info)
            self._calc._set_state(calc_states.COMPUTED)

        return job_done


class RetrieveJob(TransportTask):
    """ A task to retrieve a completed calculation """

    def __init__(self, calc_node, transport_queue, retrieved_temporary_folder):
        self._retrieved_temporary_folder = retrieved_temporary_folder
        super(RetrieveJob, self).__init__(calc_node, transport_queue)

    def execute(self, transport):
        """ This returns the retrieved temporary folder """
        try:
            return execmanager.retrieve_all(self._calc, transport, self._retrieved_temporary_folder)
        except Exception as exception:
            raise TransportTaskException(calc_states.RETRIEVALFAILED)


class Waiting(plumpy.Waiting):
    """
    The waiting state for the JobCalculation.
    """
    def __init__(self, process, done_callback, msg=None, data=None):
        super(Waiting, self).__init__(process, done_callback, msg, data)
        self._task = None       # The currently running task
        self._cancelling_future = None

    def enter(self):
        super(Waiting, self).enter()
        self.process.call_soon(self.action_command)

    def load_instance_state(self, saved_state, load_context):
        super(Waiting, self).load_instance_state(saved_state, load_context)
        self._task = None
        self._cancelling_future = None
        self.process.call_soon(self.action_command)

    def exit(self):
        super(Waiting, self).exit()
        if self._cancelling_future and not self._cancelling_future.done():
            self._cancelling_future.set_result(False)

    @tornado.gen.coroutine
    def action_command(self):
        calc = self.process.calc
        transport_queue = self.process.runner.transport

        try:
            if self.data == SUBMIT_COMMAND:
                self._task = SubmitJob(calc, transport_queue)
                yield self._task

                # Now get scheduler updates
                self.scheduler_update()

            elif self.data == UPDATE_SCHEDULER_COMMAND:
                self._task = UpdateSchedulerState(calc, transport_queue)
                job_done = yield self._task

                if job_done:
                    # Done, go on to retrieve
                    self.retrieve()
                else:
                    # Not done yet, keep getting updates
                    self.scheduler_update()

            elif self.data == RETRIEVE_COMMAND:
                # Create a temporary folder that has to be deleted by JobProcess.retrieved after successful parsing
                retrieved_temporary_folder = tempfile.mkdtemp()
                self._task = RetrieveJob(calc, transport_queue, retrieved_temporary_folder)
                yield self._task
                self.retrieved(retrieved_temporary_folder)

            else:
                raise RuntimeError("Unknown waiting command")

        except TransportTaskException as exception:
            # calc._set_state(exception.calc_state)
            finish_status = JobCalculationFinishStatus[exception.calc_state]
            self.finished(finish_status)
        except plumpy.KilledError:
            self.transition_to(processes.ProcessState.KILLED)
            if self._cancelling_future is not None:
                self._cancelling_future.set_result(True)
                self._cancelling_future = None
        except BaseException:
            exc_info = sys.exc_info()
            self.transition_to(processes.ProcessState.EXCEPTED, exc_info[1], exc_info[2])
        finally:
            self._task = None

    def scheduler_update(self):
        self.transition_to(
            processes.ProcessState.WAITING,
            None,
            msg='Waiting for scheduler update',
            data=UPDATE_SCHEDULER_COMMAND)

    def retrieve(self):
        self.transition_to(
            processes.ProcessState.WAITING,
            None,
            msg='Waiting to retrieve',
            data=RETRIEVE_COMMAND)

    def retrieved(self, retrieved_temporary_folder):
        self.transition_to(
            processes.ProcessState.RUNNING,
            self.process.retrieved,
            retrieved_temporary_folder)

    def finished(self, result):
        self.transition_to(processes.ProcessState.FINISHED, result)

    def cancel(self, msg=None):
        if self._cancelling_future is not None:
            return self._cancelling_future
        # Are we currently busy with a task?
        if self._task is not None:
            self._cancelling_future = plumpy.Future()
            self._task.cancel()
            return self._cancelling_future
        else:
            return super(Waiting, self).cancel(msg)


class JobProcess(processes.Process):
    TRANSPORT_OPERATION = 'TRANSPORT_OPERATION'
    CALC_NODE_LABEL = 'calc_node'
    OPTIONS_INPUT_LABEL = 'options'
    _CALC_CLASS = None

    @classmethod
    def build(cls, calc_class):
        from aiida.orm.data import Data
        from aiida.orm.computer import Computer

        def define(cls_, spec):
            super(JobProcess, cls_).define(spec)

            # Calculation options
            options = {
                'max_wallclock_seconds': int,
                'resources': dict,
                'custom_scheduler_commands': basestring,
                'queue_name': basestring,
                'computer': Computer,
                'withmpi': bool,
                'mpirun_extra_params': Any(list, tuple),
                'import_sys_environment': bool,
                'environment_variables': dict,
                'priority': basestring,
                'max_memory_kb': int,
                'prepend_text': basestring,
                'append_text': basestring,
                'parser_name': basestring,
            }
            spec.input(cls.OPTIONS_INPUT_LABEL, validator=DictSchema(options), non_db=True)

            # Inputs from use methods
            for key, use_method in calc_class._use_methods.iteritems():

                valid_type = use_method['valid_types']
                docstring = use_method.get('docstring', None)
                additional_parameter = use_method.get('additional_parameter')

                if additional_parameter:
                    spec.input_namespace(key, help=docstring, valid_type=valid_type, required=False, dynamic=True)
                else:
                    spec.input(key, help=docstring, valid_type=valid_type, required=False)

            # Outputs
            spec.outputs.valid_type = Data

        class_name = "{}_{}".format(cls.__name__, utils.class_name(calc_class))

        # Dynamically create the type for this Process
        return type(
            class_name, (cls,),
            {
                plumpy.Process.define.__name__: classmethod(define),
                '_CALC_CLASS': calc_class
            }
        )

    @classmethod
    def get_state_classes(cls):
        # Overwrite the waiting state
        states_map = super(JobProcess, cls).get_state_classes()
        states_map[processes.ProcessState.WAITING] = Waiting
        return states_map

    # region Process overrides
    @override
    def update_outputs(self):
        # DO NOT REMOVE:
        # Don't do anything, this is taken care of by the job calculation node itself
        pass

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
                getattr(self._calc, 'set_{}'.format(name))(value)

        # Use the use_[x] methods to join up the links in this case
        for name, input_value in self.get_provenance_inputs_iterator():

            port = self.spec().inputs[name]

            if input_value is None or port.non_db:
                continue

            # Call the 'use' methods to set up the data-calc links
            if isinstance(port, PortNamespace):
                additional = self._CALC_CLASS._use_methods[name]['additional_parameter']

                for k, v in input_value.iteritems():
                    try:
                        getattr(self._calc, 'use_{}'.format(name))(v, **{additional: k})
                    except AttributeError:
                        raise AttributeError(
                            "You have provided for an input the key '{}' but"
                            "the JobCalculation has no such use_{} method".format(name, name))

            else:
                getattr(self._calc, 'use_{}'.format(name))(input_value)

        # Get the computer from the code if necessary
        if self._calc.get_computer() is None and 'code' in self.inputs:
            code = self.inputs['code']
            if not code.is_local():
                self._calc.set_computer(code.get_remote_computer())

        parent_calc = self.get_parent_calc()
        if parent_calc:
            self._calc.add_link_from(parent_calc, 'CALL', LinkType.CALL)

        self._add_description_and_label()

    # endregion

    @override
    def run(self):
        """
        Run the calculation, we put it in the TOSUBMIT state and then wait for it
        to be copied over, submitted, retrieved, etc.
        """
        calc_state = self.calc.get_state()

        if calc_state != calc_states.NEW:
            raise exceptions.InvalidOperation(
                'Cannot submit a calculation not in {} state (the current state is {})'.format(
                    calc_states.NEW, calc_state
                ))

        self.calc._set_state(calc_states.TOSUBMIT)

        # Launch the submit operation
        return plumpy.Wait(msg='Waiting to submit', data=SUBMIT_COMMAND)

    def retrieved(self, retrieved_temporary_folder=None):
        """
        Parse a retrieved job calculation.  This is called once it's finished waiting
        for the calculation to be finished and the data has been retrieved.
        """
        try:
            exit_code = execmanager.parse_results(self.calc, retrieved_temporary_folder)
        except BaseException:
            try:
                self.calc._set_state(calc_states.PARSINGFAILED)
            except exceptions.ModificationNotAllowed:
                pass
            raise
        finally:
            # Delete the temporary folder
            shutil.rmtree(retrieved_temporary_folder)

        # Finally link up the outputs and we're done
        for label, node in self.calc.get_outputs_dict().iteritems():
            self.out(label, node)

        return exit_code


class ContinueJobCalculation(JobProcess):

    @classmethod
    def define(cls, spec):
        super(ContinueJobCalculation, cls).define(spec)
        spec.input('_calc', valid_type=JobCalculation, required=True, non_db=False)

    def run(self):
        state = self.calc.get_state()

        if state == calc_states.NEW:
            return super(ContinueJobCalculation, self).run()

        if state in [calc_states.TOSUBMIT, calc_states.SUBMITTING]:
            return plumpy.Wait(msg='Waiting to submit', data=SUBMIT_COMMAND)

        elif state in calc_states.WITHSCHEDULER:
            return plumpy.Wait(msg='Waiting for scheduler', data=UPDATE_SCHEDULER_COMMAND)

        elif state in [calc_states.COMPUTED, calc_states.RETRIEVING]:
            return plumpy.Wait(msg='Waiting to retrieve', data=RETRIEVE_COMMAND)

        elif state == calc_states.PARSING:
            return self.retrieved(True)

            # Otherwise nothing to do...

    def get_or_create_db_record(self):
        return self.inputs._calc
