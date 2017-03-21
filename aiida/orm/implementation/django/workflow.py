# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
import importlib
from collections import Mapping

from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q

from aiida.backends.djsite.utils import get_automatic_user
from aiida.common import aiidalogger
from aiida.common.datastructures import wf_states, wf_exit_call, calc_states
from aiida.common.exceptions import (InternalError, ModificationNotAllowed,
                                     NotExistent, ValidationError,
                                     AiidaException)
from aiida.common.folders import RepositoryFolder, SandboxFolder
from aiida.common.utils import md5_file, str_timedelta
from aiida.orm.implementation.django.calculation.job import JobCalculation
from aiida.orm.implementation.general.workflow import AbstractWorkflow
from aiida.utils import timezone


logger = aiidalogger.getChild('Workflow')


class Workflow(AbstractWorkflow):
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

        from aiida.backends.djsite.db.models import DbWorkflow
        self._to_be_stored = True

        self._logger = logger.getChild(self.__class__.__name__)

        uuid = kwargs.pop('uuid', None)

        if uuid is not None:
            self._to_be_stored = False
            if kwargs:
                raise ValueError("If you pass a UUID, you cannot pass any further parameter")

            try:
                self._dbworkflowinstance = DbWorkflow.objects.get(uuid=uuid)

                # self.logger.info("Workflow found in the database, now retrieved")
                self._repo_folder = RepositoryFolder(section=self._section_name, uuid=self.uuid)

            except ObjectDoesNotExist:
                raise NotExistent("No entry with the UUID {} found".format(uuid))

        else:
            # ATTENTION: Do not move this code outside or encapsulate it in a function
            import inspect

            stack = inspect.stack()

            # cur_fr  = inspect.currentframe()
            #call_fr = inspect.getouterframes(cur_fr, 2)

            # Get all the caller data
            caller_frame = stack[1][0]
            caller_file = stack[1][1]
            caller_funct = stack[1][3]

            caller_module = inspect.getmodule(caller_frame)
            caller_module_class = caller_frame.f_locals.get('self', None).__class__

            if not caller_funct == "__init__":
                raise SystemError("A workflow must implement the __init__ class explicitly")

            # Test if the launcher is another workflow

            # print "caller_module", caller_module
            # print "caller_module_class", caller_module_class
            # print "caller_file", caller_file
            # print "caller_funct", caller_funct

            # Accept only the aiida.workflows packages
            if caller_module == None or not caller_module.__name__.startswith("aiida.workflows"):
                raise SystemError("The superclass can't be called directly")

            self.caller_module = caller_module.__name__
            self.caller_module_class = caller_module_class.__name__
            self.caller_file = caller_file
            self.caller_funct = caller_funct

            self._temp_folder = SandboxFolder()
            self.current_folder.insert_path(self.caller_file, self.caller_module_class)
            # self.store()

            # Test if there are parameters as input
            params = kwargs.pop('params', None)

            if params is not None:
                if isinstance(params, Mapping):
                    self.set_params(params)

            # This stores the MD5 as well, to test in case the workflow has
            # been modified after the launch
            self._dbworkflowinstance = DbWorkflow(user=get_automatic_user(),
                                                  module=self.caller_module,
                                                  module_class=self.caller_module_class,
                                                  script_path=self.caller_file,
                                                  script_md5=md5_file(self.caller_file))

        self.attach_calc_lazy_storage = {}
        self.attach_subwf_lazy_storage = {}

    @property
    def dbworkflowinstance(self):
        """
        Get the DbWorkflow object stored in the super class.

        :return: DbWorkflow object from the database
        """
        from aiida.backends.djsite.db.models import DbWorkflow

        if self._dbworkflowinstance.pk is None:
            return self._dbworkflowinstance
        else:
            self._dbworkflowinstance = DbWorkflow.objects.get(pk=self._dbworkflowinstance.pk)
            return self._dbworkflowinstance

    def _get_dbworkflowinstance(self):
        return self.dbworkflowinstance

    @property
    def label(self):
        """
        Get the label of the workflow.

        :return: a string
        """
        return self.dbworkflowinstance.label

    @label.setter
    def label(self, label):
        self._update_db_label_field(label)

    def _update_db_label_field(self, field_value):
        """
        Safety method to store the label of the workflow

        :return: a string
        """
        from django.db import transaction

        self.dbworkflowinstance.label = field_value
        if not self._to_be_stored:
            with transaction.atomic():
                self._dbworkflowinstance.save()
                self._increment_version_number_db()

    @property
    def description(self):
        """
        Get the description of the workflow.

        :return: a string
        """
        return self.dbworkflowinstance.description

    @description.setter
    def description(self, desc):
        self._update_db_description_field(desc)

    def _update_db_description_field(self, field_value):
        """
        Safety method to store the description of the workflow

        :return: a string
        """
        from django.db import transaction

        self.dbworkflowinstance.description = field_value
        if not self._to_be_stored:
            with transaction.atomic():
                self._dbworkflowinstance.save()
                self._increment_version_number_db()

    def _increment_version_number_db(self):
        """
        This function increments the version number in the DB.
        This should be called every time you need to increment the version (e.g. on adding a
        extra or attribute).
        """
        from django.db.models import F
        from aiida.backends.djsite.db.models import DbWorkflow

        # I increment the node number using a filter (this should be the right way of doing it;
        # dbnode.nodeversion  = F('nodeversion') + 1
        # will do weird stuff, returning Django Objects instead of numbers, and incrementing at
        # every save; moreover in this way I should do the right thing for concurrent writings
        # I use self._dbnode because this will not do a query to update the node; here I only
        # need to get its pk
        DbWorkflow.objects.filter(pk=self.pk).update(nodeversion=F('nodeversion') + 1)

        # This reload internally the node of self._dbworkflowinstance
        _ = self.dbworkflowinstance
        # Note: I have to reload the ojbect. I don't do it here because it is done at every call
        # to self.dbnode
        # self._dbnode = DbNode.objects.get(pk=self._dbnode.pk)
    @classmethod
    def query(cls, *args, **kwargs):
        """
        Map to the aiidaobjects manager of the DbWorkflow, that returns
        Workflow objects instead of DbWorkflow entities.

        """
        from aiida.backends.djsite.db.models import DbWorkflow

        return DbWorkflow.aiidaobjects.filter(*args, **kwargs)

    # @property
    #def logger(self):
    #    """
    #    Get the logger of the Workflow object.
    #
    #   :return: Logger object
    #    """
    #    return self._logger

    @property
    def logger(self):
        """
        Get the logger of the Workflow object, so that it also logs to the
        DB.

        :return: LoggerAdapter object, that works like a logger, but also has
          the 'extra' embedded
        """
        import logging
        from aiida.utils.logger import get_dblogger_extra

        return logging.LoggerAdapter(logger=self._logger,
                                     extra=get_dblogger_extra(self))

    def store(self):
        """
        Stores the DbWorkflow object data in the database
        """
        if self._to_be_stored:
            self._dbworkflowinstance.save()

            if hasattr(self, '_params'):
                self.dbworkflowinstance.add_parameters(self._params, force=False)

            self._repo_folder = RepositoryFolder(section=self._section_name, uuid=self.uuid)
            self.repo_folder.replace_with_folder(self.get_temp_folder().abspath, move=True, overwrite=True)

            self._temp_folder = None
            self._to_be_stored = False

        # Important to allow to do w = WorkflowSubClass().store()
        return self

    @property
    def uuid(self):
        """
        Returns the DbWorkflow uuid
        """
        return self.dbworkflowinstance.uuid

    @property
    def pk(self):
        """
        Returns the DbWorkflow pk
        """
        return self.dbworkflowinstance.pk

    def info(self):
        """
        Returns an array with all the informations about the modules, file, class to locate
        the workflow source code
        """
        return [self.dbworkflowinstance.module,
                self.dbworkflowinstance.module_class,
                self.dbworkflowinstance.script_path,
                self.dbworkflowinstance.script_md5,
                self.dbworkflowinstance.ctime,
                self.dbworkflowinstance.state]

    def set_params(self, params, force=False):
        """
        Adds parameters to the Workflow that are both stored and used every time
        the workflow engine re-initialize the specific workflow to launch the new methods.
        """

        def par_validate(params):
            the_params = {}
            for k, v in params.iteritems():
                if any([isinstance(v, int),
                        isinstance(v, bool),
                        isinstance(v, float),
                        isinstance(v, str)]):
                    the_params[k] = v
                else:
                    raise ValidationError("Cannot store in the DB a parameter "
                                          "which is not of type int, bool, float or str.")
            return the_params

        if self._to_be_stored:
            self._params = params
        else:
            the_params = par_validate(params)
            self.dbworkflowinstance.add_parameters(the_params, force=force)

    def get_parameters(self):
        """
        Get the Workflow paramenters
        :return: a dictionary of storable objects
        """
        if self._to_be_stored:
            return self._params
        else:
            return self.dbworkflowinstance.get_parameters()

    def get_parameter(self, _name):
        """
        Get one Workflow paramenter
        :param name: a string with the parameters name to retrieve
        :return: a dictionary of storable objects
        """
        if self._to_be_stored:
            return self._params(_name)
        else:
            return self.dbworkflowinstance.get_parameter(_name)

    def get_attributes(self):
        """
        Get the Workflow attributes
        :return: a dictionary of storable objects
        """
        return self.dbworkflowinstance.get_attributes()

    def get_attribute(self, _name):
        """
        Get one Workflow attribute
        :param name: a string with the attribute name to retrieve
        :return: a dictionary of storable objects
        """
        return self.dbworkflowinstance.get_attribute(_name)

    def add_attributes(self, _params):
        """
        Add a set of attributes to the Workflow. If another attribute is present with the same name it will
        be overwritten.
        :param name: a string with the attribute name to store
        :param value: a storable object to store
        """
        if self._to_be_stored:
            raise ModificationNotAllowed("You cannot add attributes before storing")
        self.dbworkflowinstance.add_attributes(_params)

    def add_attribute(self, _name, _value):
        """
        Add one attributes to the Workflow. If another attribute is present with the same name it will
        be overwritten.
        :param name: a string with the attribute name to store
        :param value: a storable object to store
        """
        if self._to_be_stored:
            raise ModificationNotAllowed("You cannot add attributes before storing")
        self.dbworkflowinstance.add_attribute(_name, _value)

    def get_results(self):
        """
        Get the Workflow results
        :return: a dictionary of storable objects
        """
        return self.dbworkflowinstance.get_results()

    def get_result(self, _name):
        """
        Get one Workflow result
        :param name: a string with the result name to retrieve
        :return: a dictionary of storable objects
        """
        return self.dbworkflowinstance.get_result(_name)

    def add_results(self, _params):
        """
        Add a set of results to the Workflow. If another result is present with the same name it will
        be overwritten.
        :param name: a string with the result name to store
        :param value: a storable object to store
        """
        self.dbworkflowinstance.add_results(_params)

    def add_result(self, _name, _value):
        """
        Add one result to the Workflow. If another result is present with the same name it will
        be overwritten.
        :param name: a string with the result name to store
        :param value: a storable object to store
        """
        self.dbworkflowinstance.add_result(_name, _value)

    def get_state(self):
        """
        Get the Workflow's state
        :return: a state from wf_states in aiida.common.datastructures
        """
        return self.dbworkflowinstance.state

    def set_state(self, state):
        """
        Set the Workflow's state
        :param name: a state from wf_states in aiida.common.datastructures
        """
        self.dbworkflowinstance.set_state(state)

    def is_new(self):
        """
        Returns True is the Workflow's state is CREATED
        """
        return self.dbworkflowinstance.state == wf_states.CREATED

    def is_running(self):
        """
        Returns True is the Workflow's state is RUNNING
        """
        return self.dbworkflowinstance.state == wf_states.RUNNING

    def has_finished_ok(self):
        """
        Returns True is the Workflow's state is FINISHED
        """
        return self.dbworkflowinstance.state in [wf_states.FINISHED, wf_states.SLEEP]

    def has_failed(self):
        """
        Returns True is the Workflow's state is ERROR
        """
        return self.dbworkflowinstance.state == wf_states.ERROR

    def is_subworkflow(self):
        """
        Return True is this is a subworkflow (i.e., if it has a parent),
        False otherwise.
        """
        return self.dbworkflowinstance.is_subworkflow()

    def get_step(self, step_method):

        """
        Retrieves by name a step from the Workflow.
        :param step_method: a string with the name of the step to retrieve or a method
        :raise: ObjectDoesNotExist: if there is no step with the specific name.
        :return: a DbWorkflowStep object.
        """
        if isinstance(step_method, basestring):
            step_method_name = step_method
        else:

            if not getattr(step_method, "is_wf_step"):
                raise AiidaException("Cannot get step calculations from a method not decorated as Workflow method")

            step_method_name = step_method.wf_step_name

        if (step_method_name == wf_exit_call):
            raise InternalError("Cannot query a step with name {0}, reserved string".format(step_method_name))

        try:
            step = self.dbworkflowinstance.steps.get(name=step_method_name, user=get_automatic_user())
            return step
        except ObjectDoesNotExist:
            return None

    def get_steps(self, state=None):
        """
        Retrieves all the steps from a specific workflow Workflow with the possibility to limit the list
        to a specific step's state.
        :param state: a state from wf_states in aiida.common.datastructures
        :return: a list of DbWorkflowStep objects.
        """
        if state is None:
            return self.dbworkflowinstance.steps.all().order_by('time')  #.values_list('name',flat=True)
        else:
            return self.dbworkflowinstance.steps.filter(state=state).order_by('time')

    def get_report(self):
        """
        Return the Workflow report.

        :note: once, in case the workflow is a subworkflow of any other Workflow this method
          calls the parent ``get_report`` method.
          This is not the case anymore.
        :return: a list of strings
        """
        return self.dbworkflowinstance.report.splitlines()

    def clear_report(self):
        """
        Wipe the Workflow report. In case the workflow is a subworflow of any other Workflow this method
        calls the parent ``clear_report`` method.
        """
        if len(self.dbworkflowinstance.parent_workflow_step.all()) == 0:
            self.dbworkflowinstance.clear_report()
        else:
            Workflow(uuid=self.dbworkflowinstance.parent_workflow_step.get().parent.uuid).clear_report()

    def append_to_report(self, text):
        """
        Adds text to the Workflow report.

        :note: Once, in case the workflow is a subworkflow of any other Workflow this method
         calls the parent ``append_to_report`` method; now instead this is not the
         case anymore
        """
        self.dbworkflowinstance.append_to_report(text)

    @classmethod
    def get_subclass_from_dbnode(cls, wf_db):
        module = wf_db.module
        module_class = wf_db.module_class
        try:
            wf_mod = importlib.import_module(module)
        except ImportError:
            raise InternalError("Unable to load the workflow module {}".format(module))

        for elem_name, elem in wf_mod.__dict__.iteritems():

            if module_class == elem_name:  #and issubclass(elem, Workflow):
                return getattr(wf_mod, elem_name)(uuid=wf_db.uuid)

    @classmethod
    def get_subclass_from_pk(cls, pk):
        from aiida.backends.djsite.db.models import DbWorkflow
        try:
            dbworkflowinstance = DbWorkflow.objects.get(pk=pk)
            return cls.get_subclass_from_dbnode(dbworkflowinstance)

        except ObjectDoesNotExist:
            raise NotExistent("No entry with pk= {} found".format(pk))

    @classmethod
    def get_subclass_from_uuid(cls, uuid):
        from aiida.backends.djsite.db.models import DbWorkflow
        try:

            dbworkflowinstance = DbWorkflow.objects.get(uuid=uuid)
            return cls.get_subclass_from_dbnode(dbworkflowinstance)

        except ObjectDoesNotExist:
            raise NotExistent("No entry with the UUID {} found".format(uuid))

def kill_all():
    from aiida.backends.djsite.db.models import DbWorkflow
    q_object = Q(user=get_automatic_user())
    q_object.add(~Q(state=wf_states.FINISHED), Q.AND)
    w_list = DbWorkflow.objects.filter(q_object)

    for w in w_list:
        Workflow.get_subclass_from_uuid(w.uuid).kill()

def get_all_running_steps():
    from aiida.backends.djsite.db.models import DbWorkflowStep
    return DbWorkflowStep.objects.filter(state=wf_states.RUNNING)

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


        # get all subworkflows for all steps
        wflows = DbWorkflow.objects.filter(parent_workflow_step__in=steps_pk)  #.order_by('ctime')
        # dictionary mapping pks into workflows
        workflow_mapping = {_.pk: _ for _ in wflows}

        # get all calculations for all steps
        calcs = JobCalculation.query(workflow_step__in=steps_pk)  #.order_by('ctime')
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
