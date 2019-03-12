# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Module with `Node` sub class for calculation job processes."""
from __future__ import division
from __future__ import absolute_import
from __future__ import print_function

import six

from aiida.common import exceptions
from aiida.common.datastructures import CalcJobState
from aiida.common.lang import classproperty

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
    SCHEUDLER_LAST_JOB_INFO_KEY = 'last_jobinfo'

    # Flag that determines whether the class can be cached.
    _cachable = True

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
        from aiida.common.exceptions import MultipleEntryPointError, MissingEntryPointError, LoadingEntryPointError
        from aiida.plugins.entry_point import is_valid_entry_point_string, get_entry_point_from_string, load_entry_point
        from aiida.tools.calculations import CalculationTools

        if self._tools is None:
            entry_point_string = self.process_type

            if is_valid_entry_point_string(entry_point_string):
                entry_point = get_entry_point_from_string(entry_point_string)

                try:
                    tools_class = load_entry_point('aiida.tools.calculations', entry_point.name)
                    self._tools = tools_class(self)
                except (MultipleEntryPointError, MissingEntryPointError, LoadingEntryPointError) as exception:
                    self._tools = CalculationTools(self)
                    self.logger.warning('could not load the calculation tools entry point {}: {}'.format(
                        entry_point.name, exception))

        return self._tools

    @classproperty
    def _updatable_attributes(cls):  # pylint: disable=no-self-argument
        return super(CalcJobNode, cls)._updatable_attributes + (
            cls.CALC_JOB_STATE_KEY,
            cls.REMOTE_WORKDIR_KEY,
            cls.RETRIEVE_LIST_KEY,
            cls.RETRIEVE_TEMPORARY_LIST_KEY,
            cls.RETRIEVE_SINGLE_FILE_LIST_KEY,
            cls.SCHEDULER_JOB_ID_KEY,
            cls.SCHEDULER_STATE_KEY,
            cls.SCHEDULER_LAST_CHECK_TIME_KEY,
            cls.SCHEUDLER_LAST_JOB_INFO_KEY,
        )

    @classproperty
    def _hash_ignored_attributes(cls):  # pylint: disable=no-self-argument
        return super(CalcJobNode, cls)._hash_ignored_attributes + (
            'queue_name',
            'account',
            'qos',
            'priority',
            'max_wallclock_seconds',
            'max_memory_kb',
        )

    def get_hash(self, ignore_errors=True, ignored_folder_content=('raw_input',), **kwargs):  # pylint: disable=arguments-differ
        return super(CalcJobNode, self).get_hash(
            ignore_errors=ignore_errors, ignored_folder_content=ignored_folder_content, **kwargs)

    @property
    def process_class(self):
        """Return the CalcJob class that was used to create this node.

        :return: CalcJob class
        :raises ValueError: if no process type is defined or it is an invalid process type string
        """
        from aiida.common.exceptions import MultipleEntryPointError, MissingEntryPointError, LoadingEntryPointError
        from aiida.plugins.entry_point import load_entry_point_from_string

        if not self.process_type:
            raise ValueError('no process type for CalcJobNode<{}>: cannot recreate process class'.format(self.pk))

        try:
            process_class = load_entry_point_from_string(self.process_type)
        except ValueError:
            raise ValueError('process type for CalcJobNode<{}> contains an invalid entry point string: {}'.format(
                self.pk, self.process_type))
        except (MissingEntryPointError, MultipleEntryPointError, LoadingEntryPointError) as exception:
            raise ValueError('could not load process class for entry point {} for CalcJobNode<{}>: {}'.format(
                self.pk, self.process_type, exception))

        return process_class

    def get_builder_restart(self):
        """
        Return a CalcJobBuilder instance, tailored for this calculation instance

        This builder is a mapping of the inputs of the CalcJobNode class, supports tab-completion, automatic
        validation when settings values as well as automated docstrings for each input.

        The fields of the builder will be pre-populated with all the inputs recorded for this instance as well as
        settings all the options that were explicitly set for this calculation instance.

        This builder can then directly be launched again to effectively run a duplicate calculation. But more useful
        is that it serves as a starting point to, after changing one or more inputs, launch a similar calculation by
        using this already completed calculation as a starting point.

        :return: CalcJobBuilder instance
        """
        from aiida.engine.processes.ports import PortNamespace

        process_class = self.process_class
        inputs = self.get_incoming()
        options = self.get_options()
        builder = process_class.get_builder()

        for port_name, port in process_class.spec().inputs.items():
            if port_name == process_class.spec().metadata_key:
                builder.metadata.options = options
            elif isinstance(port, PortNamespace):
                namespace = port_name + '_'
                sub = {
                    entry.link_label[len(namespace):]: entry.node
                    for entry in inputs
                    if entry.link_label.startswith(namespace)
                }
                if sub:
                    setattr(builder, port_name, sub)
            else:
                if port_name in inputs.all_link_labels():
                    setattr(builder, port_name, inputs.get_node_by_label(port_name))

        return builder

    def _validate(self):
        """
        Verify if all the input nodes are present and valid.

        :raise: ValidationError: if invalid parameters are found.
        """
        super(CalcJobNode, self)._validate()

        if self.computer is None:
            raise exceptions.ValidationError('no computer was specified')

        if self.get_state() and self.get_state() not in CalcJobState:
            raise exceptions.ValidationError('invalid calculation state `{}`'.format(self.get_state()))

        try:
            self.get_parser_class()
        except exceptions.MissingPluginError:
            raise exceptions.ValidationError("No valid class/implementation found for the parser '{}'. "
                                             "Set the parser to None if you do not need an automatic "
                                             "parser.".format(self.get_option('parser_name')))

        computer = self.computer
        scheduler = computer.get_scheduler()
        resources = self.get_option('resources')
        def_cpus_machine = computer.get_default_mpiprocs_per_machine()

        if def_cpus_machine is not None:
            resources['default_mpiprocs_per_machine'] = def_cpus_machine

        try:
            scheduler.create_job_resource(**resources)
        except (TypeError, ValueError) as exc:
            raise exceptions.ValidationError(
                "Invalid resources for the scheduler of the specified computer: {}".format(exc))

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

    @property
    def options(self):
        """Return the available process options for the process class that created this node."""
        try:
            return self.process_class.spec().inputs._ports['metadata']['options']  # pylint: disable=protected-access
        except ValueError:
            return {}

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
        for name in self.options.keys():
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
        """Return the state of the calculation job.

        :return: the calculation job state
        """
        state = self.get_attribute(self.CALC_JOB_STATE_KEY, None)

        if state:
            return CalcJobState(state)

        return None

    def set_state(self, state):
        """
        Set the state of the calculation job.

        :param state: a string with the state from ``aiida.common.datastructures.CalcJobState``.
        :raise: ValueError if state is invalid
        """
        if state not in CalcJobState:
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
            if isinstance(directive, six.string_types):
                continue

            # Otherwise, it has to be a tuple of length three with specific requirements
            if not isinstance(directive, (tuple, list)) or len(directive) != 3:
                raise ValueError('invalid directive, not a list or tuple of length three: {}'.format(directive))

            if not isinstance(directive[0], six.string_types):
                raise ValueError('invalid directive, first element has to be a string representing remote path')

            if not isinstance(directive[1], six.string_types):
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
        """
        if not isinstance(retrieve_singlefile_list, (tuple, list)):
            raise TypeError('retrieve_singlefile_list has to be a list or tuple')

        for j in retrieve_singlefile_list:
            if not isinstance(j, (tuple, list)) or not all(isinstance(i, six.string_types) for i in j):
                raise ValueError('You have to pass a list (or tuple) of lists of strings as retrieve_singlefile_list')

        self.set_attribute(self.RETRIEVE_SINGLE_FILE_LIST_KEY, retrieve_singlefile_list)

    def get_retrieve_singlefile_list(self):
        """Return the list of files to be retrieved on the cluster after the calculation has completed.

        :return: list of single file retrieval directives
        """
        return self.get_attribute(self.RETRIEVE_SINGLE_FILE_LIST_KEY, None)

    def set_job_id(self, job_id):
        """Set the job id that was assigned to the calculation by the scheduler.

        .. note:: the id will always be stored as a string

        :param job_id: the id assigned by the scheduler after submission
        """
        return self.set_attribute(self.SCHEDULER_JOB_ID_KEY, six.text_type(job_id))

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
        self.set_attribute(self.SCHEDULER_LAST_CHECK_TIME_KEY, timezone.now())

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
        return self.get_attribute(self.SCHEDULER_LAST_CHECK_TIME_KEY, None)

    def set_last_job_info(self, last_job_info):
        """Set the last job info.

        :param last_job_info: a `JobInfo` object
        """
        self.set_attribute(self.SCHEUDLER_LAST_JOB_INFO_KEY, last_job_info.serialize())

    def get_last_job_info(self):
        """Return the last information asked to the scheduler about the status of the job.

        :return: a `JobInfo` object (that closely resembles a dictionary) or None.
        """
        from aiida.schedulers.datastructures import JobInfo

        last_job_info_serialized = self.get_attribute(self.SCHEUDLER_LAST_JOB_INFO_KEY, None)

        if last_job_info_serialized is not None:
            job_info = JobInfo()
            job_info.load_from_serialized(last_job_info_serialized)
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
            raise exceptions.NotExistent("No computer has been set for this calculation")

        return AuthInfo.from_backend_entity(self.backend.authinfos.get(computer=computer, user=self.user))

    def get_transport(self):
        """Return the transport for this calculation.

        :return: `Transport` configured with the `AuthInfo` associated to the computer of this node
        """
        return self.get_authinfo().get_transport()

    def get_parser_class(self):
        """Return the output parser object for this calculation or None if no parser is set.

        :return: a `Parser` class.
        :raise: MissingPluginError from ParserFactory no plugin is found.
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
        except exceptions.NotExistent:
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
        except exceptions.NotExistent:
            stderr = None

        return stderr

    def get_description(self):
        """Return a string with a description of the node based on its properties."""
        return self.get_state()
