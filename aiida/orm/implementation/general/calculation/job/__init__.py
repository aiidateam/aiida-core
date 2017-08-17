# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################

from abc import abstractmethod
import datetime
import copy

from aiida.utils import timezone
from aiida.common.utils import str_timedelta
from aiida.common.datastructures import calc_states
from aiida.common.exceptions import ModificationNotAllowed, MissingPluginError
from aiida.common.links import LinkType
from aiida.backends.utils import get_automatic_user
from aiida.common.old_pluginloader import from_type_to_pluginclassname

# TODO: set the following as properties of the Calculation
# 'email',
# 'email_on_started',
# 'email_on_terminated',
# 'rerunnable',
# 'resourceLimits',


_input_subfolder = 'raw_input'


class AbstractJobCalculation(object):
    """
    This class provides the definition of an AiiDA calculation that is run
    remotely on a job scheduler.
    """

    @classmethod
    def process(cls):
        from aiida.work.legacy.job_process import JobProcess
        return JobProcess.build(cls)

    def _init_internal_params(self):
        """
        Define here internal parameters that should be defined
        right after the __init__. This function is actually called
        by the __init__.

        :note: if you inherit this function, ALWAYS remember to
          call super()._init_internal_params() as the first thing
          in your inherited function.
        """
        # By default, no output parser
        self._default_parser = None
        # Set default for the link to the retrieved folder (after calc is done)
        self._linkname_retrieved = 'retrieved'

        self._updatable_attributes = (
            'state', 'job_id', 'scheduler_state',
            'scheduler_lastchecktime',
            'last_jobinfo', 'remote_workdir', 'retrieve_list',
            'retrieve_singlefile_list'
        )

        # Files in which the scheduler output and error will be stored.
        # If they are identical, outputs will be joined.
        self._SCHED_OUTPUT_FILE = '_scheduler-stdout.txt'
        self._SCHED_ERROR_FILE = '_scheduler-stderr.txt'

        # Files that should be shown by default
        # Set it to None if you do not have a default file
        # Used, e.g., by 'verdi calculation inputshow/outputshow
        self._DEFAULT_INPUT_FILE = None
        self._DEFAULT_OUTPUT_FILE = None

    @property
    def _set_defaults(self):
        """
        Return the default parameters to set.
        It is done as a property so that it can read the default parameters
        defined in _init_internal_params.

        :note: It is a property because in this way, e.g. the
        parser_name is taken from the actual subclass of calculation,
        and not from the parent Calculation class
        """
        parent_dict = super(AbstractJobCalculation, self)._set_defaults

        parent_dict.update({
            "parser_name": self._default_parser,
            "_linkname_retrieved": self._linkname_retrieved})

        return parent_dict

    def store(self, *args, **kwargs):
        """
        Override the store() method to store also the calculation in the NEW
        state as soon as this is stored for the first time.
        """
        super(AbstractJobCalculation, self).store(*args, **kwargs)

        # I get here if the calculation was successfully stored.
        self._set_state(calc_states.NEW)

        # Important to return self to allow the one-liner
        # c = Calculation().store()
        return self

    def _validate(self):
        """
        Verify if all the input nodes are present and valid.

        :raise: ValidationError: if invalid parameters are found.
        """
        from aiida.common.exceptions import MissingPluginError, ValidationError

        super(AbstractJobCalculation, self)._validate()

        if self.get_computer() is None:
            raise ValidationError("You did not specify a computer")

        if self.get_state() not in calc_states:
            raise ValidationError("Calculation state '{}' is not valid".format(
                self.get_state()))

        try:
            _ = self.get_parserclass()
        except MissingPluginError:
            raise ValidationError(
                "No valid plugin found for the parser '{}'. "
                "Set the parser to None if you do not need an automatic "
                "parser.".format(self.get_parser_name())
            )

        computer = self.get_computer()
        s = computer.get_scheduler()
        try:
            _ = s.create_job_resource(**self.get_resources(full=True))
        except (TypeError, ValueError) as e:
            raise ValidationError("Invalid resources for the scheduler of the "
                                  "specified computer: {}".format(e.message))

        if not isinstance(self.get_withmpi(), bool):
            raise ValidationError(
                "withmpi property must be boolean! It in instead {}"
                "".format(str(type(self.get_withmpi())))
            )

    def _linking_as_output(self, dest, link_type):
        """
        An output of a JobCalculation can only be set
        when the calculation is in the SUBMITTING or RETRIEVING or
        PARSING state.
        (during SUBMITTING, the execmanager adds a link to the remote folder;
        all other links are added while in the retrieving phase).

        :note: Further checks, such as that the output data type is 'Data',
          are done in the super() class.

        :param dest: a Data object instance of the database
        :raise: ValueError if a link from self to dest is not allowed.
        """
        valid_states = [
            calc_states.SUBMITTING,
            calc_states.RETRIEVING,
            calc_states.PARSING,
        ]

        if self.get_state() not in valid_states:
            raise ModificationNotAllowed(
                "Can add an output node to a calculation only if it is in one "
                "of the following states: {}, it is instead {}".format(
                    valid_states, self.get_state()))

        return super(AbstractJobCalculation, self)._linking_as_output(dest,
                                                                      link_type)

    def _store_raw_input_folder(self, folder_path):
        """
        Copy the content of the folder internally, in a subfolder called
        'raw_input'

        :param folder_path: the path to the folder from which the content
               should be taken
        """
        # This function can be called only if the state is SUBMITTING
        if self.get_state() != calc_states.SUBMITTING:
            raise ModificationNotAllowed(
                "The raw input folder can be stored only if the "
                "state is SUBMITTING, it is instead {}".format(
                    self.get_state()))

        # get subfolder and replace with copy
        _raw_input_folder = self.folder.get_subfolder(
            _input_subfolder, create=True)
        _raw_input_folder.replace_with_folder(
            folder_path, move=False, overwrite=True)

    @property
    def _raw_input_folder(self):
        """
        Get the input folder object.

        :return: the input folder object.
        :raise: NotExistent: if the raw folder hasn't been created yet
        """
        from aiida.common.exceptions import NotExistent

        return_folder = self.folder.get_subfolder(_input_subfolder)
        if return_folder.exists():
            return return_folder
        else:
            raise NotExistent("_raw_input_folder not created yet")

    def set_queue_name(self, val):
        """
        Set the name of the queue on the remote computer.

        :param str val: the queue name
        """
        if val is None:
            self._set_attr('queue_name', None)
        else:
            self._set_attr('queue_name', unicode(val))

    def set_import_sys_environment(self, val):
        """
        If set to true, the submission script will load the system
        environment variables.

        :param bool val: load the environment if True
        """
        self._set_attr('import_sys_environment', bool(val))

    def get_import_sys_environment(self):
        """
        To check if it's loading the system environment
        on the submission script.

        :return: a boolean. If True the system environment will be load.
        """
        return self.get_attr('import_sys_environment', True)

    def set_environment_variables(self, env_vars_dict):
        """
        Set a dictionary of custom environment variables for this calculation.

        Both keys and values must be strings.

        In the remote-computer submission script, it's going to export
        variables as ``export 'keys'='values'``
        """
        if not isinstance(env_vars_dict, dict):
            raise ValueError("You have to pass a "
                             "dictionary to set_environment_variables")

        for k, v in env_vars_dict.iteritems():
            if not isinstance(k, basestring) or not isinstance(v, basestring):
                raise ValueError(
                    "Both the keys and the values of the "
                    "dictionary passed to set_environment_variables must be "
                    "strings."
                )

        return self._set_attr('custom_environment_variables', env_vars_dict)

    def get_environment_variables(self):
        """
        Return a dictionary of the environment variables that are set
        for this calculation.

        Return an empty dictionary if no special environment variables have
        to be set for this calculation.
        """
        return self.get_attr('custom_environment_variables', {})

    def set_priority(self, val):
        """
        Set the priority of the job to be queued.

        :param val: the values of priority as accepted by the cluster scheduler.
        """
        self._set_attr('priority', unicode(val))

    def set_max_memory_kb(self, val):
        """
        Set the maximum memory (in KiloBytes) to be asked to the scheduler.

        :param val: an integer. Default=None
        """
        self._set_attr('max_memory_kb', int(val))

    def get_max_memory_kb(self):
        """
        Get the memory (in KiloBytes) requested to the scheduler.

        :return: an integer
        """
        return self.get_attr('max_memory_kb', None)

    def set_max_wallclock_seconds(self, val):
        """
        Set the wallclock in seconds asked to the scheduler.

        :param val: An integer. Default=None
        """
        self._set_attr('max_wallclock_seconds', int(val))

    def get_max_wallclock_seconds(self):
        """
        Get the max wallclock time in seconds requested to the scheduler.

        :return: an integer
        :rtype: int
        """
        return self.get_attr('max_wallclock_seconds', None)

    def set_resources(self, resources_dict):
        """
        Set the dictionary of resources to be used by the scheduler plugin,
        like the number of nodes, cpus, ...
        This dictionary is scheduler-plugin dependent. Look at the documentation
        of the scheduler.
        (scheduler type can be found with
        calc.get_computer().get_scheduler_type() )
        """
        # Note: for the time being, resources are only validated during the
        # 'store' because here we are not sure that a Computer has been set
        # yet (in particular, if both computer and resources are set together
        # using the .set() method).
        self._set_attr('jobresource_params', resources_dict)

    def set_withmpi(self, val):
        """
        Set the calculation to use mpi.

        :param val: A boolean. Default=True
        """
        self._set_attr('withmpi', val)

    def get_withmpi(self):
        """
        Get whether the job is set with mpi execution.

        :return: a boolean. Default=True.
        """
        return self.get_attr('withmpi', True)

    def get_resources(self, full=False):
        """
        Returns the dictionary of the job resources set.

        :param full: if True, also add the default values, e.g.
            ``default_mpiprocs_per_machine``

        :return: a dictionary
        """
        resources_dict = self.get_attr('jobresource_params', {})

        if full:
            computer = self.get_computer()
            def_cpus_machine = computer.get_default_mpiprocs_per_machine()
            if def_cpus_machine is not None:
                resources_dict[
                    'default_mpiprocs_per_machine'] = def_cpus_machine

        return resources_dict

    def get_queue_name(self):
        """
        Get the name of the queue on cluster.

        :return: a string or None.
        """
        return self.get_attr('queue_name', None)

    def get_priority(self):
        """
        Get the priority, if set, of the job on the cluster.

        :return: a string or None
        """
        return self.get_attr('priority', None)

    def get_prepend_text(self):
        """
        Get the calculation-specific prepend text,
        which is going to be prepended in the scheduler-job script, just before
        the code execution.
        """
        return self.get_attr("prepend_text", "")

    def set_prepend_text(self, val):
        """
        Set the calculation-specific prepend text,
        which is going to be prepended in the scheduler-job script, just before
        the code execution.

        See also ``set_custom_scheduler_commands``

        :param val: a (possibly multiline) string
        """
        self._set_attr("prepend_text", unicode(val))

    def get_append_text(self):
        """
        Get the calculation-specific append text,
        which is going to be appended in the scheduler-job script, just after
        the code execution.
        """
        return self.get_attr("append_text", "")

    def set_append_text(self, val):
        """
        Set the calculation-specific append text,
        which is going to be appended in the scheduler-job script, just after
        the code execution.

        :param val: a (possibly multiline) string
        """
        self._set_attr("append_text", unicode(val))

    def set_custom_scheduler_commands(self, val):
        """
        Set a (possibly multiline) string with the commands that the user
        wants to manually set for the scheduler.

        The difference of this method with respect to the set_prepend_text
        is the position in the scheduler submission file where such text is
        inserted: with this method, the string is inserted before any
        non-scheduler command.
        """
        self._set_attr("custom_scheduler_commands", unicode(val))

    def get_custom_scheduler_commands(self):
        """
        Return a (possibly multiline) string with the commands that the user
        wants to manually set for the scheduler.
        See also the documentation of the corresponding
        ``set_`` method.

        :return: the custom scheduler command, or an empty string if no
          custom command was defined.
        """
        return self.get_attr("custom_scheduler_commands", "")

    def get_mpirun_extra_params(self):
        """
        Return a list of strings, that are the extra params to pass to the
        mpirun (or equivalent) command after the one provided in
        computer.mpirun_command.
        Example: mpirun -np 8 extra_params[0] extra_params[1] ... exec.x

        Return an empty list if no parameters have been defined.
        """
        return self.get_attr("mpirun_extra_params", [])

    def set_mpirun_extra_params(self, extra_params):
        """
        Set the extra params to pass to the
        mpirun (or equivalent) command after the one provided in
        computer.mpirun_command.
        Example: mpirun -np 8 extra_params[0] extra_params[1] ... exec.x

        :param extra_params: must be a list of strings, one for each
            extra parameter
        """
        if extra_params is None:
            try:
                self._del_attr("mpirun_extra_params")
            except AttributeError:
                # it was not saved, yet
                pass
            return

        if not isinstance(extra_params, (list, tuple)):
            raise ValueError("You must pass a list of strings to "
                             "set_mpirun_extra_params")
        for param in extra_params:
            if not isinstance(param, basestring):
                raise ValueError("You must pass a list of strings to "
                                 "set_mpirun_extra_params")

        self._set_attr("mpirun_extra_params", list(extra_params))

    def add_link_from(self, src, label=None, link_type=LinkType.INPUT):
        """
        Add a link with a code as destination. Add the additional
        contraint that this is only possible if the calculation
        is in state NEW.

        You can use the parameters of the base Node class, in particular the
        label parameter to label the link.

        :param src: a node of the database. It cannot be a Calculation object.
        :param str label: Name of the link. Default=None
        :param link_type: The type of link, must be one of the enum values form
          :class:`~aiida.common.links.LinkType`
        """
        valid_states = [calc_states.NEW]

        if self.get_state() not in valid_states:
            raise ModificationNotAllowed(
                "Can add an input link to a JobCalculation only if it is in "
                "one of the following states: {}, it is instead {}".format(
                    valid_states, self.get_state()))

        return super(AbstractJobCalculation, self).add_link_from(src, label,
                                                                 link_type)

    def _replace_link_from(self, src, label, link_type=LinkType.INPUT):
        """
        Replace a link. Add the additional constraint that this is
        only possible if the calculation is in state NEW.

        :param src: a node of the database. It cannot be a Calculation object.
        :param label: Name of the link.
        :type label: str
        """
        valid_states = [calc_states.NEW]

        if self.get_state() not in valid_states:
            raise ModificationNotAllowed(
                "Can replace an input link to a Jobalculation only if it is in "
                "one of the following states: {}, it is instead {}".format(
                    valid_states, self.get_state()))

        return super(AbstractJobCalculation, self)._replace_link_from(src,
                                                                      label,
                                                                      link_type)

    def _remove_link_from(self, label):
        """
        Remove a link. Only possible if the calculation is in state NEW.

        :param str label: Name of the link to remove.
        """
        valid_states = [calc_states.NEW]

        if self.get_state() not in valid_states:
            raise ModificationNotAllowed(
                "Can remove an input link to a calculation only if it is in one "
                "of the following states:\n   {}\n it is instead {}".format(
                    valid_states, self.get_state()))

        return super(AbstractJobCalculation, self)._remove_link_from(label)

    @abstractmethod
    def _set_state(self, state):
        """
        Set the state of the calculation.

        Set it in the DbCalcState to have also the uniqueness check.
        Moreover (except for the IMPORTED state) also store in the 'state'
        attribute, useful to know it also after importing, and for faster
        querying.

        .. todo:: Add further checks to enforce that the states are set
           in order?

        :param state: a string with the state. This must be a valid string,
          from ``aiida.common.datastructures.calc_states``.
        :raise: ModificationNotAllowed if the given state was already set.
        """
        pass

    @abstractmethod
    def get_state(self, from_attribute=False):
        """
        Get the state of the calculation.

        .. note:: the 'most recent' state is obtained using the logic in the
          ``aiida.common.datastructures.sort_states`` function.

        .. todo:: Understand if the state returned when no state entry is found
          in the DB is the best choice.

        :param from_attribute: if set to True, read it from the attributes
          (the attribute is also set with set_state, unless the state is set
          to IMPORTED; in this way we can also see the state before storing).

        :return: a string. If from_attribute is True and no attribute is found,
          return None. If from_attribute is False and no entry is found in the
          DB, also return None.
        """
        pass

    def _get_state_string(self):
        """
        Return a string, that is correct also when the state is imported
        (in this case, the string will be in the format IMPORTED/ORIGSTATE
        where ORIGSTATE is the original state from the node attributes).
        """
        state = self.get_state(from_attribute=False)
        if state == calc_states.IMPORTED:
            attribute_state = self.get_state(from_attribute=True)
            if attribute_state is None:
                attribute_state = "NOTFOUND"
            return 'IMPORTED/{}'.format(attribute_state)
        else:
            return state

    def _is_new(self):
        """
        Get whether the calculation is in the NEW status.

        :return: a boolean
        """
        return self.get_state() in [calc_states.NEW, None]

    def _is_running(self):
        """
        Get whether the calculation is in a running state,
        i.e. one of TOSUBMIT, SUBMITTING, WITHSCHEDULER,
        COMPUTED, RETRIEVING or PARSING.

        :return: a boolean
        """
        return self.get_state() in [
            calc_states.TOSUBMIT,
            calc_states.SUBMITTING,
            calc_states.WITHSCHEDULER,
            calc_states.COMPUTED,
            calc_states.RETRIEVING,
            calc_states.PARSING
        ]

    def has_finished(self):
        """
        Determine if the calculation is finished for whatever reason.
        This may be because it finished successfully or because of a failure.

        :return: True if the job has finished running, False otherwise.
        :rtype: bool
        """
        return self.has_finished_ok() or self.has_failed()

    def has_finished_ok(self):
        """
        Get whether the calculation is in the FINISHED status.

        :return: a boolean
        """
        return self.get_state() in [calc_states.FINISHED]

    def has_failed(self):
        """
        Get whether the calculation is in a failed status,
        i.e. SUBMISSIONFAILED, RETRIEVALFAILED, PARSINGFAILED or FAILED.

        :return: a boolean
        """
        return self.get_state() in [calc_states.SUBMISSIONFAILED,
                                    calc_states.RETRIEVALFAILED,
                                    calc_states.PARSINGFAILED,
                                    calc_states.FAILED]

    def _set_remote_workdir(self, remote_workdir):
        if self.get_state() != calc_states.SUBMITTING:
            raise ModificationNotAllowed(
                "Cannot set the remote workdir if you are not "
                "submitting the calculation (current state is "
                "{})".format(self.get_state()))
        self._set_attr('remote_workdir', remote_workdir)

    def _get_remote_workdir(self):
        """
        Get the path to the remote (on cluster) scratch
        folder of the calculation.

        :return: a string with the remote path
        """
        return self.get_attr('remote_workdir', None)

    def _set_retrieve_list(self, retrieve_list):
        if self.get_state() not in (calc_states.SUBMITTING,
                                    calc_states.NEW):
            raise ModificationNotAllowed(
                "Cannot set the retrieve_list for a calculation "
                "that is neither NEW nor SUBMITTING (current state is "
                "{})".format(self.get_state()))

        # accept format of: [ 'remotename',
        #                     ['remotepath','localpath',0] ]
        # where the last number is used
        # to decide the localname, see CalcInfo or execmanager

        if not (isinstance(retrieve_list, (tuple, list))):
            raise ValueError("You should pass a list/tuple")
        for item in retrieve_list:
            if not isinstance(item, basestring):
                if (not (isinstance(item, (tuple, list))) or
                            len(item) != 3):
                    raise ValueError(
                        "You should pass a list containing either "
                        "strings or lists/tuples"
                    )
                if (not (isinstance(item[0], basestring)) or
                        not (isinstance(item[1], basestring)) or
                        not (isinstance(item[2], int))):
                    raise ValueError(
                        "You have to pass a list (or tuple) of "
                        "lists, with remotepath(string), "
                        "localpath(string) and depth (integer)"
                    )

        self._set_attr('retrieve_list', retrieve_list)

    def _get_retrieve_list(self):
        """
        Get the list of files/directories to be retrieved on the cluster.
        Their path is relative to the remote workdirectory path.

        :return: a list of strings for file/directory names
        """
        return self.get_attr('retrieve_list', None)

    def _set_retrieve_singlefile_list(self, retrieve_singlefile_list):
        """
        Set the list of information for the retrieval of singlefiles
        """
        if self.get_state() not in (calc_states.SUBMITTING,
                                    calc_states.NEW):
            raise ModificationNotAllowed(
                "Cannot set the retrieve_singlefile_list for a calculation "
                "that is neither NEW nor SUBMITTING (current state is "
                "{})".format(self.get_state()))

        if not isinstance(retrieve_singlefile_list, (tuple, list)):
            raise ValueError("You have to pass a list (or tuple) of lists of "
                             "strings as retrieve_singlefile_list")
        for j in retrieve_singlefile_list:
            if (not (isinstance(j, (tuple, list))) or
                    not (all(isinstance(i, basestring) for i in j))):
                raise ValueError("You have to pass a list (or tuple) of lists "
                                 "of strings as retrieve_singlefile_list")
        self._set_attr('retrieve_singlefile_list', retrieve_singlefile_list)

    def _get_retrieve_singlefile_list(self):
        """
        Get the list of files to be retrieved from the cluster and stored as
        SinglefileData's (or subclasses of it).
        Their path is relative to the remote workdirectory path.

        :return: a list of lists of strings for 1) linknames,
                 2) Singlefile subclass name 3) file names
        """
        return self.get_attr('retrieve_singlefile_list', None)

    def _set_job_id(self, job_id):
        """
        Always set as a string
        """
        if self.get_state() != calc_states.SUBMITTING:
            raise ModificationNotAllowed(
                "Cannot set the job id if you are not "
                "submitting the calculation (current state is "
                "{})".format(self.get_state())
            )

        return self._set_attr('job_id', unicode(job_id))

    def get_job_id(self):
        """
        Get the scheduler job id of the calculation.

        :return: a string
        """
        return self.get_attr('job_id', None)

    def _set_scheduler_state(self, state):
        # I don't do any test here on the possible valid values,
        # I just convert it to a string
        from aiida.utils import timezone

        self._set_attr('scheduler_state', unicode(state))
        self._set_attr('scheduler_lastchecktime', timezone.now())

    def get_scheduler_state(self):
        """
        Return the status of the calculation according to the cluster scheduler.

        :return: a string.
        """
        return self.get_attr('scheduler_state', None)

    def _get_scheduler_lastchecktime(self):
        """
        Return the time of the last update of the scheduler state by the daemon,
        or None if it was never set.

        :return: a datetime object.
        """
        return self.get_attr('scheduler_lastchecktime', None)

    def _set_last_jobinfo(self, last_jobinfo):
        import pickle

        self._set_attr('last_jobinfo', last_jobinfo.serialize())

    def _get_last_jobinfo(self):
        """
        Get the last information asked to the scheduler
        about the status of the job.

        :return: a JobInfo object (that closely resembles a dictionary) or None.
        """
        import pickle
        from aiida.scheduler.datastructures import JobInfo

        last_jobinfo_serialized = self.get_attr('last_jobinfo', None)
        if last_jobinfo_serialized is not None:
            jobinfo = JobInfo()
            jobinfo.load_from_serialized(last_jobinfo_serialized)
            return jobinfo
        else:
            return None

    projection_to_qb_tag_map = {
        'pk': ('calculation', 'id'),
        'ctime': ('calculation', 'ctime'),
        'mtime': ('calculation', 'mtime'),
        'sched': ('calculation', 'attributes.scheduler_state'),
        'state': ('calculation', 'state'),
        'type': ('calculation', 'type'),
        'description': ('calculation', 'description'),
        'label': ('calculation', 'label'),
        'uuid': ('calculation', 'uuid'),
        'user': ('user', 'email'),
        'computer': ('computer', 'name')
    }

    @classmethod
    def _list_calculations(
            cls, states=None, past_days=None, group=None,
            group_pk=None, all_users=False, pks=tuple(),
            relative_ctime=True, with_scheduler_state=False,
            order_by=None, limit=None,
            projections=('pk', 'state', 'ctime', 'sched', 'computer', 'type')
    ):
        """
        Print a description of the AiiDA calculations.

        :param states: a list of string with states. If set, print only the
            calculations in the states "states", otherwise shows all.
            Default = None.
        :param past_days: If specified, show only calculations that were
            created in the given number of past days.
        :param group: If specified, show only calculations belonging to a
            user-defined group with the given name.
            Can use colons to separate the group name from the type,
            as specified in :py:meth:`aiida.orm.group.Group.get_from_string`
            method.
        :param group_pk: If specified, show only calculations belonging to a
            user-defined group with the given PK.
        :param pks: if specified, must be a list of integers, and only
            calculations within that list are shown. Otherwise, all
            calculations are shown.
            If specified, sets state to None and ignores the
            value of the ``past_days`` option.")
        :param relative_ctime: if true, prints the creation time relative from now.
                               (like 2days ago). Default = True
        :param all_users: if True, list calculation belonging to all users.
                           Default = False

        :return: a string with description of calculations.
        """

        from aiida.orm.querybuilder import QueryBuilder
        from tabulate import tabulate

        projection_label_dict = {
            'pk': 'PK',
            'state': 'State',
            'ctime': 'Creation',
            'mtime': 'Modification',
            'sched': 'Sched. state',
            'computer': 'Computer',
            'type': 'Type',
            'description': 'Description',
            'label': 'Label',
            'uuid': 'UUID',
            'user': 'User',
        }

        now = timezone.now()

        # Let's check the states:
        if states:
            for state in states:
                if state not in calc_states:
                    return "Invalid state provided: {}.".format(state)

        # Let's check if there is something to order_by:
        valid_order_parameters = (None, 'id', 'ctime')
        assert order_by in valid_order_parameters, \
            "invalid order by parameter {}\n" \
            "valid parameters are:\n".format(order_by, valid_order_parameters)

        # Limit:
        if limit is not None:
            assert isinstance(limit, int), \
                "Limit (set to {}) has to be an integer or None".format(limit)

        print(cls._get_last_daemon_check_string(now))

        calculation_filters = {}

        # filter for calculation pks:
        if pks:
            calculation_filters['id'] = {'in': pks}
            group_filters = None
        else:
            # The wanted behavior:
            # You know what you're looking for and specify pks,
            # Otherwise the other filters apply.
            # Open question: Is that the best way?

            # filter for states:
            if states:
                calculation_filters['state'] = {'in': states}

            # Filter on the users, if not all users
            if not all_users:
                user_id = get_automatic_user().id
                calculation_filters['user_id'] = {'==': user_id}

            if past_days is not None:
                n_days_ago = now - datetime.timedelta(days=past_days)
                calculation_filters['ctime'] = {'>': n_days_ago}

            # Filter on the group, either name or by pks
            if group:
                group_filters = {'name': {'like': '%{}%'.format(group)}}
            elif group_pk:
                group_filters = {'id': {'==': group_pk}}
            else:
                group_filters = None

        calc_list_header = [projection_label_dict[p] for p in projections]

        qb = QueryBuilder()
        qb.append(
            cls,
            filters=calculation_filters,
            tag='calculation'
        )
        if group_filters is not None:
            qb.append(type="group", filters=group_filters,
                      group_of="calculation")
        qb.append(type="computer", computer_of='calculation', tag='computer')
        qb.append(type="user", creator_of="calculation", tag="user")
        # The joining is done
        # Now the projections:
        projections_dict = {'calculation': [], 'user': [], 'computer': []}

        for k, v in [cls.projection_to_qb_tag_map[p] for p in projections]:
            projections_dict[k].append(v)

        if 'state' in projections:
            projections_dict['calculation'].append('attributes.state')
        for k, v in projections_dict.iteritems():
            qb.add_projection(k, v)

        # ORDER
        if order_by is not None:
            qb.order_by({'calculation': [order_by]})

        # LIMIT
        if limit is not None:
            qb.limit(limit)

        results_generator = qb.iterdict()

        counter = 0
        while True:
            calc_list_data = []
            try:
                for i in range(100):
                    res = results_generator.next()
                    row = cls._get_calculation_info_row(
                        res, projections, now if relative_ctime else None)

                    # Build the row of information
                    calc_list_data.append(row)

                    counter += 1

                print(tabulate(calc_list_data, headers=calc_list_header))

            except StopIteration:
                print(tabulate(calc_list_data, headers=calc_list_header))
                break

        print("\nTotal results: {}\n".format(counter))

    @classmethod
    def _get_last_daemon_check_string(cls, since):
        """
        Get a string showing the how long it has been since the daemon was
        last ticked relative to a particular timepoint.

        :param since: The timepoint to get the last check time since.
        :return: A string indicating the elapsed period, or an information
        message.
        """
        from aiida.daemon.timestamps import get_last_daemon_timestamp

        # get the last daemon check:
        try:
            last_daemon_check = \
                get_last_daemon_timestamp('updater', when='stop')
        except ValueError:
            last_check_string = (
                "# Last daemon state_updater check: "
                "(Error while retrieving the information)"
            )
        else:
            if last_daemon_check is None:
                last_check_string = "# Last daemon state_updater check: (Never)"
            else:
                last_check_string = (
                    "# Last daemon state_updater check: "
                    "{} ({})".format(
                        str_timedelta(
                            timezone.delta(last_daemon_check, since),
                            negative_to_zero=True
                        ),
                        timezone.localtime(
                            last_daemon_check
                        ).strftime("at %H:%M:%S on %Y-%m-%d")
                    )
                )

        return last_check_string

    @classmethod
    def _get_calculation_info_row(cls, res, projections, times_since=None):
        """
        Get a row of information about a calculation.

        :param res: Results from the calculations query.
        :type res: dict
        :param times_since: Times are relative to this timepoint, if None then
            absolute times will be used.
        :param projections: The projections used in the calculation query
        :type projections: list
        :type times_since: :class:`datetime.datetime`
        :return: A list of string with information about the calculation.
        """
        d = copy.deepcopy(res)

        try:
            d['calculation']['type'] = from_type_to_pluginclassname(
                d['calculation']['type']
            ).rsplit(".", 1)[0].lstrip('calculation.job.')
        except KeyError:
            pass
        for proj in ('ctime', 'mtime'):
            try:
                time = d['calculation'][proj]
                if times_since:
                    dt = timezone.delta(time, times_since)
                    d['calculation'][proj] = str_timedelta(
                        dt, negative_to_zero=True, max_num_fields=1)
                else:
                    d['calculation'][proj] = " ".join([
                        timezone.localtime(time).isoformat().split('T')[0],
                        timezone.localtime(time).isoformat().split('T')[
                            1].split('.')[0].rsplit(":", 1)[0]])
            except (KeyError, ValueError):
                pass
        try:
            if d['calculation']['state'] == calc_states.IMPORTED:
                d['calculation']['state'] = d['calculation']['attributes.state'] or "UNKNOWN"
        except KeyError:
            pass

        return [d[cls.projection_to_qb_tag_map[p][0]][cls.projection_to_qb_tag_map[p][1]]
                for p in projections]

    @classmethod
    def _get_all_with_state(
            cls, state, computer=None, user=None,
            only_computer_user_pairs=False,
            only_enabled=True, limit=None
    ):
        """
        Filter all calculations with a given state.

        Issue a warning if the state is not in the list of valid states.

        :param string state: The state to be used to filter (should be a string among
                those defined in aiida.common.datastructures.calc_states)
        :param computer: a Django DbComputer entry, or a Computer object, of a
                computer in the DbComputer table.
                A string for the hostname is also valid.
        :param user: a Django entry (or its pk) of a user in the DbUser table;
                if present, the results are restricted to calculations of that
                specific user
        :param bool only_computer_user_pairs: if False (default) return a queryset
                where each element is a suitable instance of Node (it should
                be an instance of Calculation, if everything goes right!)
                If True, return only a list of tuples, where each tuple is
                in the format
                ('dbcomputer__id', 'user__id')
                [where the IDs are the IDs of the respective tables]
        :param int limit: Limit the number of rows returned

        :return: a list of calculation objects matching the filters.
        """
        # I assume that calc_states are strings. If this changes in the future,
        # update the filter below from dbattributes__tval to the correct field.
        from aiida.orm.computer import Computer
        from aiida.orm.user import User
        from aiida.orm.querybuilder import QueryBuilder

        if state not in calc_states:
            cls._logger.warning("querying for calculation state='{}', but it "
                                "is not a valid calculation state".format(state))

        calcfilter = {'state': {'==': state}}
        computerfilter = {"enabled": {'==': True}}
        userfilter = {}

        if computer is None:
            pass
        elif isinstance(computer, int):
            # An ID was provided
            computerfilter.update({'id': {'==': computer}})
        elif isinstance(computer, Computer):
            computerfilter.update({'id': {'==': computer.pk}})
        else:
            try:
                computerfilter.update({'id': {'==': computer.id}})
            except AttributeError as e:
                raise Exception(
                    "{} is not a valid computer\n{}".format(computer, e)
                )

        if user is None:
            pass
        elif isinstance(user, int):
            userfilter.update({'id': {'==': user}})
        else:
            try:
                userfilter.update({'id': {'==': int(user.id)}})
                # Is that safe?
            except:
                raise Exception("{} is not a valid user".format(user))

        qb = QueryBuilder()
        qb.append(type="computer", tag='computer', filters=computerfilter)
        qb.append(cls, filters=calcfilter, tag='calc', has_computer='computer')
        qb.append(type="user", tag='user', filters=userfilter,
                  creator_of="calc")

        if only_computer_user_pairs:
            qb.add_projection("computer", "*")
            qb.add_projection("user", "*")
            returnresult = qb.distinct().all()
        else:
            qb.add_projection("calc", "*")
            if limit is not None:
                qb.limit(limit)
            returnresult = qb.all()
            returnresult = zip(*returnresult)[0]
        return returnresult

    def _prepare_for_submission(self, tempfolder, inputdict):
        """
        This is the routine to be called when you want to create
        the input files and related stuff with a plugin.

        Args:
            tempfolder: a aiida.common.folders.Folder subclass where
                the plugin should put all its files.
            inputdict: A dictionary where
                each key is an input link name and each value an AiiDA
                node, as it would be returned by the
                self.get_inputs_dict() method (with the Code!).
                The advantage of having this explicitly passed is that this
                allows to choose outside which nodes to use, and whether to
                use also unstored nodes, e.g. in a test_submit phase.

        TODO: document what it has to return (probably a CalcInfo object)
              and what is the behavior on the tempfolder
        """
        raise NotImplementedError

    def _get_authinfo(self):
        from aiida.backends.utils import get_authinfo
        from aiida.common.exceptions import NotExistent

        computer = self.get_computer()
        if computer is None:
            raise NotExistent("No computer has been set for this calculation")

        return get_authinfo(computer=computer._dbcomputer,
                            aiidauser=self.dbnode.user)

    def _get_transport(self):
        """
        Return the transport for this calculation.
        """
        return self._get_authinfo().get_transport()

    def submit(self):
        """
        Puts the calculation in the TOSUBMIT status.

        Actual submission is performed by the daemon.
        """
        from aiida.common.exceptions import InvalidOperation

        current_state = self.get_state()
        if current_state != calc_states.NEW:
            raise InvalidOperation("Cannot submit a calculation not in {} "
                                   "state (the current state is {})"
                                   .format(calc_states.NEW, current_state))

        self._set_state(calc_states.TOSUBMIT)

    def set_parser_name(self, parser):
        """
        Set a string for the output parser
        Can be None if no output plugin is available or needed.

        :param parser: a string identifying the module of the parser.
              Such module must be located within the folder 'aiida/parsers/plugins'
        """
        self._set_attr('parser', parser)

    def get_parser_name(self):
        """
        Return a string locating the module that contains
        the output parser of this calculation, that will be searched
        in the 'aiida/parsers/plugins' directory. None if no parser is needed/set.

        :return: a string.
        """
        from aiida.parsers import ParserFactory

        return self.get_attr('parser', None)

    def get_parserclass(self):
        """
        Return the output parser object for this calculation, or None
        if no parser is set.

        :return: a Parser class.
        :raise: MissingPluginError from ParserFactory no plugin is found.
        """
        from aiida.parsers import ParserFactory

        parser_name = self.get_parser_name()

        if parser_name is not None:
            return ParserFactory(parser_name)
        else:
            return None

    def _set_linkname_retrieved(self, linkname):
        """
        Set the linkname of the retrieved data folder object.

        :param linkname: a string.
        """
        self._set_attr('linkname_retrieved', linkname)

    def _get_linkname_retrieved(self):
        """
        Get the linkname of the retrieved data folder object.

        :return: a string
        """
        return self.get_attr('linkname_retrieved')

    def get_retrieved_node(self):
        """
        Return the retrieved data folder, if present.

        :return: the retrieved data folder object, or None if no such output
            node is found.

        :raise MultipleObjectsError: if more than one output node is found.
        """
        from aiida.common.exceptions import MultipleObjectsError
        from aiida.orm.data.folder import FolderData

        outputs = self.get_outputs(also_labels=True)

        retrieved_node = None
        retrieved_linkname = self._get_linkname_retrieved()

        for label, node in outputs:
            if label == retrieved_linkname:
                if retrieved_node is None:
                    retrieved_node = node
                else:
                    raise MultipleObjectsError("More than one output node "
                                               "with label '{}' for calc with pk= {}".format(
                        retrieved_linkname, self.pk))

        if retrieved_node is None:
            return None

        if not isinstance(retrieved_node, FolderData):
            raise TypeError("The retrieved node of calc with pk= {} is not of "
                            "type FolderData".format(self.pk))

        return retrieved_node

    def kill(self):
        """
        Kill a calculation on the cluster.

        Can only be called if the calculation is in status WITHSCHEDULER.

        The command tries to run the kill command as provided by the scheduler,
        and raises an exception is something goes wrong.
        No changes of calculation status are done (they will be done later by
        the calculation manager).

        .. todo: if the status is TOSUBMIT, check with some lock that it is not
            actually being submitted at the same time in another thread.
        """
        # TODO: Check if we want to add a status "KILLED" or something similar.
        from aiida.common.exceptions import (InvalidOperation,
                                             RemoteOperationError)

        old_state = self.get_state()

        if (old_state == calc_states.NEW or old_state == calc_states.TOSUBMIT):
            self._set_state(calc_states.FAILED)
            self.logger.warning(
                "Calculation {} killed by the user "
                "(it was in {} state)".format(self.pk, old_state))
            return

        if old_state != calc_states.WITHSCHEDULER:
            raise InvalidOperation("Cannot kill a calculation in {} state"
                                   .format(old_state))

        # I get the scheduler plugin class and initialize it with the correct
        # transport
        computer = self.get_computer()
        t = self._get_transport()
        s = computer.get_scheduler()
        s.set_transport(t)

        # And I call the proper kill method for the job ID of this calculation
        with t:
            retval = s.kill(self.get_job_id())

        # Raise error is something went wrong
        if not retval:
            raise RemoteOperationError(
                "An error occurred while trying to kill "
                "calculation {} (jobid {}), see log "
                "(maybe the calculation already finished?)"
                    .format(self.pk, self.get_job_id()))
        else:
            # Do not set the state, but let the parser do its job
            # self._set_state(calc_states.FAILED)
            self._logger.warning(
                "Calculation {} killed by the user "
                "(it was {})".format(self.pk,
                                     calc_states.WITHSCHEDULER))

    def _presubmit(self, folder, use_unstored_links=False):
        """
        Prepares the calculation folder with all inputs, ready to be copied to the cluster
        :param folder: a SandboxFolder, empty in input, that will be filled with
          calculation input files and the scheduling script.
        :param use_unstored_links: if set to True, it will the presubmit will
          try to launch the calculation using also unstored nodes linked to the
          Calculation only in the cache.

        :return calcinfo: the CalcInfo object containing the information
          needed by the daemon to handle operations.
        :return script_filename: the name of the job scheduler script
        """
        import os
        import StringIO
        import json

        from aiida.common.exceptions import (NotExistent,
                                             PluginInternalError,
                                             ValidationError)
        from aiida.scheduler.datastructures import JobTemplate
        from aiida.common.utils import validate_list_of_string_tuples
        from aiida.orm.computer import Computer
        from aiida.orm import DataFactory
        from aiida.common.datastructures import CodeInfo, code_run_modes
        from aiida.orm.code import Code
        from aiida.orm.utils import load_node

        computer = self.get_computer()
        inputdict = self.get_inputs_dict(
            only_in_db=not use_unstored_links, link_type=LinkType.INPUT)

        codes = [_ for _ in inputdict.itervalues() if isinstance(_, Code)]

        calcinfo = self._prepare_for_submission(folder, inputdict)
        s = computer.get_scheduler()

        for code in codes:
            if code.is_local():
                if code.get_local_executable() in folder.get_content_list():
                    raise PluginInternalError(
                        "The plugin created a file {} that is also "
                        "the executable name!".format(
                            code.get_local_executable()))

        # I create the job template to pass to the scheduler
        job_tmpl = JobTemplate()
        ## TODO: in the future, allow to customize the following variables
        job_tmpl.submit_as_hold = False
        job_tmpl.rerunnable = False
        job_tmpl.job_environment = {}
        # 'email', 'email_on_started', 'email_on_terminated',
        job_tmpl.job_name = 'aiida-{}'.format(self.pk)
        job_tmpl.sched_output_path = self._SCHED_OUTPUT_FILE
        if self._SCHED_ERROR_FILE == self._SCHED_OUTPUT_FILE:
            job_tmpl.sched_join_files = True
        else:
            job_tmpl.sched_error_path = self._SCHED_ERROR_FILE
            job_tmpl.sched_join_files = False

        # Set retrieve path, add also scheduler STDOUT and STDERR
        retrieve_list = (calcinfo.retrieve_list
                         if calcinfo.retrieve_list is not None
                         else [])
        if (job_tmpl.sched_output_path is not None and
                    job_tmpl.sched_output_path not in retrieve_list):
            retrieve_list.append(job_tmpl.sched_output_path)
        if not job_tmpl.sched_join_files:
            if (job_tmpl.sched_error_path is not None and
                        job_tmpl.sched_error_path not in retrieve_list):
                retrieve_list.append(job_tmpl.sched_error_path)
        self._set_retrieve_list(retrieve_list)

        retrieve_singlefile_list = (calcinfo.retrieve_singlefile_list
                                    if calcinfo.retrieve_singlefile_list is not None
                                    else [])
        # a validation on the subclasses of retrieve_singlefile_list
        SinglefileData = DataFactory('singlefile')
        for _, subclassname, _ in retrieve_singlefile_list:
            FileSubclass = DataFactory(subclassname)
            if not issubclass(FileSubclass, SinglefileData):
                raise PluginInternalError("[presubmission of calc {}] "
                                          "retrieve_singlefile_list subclass problem: "
                                          "{} is not subclass of SinglefileData".format(
                    self.pk, FileSubclass.__name__))
        self._set_retrieve_singlefile_list(retrieve_singlefile_list)

        # the if is done so that if the method returns None, this is
        # not added. This has two advantages:
        # - it does not add too many \n\n if most of the prepend_text are empty
        # - most importantly, skips the cases in which one of the methods
        #   would return None, in which case the join method would raise
        #   an exception
        job_tmpl.prepend_text = "\n\n".join(_ for _ in
                                            [computer.get_prepend_text()] +
                                            [code.get_prepend_text() for code in codes] +
                                            [calcinfo.prepend_text,
                                             self.get_prepend_text()] if _)

        job_tmpl.append_text = "\n\n".join(_ for _ in
                                           [self.get_append_text(),
                                            calcinfo.append_text,
                                            code.get_append_text(),
                                            computer.get_append_text()] if _)

        # Set resources, also with get_default_mpiprocs_per_machine
        resources_dict = self.get_resources(full=True)
        job_tmpl.job_resource = s.create_job_resource(**resources_dict)

        subst_dict = {'tot_num_mpiprocs':
                          job_tmpl.job_resource.get_tot_num_mpiprocs()}

        for k, v in job_tmpl.job_resource.iteritems():
            subst_dict[k] = v
        mpi_args = [arg.format(**subst_dict) for arg in
                    computer.get_mpirun_command()]
        extra_mpirun_params = self.get_mpirun_extra_params()  # this is the same for all codes in the same calc

        ########################################################################
        #         if self.get_withmpi():
        #             job_tmpl.argv = (mpi_args + extra_mpirun_params +
        #                              [code.get_execname()] +
        #                              (calcinfo.cmdline_params if
        #                               calcinfo.cmdline_params is not None else []))
        #         else:
        #             job_tmpl.argv = [code.get_execname()] + (
        #                 calcinfo.cmdline_params if
        #                 calcinfo.cmdline_params is not None else [])
        #         job_tmpl.stdin_name = calcinfo.stdin_name
        #         job_tmpl.stdout_name = calcinfo.stdout_name

        # set the codes_info
        if not isinstance(calcinfo.codes_info, (list, tuple)):
            raise PluginInternalError("codes_info passed to CalcInfo must be a "
                                      "list of CalcInfo objects")

        codes_info = []
        for code_info in calcinfo.codes_info:

            if not isinstance(code_info, CodeInfo):
                raise PluginInternalError("Invalid codes_info, must be a list "
                                          "of CodeInfo objects")

            if code_info.code_uuid is None:
                raise PluginInternalError("CalcInfo should have "
                                          "the information of the code "
                                          "to be launched")
            this_code = load_node(code_info.code_uuid, parent_class=Code)

            this_withmpi = code_info.withmpi  # to decide better how to set the default
            if this_withmpi is None:
                if len(calcinfo.codes_info) > 1:
                    raise PluginInternalError("For more than one code, it is "
                                              "necessary to set withmpi in "
                                              "codes_info")
                else:
                    this_withmpi = self.get_withmpi()

            if this_withmpi:
                this_argv = (mpi_args + extra_mpirun_params +
                             [this_code.get_execname()] +
                             (code_info.cmdline_params if
                              code_info.cmdline_params is not None else []))
            else:
                this_argv = [this_code.get_execname()] + (
                    code_info.cmdline_params if
                    code_info.cmdline_params is not None else [])

            this_stdin_name = code_info.stdin_name
            this_stdout_name = code_info.stdout_name
            this_stderr_name = code_info.stderr_name
            this_join_files = code_info.join_files

            # overwrite the old cmdline_params and add codename and mpirun stuff
            code_info.cmdline_params = this_argv

            codes_info.append(code_info)
        job_tmpl.codes_info = codes_info

        # set the codes execution mode

        if len(codes) > 1:
            try:
                job_tmpl.codes_run_mode = calcinfo.codes_run_mode
            except KeyError:
                raise PluginInternalError("Need to set the order of the code "
                                          "execution (parallel or serial?)")
        else:
            job_tmpl.codes_run_mode = code_run_modes.SERIAL
        ########################################################################

        custom_sched_commands = self.get_custom_scheduler_commands()
        if custom_sched_commands:
            job_tmpl.custom_scheduler_commands = custom_sched_commands

        job_tmpl.import_sys_environment = self.get_import_sys_environment()

        job_tmpl.job_environment = self.get_environment_variables()

        queue_name = self.get_queue_name()
        if queue_name is not None:
            job_tmpl.queue_name = queue_name
        priority = self.get_priority()
        if priority is not None:
            job_tmpl.priority = priority
        max_memory_kb = self.get_max_memory_kb()
        if max_memory_kb is not None:
            job_tmpl.max_memory_kb = max_memory_kb
        max_wallclock_seconds = self.get_max_wallclock_seconds()
        if max_wallclock_seconds is not None:
            job_tmpl.max_wallclock_seconds = max_wallclock_seconds
        max_memory_kb = self.get_max_memory_kb()
        if max_memory_kb is not None:
            job_tmpl.max_memory_kb = max_memory_kb

        # TODO: give possibility to use a different name??
        script_filename = '_aiidasubmit.sh'
        script_content = s.get_submit_script(job_tmpl)
        folder.create_file_from_filelike(
            StringIO.StringIO(script_content), script_filename)

        subfolder = folder.get_subfolder('.aiida', create=True)
        subfolder.create_file_from_filelike(
            StringIO.StringIO(json.dumps(job_tmpl)), 'job_tmpl.json')
        subfolder.create_file_from_filelike(
            StringIO.StringIO(json.dumps(calcinfo)), 'calcinfo.json')

        if calcinfo.local_copy_list is None:
            calcinfo.local_copy_list = []

        if calcinfo.remote_copy_list is None:
            calcinfo.remote_copy_list = []

        # Some validation
        this_pk = self.pk if self.pk is not None else "[UNSTORED]"
        local_copy_list = calcinfo.local_copy_list
        try:
            validate_list_of_string_tuples(local_copy_list,
                                           tuple_length=2)
        except ValidationError as e:
            raise PluginInternalError(
                "[presubmission of calc {}] "
                "local_copy_list format problem: {}".format(this_pk, e.message))

        remote_copy_list = calcinfo.remote_copy_list
        try:
            validate_list_of_string_tuples(remote_copy_list,
                                           tuple_length=3)
        except ValidationError as e:
            raise PluginInternalError(
                "[presubmission of calc {}] "
                "remote_copy_list format problem: {}".
                    format(this_pk, e.message))

        for (remote_computer_uuid, remote_abs_path,
             dest_rel_path) in remote_copy_list:
            try:
                remote_computer = Computer(uuid=remote_computer_uuid)
            except NotExistent:
                raise PluginInternalError(
                    "[presubmission of calc {}] "
                    "The remote copy requires a computer with UUID={}"
                    "but no such computer was found in the "
                    "database".format(this_pk, remote_computer_uuid))
            if os.path.isabs(dest_rel_path):
                raise PluginInternalError(
                    "[presubmission of calc {}] "
                    "The destination path of the remote copy "
                    "is absolute! ({})".format(this_pk, dest_rel_path))

        return calcinfo, script_filename

    @property
    def res(self):
        """
        To be used to get direct access to the parsed parameters.

        :return: an instance of the CalculationResultManager.

        :note: a practical example on how it is meant to be used: let's say that there is a key 'energy'
          in the dictionary of the parsed results which contains a list of floats.
          The command `calc.res.energy` will return such a list.
        """
        return CalculationResultManager(self)

    def submit_test(self, folder=None, subfolder_name=None):
        """
        Test submission, creating the files in a local folder.

        :note: this submit_test function does not require any node
            (neither the calculation nor the input links) to be stored yet.

        :param folder: A Folder object, within which each calculation files
            are created; if not passed, a subfolder 'submit_test' of the current
            folder is used.
        :param subfolder_name: the name of the subfolder to use for this
            calculation (within Folder). If not passed, a unique string
            starting with the date and time in the format ``yymmdd-HHMMSS-``
            is used.
        """
        import os
        import errno
        from aiida.utils import timezone

        from aiida.transport.plugins.local import LocalTransport
        from aiida.orm.computer import Computer
        from aiida.common.folders import Folder
        from aiida.common.exceptions import NotExistent

        if folder is None:
            folder = Folder(os.path.abspath('submit_test'))

        # In case it is not created yet
        folder.create()

        if subfolder_name is None:
            subfolder_basename = timezone.localtime(timezone.now()).strftime(
                '%Y%m%d')
        else:
            subfolder_basename = subfolder_name

        ## Find a new subfolder.
        ## I do not user tempfile.mkdtemp, because it puts random characters
        # at the end of the directory name, therefore making difficult to
        # understand the order in which directories where stored
        counter = 0
        while True:
            counter += 1
            subfolder_path = os.path.join(folder.abspath,
                                          "{}-{:05d}".format(subfolder_basename,
                                                             counter))
            # This check just tried to avoid to try to create the folder
            # (hoping that a test of existence is faster than a
            # test and failure in directory creation)
            # But it could be removed
            if os.path.exists(subfolder_path):
                continue

            try:
                # Directory found, and created
                os.mkdir(subfolder_path)
                break
            except OSError as e:
                if e.errno == errno.EEXIST:
                    # The directory has been created in the meantime,
                    # retry with a new one...
                    continue
                # Some other error: raise, so we avoid infinite loops
                # e.g. if we are in a folder in which we do not have write
                # permissions
                raise

        subfolder = folder.get_subfolder(
            os.path.relpath(subfolder_path, folder.abspath),
            reset_limit=True)

        # I use the local transport where possible, to be as similar
        # as possible to a real submission
        t = LocalTransport()
        with t:
            t.chdir(subfolder.abspath)

            calcinfo, script_filename = self._presubmit(
                subfolder, use_unstored_links=True)

            code = self.get_code()

            if code.is_local():
                # Note: this will possibly overwrite files
                for f in code.get_folder_list():
                    t.put(code.get_abs_path(f), f)
                t.chmod(code.get_local_executable(), 0755)  # rwxr-xr-x

            local_copy_list = calcinfo.local_copy_list
            remote_copy_list = calcinfo.remote_copy_list
            remote_symlink_list = calcinfo.remote_symlink_list

            for src_abs_path, dest_rel_path in local_copy_list:
                t.put(src_abs_path, dest_rel_path)

            if remote_copy_list:
                with open(os.path.join(subfolder.abspath,
                                       '_aiida_remote_copy_list.txt'),
                          'w') as f:
                    for (remote_computer_uuid, remote_abs_path,
                         dest_rel_path) in remote_copy_list:
                        try:
                            remote_computer = Computer(
                                uuid=remote_computer_uuid)
                        except NotExistent:
                            remote_computer = "[unknown]"
                        f.write("* I WOULD REMOTELY COPY "
                                "FILES/DIRS FROM COMPUTER {} (UUID {}) "
                                "FROM {} TO {}\n".format(remote_computer.name,
                                                         remote_computer_uuid,
                                                         remote_abs_path,
                                                         dest_rel_path))

            if remote_symlink_list:
                with open(os.path.join(subfolder.abspath,
                                       '_aiida_remote_symlink_list.txt'),
                          'w') as f:
                    for (remote_computer_uuid, remote_abs_path,
                         dest_rel_path) in remote_symlink_list:
                        try:
                            remote_computer = Computer(
                                uuid=remote_computer_uuid)
                        except NotExistent:
                            remote_computer = "[unknown]"
                        f.write("* I WOULD PUT SYMBOLIC LINKS FOR "
                                "FILES/DIRS FROM COMPUTER {} (UUID {}) "
                                "FROM {} TO {}\n".format(remote_computer.name,
                                                         remote_computer_uuid,
                                                         remote_abs_path,
                                                         dest_rel_path))

        return subfolder, script_filename

    def get_scheduler_output(self):
        """
        Return the output of the scheduler output (a string) if the calculation
        has finished, and output node is present, and the output of the
        scheduler was retrieved.

        Return None otherwise.
        """
        from aiida.common.exceptions import NotExistent

        # Shortcut if no error file is set
        if self._SCHED_OUTPUT_FILE is None:
            return None

        retrieved_node = self.get_retrieved_node()
        if retrieved_node is None:
            return None

        try:
            outfile_content = retrieved_node.get_file_content(
                self._SCHED_OUTPUT_FILE)
        except (NotExistent):
            # Return None if no file is found
            return None

        return outfile_content

    def get_scheduler_error(self):
        """
        Return the output of the scheduler error (a string) if the calculation
        has finished, and output node is present, and the output of the
        scheduler was retrieved.

        Return None otherwise.
        """
        from aiida.common.exceptions import NotExistent

        # Shortcut if no error file is set
        if self._SCHED_ERROR_FILE is None:
            return None

        retrieved_node = self.get_retrieved_node()
        if retrieved_node is None:
            return None

        try:
            errfile_content = retrieved_node.get_file_content(
                self._SCHED_ERROR_FILE)
        except (NotExistent):
            # Return None if no file is found
            return None

        return errfile_content


class CalculationResultManager(object):
    """
    An object used internally to interface the calculation object with the Parser
    and consequentially with the ParameterData object result.
    It shouldn't be used explicitly by a user.
    """

    def __init__(self, calc):
        """
        :param calc: the calculation object.
        """
        # Import parser base class
        from aiida.parsers import Parser

        # Possibly add checks here
        self._calc = calc
        try:
            ParserClass = calc.get_parserclass()
            if ParserClass is None:
                # raise AttributeError("No output parser is attached to the calculation")
                self._parser = Parser(calc)
            else:
                self._parser = ParserClass(calc)
        except MissingPluginError:
            self._parser = Parser(calc)  # Use base class

    def __dir__(self):
        """
        Allow to list all valid attributes
        """
        from aiida.common.exceptions import UniquenessError

        try:
            calc_attributes = self._parser.get_result_keys()
        except UniquenessError:
            calc_attributes = []

        return sorted(set(list(dir(type(self))) + list(calc_attributes)))

    def __iter__(self):
        from aiida.common.exceptions import UniquenessError

        try:
            calc_attributes = self._parser.get_result_keys()
        except UniquenessError:
            calc_attributes = []

        for k in calc_attributes:
            yield k

    def _get_dict(self):
        """
        Return a dictionary of all results
        """
        return self._parser.get_result_dict()

    def __getattr__(self, name):
        """
        interface to get to the parser results as an attribute.

        :param name: name of the attribute to be asked to the parser results.
        """
        try:
            return self._parser.get_result(name)
        except AttributeError:
            raise AttributeError("Parser '{}' did not provide a result '{}'"
                                 .format(self._parser.__class__.__name__, name))

    def __getitem__(self, name):
        """
        interface to get to the parser results as a dictionary.

        :param name: name of the attribute to be asked to the parser results.
        """
        try:
            return self._parser.get_result(name)
        except AttributeError:
            raise KeyError("Parser '{}' did not provide a result '{}'"
                           .format(self._parser.__class__.__name__, name))
