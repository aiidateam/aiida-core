###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Module with `Node` sub class for calculation job processes."""

import datetime
from typing import TYPE_CHECKING, Any, AnyStr, Dict, List, Optional, Sequence, Tuple, Type, Union, cast

from aiida.common import exceptions
from aiida.common.datastructures import CalcJobState
from aiida.common.lang import classproperty
from aiida.common.pydantic import MetadataField

from ..process import ProcessNodeCaching
from .calculation import CalculationNode

if TYPE_CHECKING:
    from aiida.orm import FolderData
    from aiida.orm.authinfos import AuthInfo
    from aiida.orm.utils.calcjob import CalcJobResultManager
    from aiida.parsers import Parser
    from aiida.schedulers.datastructures import JobInfo, JobState
    from aiida.tools.calculations import CalculationTools
    from aiida.transports import Transport

__all__ = ('CalcJobNode',)


class CalcJobNodeCaching(ProcessNodeCaching):
    """Interface to control caching of a node instance."""

    def get_objects_to_hash(self) -> List[Any]:
        """Return a list of objects which should be included in the hash.

        This method is purposefully overridden from the base `Node` class, because we do not want to include the
        repository folder in the hash. The reason is that the hash of this node is computed in the `store` method, at
        which point the input files that will be stored in the repository have not yet been generated. Including these
        anyway in the computation of the hash would mean that the hash of the node would change as soon as the process
        has started and the input files have been written to the repository.
        """
        objects = super().get_objects_to_hash()
        objects.pop('repository_hash', None)
        return objects


class CalcJobNode(CalculationNode):
    """ORM class for all nodes representing the execution of a CalcJob."""

    _CLS_NODE_CACHING = CalcJobNodeCaching

    IMMIGRATED_KEY = 'imported'
    CALC_JOB_STATE_KEY = 'state'
    REMOTE_WORKDIR_KEY = 'remote_workdir'
    RETRIEVE_LIST_KEY = 'retrieve_list'
    RETRIEVE_TEMPORARY_LIST_KEY = 'retrieve_temporary_list'
    SCHEDULER_JOB_ID_KEY = 'job_id'
    SCHEDULER_STATE_KEY = 'scheduler_state'
    SCHEDULER_LAST_CHECK_TIME_KEY = 'scheduler_lastchecktime'
    SCHEDULER_LAST_JOB_INFO_KEY = 'last_job_info'
    SCHEDULER_DETAILED_JOB_INFO_KEY = 'detailed_job_info'

    class Model(CalculationNode.Model):
        scheduler_state: Optional[str] = MetadataField(
            None,
            description='The state of the scheduler',
            orm_to_model=lambda node, _: cast('CalcJobNode', node).get_scheduler_state(),
        )
        state: Optional[str] = MetadataField(
            None,
            description='The active state of the calculation job',
            orm_to_model=lambda node, _: cast('CalcJobNode', node).get_state(),
        )
        remote_workdir: Optional[str] = MetadataField(
            None,
            description='The path to the remote (on cluster) scratch folder',
            orm_to_model=lambda node, _: cast('CalcJobNode', node).get_remote_workdir(),
        )
        job_id: Optional[str] = MetadataField(
            None,
            description='The scheduler job id',
            orm_to_model=lambda node, _: cast('CalcJobNode', node).get_job_id(),
        )
        scheduler_lastchecktime: Optional[datetime.datetime] = MetadataField(
            None,
            description='The last time the scheduler was checked, in isoformat',
            orm_to_model=lambda node, _: cast('CalcJobNode', node).get_scheduler_lastchecktime(),
            exclude_to_orm=True,
        )
        last_job_info: Optional[dict] = MetadataField(
            None,
            description='The last job info returned by the scheduler',
            orm_to_model=lambda node, _: dict(cast('CalcJobNode', node).get_last_job_info() or {}),
        )
        detailed_job_info: Optional[dict] = MetadataField(
            None,
            description='The detailed job info returned by the scheduler',
            orm_to_model=lambda node, _: cast('CalcJobNode', node).get_detailed_job_info(),
        )
        retrieve_list: Optional[Sequence[Union[str, Tuple[str, str, int]]]] = MetadataField(
            None,
            description='The list of files to retrieve from the remote cluster',
            orm_to_model=lambda node, _: cast('CalcJobNode', node).get_retrieve_list(),
        )
        retrieve_temporary_list: Optional[Sequence[Union[str, Tuple[str, str, int]]]] = MetadataField(
            None,
            description='The list of temporary files to retrieve from the remote cluster',
            orm_to_model=lambda node, _: cast('CalcJobNode', node).get_retrieve_temporary_list(),
        )
        imported: Optional[bool] = MetadataField(
            None,
            description='Whether the node has been migrated',
            orm_to_model=lambda node, _: cast('CalcJobNode', node).is_imported,
            exclude_to_orm=True,
        )

    # An optional entry point for a CalculationTools instance
    _tools = None

    @property
    def tools(self) -> 'CalculationTools':
        """Return the calculation tools that are registered for the process type associated with this calculation.

        If the entry point name stored in the `process_type` of the CalcJobNode has an accompanying entry point in the
        `aiida.tools.calculations` entry point category, it will attempt to load the entry point and instantiate it
        passing the node to the constructor. If the entry point does not exist, cannot be resolved or loaded, a warning
        will be logged and the base CalculationTools class will be instantiated and returned.

        :return: CalculationTools instance
        """
        from aiida.plugins.entry_point import get_entry_point_from_string, is_valid_entry_point_string, load_entry_point
        from aiida.tools.calculations import CalculationTools

        if self._tools is None:
            entry_point_string = self.process_type

            if entry_point_string and is_valid_entry_point_string(entry_point_string):
                entry_point = get_entry_point_from_string(entry_point_string)

                try:
                    tools_class = load_entry_point('aiida.tools.calculations', entry_point.name)
                    self._tools = tools_class(self)
                except exceptions.EntryPointError as exception:
                    self._tools = CalculationTools(self)
                    self.logger.warning(
                        f'could not load the calculation tools entry point {entry_point.name}: {exception}'
                    )

        return self._tools

    @classproperty
    def _updatable_attributes(cls) -> Tuple[str, ...]:  # noqa: N805
        return super()._updatable_attributes + (
            cls.CALC_JOB_STATE_KEY,
            cls.IMMIGRATED_KEY,
            cls.REMOTE_WORKDIR_KEY,
            cls.RETRIEVE_LIST_KEY,
            cls.RETRIEVE_TEMPORARY_LIST_KEY,
            cls.SCHEDULER_JOB_ID_KEY,
            cls.SCHEDULER_STATE_KEY,
            cls.SCHEDULER_LAST_CHECK_TIME_KEY,
            cls.SCHEDULER_LAST_JOB_INFO_KEY,
            cls.SCHEDULER_DETAILED_JOB_INFO_KEY,
        )

    @classproperty
    def _hash_ignored_attributes(cls) -> Tuple[str, ...]:  # noqa: N805
        return super()._hash_ignored_attributes + (
            'queue_name',
            'account',
            'qos',
            'priority',
            'max_wallclock_seconds',
            'max_memory_kb',
            'version',
        )

    @property
    def is_imported(self) -> bool:
        """Return whether the calculation job was imported instead of being an actual run."""
        return self.base.attributes.get(self.IMMIGRATED_KEY, None) is True

    def get_option(self, name: str) -> Optional[Any]:
        """Return the value of an option that was set for this CalcJobNode.

        :param name: the option name
        :return: the option value or None
        :raises: ValueError for unknown option
        """
        return self.base.attributes.get(name, None)

    def set_option(self, name: str, value: Any) -> None:
        """Set an option to the given value

        :param name: the option name
        :param value: the value to set
        :raises: ValueError for unknown option
        :raises: TypeError for values with invalid type
        """
        self.base.attributes.set(name, value)

    def get_options(self) -> Dict[str, Any]:
        """Return the dictionary of options set for this CalcJobNode

        :return: dictionary of the options and their values
        """
        options = {}
        for name in self.process_class.spec_options.keys():  # type: ignore[attr-defined]
            value = self.get_option(name)
            if value is not None:
                options[name] = value

        return options

    def set_options(self, options: Dict[str, Any]) -> None:
        """Set the options for this CalcJobNode

        :param options: dictionary of option and their values to set
        """
        for name, value in options.items():
            self.set_option(name, value)

    def get_state(self) -> Optional[CalcJobState]:
        """Return the calculation job active sub state.

        The calculation job state serves to give more granular state information to `CalcJobs`, in addition to the
        generic process state, while the calculation job is active. The state can take values from the enumeration
        defined in `aiida.common.datastructures.CalcJobState` and can be used to query for calculation jobs in specific
        active states.

        :return: instance of `aiida.common.datastructures.CalcJobState` or `None` if invalid value, or not set
        """
        state = self.base.attributes.get(self.CALC_JOB_STATE_KEY, None)

        try:
            state = CalcJobState(state)
        except ValueError:
            state = None

        return state

    def set_state(self, state: CalcJobState) -> None:
        """Set the calculation active job state.

        :raise: ValueError if state is invalid
        """
        if not isinstance(state, CalcJobState):
            raise ValueError(f'{state} is not a valid CalcJobState')

        self.base.attributes.set(self.CALC_JOB_STATE_KEY, state.value)

    def delete_state(self) -> None:
        """Delete the calculation job state attribute if it exists."""
        try:
            self.base.attributes.delete(self.CALC_JOB_STATE_KEY)
        except AttributeError:
            pass

    def set_remote_workdir(self, remote_workdir: str) -> None:
        """Set the absolute path to the working directory on the remote computer where the calculation is run.

        :param remote_workdir: absolute filepath to the remote working directory
        """
        self.base.attributes.set(self.REMOTE_WORKDIR_KEY, remote_workdir)

    def get_remote_workdir(self) -> Optional[str]:
        """Return the path to the remote (on cluster) scratch folder of the calculation.

        :return: a string with the remote path
        """
        return self.base.attributes.get(self.REMOTE_WORKDIR_KEY, None)

    @staticmethod
    def _validate_retrieval_directive(directives: Sequence[Union[str, Tuple[str, str, int]]]) -> None:
        """Validate a list or tuple of file retrieval directives.

        :param directives: a list or tuple of file retrieval directives
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
                raise ValueError(f'invalid directive, not a list or tuple of length three: {directive}')

            if not isinstance(directive[0], str):
                raise ValueError('invalid directive, first element has to be a string representing remote path')

            if not isinstance(directive[1], str):
                raise ValueError('invalid directive, second element has to be a string representing local path')

            if not isinstance(directive[2], (int, type(None))):
                raise ValueError('invalid directive, third element has to be an integer representing the depth')

    def set_retrieve_list(self, retrieve_list: Sequence[Union[str, Tuple[str, str, int]]]) -> None:
        """Set the retrieve list.

        This list of directives will instruct the daemon what files to retrieve after the calculation has completed.
        list or tuple of files or paths that should be retrieved by the daemon.

        :param retrieve_list: list or tuple of with filepath directives
        """
        self._validate_retrieval_directive(retrieve_list)
        self.base.attributes.set(self.RETRIEVE_LIST_KEY, retrieve_list)

    def get_retrieve_list(self) -> Optional[Sequence[Union[str, Tuple[str, str, int]]]]:
        """Return the list of files/directories to be retrieved on the cluster after the calculation has completed.

        :return: a list of file directives
        """
        return self.base.attributes.get(self.RETRIEVE_LIST_KEY, None)

    def set_retrieve_temporary_list(self, retrieve_temporary_list: Sequence[Union[str, Tuple[str, str, int]]]) -> None:
        """Set the retrieve temporary list.

        The retrieve temporary list stores files that are retrieved after completion and made available during parsing
        and are deleted as soon as the parsing has been completed.

        :param retrieve_temporary_list: list or tuple of with filepath directives
        """
        self._validate_retrieval_directive(retrieve_temporary_list)
        self.base.attributes.set(self.RETRIEVE_TEMPORARY_LIST_KEY, retrieve_temporary_list)

    def get_retrieve_temporary_list(self) -> Optional[Sequence[Union[str, Tuple[str, str, int]]]]:
        """Return list of files to be retrieved from the cluster which will be available during parsing.

        :return: a list of file directives
        """
        return self.base.attributes.get(self.RETRIEVE_TEMPORARY_LIST_KEY, None)

    def set_job_id(self, job_id: Union[int, str]) -> None:
        """Set the job id that was assigned to the calculation by the scheduler.

        .. note:: the id will always be stored as a string

        :param job_id: the id assigned by the scheduler after submission
        """
        return self.base.attributes.set(self.SCHEDULER_JOB_ID_KEY, str(job_id))

    def get_job_id(self) -> Optional[str]:
        """Return job id that was assigned to the calculation by the scheduler.

        :return: the string representation of the scheduler job id
        """
        return self.base.attributes.get(self.SCHEDULER_JOB_ID_KEY, None)

    def set_scheduler_state(self, state: 'JobState') -> None:
        """Set the scheduler state.

        :param state: an instance of `JobState`
        """
        from aiida.common import timezone
        from aiida.schedulers.datastructures import JobState

        if not isinstance(state, JobState):
            raise ValueError(f'scheduler state should be an instance of JobState, got: {state}')

        self.base.attributes.set(self.SCHEDULER_STATE_KEY, state.value)
        self.base.attributes.set(self.SCHEDULER_LAST_CHECK_TIME_KEY, timezone.now().isoformat())

    def get_scheduler_state(self) -> Optional['JobState']:
        """Return the status of the calculation according to the cluster scheduler.

        :return: a JobState enum instance.
        """
        from aiida.schedulers.datastructures import JobState

        state = self.base.attributes.get(self.SCHEDULER_STATE_KEY, None)

        if state is None:
            return state

        return JobState(state)

    def get_scheduler_lastchecktime(self) -> Optional[datetime.datetime]:
        """Return the time of the last update of the scheduler state by the daemon or None if it was never set.

        :return: a datetime object or None
        """
        value = self.base.attributes.get(self.SCHEDULER_LAST_CHECK_TIME_KEY, None)

        if value is not None:
            value = datetime.datetime.fromisoformat(value)

        return value

    def set_detailed_job_info(self, detailed_job_info: Optional[dict]) -> None:
        """Set the detailed job info dictionary.

        :param detailed_job_info: a dictionary with metadata with the accounting of a completed job
        """
        self.base.attributes.set(self.SCHEDULER_DETAILED_JOB_INFO_KEY, detailed_job_info)

    def get_detailed_job_info(self) -> Optional[dict]:
        """Return the detailed job info dictionary.

        The scheduler is polled for the detailed job info after the job is completed and ready to be retrieved.

        :return: the dictionary with detailed job info if defined or None
        """
        return self.base.attributes.get(self.SCHEDULER_DETAILED_JOB_INFO_KEY, None)

    def set_last_job_info(self, last_job_info: 'JobInfo') -> None:
        """Set the last job info.

        :param last_job_info: a `JobInfo` object
        """
        from aiida.schedulers.datastructures import JobInfo

        if not isinstance(last_job_info, JobInfo):
            raise ValueError(f'last job info should be an instance of JobInfo, got: {last_job_info}')

        self.base.attributes.set(self.SCHEDULER_LAST_JOB_INFO_KEY, last_job_info.get_dict())

    def get_last_job_info(self) -> Optional['JobInfo']:
        """Return the last information asked to the scheduler about the status of the job.

        The last job info is updated on every poll of the scheduler, except for the final poll when the job drops from
        the scheduler's job queue.
        For completed jobs, the last job info therefore contains the "second-to-last" job info that still shows the job
        as running. Please use :meth:`~aiida.orm.nodes.process.calculation.calcjob.CalcJobNode.get_detailed_job_info`
        instead.

        :return: a `JobInfo` object (that closely resembles a dictionary) or None.
        """
        from aiida.schedulers.datastructures import JobInfo

        last_job_info_dictserialized = self.base.attributes.get(self.SCHEDULER_LAST_JOB_INFO_KEY, None)

        if last_job_info_dictserialized is not None:
            job_info = JobInfo.load_from_dict(last_job_info_dictserialized)
        else:
            job_info = None

        return job_info

    def get_authinfo(self) -> 'AuthInfo':
        """Return the `AuthInfo` that is configured for the `Computer` set for this node.

        :return: `AuthInfo`
        """
        computer = self.computer

        if computer is None:
            raise exceptions.NotExistent('No computer has been set for this calculation')

        return computer.get_authinfo(self.user)

    def get_transport(self) -> 'Transport':
        """Return the transport for this calculation.

        :return: Transport configured
            with the `AuthInfo` associated to the computer of this node
        """
        return self.get_authinfo().get_transport()

    def get_parser_class(self) -> Optional[Type['Parser']]:
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
    def link_label_retrieved(self) -> str:
        """Return the link label used for the retrieved FolderData node."""
        return 'retrieved'

    def get_retrieved_node(self) -> Optional['FolderData']:
        """Return the retrieved data folder.

        :return: the retrieved FolderData node or None if not found
        """
        from aiida.orm import FolderData

        try:
            return (
                self.base.links.get_outgoing(node_class=FolderData, link_label_filter=self.link_label_retrieved)
                .one()
                .node
            )
        except ValueError:
            return None

    @property
    def res(self) -> 'CalcJobResultManager':
        """To be used to get direct access to the parsed parameters.

        :return: an instance of the CalcJobResultManager.

        :note: a practical example on how it is meant to be used: let's say that there is a key 'energy'
            in the dictionary of the parsed results which contains a list of floats.
            The command `calc.res.energy` will return such a list.
        """
        from aiida.orm.utils.calcjob import CalcJobResultManager

        return CalcJobResultManager(self)

    def get_scheduler_stdout(self) -> Optional[AnyStr]:
        """Return the scheduler stderr output if the calculation has finished and been retrieved, None otherwise.

        :return: scheduler stderr output or None
        """
        filename = self.get_option('scheduler_stdout')
        retrieved_node = self.get_retrieved_node()

        if filename is None or retrieved_node is None:
            return None

        try:
            stdout = retrieved_node.base.repository.get_object_content(filename)
        except OSError:
            stdout = None

        return stdout

    def get_scheduler_stderr(self) -> Optional[AnyStr]:
        """Return the scheduler stdout output if the calculation has finished and been retrieved, None otherwise.

        :return: scheduler stdout output or None
        """
        filename = self.get_option('scheduler_stderr')
        retrieved_node = self.get_retrieved_node()

        if filename is None or retrieved_node is None:
            return None

        try:
            stderr = retrieved_node.base.repository.get_object_content(filename)
        except OSError:
            stderr = None

        return stderr

    def get_description(self) -> str:
        """Return a description of the node based on its properties."""
        state = self.get_state()
        if not state:
            return ''
        return state.value
