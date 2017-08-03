# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
import os
import sys
import traceback
import inspect
import logging

from abc import abstractmethod, abstractproperty

from aiida.common.exceptions import (InternalError, AiidaException,
                                     InvalidOperation, RemoteOperationError)
from aiida.common.datastructures import (wf_states, wf_exit_call,
                                         wf_default_call, calc_states)
from aiida.common.utils import str_timedelta
from aiida.common import aiidalogger
from aiida.orm.implementation.calculation import JobCalculation

from aiida.backends.utils import get_automatic_user

from aiida.utils import timezone
from aiida.utils.logger import get_dblogger_extra
from aiida.common.utils import abstractclassmethod

logger = aiidalogger.getChild('Workflow')


class WorkflowKillError(AiidaException):
    """
    An exception raised when a workflow failed to be killed.
    The error_message_list attribute contains the error messages from
    all the subworkflows.
    """

    def __init__(self, *args, **kwargs):
        # Call the base class constructor with the parameters it needs
        super(WorkflowKillError, self).__init__(*args)

        self.error_message_list = kwargs.pop('error_message_list', [])
        if kwargs:
            raise ValueError("Unknown parameters passed to WorkflowKillError")


class WorkflowUnkillable(AiidaException):
    """
    Raised when a workflow cannot be killed because it is in the FINISHED or
    ERROR state.
    """
    pass


class AbstractWorkflow(object):
    """
    Base class to represent a workflow. This is the superclass of any workflow implementations,
    and provides all the methods necessary to interact with the database.

    The typical use case are workflow stored in the aiida.workflow packages, that are initiated
    either by the user in the shell or by some scripts, and that are monitored by the aiida daemon.

    Workflow can have steps, and each step must contain some calculations to be executed. At the
    end of the step's calculations the workflow is reloaded in memory and the next methods is called.

    .. todo: verify if there are other places (beside label and description) where
      the _increment_version_number_db routine needs to be called to increase
      the nodeversion after storing
    """
    # Name to be used for the repository section
    _section_name = 'workflow'

    # The name of the subfolder in which to put the files/directories added with add_path
    _path_subfolder_name = 'path'

    @abstractmethod
    def __init__(self, **kwargs):
        """
        Initializes the Workflow super class, store the instance in the DB and in case
        stores the starting parameters.

        If initialized with an uuid the Workflow is loaded from the DB, if not a new
        workflow is generated and added to the DB following the stack frameworks. This
        means that only modules inside aiida.workflows are allowed to implements
        the workflow super calls and be stored. The caller names, modules and files are
        retrieved from the stack.

        :param uuid: a string with the uuid of the object to be loaded.
        :param params: a dictionary of storable objects to initialize the specific workflow
        :raise: NotExistent: if there is no entry of the desired workflow kind with
                             the given uuid.
        """
        pass

    def __repr__(self):
        return '<{}: {}>'.format(self.__class__.__name__, str(self))

    def __str__(self):
        if self._to_be_stored:
            return "uuid: {} (unstored)".format(self.uuid)
        else:
            return "uuid: {} (pk: {})".format(self.uuid, self.pk)

    @abstractproperty
    def dbworkflowinstance(self):
        """
        Get the DbWorkflow object stored in the super class.

        :return: DbWorkflow object from the database
        """
        pass

    @abstractmethod
    def _get_dbworkflowinstance(self):
        pass

    @abstractproperty
    def label(self):
        """
        Get the label of the workflow.

        :return: a string
        """
        pass

    @label.setter
    @abstractmethod
    def label(self, label):
        """
        Set the label of the workflow.

        :param label: a string
        """
        pass

    @abstractmethod
    def _update_db_label_field(self, field_value):
        """
        Safety method to store the label of the workflow

        :return: a string
        """
        pass

    @abstractproperty
    def description(self):
        """
        Get the description of the workflow.

        :return: a string
        """
        pass

    @description.setter
    @abstractmethod
    def description(self, desc):
        """
        Set the description of the workflow

        :param desc: a string
        """
        pass

    @abstractmethod
    def _update_db_description_field(self, field_value):
        """
        Safety method to store the description of the workflow

        :return: a string
        """
        pass

    @abstractmethod
    def _increment_version_number_db(self):
        """
        This function increments the version number in the DB.
        This should be called every time you need to increment the version (e.g. on adding a
        extra or attribute).
        """
        pass

    @property
    def repo_folder(self):
        """
        Get the permanent repository folder.
        Use preferentially the current_folder method.

        :return: the permanent RepositoryFolder object
        """
        return self._repo_folder

    @property
    def current_folder(self):
        """
        Get the current repository folder,
        whether the temporary or the permanent.

        :return: the RepositoryFolder object.
        """
        if self._to_be_stored:
            return self.get_temp_folder()
        else:
            return self.repo_folder

    @property
    def _get_folder_pathsubfolder(self):
        """
        Get the subfolder in the repository.

        :return: a Folder object.
        """
        return self.current_folder.get_subfolder(
            self._path_subfolder_name, reset_limit=True)

    def get_folder_list(self, subfolder='.'):
        """
        Get the the list of files/directory in the repository of the object.

        :param subfolder: get the list of a subfolder
        :return: a list of strings.
        """
        return self._get_folder_pathsubfolder.get_subfolder(subfolder).get_content_list()

    def get_temp_folder(self):
        """
        Get the folder of the Node in the temporary repository.

        :return: a SandboxFolder object mapping the node in the repository.
        """
        if self._temp_folder is None:
            raise InternalError("The temp_folder was asked for node {}, but it is "
                                "not set!".format(self.uuid))
        return self._temp_folder

    def remove_path(self, path):
        """
        Remove a file or directory from the repository directory.

        Can be called only before storing.
        """
        if not self._to_be_stored:
            raise ValueError("Cannot delete a path after storing the node")

        if os.path.isabs(path):
            raise ValueError("The destination path in remove_path must be a relative path")
        self._get_folder_pathsubfolder.remove_path(path)

    def add_path(self, src_abs, dst_path):
        """
        Copy a file or folder from a local file inside the repository directory.
        If there is a subpath, folders will be created.

        Copy to a cache directory if the entry has not been saved yet.
        src_abs: the absolute path of the file to copy.
        dst_filename: the (relative) path on which to copy.
        """
        if not self._to_be_stored:
            raise ValueError("Cannot insert a path after storing the node")

        if not os.path.isabs(src_abs):
            raise ValueError("The source path in add_path must be absolute")
        if os.path.isabs(dst_path):
            raise ValueError("The destination path in add_path must be a filename without any subfolder")
        self._get_folder_pathsubfolder.insert_path(src_abs, dst_path)

    def get_abs_path(self, path, section=None):
        """
        TODO: For the moment works only for one kind of files, 'path' (internal files)
        """
        if section is None:
            section = self._path_subfolder_name

        if os.path.isabs(path):
            raise ValueError("The path in get_abs_path must be relative")
        return self.current_folder.get_subfolder(section, reset_limit=True).get_abs_path(path, check_existence=True)

    @abstractclassmethod
    def query(cls, *args, **kwargs):
        """
        Map to the aiidaobjects manager of the DbWorkflow, that returns
        Workflow objects instead of DbWorkflow entities.

        """
        pass

    @property
    def logger(self):
        """
        Get the logger of the Workflow object, so that it also logs to the
        DB.

        :return: LoggerAdapter object, that works like a logger, but also has
          the 'extra' embedded
        """
        return logging.LoggerAdapter(logger=self._logger,
                                     extra=get_dblogger_extra(self))

    @abstractmethod
    def store(self):
        """
        Stores the DbWorkflow object data in the database
        """
        pass

    @abstractproperty
    def uuid(self):
        """
        Returns the DbWorkflow uuid
        """
        pass

    @abstractproperty
    def pk(self):
        """
        Returns the DbWorkflow pk
        """
        pass

    @abstractmethod
    def info(self):
        """
        Returns an array with all the informations about the modules, file, class to locate
        the workflow source code
        """
        pass

    @abstractmethod
    def set_params(self, params, force=False):
        """
        Adds parameters to the Workflow that are both stored and used every time
        the workflow engine re-initialize the specific workflow to launch the new methods.
        """
        pass

    @abstractmethod
    def get_parameters(self):
        """
        Get the Workflow paramenters
        :return: a dictionary of storable objects
        """
        pass

    @abstractmethod
    def get_parameter(self, _name):
        """
        Get one Workflow paramenter
        :param name: a string with the parameters name to retrieve
        :return: a dictionary of storable objects
        """
        pass

    @abstractmethod
    def get_attributes(self):
        """
        Get the Workflow attributes
        :return: a dictionary of storable objects
        """
        pass

    @abstractmethod
    def get_attribute(self, _name):
        """
        Get one Workflow attribute
        :param name: a string with the attribute name to retrieve
        :return: a dictionary of storable objects
        """
        pass

    @abstractmethod
    def add_attributes(self, _params):
        """
        Add a set of attributes to the Workflow. If another attribute is present with the same name it will
        be overwritten.
        :param name: a string with the attribute name to store
        :param value: a storable object to store
        """
        pass

    @abstractmethod
    def add_attribute(self, _name, _value):
        """
        Add one attributes to the Workflow. If another attribute is present with the same name it will
        be overwritten.
        :param name: a string with the attribute name to store
        :param value: a storable object to store
        """
        pass

    @abstractmethod
    def get_results(self):
        """
        Get the Workflow results
        :return: a dictionary of storable objects
        """
        pass

    @abstractmethod
    def get_result(self, _name):
        """
        Get one Workflow result
        :param name: a string with the result name to retrieve
        :return: a dictionary of storable objects
        """
        pass

    @abstractmethod
    def add_results(self, _params):
        """
        Add a set of results to the Workflow. If another result is present with the same name it will
        be overwritten.
        :param name: a string with the result name to store
        :param value: a storable object to store
        """
        pass

    @abstractmethod
    def add_result(self, _name, _value):
        """
        Add one result to the Workflow. If another result is present with the same name it will
        be overwritten.
        :param name: a string with the result name to store
        :param value: a storable object to store
        """
        pass

    @abstractmethod
    def get_state(self):
        """
        Get the Workflow's state
        :return: a state from wf_states in aiida.common.datastructures
        """
        pass

    @abstractmethod
    def set_state(self, state):
        """
        Set the Workflow's state
        :param name: a state from wf_states in aiida.common.datastructures
        """
        pass

    @abstractmethod
    def is_new(self):
        """
        Returns True is the Workflow's state is CREATED
        """
        pass

    @abstractmethod
    def is_running(self):
        """
        Returns True is the Workflow's state is RUNNING
        """
        pass

    @abstractmethod
    def has_finished_ok(self):
        """
        Returns True is the Workflow's state is FINISHED
        """
        pass

    @abstractmethod
    def has_failed(self):
        """
        Returns True is the Workflow's state is ERROR
        """
        pass

    @abstractmethod
    def is_subworkflow(self):
        """
        Return True is this is a subworkflow (i.e., if it has a parent),
        False otherwise.
        """
        pass

    @abstractmethod
    def get_step(self, step_method):

        """
        Retrieves by name a step from the Workflow.
        :param step_method: a string with the name of the step to retrieve or a method
        :raise: ObjectDoesNotExist: if there is no step with the specific name.
        :return: a DbWorkflowStep object.
        """
        pass

    @abstractmethod
    def get_steps(self, state=None):
        """
        Retrieves all the steps from a specific workflow Workflow with the possibility to limit the list
        to a specific step's state.
        :param state: a state from wf_states in aiida.common.datastructures
        :return: a list of DbWorkflowStep objects.
        """
        pass

    def has_step(self, step_method):
        """
        Return if the Workflow has a step with a specific name.
        :param step_method: a string with the name of the step to retrieve or a method
        """
        return not self.get_step(step_method) == None

    @classmethod
    def step(cls, fun):
        """
        This method is used as a decorator for workflow steps, and handles the method's execution,
        the state updates and the eventual errors.

        The decorator generates a wrapper around the input function to execute, adding with the correct
        step name and a utility variable to make it distinguishable from non-step methods.

        When a step is launched, the wrapper tries to run the function in case of error the state of
        the workflow is moved to ERROR and the traceback is stored in the report. In general the input
        method is a step obtained from the Workflow object, and the decorator simply handles a controlled
        execution of the step allowing the code not to break in case of error in the step's source code.

        The wrapper also tests not to run two times the same step, unless a Workflow is in ERROR state, in this
        case all the calculations and subworkflows of the step are killed and a new execution is allowed.

        :param fun: a methods to wrap, making it a Workflow step
        :raise: AiidaException: in case the workflow state doesn't allow the execution
        :return: the wrapped methods,
        """
        wrapped_method = fun.__name__

        # This function gets called only if the method is launched with the execution brackets ()
        # Otherwise, when the method is addressed in a next() call this never gets called and only the
        # attributes are added
        def wrapper(cls, *args, **kwargs):
            # Store the workflow at the first step executed
            if cls._to_be_stored:
                cls.store()

            if len(args) > 0:
                raise AiidaException("A step method cannot have any argument, use add_attribute to the workflow")

            # If a method is launched and the step is RUNNING or INITIALIZED we should stop
            if cls.has_step(wrapped_method) and \
                    not (cls.get_step(wrapped_method).state == wf_states.ERROR or \
                                     cls.get_step(wrapped_method).state == wf_states.SLEEP or \
                                     cls.get_step(wrapped_method).nextcall == wf_default_call or \
                                     cls.get_step(wrapped_method).nextcall == wrapped_method \
                         # cls.has_step(wrapped_method) \
                         ):
                raise AiidaException(
                    "The step {0} has already been initialized, cannot change this outside the parent workflow !".format(
                        wrapped_method))

            # If a method is launched and the step is halted for ERROR, then clean the step and re-launch
            if cls.has_step(wrapped_method) and \
                    (cls.get_step(wrapped_method).state == wf_states.ERROR or \
                                 cls.get_step(wrapped_method).state == wf_states.SLEEP):

                for w in cls.get_step(wrapped_method).get_sub_workflows(): w.kill()
                cls.get_step(wrapped_method).remove_sub_workflows()

                for c in cls.get_step(wrapped_method).get_calculations(): c.kill()
                cls.get_step(wrapped_method).remove_calculations()

                # self.get_steps(wrapped_method).set_nextcall(wf_exit_call)

            method_step, created = cls.dbworkflowinstance.steps.get_or_create(name=wrapped_method,
                                                                              user=get_automatic_user())
            try:
                fun(cls)
            except:
                # exc_type, exc_value, exc_traceback = sys.exc_info()
                cls.append_to_report(
                    "ERROR ! This workflow got an error in the {0} method, we report down the stack trace".format(
                        wrapped_method))
                cls.append_to_report("full traceback: {0}".format(traceback.format_exc()))
                method_step.set_state(wf_states.ERROR)
                cls.set_state(wf_states.ERROR)
            return None

        out = wrapper
        wrapper.is_wf_step = True
        wrapper.wf_step_name = fun.__name__

        return wrapper

    def next(self, next_method):
        """
        Adds the a new step to be called after the completion of the caller method's calculations and subworkflows.

        This method must be called inside a Workflow step, otherwise an error is thrown. The
        code finds the caller method and stores in the database the input next_method as the next
        method to be called. At this point no execution in made, only configuration updates in the database.

        If during the execution of the caller method the user launched calculations or subworkflows, this
        method will add them to the database, making them available to the workflow manager to be launched.
        In fact all the calculation and subworkflow submissions are lazy method, really executed by this call.

        :param next_method: a Workflow step method to execute after the caller method
        :raise: AiidaException: in case the caller method cannot be found or validated
        :return: the wrapped methods, decorated with the correct step name
        """

        md5 = self.dbworkflowinstance.script_md5
        script_path = self.dbworkflowinstance.script_path

        # TODO: in principles, the file containing the workflow description
        # should be copied in a repository, and, on that file, the workflow
        # should check to be sure of loading the same description of the
        # workflow. At the moment, this is not done and is checking the source
        # in aiida/workflows/... resulting essentially in the impossibility of
        # developing a workflow without rendering most of the trial run
        # unaccessible. I comment these lines for this moment.

        # if md5 != md5_file(script_path):
        #    raise ValidationError("Unable to load the original workflow module from {}, MD5 has changed".format(script_path))

        # ATTENTION: Do not move this code outside or encapsulate it in a function
        curframe = inspect.currentframe()
        calframe = inspect.getouterframes(curframe, 2)
        caller_method = calframe[1][3]

        if next_method is None:
            raise AiidaException("The next method is None, probably you passed a method with parenthesis ??")

        if not self.has_step(caller_method):
            raise AiidaException("The caller method is either not a step or has not been registered as one")

        if not next_method.__name__ == wf_exit_call:
            try:
                is_wf_step = getattr(next_method, "is_wf_step", None)
            except AttributeError:
                raise AiidaException("Cannot add as next call a method not decorated as Workflow method")

        # TODO SP: abstract this, this depends on the DB. The better would be
        # to add a method to the DbWorkflow from SQLA and Django to get steps
        # with particular filters, in order to avoid repetition of all the code
        # arround

        # Retrieve the caller method
        method_step = self.dbworkflowinstance.steps.get(name=caller_method, user=get_automatic_user())

        # Attach calculations
        if caller_method in self.attach_calc_lazy_storage:
            for c in self.attach_calc_lazy_storage[caller_method]:
                method_step.add_calculation(c)

        # Attach sub-workflows
        if caller_method in self.attach_subwf_lazy_storage:
            for w in self.attach_subwf_lazy_storage[caller_method]:
                method_step.add_sub_workflow(w)

        # Set the next method
        if not next_method.__name__ == wf_exit_call:
            next_method_name = next_method.wf_step_name
        else:
            next_method_name = wf_exit_call

        # logger.info("Adding step {0} after {1} in {2}".format(next_method_name, caller_method, self.uuid))
        method_step.set_nextcall(next_method_name)
        #
        self.dbworkflowinstance.set_state(wf_states.RUNNING)
        method_step.set_state(wf_states.RUNNING)

    def attach_calculation(self, calc):
        """
        Adds a calculation to the caller step in the database. This is a lazy call, no
        calculations will be launched until the ``next`` method gets called. For a step to be
        completed all the calculations linked have to be in RETRIEVED state, after which the next
        method gets called from the workflow manager.
        :param calc: a JobCalculation object
        :raise: AiidaException: in case the input is not of JobCalculation type
        """

        if (not issubclass(calc.__class__, JobCalculation) and not isinstance(calc, JobCalculation)):
            raise AiidaException("Cannot add a calculation not of type JobCalculation")

        for node in calc.get_inputs():
            if node.pk is None:
                raise AiidaException("Cannot add a calculation with "
                                     "unstored inputs")

                #        if calc.pk is None:
                #            raise AiiDAException("Cannot add an unstored calculation")

        curframe = inspect.currentframe()
        calframe = inspect.getouterframes(curframe, 2)
        caller_funct = calframe[1][3]

        if not caller_funct in self.attach_calc_lazy_storage:
            self.attach_calc_lazy_storage[caller_funct] = []
        self.attach_calc_lazy_storage[caller_funct].append(calc)

    def attach_workflow(self, sub_wf):
        """
        Adds a workflow to the caller step in the database. This is a lazy call, no
        workflow will be started until the ``next`` method gets called. For a step to be
        completed all the workflows linked have to be in FINISHED state, after which the next
        method gets called from the workflow manager.
        :param next_method: a Workflow object
        """
        curframe = inspect.currentframe()
        calframe = inspect.getouterframes(curframe, 2)
        caller_funct = calframe[1][3]

        if not caller_funct in self.attach_subwf_lazy_storage:
            self.attach_subwf_lazy_storage[caller_funct] = []
        self.attach_subwf_lazy_storage[caller_funct].append(sub_wf)

    def get_step_calculations(self, step_method, calc_state=None):
        """
        Retrieves all the calculations connected to a specific step in the database. If the step
        is not existent it returns None, useful for simpler grammatic in the workflow definition.
        :param next_method: a Workflow step (decorated) method
        :param calc_state: a specific state to filter the calculations to retrieve
        :return: a list of JobCalculations objects
        """
        if not getattr(step_method, "is_wf_step"):
            raise AiidaException("Cannot get step calculations from a method not decorated as Workflow method")

        step_method_name = step_method.wf_step_name

        try:
            stp = self.get_step(step_method_name)
            return stp.get_calculations(state=calc_state)
        except:
            raise AiidaException("Cannot retrieve step's calculations")

    def get_step_workflows(self, step_method):
        """
        Retrieves all the workflows connected to a specific step in the database. If the step
        is not existent it returns None, useful for simpler grammatic in the workflow definition.
        :param next_method: a Workflow step (decorated) method
        """
        if not getattr(step_method, "is_wf_step"):
            raise AiidaException("Cannot get step calculations from a method not decorated as Workflow method")

        step_method_name = step_method.wf_step_name

        stp = self.get_step(step_method_name)
        return stp.get_sub_workflows()

    def kill_step_calculations(self, step):
        """
        Calls the ``kill`` method for each Calculation linked to the step method passed as argument.
        :param step: a Workflow step (decorated) method
        """
        counter = 0
        for c in step.get_calculations():
            if c._is_new() or c._is_running():
                try:
                    c.kill()
                except (InvalidOperation, RemoteOperationError) as e:
                    counter += 1
                    self.logger.error(e.message)

        if counter:
            raise InvalidOperation("{} step calculation{} could not be killed"
                                   "".format(counter, "" if counter == 1 else "s"))

    def kill(self, verbose=False):
        """
        Stop the Workflow execution and change its state to FINISHED.

        This method calls the ``kill`` method for each Calculation and each
        subworkflow linked to each RUNNING step.

        :param verbose: True to print the pk of each subworkflow killed
        :raise InvalidOperation: if some calculations cannot be killed (the
                                 workflow will be also put to SLEEP so that it
                                 can be killed later on)
        """
        if self.get_state() not in [wf_states.FINISHED, wf_states.ERROR]:

            # put in SLEEP state first
            self.dbworkflowinstance.set_state(wf_states.SLEEP)

            error_messages = []
            for s in self.get_steps(state=wf_states.RUNNING):

                try:
                    self.kill_step_calculations(s)
                except InvalidOperation as e:
                    error_message = ("'{}' for workflow with pk= {}"
                                     "".format(e.message, self.pk))
                    error_messages.append(error_message)

                for w in s.get_sub_workflows():
                    if verbose:
                        print "Killing workflow with pk: {}".format(w.pk)

                    try:
                        w.kill(verbose=verbose)
                    except WorkflowKillError as e:
                        # self.logger.error(e.message)
                        error_messages.extend(e.error_message_list)
                    except WorkflowUnkillable:
                        # A subwf cannot be killed, skip
                        pass

            if self.get_steps(state=wf_states.CREATED):
                error_messages.append("Workflow with pk= {} cannot be killed "
                                      "because some steps are in {} state"
                                      "".format(self.pk, wf_states.CREATED))

            if error_messages:
                raise WorkflowKillError("Workflow with pk= {} cannot be "
                                        "killed and was put to {} state instead; "
                                        "try again later".format(self.pk, wf_states.SLEEP),
                                        error_message_list=error_messages)
            else:
                self.dbworkflowinstance.set_state(wf_states.FINISHED)
        else:
            raise WorkflowUnkillable("Cannot kill a workflow in {} or {} state"
                                     "".format(wf_states.FINISHED, wf_states.ERROR))

    def get_all_calcs(self, calc_class=JobCalculation, calc_state=None, depth=15):
        """
        Get all calculations connected with this workflow and all its subworflows up to a given depth.
        The list of calculations can be restricted to a given calculation type and state
        :param calc_class: the calculation class to which the calculations should belong (default: JobCalculation)

        :param calc_state: a specific state to filter the calculations to retrieve

        :param depth: the maximum depth level the recursion on sub-workflows will
          try to reach (0 means we stay at the step level and don't go
          into sub-workflows, 1 means we go down to one step level of
          the sub-workflows, etc.)

        :return: a list of JobCalculation objects
        """

        all_calcs = []
        for st in self.get_steps():
            all_calcs += [c for c in st.get_calculations(state=calc_state) if isinstance(c, calc_class)]
            if depth > 0:
                for subw in st.get_sub_workflows():
                    all_calcs += subw.get_all_calcs(calc_state=calc_state, calc_class=calc_class, depth=depth - 1)
        return all_calcs

    def sleep(self):
        """
        Changes the workflow state to SLEEP, only possible to call from a Workflow step decorated method.
        """
        # ATTENTION: Do not move this code outside or encapsulate it in a function
        curframe = inspect.currentframe()
        calframe = inspect.getouterframes(curframe, 2)
        caller_method = calframe[1][3]

        if not self.has_step(caller_method):
            raise AiidaException("The caller method is either not a step or has not been registered as one")

        self.get_step(caller_method).set_state(wf_states.SLEEP)

    @abstractmethod
    def get_report(self):
        """
        Return the Workflow report.

        :note: once, in case the workflow is a subworkflow of any other Workflow this method
          calls the parent ``get_report`` method.
          This is not the case anymore.
        :return: a list of strings
        """
        pass

    @abstractmethod
    def clear_report(self):
        """
        Wipe the Workflow report. In case the workflow is a subworflow of any other Workflow this method
        calls the parent ``clear_report`` method.
        """
        pass

    @abstractmethod
    def append_to_report(self, text):
        """
        Adds text to the Workflow report.

        :note: Once, in case the workflow is a subworkflow of any other Workflow this method
         calls the parent ``append_to_report`` method; now instead this is not the
         case anymore
        """
        pass

    @abstractclassmethod
    def get_subclass_from_dbnode(cls, wf_db):
        """
        Loads the workflow object and reaoads the python script in memory with the importlib library, the
        main class is searched and then loaded.
        :param wf_db: a specific DbWorkflowNode object representing the Workflow
        :return: a Workflow subclass from the specific source code
        """
        pass

    @abstractclassmethod
    def get_subclass_from_pk(cls, pk):
        """
        Calls the ``get_subclass_from_dbnode`` selecting the DbWorkflowNode from
        the input pk.
        :param pk: a primary key index for the DbWorkflowNode
        :return: a Workflow subclass from the specific source code
        """
        pass

    @abstractclassmethod
    def get_subclass_from_uuid(cls, uuid):
        """
        Calls the ``get_subclass_from_dbnode`` selecting the DbWorkflowNode from
        the input uuid.
        :param uuid: a uuid for the DbWorkflowNode
        :return: a Workflow subclass from the specific source code
        """
        pass

    def exit(self):
        """
        This is the method to call in  ``next`` to finish the Workflow. When exit is the next method,
        and no errors are found, the Workflow is set to FINISHED and removed from the execution manager
        duties.
        """
        pass


# def revive(self):
#
#         from aiida.common.utils import md5_file
#         md5 = self.dbworkflowinstance.script_md5
#         script_path = self.dbworkflowinstance.script_path
#
#         md5_check = md5_file(script_path)
#
#         # MD5 Check before revive
#         if md5 != md5_check:
#             logger.info("The script has changed, MD5 is now updated")
#             self.dbworkflowinstance.set_script_md5(md5_check)
#
#         # Clear all the erroneous steps
#         err_steps    = self.get_steps(state=wf_states.ERROR)
#         for s in err_steps:
#
#             for w in s.get_sub_workflows(): w.kill()
#             s.remove_sub_workflows()
#
#             for c in s.get_calculations(): c.kill()
#             s.remove_calculations()
#
#             s.set_state(wf_states.INITIALIZED)
#
#         self.set_state(wf_states.RUNNING)



def kill_all():
    """
    Kills all the workflows not in FINISHED state running the ``kill_from_uuid``
    method in a loop.

    :param uuid: the UUID of the workflow to kill
    """

    raise NotImplementedError


def kill_from_pk():
    """
    Kills a workflow from its pk.

    :param pk: the Pkof the workflow to kill
    """

    raise NotImplementedError


def get_workflow_info(w, tab_size=2, short=False, pre_string="",
                      depth=16):
    """
    Return a string with all the information regarding the given workflow and
    all its calculations and subworkflows.
    This is a recursive function (to print all subworkflows info as well).

    :param w: a DbWorkflow instance
    :param tab_size: number of spaces to use for the indentation
    :param short: if True, provide a shorter output (only total number of
        calculations, rather than the state of each calculation)
    :param pre_string: string appended at the beginning of each line
    :param depth: the maximum depth level the recursion on sub-workflows will
                  try to reach (0 means we stay at the step level and don't go
                  into sub-workflows, 1 means we go down to one step level of
                  the sub-workflows, etc.)

    :return lines: list of lines to be outputed
    """
    # Note: pre_string becomes larger at each call of get_workflow_info on the
    #       subworkflows: pre_string -> pre_string + "|" + " "*(tab_size-1))
    # TODO SP: abstract the dependence on DbWorkflow

    from aiida.backends.djsite.db.models import DbWorkflow

    if tab_size < 2:
        raise ValueError("tab_size must be > 2")

    now = timezone.now()

    lines = []

    if w.label:
        wf_labelstring = "'{}', ".format(w.label)
    else:
        wf_labelstring = ""

    lines.append(pre_string)  # put an empty line before any workflow
    lines.append(pre_string + "+ Workflow {} ({}pk: {}) is {} [{}]".format(
        w.module_class, wf_labelstring, w.pk, w.state, str_timedelta(
            now - w.ctime, negative_to_zero=True)))

    # print information on the steps only if depth is higher than 0
    if depth > 0:

        # order all steps by time and  get all the needed values
        steps_and_subwf_pks = w.steps.all().order_by('time', 'sub_workflows__ctime',
                                                     'calculations__ctime').values_list('pk',
                                                                                        'sub_workflows__pk',
                                                                                        'calculations', 'name',
                                                                                        'nextcall', 'state')
        # get the list of step pks (distinct), preserving the order
        steps_pk = []
        for item in steps_and_subwf_pks:
            if item[0] not in steps_pk:
                steps_pk.append(item[0])

        # build a dictionary with all the infos for each step pk
        subwfs_of_steps = {}
        for step_pk, subwf_pk, calc_pk, name, nextcall, state in steps_and_subwf_pks:
            if step_pk not in subwfs_of_steps.keys():
                subwfs_of_steps[step_pk] = {'name': name,
                                            'nextcall': nextcall,
                                            'state': state,
                                            'subwf_pks': [],
                                            'calc_pks': [],
                                            }
            if subwf_pk:
                subwfs_of_steps[step_pk]['subwf_pks'].append(subwf_pk)
            if calc_pk:
                subwfs_of_steps[step_pk]['calc_pks'].append(calc_pk)

        # TODO SP: abstract this
        # get all subworkflows for all steps
        wflows = DbWorkflow.objects.filter(parent_workflow_step__in=steps_pk)  # .order_by('ctime')
        # dictionary mapping pks into workflows
        workflow_mapping = {_.pk: _ for _ in wflows}

        # get all calculations for all steps
        calcs = JobCalculation.query(workflow_step__in=steps_pk)  # .order_by('ctime')
        # dictionary mapping pks into calculations
        calc_mapping = {_.pk: _ for _ in calcs}

        for step_pk in steps_pk:
            lines.append(pre_string + "|" + '-' * (tab_size - 1) +
                         "* Step: {0} [->{1}] is {2}".format(
                             subwfs_of_steps[step_pk]['name'],
                             subwfs_of_steps[step_pk]['nextcall'],
                             subwfs_of_steps[step_pk]['state']))

            calc_pks = subwfs_of_steps[step_pk]['calc_pks']

            # print calculations only if it is not short
            if short:
                lines.append(pre_string + "|" + " " * (tab_size - 1) +
                             "| [{0} calculations]".format(len(calc_pks)))
            else:
                for calc_pk in calc_pks:
                    c = calc_mapping[calc_pk]
                    calc_state = c.get_state()
                    if c.label:
                        labelstring = "'{}', ".format(c.label)
                    else:
                        labelstring = ""

                    if calc_state == calc_states.WITHSCHEDULER:
                        sched_state = c.get_scheduler_state()
                        if sched_state is None:
                            remote_state = "(remote state still unknown)"
                        else:
                            last_check = c._get_scheduler_lastchecktime()
                            if last_check is not None:
                                when_string = " {}".format(
                                    str_timedelta(now - last_check, short=True,
                                                  negative_to_zero=True))
                                verb_string = "was "
                            else:
                                when_string = ""
                                verb_string = ""
                            remote_state = " ({}{}{})".format(verb_string,
                                                              sched_state, when_string)
                    else:
                        remote_state = ""
                    lines.append(pre_string + "|" + " " * (tab_size - 1) +
                                 "| Calculation ({}pk: {}) is {}{}".format(
                                     labelstring, calc_pk, calc_state, remote_state))

            ## SubWorkflows
            for subwf_pk in subwfs_of_steps[step_pk]['subwf_pks']:
                subwf = workflow_mapping[subwf_pk]
                lines.extend(get_workflow_info(subwf,
                                               short=short, tab_size=tab_size,
                                               pre_string=pre_string + "|" + " " * (tab_size - 1),
                                               depth=depth - 1))

            lines.append(pre_string + "|")

    return lines
