# -*- coding: utf-8 -*-
from aiida.common.datastructures import calc_states
from aiida.common.exceptions import ModificationNotAllowed
from aiida.orm.calculation import Calculation

# TODO: set the following as properties of the Calculation
# 'email',
# 'email_on_started',
# 'email_on_terminated',
# 'rerunnable',
# 'resourceLimits',

__copyright__ = u"Copyright (c), 2015, ECOLE POLYTECHNIQUE FEDERALE DE LAUSANNE (Theory and Simulation of Materials (THEOS) and National Centre for Computational Design and Discovery of Novel Materials (NCCR MARVEL)), Switzerland and ROBERT BOSCH LLC, USA. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file"
__version__ = "0.5.0"
__contributors__ = "Andrea Cepellotti, Andrius Merkys, Boris Kozinsky, Eric Hontz, Gianluca Prandini, Giovanni Pizzi, Marco Dorigo, Martin Uhrin, Nicolas Mounet, Riccardo Sabatini"

_input_subfolder = 'raw_input'


class JobCalculation(Calculation):
    """
    This class provides the definition of an AiiDA calculation that is run
    remotely on a job scheduler.
    """

    def _init_internal_params(self):
        """
        Define here internal parameters that should be defined
        right after the __init__. This function is actually called
        by the __init__.

        :note: if you inherit this function, ALWAYS remember to
          call super()._init_internal_params() as the first thing
          in your inherited function.
        """
        super(JobCalculation, self)._init_internal_params()

        # By default, no output parser
        self._default_parser = None
        # Set default for the link to the retrieved folder (after calc is done)
        self._linkname_retrieved = 'retrieved'

        self._updatable_attributes = ('state', 'job_id', 'scheduler_state',
                                      'scheduler_lastchecktime',
                                      'last_jobinfo', 'remote_workdir', 'retrieve_list',
                                      'retrieve_singlefile_list')

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
        parent_dict = super(JobCalculation, self)._set_defaults

        parent_dict.update({
            "parser_name": self._default_parser,
            "_linkname_retrieved": self._linkname_retrieved})

        return parent_dict

    def store(self, *args, **kwargs):
        """
        Override the store() method to store also the calculation in the NEW
        state as soon as this is stored for the first time.
        """
        super(JobCalculation, self).store(*args, **kwargs)

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

        super(JobCalculation, self)._validate()

        if self.get_computer() is None:
            raise ValidationError("You did not specify any computer")

        if self.get_state() not in calc_states:
            raise ValidationError("Calculation state '{}' is not valid".format(
                self.get_state()))

        try:
            _ = self.get_parserclass()
        except MissingPluginError:
            raise ValidationError("No valid plugin found for the parser '{}'. "
                                  "Set the parser to None if you do not need an automatic "
                                  "parser.".format(self.get_parser_name()))

        computer = self.get_computer()
        s = computer.get_scheduler()
        try:
            _ = s.create_job_resource(**self.get_resources(full=True))
        except (TypeError, ValueError) as e:
            raise ValidationError("Invalid resources for the scheduler of the "
                                  "specified computer: {}".format(e.message))

        if not isinstance(self.get_withmpi(), bool):
            raise ValidationError(
                "withmpi property must be boolean! It in instead {}".format(str(type(self.get_withmpi()))))

    def _can_link_as_output(self, dest):
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

        return super(JobCalculation, self)._can_link_as_output(dest)

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
        To check if it's loading the system environment on the submission script.

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
                raise ValueError("Both the keys and the values of the "
                                 "dictionary passed to set_environment_variables must be "
                                 "strings.")

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
        """
        return self.get_attr('max_wallclock_seconds', None)

    def set_resources(self, resources_dict):
        """
        Set the dictionary of resources to be used by the scheduler plugin,
        like the number of nodes, cpus, ...
        This dictionary is scheduler-plugin dependent. Look at the documentation
        of the scheduler.
        (scheduler type can be found with calc.get_computer().get_scheduler_type() )
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
                resources_dict['default_mpiprocs_per_machine'] = def_cpus_machine

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

    def _add_link_from(self, src, label=None):
        '''
        Add a link with a code as destination. Add the additional
        contraint that this is only possible if the calculation
        is in state NEW.

        You can use the parameters of the base Node class, in particular the
        label parameter to label the link.

        :param src: a node of the database. It cannot be a Calculation object.
        :param str label: Name of the link. Default=None
        '''
        valid_states = [calc_states.NEW]

        if self.get_state() not in valid_states:
            raise ModificationNotAllowed(
                "Can add an input link to a JobCalculation only if it is in "
                "one of the following states: {}, it is instead {}".format(
                    valid_states, self.get_state()))

        return super(JobCalculation, self)._add_link_from(src, label)

    def _replace_link_from(self, src, label):
        '''
        Replace a link. Add the additional constratint that this is
        only possible if the calculation is in state NEW.

        :param src: a node of the database. It cannot be a Calculation object.
        :param str label: Name of the link.
        '''
        valid_states = [calc_states.NEW]

        if self.get_state() not in valid_states:
            raise ModificationNotAllowed(
                "Can replace an input link to a Jobalculation only if it is in "
                "one of the following states: {}, it is instead {}".format(
                    valid_states, self.get_state()))

        return super(JobCalculation, self)._replace_link_from(src, label)

    def _remove_link_from(self, label):
        '''
        Remove a link. Only possible if the calculation is in state NEW.

        :param str label: Name of the link to remove.
        '''
        valid_states = [calc_states.NEW]

        if self.get_state() not in valid_states:
            raise ModificationNotAllowed(
                "Can remove an input link to a calculation only if it is in one "
                "of the following states: {}, it is instead {}".format(
                    valid_states, self.get_state()))

        return super(JobCalculation, self)._remove_link_from(label)

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
        from django.db import transaction, IntegrityError

        from aiida.djsite.db.models import DbCalcState
        from aiida.common.datastructures import sort_states

        if self._to_be_stored:
            raise ModificationNotAllowed("Cannot set the calculation state "
                                         "before storing")

        if state not in calc_states:
            raise ValueError(
                "'{}' is not a valid calculation status".format(state))

        old_state = self.get_state()
        if old_state:
            state_sequence = [state, old_state]

            # sort from new to old: if they are equal, then it is a valid
            # advance in state (otherwise, we are going backwards...)
            if sort_states(state_sequence) != state_sequence:
                raise ModificationNotAllowed("Cannot change the state from {} "
                                             "to {}".format(old_state, state))

        try:
            with transaction.commit_on_success():
                new_state = DbCalcState(dbnode=self.dbnode, state=state).save()
        except IntegrityError:
            raise ModificationNotAllowed("Calculation pk= {} already transited through "
                                         "the state {}".format(self.pk, state))

        # For non-imported states, also set in the attribute (so that, if we
        # export, we can still see the original state the calculation had.
        if state != calc_states.IMPORTED:
            self._set_attr('state', state)

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
        from aiida.djsite.db.models import DbCalcState
        from aiida.common.exceptions import DbContentError
        from aiida.common.datastructures import sort_states

        if from_attribute:
            return self.get_attr('state', None)
        else:
            if self._to_be_stored:
                return calc_states.NEW
            else:
                this_calc_states = DbCalcState.objects.filter(
                    dbnode=self).values_list('state', flat=True)
                if not this_calc_states:
                    return None
                else:
                    try:
                        most_recent_state = sort_states(this_calc_states)[0]
                    except ValueError as e:
                        raise DbContentError("Error in the content of the "
                                             "DbCalcState table ({})".format(e.message))

                    return most_recent_state

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
            calc_states.TOSUBMIT, calc_states.SUBMITTING, calc_states.WITHSCHEDULER,
            calc_states.COMPUTED, calc_states.RETRIEVING, calc_states.PARSING]

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
        Get the path to the remote (on cluster) scratch folder of the calculation.

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
        # where the last number is used to decide the localname, see CalcInfo or execmanager

        if not (isinstance(retrieve_list, (tuple, list))):
            raise ValueError("You should pass a list/tuple")
        for item in retrieve_list:
            if not isinstance(item, basestring):
                if (not (isinstance(item, (tuple, list))) or
                            len(item) != 3):
                    raise ValueError("You should pass a list containing either "
                                     "strings or lists/tuples")
                if (not (isinstance(item[0], basestring)) or
                        not (isinstance(item[1], basestring)) or
                        not (isinstance(item[2], int))):
                    raise ValueError("You have to pass a list (or tuple) of "
                                     "lists, with remotepath(string), "
                                     "localpath(string) and depth (integer)")

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
            raise ModificationNotAllowed("Cannot set the job id if you are not "
                                         "submitting the calculation (current state is "
                                         "{})".format(self.get_state()))

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
        from django.utils import timezone

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
        Get the last information asked to the scheduler about the status of the job.

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

    @classmethod
    def _list_calculations(cls, states=None, past_days=None, group=None,
                           group_pk=None, all_users=False, pks=[],
                           relative_ctime=True):
        """
        Return a string with a description of the AiiDA calculations.

        .. todo:: does not support the query for the IMPORTED state (since it
          checks the state in the Attributes, not in the DbCalcState table).
          Decide which is the correct logi and implement the correct query.

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
        # I assume that calc_states are strings. If this changes in the future,
        # update the filter below from dbattributes__tval to the correct field.

        if states:
            for state in states:
                if state not in calc_states:
                    return "Invalid state provided: {}.".format(state)

        from django.utils import timezone
        import datetime
        from django.db.models import Q, F
        from aiida.djsite.db.models import DbNode, DbComputer, DbAuthInfo
        from aiida.djsite.utils import get_automatic_user
        from aiida.djsite.db.tasks import get_last_daemon_timestamp
        from aiida.common.utils import str_timedelta
        from aiida.orm.node import from_type_to_pluginclassname
        from aiida.orm import Group
        from aiida.common.exceptions import NotExistent

        warnings_list = []

        now = timezone.now()

        if pks:
            q_object = Q(pk__in=pks)
        else:
            q_object = Q()

            if group is not None:
                g_pk = Group.get_from_string(group).pk
                q_object.add(Q(dbgroups__pk=g_pk), Q.AND)

            if group_pk is not None:
                q_object.add(Q(dbgroups__pk=group_pk), Q.AND)

            if not all_users:
                q_object.add(Q(user=get_automatic_user()), Q.AND)

            if states is not None:
                q_object.add(Q(dbattributes__key='state',
                               dbattributes__tval__in=states, ), Q.AND)
            if past_days is not None:
                now = timezone.now()
                n_days_ago = now - datetime.timedelta(days=past_days)
                q_object.add(Q(ctime__gte=n_days_ago), Q.AND)

        calc_list_pk = list(cls.query(q_object).distinct().values_list('pk', flat=True))

        calc_list = cls.query(pk__in=calc_list_pk).order_by('ctime')

        from aiida.djsite.db.models import DbAttribute

        scheduler_states = dict(DbAttribute.objects.filter(dbnode__pk__in=calc_list_pk,
                                                           key='scheduler_state').values_list('dbnode__pk', 'tval'))

        # I do the query now, so that the list of pks gets cached
        calc_list_data = list(
            calc_list.filter(
                # dbcomputer__dbauthinfo__aiidauser=F('user')
            ).distinct().order_by('ctime').values(
                'pk', 'dbcomputer__name', 'ctime',
                'type', 'dbcomputer__enabled',
                'dbcomputer__pk',
                'user__pk'))
        list_comp_pk = [i['dbcomputer__pk'] for i in calc_list_data]
        list_aiduser_pk = [i['user__pk']
                           for i in calc_list_data]
        enabled_data = DbAuthInfo.objects.filter(
            dbcomputer__pk__in=list_comp_pk, aiidauser__pk__in=list_aiduser_pk
        ).values_list('dbcomputer__pk', 'aiidauser__pk', 'enabled')

        enabled_auth_dict = {(i[0], i[1]): i[2] for i in enabled_data}

        states = {c.pk: c._get_state_string() for c in calc_list}

        scheduler_lastcheck = dict(DbAttribute.objects.filter(
            dbnode__in=calc_list,
            key='scheduler_lastchecktime').values_list('dbnode__pk', 'dval'))

        ## Get the last daemon check
        try:
            last_daemon_check = get_last_daemon_timestamp('updater', when='stop')
        except ValueError:
            last_check_string = ("# Last daemon state_updater check: "
                                 "(Error while retrieving the information)")
        else:
            if last_daemon_check is None:
                last_check_string = "# Last daemon state_updater check: (Never)"
            else:
                last_check_string = ("# Last daemon state_updater check: "
                                     "{} ({})".format(
                    str_timedelta(now - last_daemon_check, negative_to_zero=True),
                    timezone.localtime(last_daemon_check).strftime("at %H:%M:%S on %Y-%m-%d")))

        disabled_ignorant_states = [
            None, calc_states.FINISHED, calc_states.SUBMISSIONFAILED,
            calc_states.RETRIEVALFAILED, calc_states.PARSINGFAILED,
            calc_states.FAILED
        ]

        if not calc_list:
            return last_check_string
        else:
            # first save a matrix of results to be printed
            res_str_list = [last_check_string]
            str_matrix = []
            title = ['# Pk', 'State', 'Creation',
                     'Sched. state', 'Computer', 'Type']
            str_matrix.append(title)
            len_title = [len(i) for i in title]

            for calcdata in calc_list_data:
                remote_state = "None"

                calc_state = states[calcdata['pk']]
                remote_computer = calcdata['dbcomputer__name']
                try:
                    sched_state = scheduler_states.get(calcdata['pk'], None)
                    if sched_state is None:
                        remote_state = "(unknown)"
                    else:
                        remote_state = '{}'.format(sched_state)
                        if calc_state == calc_states.WITHSCHEDULER:
                            last_check = scheduler_lastcheck.get(calcdata['pk'], None)
                            if last_check is not None:
                                when_string = " {}".format(
                                    str_timedelta(now - last_check, short=True,
                                                  negative_to_zero=True))
                                verb_string = "was "
                            else:
                                when_string = ""
                                verb_string = ""
                            remote_state = "{}{}{}".format(verb_string,
                                                           sched_state, when_string)
                except ValueError:
                    raise

                calc_module = from_type_to_pluginclassname(calcdata['type']).rsplit(".", 1)[0]
                prefix = 'calculation.job.'
                prefix_len = len(prefix)
                if calc_module.startswith(prefix):
                    calc_module = calc_module[prefix_len:].strip()

                if relative_ctime:
                    calc_ctime = str_timedelta(now - calcdata['ctime'],
                                               negative_to_zero=True,
                                               max_num_fields=1)
                else:
                    calc_ctime = " ".join([timezone.localtime(calcdata['ctime']).isoformat().split('T')[0],
                                           timezone.localtime(calcdata['ctime']).isoformat().split('T')[1].split('.')[
                                               0].rsplit(":", 1)[0]])

                the_state = states[calcdata['pk']]

                # decide if it is needed to print enabled/disabled information
                # By default, if the computer is not configured for the
                # given user, assume it is user_enabled
                user_enabled = enabled_auth_dict.get((calcdata['dbcomputer__pk'],
                                                      calcdata['user__pk']), True)
                global_enabled = calcdata["dbcomputer__enabled"]

                enabled = "" if (user_enabled and global_enabled or
                                 the_state in disabled_ignorant_states) else " [Disabled]"

                str_matrix.append([calcdata['pk'],
                                   the_state,
                                   calc_ctime,
                                   remote_state,
                                   remote_computer + "{}".format(enabled),
                                   calc_module
                                   ])

            # prepare a formatted text of minimal row length (to fit in terminals!)
            rows = []
            for j in range(len(str_matrix[0])):
                rows.append([len(str(i[j])) for i in str_matrix])
            line_lengths = [str(max(max(rows[i]), len_title[i])) for i in range(len(rows))]
            fmt_string = "{:<" + "}|{:<".join(line_lengths) + "}"
            for row in str_matrix:
                res_str_list.append(fmt_string.format(*[str(i) for i in row]))

            res_str_list += ["# {}".format(_) for _ in warnings_list]
            return "\n".join(res_str_list)

    @classmethod
    def _get_all_with_state(cls, state, computer=None, user=None,
                            only_computer_user_pairs=False):
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

        :return: a list of calculation objects matching the filters.
        """
        # I assume that calc_states are strings. If this changes in the future,
        # update the filter below from dbattributes__tval to the correct field.
        from aiida.orm import Computer

        if state not in calc_states:
            cls.logger.warning("querying for calculation state='{}', but it "
                               "is not a valid calculation state".format(state))

        kwargs = {}
        if computer is not None:
            # I convert it from various type of inputs
            # (string, DbComputer, Computer)
            # to a DbComputer type
            kwargs['dbcomputer'] = Computer.get(computer).dbcomputer
        if user is not None:
            kwargs['user'] = user

        queryresults = cls.query(
            dbattributes__key='state',
            dbattributes__tval=state,
            **kwargs)

        if only_computer_user_pairs:
            return queryresults.values_list(
                'dbcomputer__id', 'user__id')
        else:
            return queryresults

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
        import aiida.execmanager
        from aiida.common.exceptions import NotExistent

        computer = self.get_computer()
        if computer is None:
            raise NotExistent("No computer has been set for this calculation")

        return aiida.execmanager.get_authinfo(computer=computer,
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
        from aiida.common.exceptions import InvalidOperation, RemoteOperationError

        old_state = self.get_state()

        if (old_state == calc_states.NEW or
                    old_state == calc_states.TOSUBMIT):
            self._set_state(calc_states.FAILED)
            self.logger.warning("Calculation {} killed by the user "
                                "(it was in {} state)".format(
                self.pk, old_state))
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
            raise RemoteOperationError("An error occurred while trying to kill "
                                       "calculation {} (jobid {}), see log "
                                       "(maybe the calculation already finished?)"
                                       .format(self.pk, self.get_job_id()))
        else:
            # Do not set the state, but let the parser do its job
            # self._set_state(calc_states.FAILED)
            self.logger.warning("Calculation {} killed by the user "
                                "(it was {})".format(self.pk, calc_states.WITHSCHEDULER))

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
                                             PluginInternalError, ValidationError)
        from aiida.scheduler.datastructures import JobTemplate
        from aiida.common.utils import validate_list_of_string_tuples
        from aiida.orm import Computer
        from aiida.orm import DataFactory
        from aiida.common.datastructures import CodeInfo, code_run_modes
        from aiida.orm.code import Code 
        from aiida.orm import load_node

        computer = self.get_computer()

        if use_unstored_links:
            inputdict = self.get_inputs_dict(only_in_db=False)
        else:
            inputdict = self.get_inputs_dict(only_in_db=True)

        codes = [ _ for _ in inputdict.itervalues() if isinstance(_,Code) ]

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
                                            [computer.get_prepend_text(),
                                             code.get_prepend_text(),
                                             calcinfo.prepend_text,
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
        extra_mpirun_params = self.get_mpirun_extra_params() # this is the same for all codes in the same calc
        
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
        if not isinstance(calcinfo.codes_info,(list,tuple)):
            raise PluginInternalError("codes_info passed to CalcInfo must be a "
                                      "list of CalcInfo objects")
        
        codes_info = []
        for code_info in calcinfo.codes_info:
            
            if not isinstance(code_info,CodeInfo):
                raise PluginInternalError("Invalid codes_info, must be a list "
                                          "of CodeInfo objects")
            
            if code_info.code_uuid is None:
                raise PluginInternalError("CalcInfo should have "
                                          "the information of the code "
                                          "to be launched")
            this_code = load_node(code_info.code_uuid, parent_class=Code)
            
            this_withmpi = code_info.withmpi    # to decide better how to set the default
            if this_withmpi is None:
                if len(calcinfo.codes_info)>1:
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
                this_argv = [this_code.get_execname()] + (code_info.cmdline_params if
                                                          code_info.cmdline_params is not None else [])

            this_stdin_name = code_info.stdin_name
            this_stdout_name = code_info.stdout_name
            this_stderr_name = code_info.stderr_name
            this_join_files = code_info.join_files
            
            # overwrite the old cmdline_params and add codename and mpirun stuff
            code_info.cmdline_params = this_argv

            codes_info.append( code_info )
        job_tmpl.codes_info = codes_info
        
        # set the codes execution mode
        
        if len(codes)>1:
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
            raise PluginInternalError("[presubmission of calc {}] "
                                      "local_copy_list format problem: {}".format(
                this_pk, e.message))

        remote_copy_list = calcinfo.remote_copy_list
        try:
            validate_list_of_string_tuples(remote_copy_list,
                                           tuple_length=3)
        except ValidationError as e:
            raise PluginInternalError("[presubmission of calc {}] "
                                      "remote_copy_list format problem: {}".format(
                this_pk, e.message))

        for (remote_computer_uuid, remote_abs_path,
             dest_rel_path) in remote_copy_list:
            try:
                remote_computer = Computer(uuid=remote_computer_uuid)
            except NotExistent:
                raise PluginInternalError("[presubmission of calc {}] "
                                          "The remote copy requires a computer with UUID={}"
                                          "but no such computer was found in the "
                                          "database".format(this_pk, remote_computer_uuid))
            if os.path.isabs(dest_rel_path):
                raise PluginInternalError("[presubmission of calc {}] "
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
        from django.utils import timezone

        from aiida.transport.plugins.local import LocalTransport
        from aiida.orm import Computer
        from aiida.common.folders import Folder
        from aiida.common.exceptions import NotExistent

        if folder is None:
            folder = Folder(os.path.abspath('submit_test'))

        # In case it is not created yet
        folder.create()

        if subfolder_name is None:
            subfolder_basename = timezone.localtime(timezone.now()).strftime('%Y%m%d')
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
                                       '_aiida_remote_copy_list.txt'), 'w') as f:
                    for (remote_computer_uuid, remote_abs_path,
                         dest_rel_path) in remote_copy_list:
                        try:
                            remote_computer = Computer(uuid=remote_computer_uuid)
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
                                       '_aiida_remote_symlink_list.txt'), 'w') as f:
                    for (remote_computer_uuid, remote_abs_path,
                         dest_rel_path) in remote_symlink_list:
                        try:
                            remote_computer = Computer(uuid=remote_computer_uuid)
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


#
#     @property
#     def files(self):
#         """
#         To be used to get direct access to the retrieved files.
#
#         :return: an instance of the CalculationFileManager.
#         """
#         return CalculationFileManager(self)


class CalculationResultManager(object):
    """
    An object used internally to interface the calculation object with the Parser
    and consequentially with the ParameterData object result.
    It shouldn't be used explicitely by a user.
    """

    def __init__(self, calc):
        """
        :param calc: the calculation object.
        """
        # Possibly add checks here
        self._calc = calc
        ParserClass = calc.get_parserclass()
        if ParserClass is None:
            raise AttributeError("No output parser is attached to the calculation")
        else:
            self._parser = ParserClass(calc)

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

#
# class CalculationFileManager(object):
#     """
#     An object used internally to interface the calculation with the FolderData
#     object result.
#     It shouldn't be used explicitely by a user, but accessed through calc.files.
#     """
#     def __init__(self, calc):
#         """
#         :param calc: the calculation object.
#         """
#         # Possibly add checks here
#         self._calc = calc
#
#     def _get_folder(self):
#         from aiida.orm.data.folder import FolderData
#         from aiida.common.exceptions import NotExistent, UniquenessError
#         folders = self._calc.get_outputs(type=FolderData)
#         if not folders:
#             raise NotExistent("No output FolderData found")
#         try:
#             folders[1]
#         except IndexError:
#             pass
#         else:
#             raise UniquenessError("More than one output folder found")
#         return folders[0]
#
#     def path(self,name='.'):
#         folder = self._get_folder()
#         return folder.get_abs_path(name)
#
#     def list(self,name='.'):
#         folder = self._get_folder()
#         return folder.get_folder_list(name)
