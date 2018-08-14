# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
import functools
import logging
import shutil
import sys
import tempfile
import traceback
from tornado.gen import coroutine, Return

import plumpy
from plumpy.ports import PortNamespace
from aiida.common.datastructures import calc_states
from aiida.common.exceptions import TransportTaskException
from aiida.common import exceptions
from aiida.common.lang import override
from aiida.daemon import execmanager
from aiida.orm.calculation.job import JobCalculation
from aiida.orm.calculation.job import JobCalculationExitStatus
from aiida.work.process_builder import JobProcessBuilder
from aiida.work.utils import exponential_backoff_retry, interruptable_task

from . import persistence
from . import processes

__all__ = ['JobProcess']

SUBMIT_COMMAND = 'submit'
UPDATE_SCHEDULER_COMMAND = 'update_scheduler'
RETRIEVE_COMMAND = 'retrieve'
KILL_COMMAND = 'kill'


logger = logging.getLogger(__name__)


@coroutine
def task_submit_job(node, transport_queue, cancel_flag):
    """
    Transport task that will attempt to submit a job calculation

    The task will first request a transport from the queue. Once the transport is yielded, the relevant execmanager
    function is called, wrapped in the exponential_backoff_retry coroutine, which, in case of a caught exception, will
    retry after an interval that increases exponentially with the number of retries, for a maximum number of retries.
    If all retries fail, the task will raise a TransportTaskException

    :param node: the node that represents the job calculation
    :param transport_queue: the TransportQueue from which to request a Transport
    :param cancel_flag: the cancelled flag that will be queried to determine whether the task was cancelled
    :raises: Return if the tasks was successfully completed
    :raises: TransportTaskException if after the maximum number of retries the transport task still excepted
    """
    initial_interval = 1
    max_attempts = 5

    authinfo = node.get_computer().get_authinfo(node.get_user())

    @coroutine
    def do_submit():
        with transport_queue.request_transport(authinfo) as request:
            transport = yield request

            # It may have taken time to get the transport, check if we've been cancelled
            if cancel_flag.is_cancelled:
                raise plumpy.CancelledError('task_submit_job for calculation<{}> cancelled'.format(node.pk))

            logger.info('submitting calculation<{}>'.format(node.pk))
            node._set_state(calc_states.SUBMITTING)
            raise Return(execmanager.submit_calculation(node, transport))

    try:
        result = yield exponential_backoff_retry(
            do_submit, initial_interval, max_attempts, logger=node.logger, ignore_exceptions=plumpy.CancelledError)
    except plumpy.CancelledError:
        pass
    except Exception:
        logger.warning('submitting calculation<{}> failed:\n{}'.format(node.pk, traceback.format_exc()))
        node._set_state(calc_states.SUBMISSIONFAILED)
        raise TransportTaskException('submit_calculation failed {} times consecutively'.format(max_attempts))
    else:
        logger.info('submitting calculation<{}> successful'.format(node.pk))
        node._set_state(calc_states.WITHSCHEDULER)
        raise Return(result)


@coroutine
def task_update_job(node, transport_queue, cancel_flag):
    """
    Transport task that will attempt to update the scheduler state of a job calculation

    The task will first request a transport from the queue. Once the transport is yielded, the relevant execmanager
    function is called, wrapped in the exponential_backoff_retry coroutine, which, in case of a caught exception, will
    retry after an interval that increases exponentially with the number of retries, for a maximum number of retries.
    If all retries fail, the task will raise a TransportTaskException

    :param node: the node that represents the job calculation
    :param transport_queue: the TransportQueue from which to request a Transport
    :param cancel_flag: the cancelled flag that will be queried to determine whether the task was cancelled
    :raises: Return if the tasks was successfully completed
    :raises: TransportTaskException if after the maximum number of retries the transport task still excepted
    """
    initial_interval = 1
    max_attempts = 5

    authinfo = node.get_computer().get_authinfo(node.get_user())

    @coroutine
    def do_update():
        with transport_queue.request_transport(authinfo) as request:
            transport = yield request

            # It may have taken time to get the transport, check if we've been cancelled
            if cancel_flag.is_cancelled:
                raise plumpy.CancelledError('task_update_job for calculation<{}> cancelled'.format(node.pk))

            logger.info('updating calculation<{}>'.format(node.pk))
            raise Return(execmanager.update_calculation(node, transport))

    try:
        result = yield exponential_backoff_retry(
            do_update, initial_interval, max_attempts, logger=node.logger, ignore_exceptions=plumpy.CancelledError)
    except plumpy.CancelledError:
        pass
    except Exception:
        logger.warning('updating calculation<{}> failed:\n{}'.format(node.pk, traceback.format_exc()))
        node._set_state(calc_states.FAILED)
        raise TransportTaskException('update_calculation failed {} times consecutively'.format(max_attempts))
    else:
        logger.info('updating calculation<{}> successful'.format(node.pk))
        if result:
            node._set_state(calc_states.COMPUTED)
        raise Return(result)


@coroutine
def task_retrieve_job(node, transport_queue, retrieved_temporary_folder, cancel_flag):
    """
    Transport task that will attempt to retrieve all files of a completed job calculation

    The task will first request a transport from the queue. Once the transport is yielded, the relevant execmanager
    function is called, wrapped in the exponential_backoff_retry coroutine, which, in case of a caught exception, will
    retry after an interval that increases exponentially with the number of retries, for a maximum number of retries.
    If all retries fail, the task will raise a TransportTaskException

    :param node: the node that represents the job calculation
    :param transport_queue: the TransportQueue from which to request a Transport
    :param cancel_flag: the cancelled flag that will be queried to determine whether the task was cancelled
    :raises: Return if the tasks was successfully completed
    :raises: TransportTaskException if after the maximum number of retries the transport task still excepted
    """
    initial_interval = 1
    max_attempts = 5

    authinfo = node.get_computer().get_authinfo(node.get_user())

    @coroutine
    def do_retrieve():
        with transport_queue.request_transport(authinfo) as request:
            transport = yield request

            # It may have taken time to get the transport, check if we've been cancelled
            if cancel_flag.is_cancelled:
                raise plumpy.CancelledError('task_retrieve_job for calculation<{}> cancelled'.format(node.pk))

            logger.info('retrieving calculation<{}>'.format(node.pk))
            node._set_state(calc_states.RETRIEVING)

            raise Return(execmanager.retrieve_calculation(node, transport, retrieved_temporary_folder))

    try:
        result = yield exponential_backoff_retry(
            do_retrieve, initial_interval, max_attempts, logger=node.logger, ignore_exceptions=plumpy.CancelledError)
    except plumpy.CancelledError:
        pass
    except Exception:
        logger.warning('retrieving calculation<{}> failed:\n{}'.format(node.pk, traceback.format_exc()))
        node._set_state(calc_states.RETRIEVALFAILED)
        raise TransportTaskException('retrieve_calculation failed {} times consecutively'.format(max_attempts))
    else:
        logger.info('retrieving calculation<{}> successful'.format(node.pk))
        raise Return(result)


@coroutine
def task_kill_job(node, transport_queue, cancel_flag):
    """
    Transport task that will attempt to kill a job calculation

    The task will first request a transport from the queue. Once the transport is yielded, the relevant execmanager
    function is called, wrapped in the exponential_backoff_retry coroutine, which, in case of a caught exception, will
    retry after an interval that increases exponentially with the number of retries, for a maximum number of retries.
    If all retries fail, the task will raise a TransportTaskException

    :param node: the node that represents the job calculation
    :param transport_queue: the TransportQueue from which to request a Transport
    :param cancel_flag: the cancelled flag that will be queried to determine whether the task was cancelled
    :raises: Return if the tasks was successfully completed
    :raises: TransportTaskException if after the maximum number of retries the transport task still excepted
    """
    initial_interval = 1
    max_attempts = 5

    if node.get_state() in [calc_states.NEW, calc_states.TOSUBMIT]:
        node._set_state(calc_states.FAILED)
        logger.warning('calculation<{}> killed, it was in the {} state'.format(node.pk, node.get_state()))
        raise Return(True)

    authinfo = node.get_computer().get_authinfo(node.get_user())

    @coroutine
    def do_kill():
        with transport_queue.request_transport(authinfo) as request:
            transport = yield request

            # It may have taken time to get the transport, check if we've been cancelled
            if cancel_flag.is_cancelled:
                raise plumpy.CancelledError('task_kill_job for calculation<{}> cancelled'.format(node.pk))

            logger.info('killing calculation<{}>'.format(node.pk))

            raise Return(execmanager.kill_calculation(node, transport))

    try:
        result = yield exponential_backoff_retry(do_kill, initial_interval, max_attempts, logger=node.logger)
    except plumpy.CancelledError:
        pass
    except Exception:
        logger.warning('killing calculation<{}> failed:\n{}'.format(node.pk, traceback.format_exc()))
        node._set_state(calc_states.FAILED)
        raise TransportTaskException('kill_calculation failed {} times consecutively'.format(max_attempts))
    else:
        logger.info('killing calculation<{}> successful'.format(node.pk))
        raise Return(result)


class Waiting(plumpy.Waiting):
    """
    The waiting state for the JobCalculation.
    """

    def __init__(self, process, done_callback, msg=None, data=None):
        super(Waiting, self).__init__(process, done_callback, msg, data)
        self._task = None

    def load_instance_state(self, saved_state, load_context):
        super(Waiting, self).load_instance_state(saved_state, load_context)
        self._task = None

    @coroutine
    def execute(self):

        calculation = self.process.calc
        transport_queue = self.process.runner.transport

        calculation._set_process_status('Waiting for transport task: {}'.format(self.data))

        try:

            if self.data == SUBMIT_COMMAND:

                try:
                    transport_task = functools.partial(task_submit_job, calculation, transport_queue)
                    self._task = interruptable_task(transport_task)
                    yield self._task
                finally:
                    self._task = None

                raise Return(self.scheduler_update())

            elif self.data == UPDATE_SCHEDULER_COMMAND:

                job_done = False

                while not job_done:
                    try:
                        transport_task = functools.partial(task_update_job, calculation, transport_queue)
                        self._task = interruptable_task(transport_task)
                        job_done = yield self._task
                    finally:
                        self._task = None

                raise Return(self.retrieve())

            elif self.data == RETRIEVE_COMMAND:

                # Create a temporary folder that has to be deleted by JobProcess.retrieved after successful parsing
                temp_folder = tempfile.mkdtemp()

                try:
                    transport_task = functools.partial(task_retrieve_job, calculation, transport_queue, temp_folder)
                    self._task = interruptable_task(transport_task)
                    yield self._task
                finally:
                    self._task = None

                raise Return(self.retrieved(temp_folder))

            else:
                raise RuntimeError('Unknown waiting command')

        except TransportTaskException:
            exit_status = JobCalculationExitStatus[calculation.get_state()].value
            raise Return(self.create_state(processes.ProcessState.FINISHED, exit_status, exit_status is 0))
        except (plumpy.Interruption, plumpy.CancelledError, Return):
            raise
        except Exception:
            exc_info = sys.exc_info()
            excepted_state = self.create_state(processes.ProcessState.EXCEPTED, exc_info[1], exc_info[2])
            raise Return(excepted_state)
        finally:
            calculation._set_process_status(None)

    def scheduler_update(self):
        """
        Create the next state to go to

        :return: The appropriate WAITING state
        """
        return self.create_state(
            processes.ProcessState.WAITING,
            None,
            msg='Waiting for scheduler update',
            data=UPDATE_SCHEDULER_COMMAND)

    def retrieve(self):
        """
        Create the next state to go to in order to retrieve

        :return: The appropriate WAITING state
        """
        return self.create_state(
            processes.ProcessState.WAITING,
            None,
            msg='Waiting to retrieve',
            data=RETRIEVE_COMMAND)

    def retrieved(self, retrieved_temporary_folder):
        """
        Create the next state to go to after retrieving
        :param retrieved_temporary_folder: The temporary folder used in retrieving, this will
            be used in parsing.
        :return: The appropriate RUNNING state
        """
        return self.create_state(
            processes.ProcessState.RUNNING,
            self.process.retrieved,
            retrieved_temporary_folder)

    def interrupt(self, reason):
        """Interrupt the Waiting state by calling interrupt on the transport task InterruptableFuture."""
        if self._task is not None:
            self._task.interrupt(reason)


class JobProcess(processes.Process):
    TRANSPORT_OPERATION = 'TRANSPORT_OPERATION'
    CALC_NODE_LABEL = 'calc_node'
    OPTIONS_INPUT_LABEL = 'options'

    _calc_class = None

    @classmethod
    def get_builder(cls):
        return JobProcessBuilder(cls)

    @classmethod
    def build(cls, calc_class):
        from aiida.orm.data import Data
        from aiida.orm.computer import Computer

        def define(cls_, spec):
            super(JobProcess, cls_).define(spec)

            # Define the 'options' inputs namespace and its input ports
            spec.input_namespace(cls.OPTIONS_INPUT_LABEL, help='various options')
            spec.input('{}.resources'.format(cls.OPTIONS_INPUT_LABEL), valid_type=dict,
                help='Set the dictionary of resources to be used by the scheduler plugin, like the number of nodes, '
                     'cpus etc. This dictionary is scheduler-plugin dependent. Look at the documentation of the scheduler.')
            spec.input('{}.max_wallclock_seconds'.format(cls.OPTIONS_INPUT_LABEL), valid_type=int, non_db=True, default=1800,
                help='Set the wallclock in seconds asked to the scheduler')
            spec.input('{}.custom_scheduler_commands'.format(cls.OPTIONS_INPUT_LABEL), valid_type=basestring, non_db=True, required=False,
                help='Set a (possibly multiline) string with the commands that the user wants to manually set for the '
                     'scheduler. The difference of this method with respect to the set_prepend_text is the position in the '
                     'scheduler submission file where such text is inserted: with this method, the string is inserted before '
                     ' any non-scheduler command')
            spec.input('{}.queue_name'.format(cls.OPTIONS_INPUT_LABEL), valid_type=basestring, non_db=True, required=False,
                help='Set the name of the queue on the remote computer')
            spec.input('{}.account'.format(cls.OPTIONS_INPUT_LABEL), valid_type=basestring, non_db=True, required=False,
                help='Set the account to use in for the queue on the remote computer')
            spec.input('{}.qos'.format(cls.OPTIONS_INPUT_LABEL), valid_type=basestring, non_db=True, required=False,
                help='Set the quality of service to use in for the queue on the remote computer')
            spec.input('{}.computer'.format(cls.OPTIONS_INPUT_LABEL), valid_type=Computer, non_db=True, required=False,
                       help='Set the computer to be used by the calculation')
            spec.input('{}.withmpi'.format(cls.OPTIONS_INPUT_LABEL), valid_type=bool, non_db=True, required=False,
                       help='Set the calculation to use mpi')
            spec.input('{}.mpirun_extra_params'.format(cls.OPTIONS_INPUT_LABEL), valid_type=(list, tuple), non_db=True,
                       required=False,
                       help='Set the extra params to pass to the mpirun (or equivalent) command after the one provided in '
                            'computer.mpirun_command. Example: mpirun -np 8 extra_params[0] extra_params[1] ... exec.x')
            spec.input('{}.import_sys_environment'.format(cls.OPTIONS_INPUT_LABEL), valid_type=bool, non_db=True,
                       required=False,
                       help='If set to true, the submission script will load the system environment variables')
            spec.input('{}.environment_variables'.format(cls.OPTIONS_INPUT_LABEL), valid_type=dict, non_db=True,
                       required=False,
                       help='Set a dictionary of custom environment variables for this calculation')
            spec.input('{}.priority'.format(cls.OPTIONS_INPUT_LABEL), valid_type=basestring, non_db=True,
                       required=False,
                       help='Set the priority of the job to be queued')
            spec.input('{}.max_memory_kb'.format(cls.OPTIONS_INPUT_LABEL), valid_type=int, non_db=True, required=False,
                       help='Set the maximum memory (in KiloBytes) to be asked to the scheduler')
            spec.input('{}.prepend_text'.format(cls.OPTIONS_INPUT_LABEL), valid_type=basestring, non_db=True,
                       required=False,
                       help='Set the calculation-specific prepend text, which is going to be prepended in the scheduler-job script, just before the code execution')
            spec.input('{}.append_text'.format(cls.OPTIONS_INPUT_LABEL), valid_type=basestring, non_db=True,
                       required=False,
                       help='Set the calculation-specific append text, which is going to be appended in the scheduler-job script, just after the code execution')
            spec.input('{}.parser_name'.format(cls.OPTIONS_INPUT_LABEL), valid_type=basestring, non_db=True,
                       required=False,
                       help='Set a string for the output parser. Can be None if no output plugin is available or needed')

            # Define the actual inputs based on the use methods of the calculation class
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

        dynamic_class_name = persistence.get_object_loader().identify_object(calc_class)
        class_name = '{}_{}'.format(cls.__name__, dynamic_class_name)

        # Dynamically create the type for this Process
        return type(
            class_name, (cls,),
            {
                plumpy.Process.define.__name__: classmethod(define),
                '_calc_class': calc_class
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
    def on_excepted(self):
        """The Process excepted so we set the calculation and scheduler state."""
        super(JobProcess, self).on_excepted()
        self.calc._set_state(calc_states.FAILED)

    @override
    def on_killed(self):
        """The Process was killed so we set the calculation and scheduler state."""
        super(JobProcess, self).on_excepted()
        self.calc._set_state(calc_states.FAILED)

    @override
    def update_outputs(self):
        # DO NOT REMOVE:
        # Don't do anything, this is taken care of by the job calculation node itself
        pass

    @override
    def get_or_create_db_record(self):
        return self._calc_class()

    @property
    def process_class(self):
        """
        Return the class that represents this Process, for the JobProcess this is JobCalculation class it wraps.

        For a standard Process or sub class of Process, this is the class itself. However, for legacy reasons,
        the Process class is a wrapper around another class. This function returns that original class, i.e. the
        class that really represents what was being executed.
        """
        return self._calc_class

    @override
    def _setup_db_inputs(self):
        """
        Create the links that connect the inputs to the calculation node that represents this Process

        For a JobProcess, the inputs also need to be mapped onto the `use_` and `set_` methods of the
        legacy JobCalculation class. If a code is defined in the inputs and no computer has been set
        yet for the calculation node, the computer configured for the code is used to set on the node.
        """
        for name, input_value in self.get_provenance_inputs_iterator():

            port = self.spec().inputs[name]

            if input_value is None or getattr(port, 'non_db', False):
                continue

            # Call the 'set' attribute methods for the contents of the 'option' namespace
            if name == self.OPTIONS_INPUT_LABEL:
                for option_name, option_value in input_value.items():
                    getattr(self.calc, 'set_{}'.format(option_name))(option_value)
                continue

            # Call the 'use' methods to set up the data-calc links
            if isinstance(port, PortNamespace):
                additional = self._calc_class._use_methods[name]['additional_parameter']

                for k, v in input_value.iteritems():
                    try:
                        getattr(self.calc, 'use_{}'.format(name))(v, **{additional: k})
                    except AttributeError:
                        raise AttributeError(
                            "You have provided for an input the key '{}' but"
                            "the JobCalculation has no such use_{} method".format(name, name))

            else:
                getattr(self.calc, 'use_{}'.format(name))(input_value)

        # Get the computer from the code if necessary
        if self.calc.get_computer() is None and 'code' in self.inputs:
            code = self.inputs['code']
            if not code.is_local():
                self.calc.set_computer(code.get_remote_computer())

    # endregion

    @override
    def run(self):
        """
        Run the calculation, we put it in the TOSUBMIT state and then wait for it
        to be copied over, submitted, retrieved, etc.
        """
        calc_state = self.calc.get_state()

        if calc_state == calc_states.FINISHED:
            return 0
        elif calc_state != calc_states.NEW:
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
        except Exception:
            try:
                self.calc._set_state(calc_states.PARSINGFAILED)
            except exceptions.ModificationNotAllowed:
                pass
            raise
        finally:
            # Delete the temporary folder
            try:
                shutil.rmtree(retrieved_temporary_folder)
            except OSError as exception:
                if exception.errno != 2:
                    raise

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

    @override
    def _setup_db_record(self):
        self._calc_class = self.inputs._calc.__class__
        super(ContinueJobCalculation, self)._setup_db_record()
