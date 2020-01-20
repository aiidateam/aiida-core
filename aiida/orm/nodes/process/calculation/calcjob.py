# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Module with `Node` sub class for calculation job processes."""

import warnings

from aiida.common import exceptions
from aiida.common.datastructures import CalcJobState
from aiida.common.lang import classproperty
from aiida.common.links import LinkType
from aiida.common.warnings import AiidaDeprecationWarning

from .calculation import CalculationNode

__all__ = ('CalcJobNode',)


class CalcJobNode(CalculationNode):
    """ORM class for all nodes representing the execution of a CalcJob."""

    # pylint: disable=too-many-public-methods

    CALC_JOB_STATE_KEY = 'state'
    REMOTE_WORKDIR_KEY = 'remote_workdir'
    RETRIEVE_LIST_KEY = 'retrieve_list'
    RETRIEVE_TEMPORARY_LIST_KEY = 'retrieve_temporary_list'
    RETRIEVE_SINGLE_FILE_LIST_KEY = 'retrieve_singlefile_list'
    SCHEDULER_JOB_ID_KEY = 'job_id'
    SCHEDULER_STATE_KEY = 'scheduler_state'
    SCHEDULER_LAST_CHECK_TIME_KEY = 'scheduler_lastchecktime'
    SCHEDULER_LAST_JOB_INFO_KEY = 'last_job_info'
    SCHEDULER_DETAILED_JOB_INFO_KEY = 'detailed_job_info'

    # Base path within the repository where to put objects by default
    _repository_base_path = 'raw_input'

    # An optional entry point for a CalculationTools instance
    _tools = None

    @property
    def tools(self):
        """Return the calculation tools that are registered for the process type associated with this calculation.

        If the entry point name stored in the `process_type` of the CalcJobNode has an accompanying entry point in the
        `aiida.tools.calculations` entry point category, it will attempt to load the entry point and instantiate it
        passing the node to the constructor. If the entry point does not exist, cannot be resolved or loaded, a warning
        will be logged and the base CalculationTools class will be instantiated and returned.

        :return: CalculationTools instance
        """
        from aiida.plugins.entry_point import is_valid_entry_point_string, get_entry_point_from_string, load_entry_point
        from aiida.tools.calculations import CalculationTools

        if self._tools is None:
            entry_point_string = self.process_type

            if is_valid_entry_point_string(entry_point_string):
                entry_point = get_entry_point_from_string(entry_point_string)

                try:
                    tools_class = load_entry_point('aiida.tools.calculations', entry_point.name)
                    self._tools = tools_class(self)
                except exceptions.EntryPointError as exception:
                    self._tools = CalculationTools(self)
                    self.logger.warning(
                        'could not load the calculation tools entry point {}: {}'.format(entry_point.name, exception)
                    )

        return self._tools

    @classproperty
    def _updatable_attributes(cls):  # pylint: disable=no-self-argument
        return super()._updatable_attributes + (
            cls.CALC_JOB_STATE_KEY,
            cls.REMOTE_WORKDIR_KEY,
            cls.RETRIEVE_LIST_KEY,
            cls.RETRIEVE_TEMPORARY_LIST_KEY,
            cls.RETRIEVE_SINGLE_FILE_LIST_KEY,
            cls.SCHEDULER_JOB_ID_KEY,
            cls.SCHEDULER_STATE_KEY,
            cls.SCHEDULER_LAST_CHECK_TIME_KEY,
            cls.SCHEDULER_LAST_JOB_INFO_KEY,
            cls.SCHEDULER_DETAILED_JOB_INFO_KEY,
        )

    @classproperty
    def _hash_ignored_attributes(cls):  # pylint: disable=no-self-argument
        return super()._hash_ignored_attributes + (
            'queue_name',
            'account',
            'qos',
            'priority',
            'max_wallclock_seconds',
            'max_memory_kb',
        )

    def _get_objects_to_hash(self):
        """Return a list of objects which should be included in the hash.

        This method is purposefully overridden from the base `Node` class, because we do not want to include the
        repository folder in the hash. The reason is that the hash of this node is computed in the `store` method, at
        which point the input files that will be stored in the repository have not yet been generated. Including these
        anyway in the computation of the hash would mean that the hash of the node would change as soon as the process
        has started and the input files have been written to the repository.
        """
        from importlib import import_module
        objects = [
            import_module(self.__module__.split('.', 1)[0]).__version__,
            {
                key: val
                for key, val in self.attributes_items()
                if key not in self._hash_ignored_attributes and key not in self._updatable_attributes  # pylint: disable=unsupported-membership-test
            },
            self.computer.uuid if self.computer is not None else None,  # pylint: disable=no-member
            {
                entry.link_label: entry.node.get_hash()
                for entry in self.get_incoming(link_type=(LinkType.INPUT_CALC, LinkType.INPUT_WORK))
                if entry.link_label not in self._hash_ignored_inputs
            }
        ]
        return objects

    def get_builder_restart(self):
        """Return a `ProcessBuilder` that is ready to relaunch the same `CalcJob` that created this node.

        The process class will be set based on the `process_type` of this node and the inputs of the builder will be
        prepopulated with the inputs registered for this node. This functionality is very useful if a process has
        completed and you want to relaunch it with slightly different inputs.

        In addition to prepopulating the input nodes, which is implemented by the base `ProcessNode` class, here we
        also add the `options` that were passed in the `metadata` input of the `CalcJob` process.

        :return: `~aiida.engine.processes.builder.ProcessBuilder` instance
        """
        builder = super().get_builder_restart()
        builder.metadata.options = self.get_options()

        return builder

    @property
    def _raw_input_folder(self):
        """
        Get the input folder object.

        :return: the input folder object.
        :raise: NotExistent: if the raw folder hasn't been created yet
        """
        from aiida.common.exceptions import NotExistent

        return_folder = self._repository._get_base_folder()  # pylint: disable=protected-access
        if return_folder.exists():
            return return_folder

        raise NotExistent('the `_raw_input_folder` has not yet been created')

    def get_option(self, name):
        """
        Retun the value of an option that was set for this CalcJobNode

        :param name: the option name
        :return: the option value or None
        :raises: ValueError for unknown option
        """
        return self.get_attribute(name, None)

    def set_option(self, name, value):
        """
        Set an option to the given value

        :param name: the option name
        :param value: the value to set
        :raises: ValueError for unknown option
        :raises: TypeError for values with invalid type
        """
        self.set_attribute(name, value)

    def get_options(self):
        """
        Return the dictionary of options set for this CalcJobNode

        :return: dictionary of the options and their values
        """
        options = {}
        for name in self.process_class.spec_options.keys():
            value = self.get_option(name)
            if value is not None:
                options[name] = value

        return options

    def set_options(self, options):
        """
        Set the options for this CalcJobNode

        :param options: dictionary of option and their values to set
        """
        for name, value in options.items():
            self.set_option(name, value)

    def get_state(self):
        """Return the calculation job active sub state.

        The calculation job state serves to give more granular state information to `CalcJobs`, in addition to the
        generic process state, while the calculation job is active. The state can take values from the enumeration
        defined in `aiida.common.datastructures.CalcJobState` and can be used to query for calculation jobs in specific
        active states.

        :return: instance of `aiida.common.datastructures.CalcJobState` or `None` if invalid value, or not set
        """
        state = self.get_attribute(self.CALC_JOB_STATE_KEY, None)

        try:
            state = CalcJobState(state)
        except ValueError:
            state = None

        return state

    def set_state(self, state):
        """Set the calculation active job state.

        :param state: a string with the state from ``aiida.common.datastructures.CalcJobState``.
        :raise: ValueError if state is invalid
        """
        if not isinstance(state, CalcJobState):
            raise ValueError('{} is not a valid CalcJobState'.format(state))

        self.set_attribute(self.CALC_JOB_STATE_KEY, state.value)

    def delete_state(self):
        """Delete the calculation job state attribute if it exists."""
        try:
            self.delete_attribute(self.CALC_JOB_STATE_KEY)
        except AttributeError:
            pass

    def set_remote_workdir(self, remote_workdir):
        """Set the absolute path to the working directory on the remote computer where the calculation is run.

        :param remote_workdir: absolute filepath to the remote working directory
        """
        self.set_attribute(self.REMOTE_WORKDIR_KEY, remote_workdir)

    def get_remote_workdir(self):
        """Return the path to the remote (on cluster) scratch folder of the calculation.

        :return: a string with the remote path
        """
        return self.get_attribute(self.REMOTE_WORKDIR_KEY, None)

    @staticmethod
    def _validate_retrieval_directive(directives):
        """Validate a list or tuple of file retrieval directives.

        :param directives: a list or tuple of file retrieveal directives
        :raise ValueError: if the format of the directives is invalid
        """
        if not isinstance(directives, (tuple, list)):
            raise TypeError('file retrieval directives has to be a list or tuple')

        for directive in directives:

            # A string as a directive is valid, so we continue
            if isinstance(directive, str):
                continue

            # Otherwise, it has to be a tuple of length three with specific requirements
            if not isinstance(directive, (tuple, list)) or len(directive) != 3:
                raise ValueError('invalid directive, not a list or tuple of length three: {}'.format(directive))

            if not isinstance(directive[0], str):
                raise ValueError('invalid directive, first element has to be a string representing remote path')

            if not isinstance(directive[1], str):
                raise ValueError('invalid directive, second element has to be a string representing local path')

            if not isinstance(directive[2], int):
                raise ValueError('invalid directive, three element has to be an integer representing the depth')

    def set_retrieve_list(self, retrieve_list):
        """Set the retrieve list.

        This list of directives will instruct the daemon what files to retrieve after the calculation has completed.
        list or tuple of files or paths that should be retrieved by the daemon.

        :param retrieve_list: list or tuple of with filepath directives
        """
        self._validate_retrieval_directive(retrieve_list)
        self.set_attribute(self.RETRIEVE_LIST_KEY, retrieve_list)

    def get_retrieve_list(self):
        """Return the list of files/directories to be retrieved on the cluster after the calculation has completed.

        :return: a list of file directives
        """
        return self.get_attribute(self.RETRIEVE_LIST_KEY, None)

    def set_retrieve_temporary_list(self, retrieve_temporary_list):
        """Set the retrieve temporary list.

        The retrieve temporary list stores files that are retrieved after completion and made available during parsing
        and are deleted as soon as the parsing has been completed.

        :param retrieve_temporary_list: list or tuple of with filepath directives
        """
        self._validate_retrieval_directive(retrieve_temporary_list)
        self.set_attribute(self.RETRIEVE_TEMPORARY_LIST_KEY, retrieve_temporary_list)

    def get_retrieve_temporary_list(self):
        """Return list of files to be retrieved from the cluster which will be available during parsing.

        :return: a list of file directives
        """
        return self.get_attribute(self.RETRIEVE_TEMPORARY_LIST_KEY, None)

    def set_retrieve_singlefile_list(self, retrieve_singlefile_list):
        """Set the retrieve singlefile list.

        The files will be stored as `SinglefileData` instances and added as output nodes to this calculation node.
        The format of a single file directive is a tuple or list of length 3 with the following entries:

            1. the link label under which the file should be added
            2. the `SinglefileData` class or sub class to use to store
            3. the filepath relative to the remote working directory of the calculation

        :param retrieve_singlefile_list: list or tuple of single file directives

        .. deprecated:: 1.0.0

            Will be removed in `v2.0.0`.
            Use :meth:`~aiida.orm.nodes.process.calculation.calcjob.CalcJobNode.set_retrieve_temporary_list` instead.

        """
        warnings.warn('method is deprecated, use `set_retrieve_temporary_list` instead', AiidaDeprecationWarning)  # pylint: disable=no-member

        if not isinstance(retrieve_singlefile_list, (tuple, list)):
            raise TypeError('retrieve_singlefile_list has to be a list or tuple')

        for j in retrieve_singlefile_list:
            if not isinstance(j, (tuple, list)) or not all(isinstance(i, str) for i in j):
                raise ValueError('You have to pass a list (or tuple) of lists of strings as retrieve_singlefile_list')

        self.set_attribute(self.RETRIEVE_SINGLE_FILE_LIST_KEY, retrieve_singlefile_list)

    def get_retrieve_singlefile_list(self):
        """Return the list of files to be retrieved on the cluster after the calculation has completed.

        :return: list of single file retrieval directives

        .. deprecated:: 1.0.0
            Will be removed in `v2.0.0`, use
            :meth:`aiida.orm.nodes.process.calculation.calcjob.CalcJobNode.get_retrieve_temporary_list` instead.
        """
        return self.get_attribute(self.RETRIEVE_SINGLE_FILE_LIST_KEY, None)

    def set_job_id(self, job_id):
        """Set the job id that was assigned to the calculation by the scheduler.

        .. note:: the id will always be stored as a string

        :param job_id: the id assigned by the scheduler after submission
        """
        return self.set_attribute(self.SCHEDULER_JOB_ID_KEY, str(job_id))

    def get_job_id(self):
        """Return job id that was assigned to the calculation by the scheduler.

        :return: the string representation of the scheduler job id
        """
        return self.get_attribute(self.SCHEDULER_JOB_ID_KEY, None)

    def set_scheduler_state(self, state):
        """Set the scheduler state.

        :param state: an instance of `JobState`
        """
        from aiida.common import timezone
        from aiida.schedulers.datastructures import JobState

        if not isinstance(state, JobState):
            raise ValueError('scheduler state should be an instance of JobState, got: {}'.format(state))

        self.set_attribute(self.SCHEDULER_STATE_KEY, state.value)
        self.set_attribute(self.SCHEDULER_LAST_CHECK_TIME_KEY, timezone.datetime_to_isoformat(timezone.now()))

    def get_scheduler_state(self):
        """Return the status of the calculation according to the cluster scheduler.

        :return: a JobState enum instance.
        """
        from aiida.schedulers.datastructures import JobState

        state = self.get_attribute(self.SCHEDULER_STATE_KEY, None)

        if state is None:
            return state

        return JobState(state)

    def get_scheduler_lastchecktime(self):
        """Return the time of the last update of the scheduler state by the daemon or None if it was never set.

        :return: a datetime object or None
        """
        from aiida.common import timezone
        value = self.get_attribute(self.SCHEDULER_LAST_CHECK_TIME_KEY, None)

        if value is not None:
            value = timezone.isoformat_to_datetime(value)

        return value

    def set_detailed_job_info(self, detailed_job_info):
        """Set the detailed job info dictionary.

        :param detailed_job_info: a dictionary with metadata with the accounting of a completed job
        """
        self.set_attribute(self.SCHEDULER_DETAILED_JOB_INFO_KEY, detailed_job_info)

    def get_detailed_job_info(self):
        """Return the detailed job info dictionary.

        :return: the dictionary with detailed job info if defined or None
        """
        return self.get_attribute(self.SCHEDULER_DETAILED_JOB_INFO_KEY, None)

    def set_last_job_info(self, last_job_info):
        """Set the last job info.

        :param last_job_info: a `JobInfo` object
        """
        self.set_attribute(self.SCHEDULER_LAST_JOB_INFO_KEY, last_job_info.get_dict())

    def get_last_job_info(self):
        """Return the last information asked to the scheduler about the status of the job.

        :return: a `JobInfo` object (that closely resembles a dictionary) or None.
        """
        from aiida.schedulers.datastructures import JobInfo

        last_job_info_dictserialized = self.get_attribute(self.SCHEDULER_LAST_JOB_INFO_KEY, None)

        if last_job_info_dictserialized is not None:
            job_info = JobInfo.load_from_dict(last_job_info_dictserialized)
        else:
            job_info = None

        return job_info

    def get_authinfo(self):
        """Return the `AuthInfo` that is configured for the `Computer` set for this node.

        :return: `AuthInfo`
        """
        from aiida.orm.authinfos import AuthInfo

        computer = self.computer

        if computer is None:
            raise exceptions.NotExistent('No computer has been set for this calculation')

        return AuthInfo.from_backend_entity(self.backend.authinfos.get(computer=computer, user=self.user))

    def get_transport(self):
        """Return the transport for this calculation.

        :return: `Transport` configured with the `AuthInfo` associated to the computer of this node
        """
        return self.get_authinfo().get_transport()

    def get_parser_class(self):
        """Return the output parser object for this calculation or None if no parser is set.

        :return: a `Parser` class.
        :raises `aiida.common.exceptions.EntryPointError`: if the parser entry point can not be resolved.
        """
        from aiida.plugins import ParserFactory

        parser_name = self.get_option('parser_name')

        if parser_name is not None:
            return ParserFactory(parser_name)

        return None

    @property
    def link_label_retrieved(self):
        """Return the link label used for the retrieved FolderData node."""
        return 'retrieved'

    def get_retrieved_node(self):
        """Return the retrieved data folder.

        :return: the retrieved FolderData node or None if not found
        """
        from aiida.orm import FolderData
        try:
            return self.get_outgoing(node_class=FolderData, link_label_filter=self.link_label_retrieved).one().node
        except ValueError:
            return None

    @property
    def res(self):
        """
        To be used to get direct access to the parsed parameters.

        :return: an instance of the CalcJobResultManager.

        :note: a practical example on how it is meant to be used: let's say that there is a key 'energy'
            in the dictionary of the parsed results which contains a list of floats.
            The command `calc.res.energy` will return such a list.
        """
        from aiida.orm.utils.calcjob import CalcJobResultManager
        return CalcJobResultManager(self)

    def get_scheduler_stdout(self):
        """Return the scheduler stderr output if the calculation has finished and been retrieved, None otherwise.

        :return: scheduler stderr output or None
        """
        filename = self.get_option('scheduler_stdout')
        retrieved_node = self.get_retrieved_node()

        if filename is None or retrieved_node is None:
            return None

        try:
            stdout = retrieved_node.get_object_content(filename)
        except IOError:
            stdout = None

        return stdout

    def get_scheduler_stderr(self):
        """Return the scheduler stdout output if the calculation has finished and been retrieved, None otherwise.

        :return: scheduler stdout output or None
        """
        filename = self.get_option('scheduler_stderr')
        retrieved_node = self.get_retrieved_node()

        if filename is None or retrieved_node is None:
            return None

        try:
            stderr = retrieved_node.get_object_content(filename)
        except IOError:
            stderr = None

        return stderr

    def get_description(self):
        """Return a string with a description of the node based on its properties."""
        return self.get_state()
