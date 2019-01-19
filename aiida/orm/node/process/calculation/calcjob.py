# -*- coding: utf-8 -*-
# pylint: disable=cyclic-import
"""ORM class for CalcJobNode."""
from __future__ import absolute_import
from __future__ import print_function

from six.moves import range
from six.moves import zip

import copy
import datetime
import six

from aiida.common.datastructures import CalcJobState
from aiida.common.lang import classproperty
from aiida.common.utils import str_timedelta
from aiida.orm.node import ProcessNode
from aiida.orm.mixins import Sealable
from aiida.common import timezone

from . import CalculationNode

__all__ = ('CalcJobNode', )

SEALED_KEY = 'attributes.{}'.format(Sealable.SEALED_KEY)
CALC_JOB_STATE_KEY = 'attributes.state'
SCHEDULER_STATE_KEY = 'attributes.scheduler_state'
PROCESS_STATE_KEY = 'attributes.{}'.format(ProcessNode.PROCESS_STATE_KEY)
EXIT_STATUS_KEY = 'attributes.{}'.format(ProcessNode.EXIT_STATUS_KEY)
DEPRECATION_DOCS_URL = 'http://aiida-core.readthedocs.io/en/latest/process/index.html#the-process-builder'

_input_subfolder = 'raw_input'


class CalcJobNode(CalculationNode):
    """ORM class for all nodes representing the execution of a CalcJob."""
    # pylint: disable=abstract-method

    CALC_JOB_STATE_KEY = 'state'
    CALC_JOB_STATE_ATTRIBUTE_KEY = 'attributes.{}'.format(CALC_JOB_STATE_KEY)

    _cacheable = True

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
    def _updatable_attributes(cls):
        return super(CalcJobNode, cls)._updatable_attributes + (
            'job_id', 'scheduler_state', 'scheduler_lastchecktime', 'last_jobinfo', 'remote_workdir', 'retrieve_list',
            'retrieve_temporary_list', 'retrieve_singlefile_list', cls.CALC_JOB_STATE_KEY)

    @classproperty
    def _hash_ignored_attributes(cls):
        return super(CalcJobNode, cls)._hash_ignored_attributes + (
            'queue_name',
            'account',
            'qos',
            'priority',
            'max_wallclock_seconds',
            'max_memory_kb',
        )

    def get_hash(self, ignore_errors=True, ignored_folder_content=('raw_input',), **kwargs):
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
        from aiida.work.ports import PortNamespace

        process_class = self.process_class
        inputs = self.get_incoming()
        options = self.get_options()
        builder = process_class.get_builder()

        for port_name, port in process_class.spec().inputs.items():
            if port_name == process_class.spec().metadata_key:
                builder.metadata.options = options
            elif isinstance(port, PortNamespace):
                namespace = port_name + '_'
                sub = {entry.link_label[len(namespace):]: entry.node for entry in inputs if entry.link_label.startswith(namespace)}
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
        from aiida.common.exceptions import MissingPluginError, ValidationError

        super(CalcJobNode, self)._validate()

        if self.get_computer() is None:
            raise ValidationError("You did not specify a computer")

        if self.get_state() and self.get_state() not in CalcJobState:
            raise ValidationError("Calculation state '{}' is not valid".format(self.get_state()))

        try:
            _ = self.get_parserclass()
        except MissingPluginError:
            raise ValidationError("No valid class/implementation found for the parser '{}'. "
                                  "Set the parser to None if you do not need an automatic "
                                  "parser.".format(self.get_option('parser_name')))

        computer = self.get_computer()
        s = computer.get_scheduler()
        resources = self.get_option('resources')
        def_cpus_machine = computer.get_default_mpiprocs_per_machine()
        if def_cpus_machine is not None:
            resources['default_mpiprocs_per_machine'] = def_cpus_machine
        try:
            _ = s.create_job_resource(**resources)
        except (TypeError, ValueError) as exc:
            raise ValidationError("Invalid resources for the scheduler of the specified computer: {}".format(exc))

    def _store_raw_input_folder(self, folder_path):
        """
        Copy the content of the folder internally, in a subfolder called
        'raw_input'

        :param folder_path: the path to the folder from which the content
               should be taken
        """
        _raw_input_folder = self.folder.get_subfolder(_input_subfolder, create=True)
        _raw_input_folder.replace_with_folder(folder_path, move=False, overwrite=True)

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

    @property
    def options(self):
        try:
            return self.process_class.spec().inputs._ports['metadata']['options']
        except ValueError:
            return {}

    def get_option(self, name):
        """
        Retun the value of an option that was set for this CalcJobNode

        :param name: the option name
        :return: the option value or None
        :raises: ValueError for unknown option
        """
        return self.get_attr(name, None)

    def set_option(self, name, value):
        """
        Set an option to the given value

        :param name: the option name
        :param value: the value to set
        :raises: ValueError for unknown option
        :raises: TypeError for values with invalid type
        """
        self._set_attr(name, value)

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
        state = self.get_attr(self.CALC_JOB_STATE_KEY, None)

        if state:
            return CalcJobState(state)

        return None

    def _set_state(self, state):
        """
        Set the state of the calculation job.

        :param state: a string with the state from ``aiida.common.datastructures.CalcJobState``.
        :raise: ValueError if state is invalid
        """
        if state not in CalcJobState:
            raise ValueError('{} is not a valid CalcJobState'.format(state))

        self._set_attr(self.CALC_JOB_STATE_KEY, state.value)

    def _del_state(self):
        """Delete the calculation job state attribute if it exists."""
        try:
            self._del_attr(self.CALC_JOB_STATE_KEY)
        except AttributeError:
            pass

    def _set_remote_workdir(self, remote_workdir):
        self._set_attr('remote_workdir', remote_workdir)

    def _get_remote_workdir(self):
        """
        Get the path to the remote (on cluster) scratch
        folder of the calculation.

        :return: a string with the remote path
        """
        return self.get_attr('remote_workdir', None)

    def _set_retrieve_list(self, retrieve_list):
        if not (isinstance(retrieve_list, (tuple, list))):
            raise ValueError("You should pass a list/tuple")
        for item in retrieve_list:
            if not isinstance(item, six.string_types):
                if (not (isinstance(item, (tuple, list))) or len(item) != 3):
                    raise ValueError("You should pass a list containing either strings or lists/tuples")
                if (not (isinstance(item[0], six.string_types)) or not (isinstance(item[1], six.string_types)) or
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

    def _set_retrieve_temporary_list(self, retrieve_temporary_list):
        """
        Set the list of paths that are to retrieved for parsing and be deleted as soon
        as the parsing has been completed.
        """
        if not (isinstance(retrieve_temporary_list, (tuple, list))):
            raise ValueError('You should pass a list/tuple')

        for item in retrieve_temporary_list:
            if not isinstance(item, six.string_types):
                if (not (isinstance(item, (tuple, list))) or len(item) != 3):
                    raise ValueError('You should pass a list containing either ' 'strings or lists/tuples')

                if (not (isinstance(item[0], six.string_types)) or not (isinstance(item[1], six.string_types)) or
                        not (isinstance(item[2], int))):
                    raise ValueError('You have to pass a list (or tuple) of lists, with remotepath(string), '
                                     'localpath(string) and depth (integer)')

        self._set_attr('retrieve_temporary_list', retrieve_temporary_list)

    def _get_retrieve_temporary_list(self):
        """
        Get the list of files/directories to be retrieved on the cluster and will be kept temporarily during parsing.
        Their path is relative to the remote workdirectory path.

        :return: a list of strings for file/directory names
        """
        return self.get_attr('retrieve_temporary_list', None)

    def _set_retrieve_singlefile_list(self, retrieve_singlefile_list):
        """
        Set the list of information for the retrieval of singlefiles
        """
        if not isinstance(retrieve_singlefile_list, (tuple, list)):
            raise ValueError("You have to pass a list (or tuple) of lists of strings as retrieve_singlefile_list")
        for j in retrieve_singlefile_list:
            if (not (isinstance(j, (tuple, list))) or not (all(isinstance(i, six.string_types) for i in j))):
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
        return self._set_attr('job_id', six.text_type(job_id))

    def get_job_id(self):
        """
        Get the scheduler job id of the calculation.

        :return: a string
        """
        return self.get_attr('job_id', None)

    def _set_scheduler_state(self, state):
        from aiida.common import timezone
        from aiida.scheduler.datastructures import JobState

        if not isinstance(state, JobState):
            raise ValueError('scheduler state should be an instance of JobState, got: {}'.format())

        self._set_attr('scheduler_state', state.value)
        self._set_attr('scheduler_lastchecktime', timezone.now())

    def get_scheduler_state(self):
        """
        Return the status of the calculation according to the cluster scheduler.

        :return: a JobState enum instance.
        """
        from aiida.scheduler.datastructures import JobState

        state = self.get_attr('scheduler_state', None)

        if state is None:
            return state

        return JobState(state)

    def _get_scheduler_lastchecktime(self):
        """
        Return the time of the last update of the scheduler state by the daemon,
        or None if it was never set.

        :return: a datetime object.
        """
        return self.get_attr('scheduler_lastchecktime', None)

    def _set_last_jobinfo(self, last_jobinfo):
        self._set_attr('last_jobinfo', last_jobinfo.serialize())

    def _get_last_jobinfo(self):
        """
        Get the last information asked to the scheduler
        about the status of the job.

        :return: a JobInfo object (that closely resembles a dictionary) or None.
        """
        from aiida.scheduler.datastructures import JobInfo

        last_jobinfo_serialized = self.get_attr('last_jobinfo', None)
        if last_jobinfo_serialized is not None:
            jobinfo = JobInfo()
            jobinfo.load_from_serialized(last_jobinfo_serialized)
            return jobinfo
        else:
            return None

    def _get_authinfo(self):
        from aiida.common.exceptions import NotExistent
        from aiida.orm.authinfos import AuthInfo

        computer = self.get_computer()
        if computer is None:
            raise NotExistent("No computer has been set for this calculation")

        return AuthInfo.from_backend_entity(self.backend.authinfos.get(computer=computer, user=self.get_user()))

    def _get_transport(self):
        """
        Return the transport for this calculation.
        """
        return self._get_authinfo().get_transport()

    def get_parserclass(self):
        """
        Return the output parser object for this calculation, or None
        if no parser is set.

        :return: a Parser class.
        :raise: MissingPluginError from ParserFactory no plugin is found.
        """
        from aiida.parsers import ParserFactory

        parser_name = self.get_option('parser_name')

        if parser_name is not None:
            return ParserFactory(parser_name)
        else:
            return None

    @property
    def link_label_retrieved(self):
        """Return the link label used for the retrieved FolderData node."""
        return 'retrieved'

    def get_retrieved_node(self):
        """Return the retrieved data folde.

        :return: the retrieved FolderData node
        :raise MultipleObjectsError: if no or more than one retrieved node is found.
        """
        from aiida.orm.data.folder import FolderData
        return self.get_outgoing(node_class=FolderData, link_label_filter=self.link_label_retrieved).one().node

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

    def get_scheduler_output(self):
        """
        Return the output of the scheduler output (a string) if the calculation
        has finished, and output node is present, and the output of the
        scheduler was retrieved.

        Return None otherwise.
        """
        from aiida.common.exceptions import NotExistent

        filename = self.get_option('scheduler_stdout')

        # Shortcut if no error file is set
        if filename is None:
            return None

        retrieved_node = self.get_retrieved_node()
        if retrieved_node is None:
            return None

        try:
            outfile_content = retrieved_node.get_file_content(filename)
        except NotExistent:
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

        filename = self.get_option('scheduler_stderr')

        # Shortcut if no error file is set
        if filename is None:
            return None

        retrieved_node = self.get_retrieved_node()
        if retrieved_node is None:
            return None

        try:
            errfile_content = retrieved_node.get_file_content(filename)
        except (NotExistent):
            # Return None if no file is found
            return None

        return errfile_content

    def get_desc(self):
        """
        Returns a string with infos retrieved from a CalcJobNode node's
        properties.
        """
        return self.get_state()

    projection_map = {
        'pk': ('calculation', 'id'),
        'ctime': ('calculation', 'ctime'),
        'mtime': ('calculation', 'mtime'),
        'scheduler_state': ('calculation', SCHEDULER_STATE_KEY),
        'calc_job_state': ('calculation', CALC_JOB_STATE_KEY),
        'process_state': ('calculation', PROCESS_STATE_KEY),
        'exit_status': ('calculation', EXIT_STATUS_KEY),
        'sealed': ('calculation', SEALED_KEY),
        'type': ('calculation', 'type'),
        'description': ('calculation', 'description'),
        'label': ('calculation', 'label'),
        'uuid': ('calculation', 'uuid'),
        'user': ('user', 'email'),
        'computer': ('computer', 'name')
    }

    compound_projection_map = {
        'state': ('calculation', (PROCESS_STATE_KEY, EXIT_STATUS_KEY)),
        'job_state': ('calculation', (CALC_JOB_STATE_KEY, SCHEDULER_STATE_KEY))
    }

    @classmethod
    def _list_calculations(cls,
                           states=None,
                           past_days=None,
                           groups=None,
                           all_users=False,
                           pks=tuple(),
                           relative_ctime=True,
                           with_scheduler_state=False,
                           order_by=None,
                           limit=None,
                           filters=None,
                           projections=('pk', 'state', 'ctime', 'sched', 'computer', 'type'),
                           raw=False):
        """
        Print a description of the AiiDA calculations.

        :param states: a list of string with states. If set, print only the
            calculations in the states "states", otherwise shows all.
            Default = None.
        :param past_days: If specified, show only calculations that were
            created in the given number of past days.
        :param groups: If specified, show only calculations belonging to these groups
        :param pks: if specified, must be a list of integers, and only
            calculations within that list are shown. Otherwise, all
            calculations are shown.
            If specified, sets state to None and ignores the
            value of the ``past_days`` option.")
        :param relative_ctime: if true, prints the creation time relative from now.
                               (like 2days ago). Default = True
        :param filters: a dictionary of filters to be passed to the QueryBuilder query
        :param all_users: if True, list calculation belonging to all users.
                           Default = False
        :param raw: Only print the query result, without any headers, footers
            or other additional information

        :return: a string with description of calculations.
        """

        from aiida.orm.querybuilder import QueryBuilder
        from tabulate import tabulate
        from aiida import orm

        projection_label_dict = {
            'pk': 'PK',
            'state': 'State',
            'process_state': 'Process state',
            'exit_status': 'Exit status',
            'sealed': 'Sealed',
            'ctime': 'Creation',
            'mtime': 'Modification',
            'job_state': 'Job state',
            'calc_job_state': 'Calculation job state',
            'scheduler_state': 'Scheduler state',
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
                if state not in CalcJobState:
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

        if filters is None:
            calculation_filters = {}
        else:
            calculation_filters = filters

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
                calculation_filters['attributes.{}'.format(cls.CALC_JOB_STATE_KEY)] = {'in': states}

            # Filter on the users, if not all users
            if not all_users:
                user_id = orm.User.objects.get_default().id
                calculation_filters['user_id'] = {'==': user_id}

            if past_days is not None:
                n_days_ago = now - datetime.timedelta(days=past_days)
                calculation_filters['ctime'] = {'>': n_days_ago}

            # Filter on the groups
            if groups:
                group_filters = {'uuid': {'in': [group.uuid for group in groups]}}
            else:
                group_filters = None

        calc_list_header = [projection_label_dict[p] for p in projections]

        qb = orm.QueryBuilder()
        qb.append(cls, filters=calculation_filters, tag='calculation')

        if group_filters is not None:
            qb.append(type='group', filters=group_filters, with_node='calculation')

        qb.append(type='computer', with_node='calculation', tag='computer')
        qb.append(type='user', with_node="calculation", tag="user")

        projections_dict = {'calculation': [], 'user': [], 'computer': []}

        # Expand compound projections
        for compound_projection in ['state', 'job_state']:
            if compound_projection in projections:
                field, values = cls.compound_projection_map[compound_projection]
                for value in values:
                    projections_dict[field].append(value)

        for p in projections:
            if p in cls.projection_map:
                for k, v in [cls.projection_map[p]]:
                    projections_dict[k].append(v)

        for k, v in projections_dict.items():
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
                    res = next(results_generator)

                    row = cls._get_calculation_info_row(res, projections, now if relative_ctime else None)

                    # Build the row of information
                    calc_list_data.append(row)

                    counter += 1

                if raw:
                    print(tabulate(calc_list_data, tablefmt='plain'))
                else:
                    print(tabulate(calc_list_data, headers=calc_list_header))

            except StopIteration:
                if raw:
                    print(tabulate(calc_list_data, tablefmt='plain'))
                else:
                    print(tabulate(calc_list_data, headers=calc_list_header))
                break

        if not raw:
            print("\nTotal results: {}\n".format(counter))

    @classmethod
    def _get_calculation_info_row(cls, res, projections, times_since=None):
        """
        Get a row of information about a calculation.

        :param res: Results from the calculations query.
        :param times_since: Times are relative to this timepoint, if None then
            absolute times will be used.
        :param projections: The projections used in the calculation query
        :type projections: list
        :type times_since: :class:`!datetime.datetime`
        :return: A list of string with information about the calculation.
        """
        d = copy.deepcopy(res)

        try:
            prefix = 'node.process.calculation.calcjob.'
            calculation_type = d['calculation']['type']
            module, class_name = calculation_type.rsplit('.', 2)[:2]

            # For the base class 'mode.process.calculation.calcjob.CalcJobNode' the module at this point equals
            # 'node.process.calculation.calcjob'. For this case we should simply set the type to the base module
            # 'node.process.calculation.calcjob. Otherwise we need to strip the prefix to get the proper sub module
            if module == prefix.rstrip('.'):
                d['calculation']['type'] = module[len(prefix):]
            else:
                assert module.startswith(prefix), "module '{}' does not start with '{}'".format(module, prefix)
                d['calculation']['type'] = module[len(prefix):]
        except KeyError:
            pass
        for proj in ('ctime', 'mtime'):
            try:
                time = d['calculation'][proj]
                if times_since:
                    dt = timezone.delta(time, times_since)
                    d['calculation'][proj] = str_timedelta(dt, negative_to_zero=True, max_num_fields=1)
                else:
                    d['calculation'][proj] =' '.join([
                        timezone.localtime(time).isoformat().split('T')[0],
                        timezone.localtime(time).isoformat().split('T')[1].split('.')[0].rsplit(":", 1)[0]
                    ])
            except (KeyError, ValueError):
                pass

        if PROCESS_STATE_KEY in d['calculation']:

            process_state = d['calculation'][PROCESS_STATE_KEY]

            if process_state is None:
                process_state = 'unknown'

            d['calculation'][PROCESS_STATE_KEY] = process_state.capitalize()

        if SEALED_KEY in d['calculation']:
            sealed = 'True' if d['calculation'][SEALED_KEY] == 1 else 'False'
            d['calculation'][SEALED_KEY] = sealed

        result = []

        for projection in projections:

            if projection in cls.compound_projection_map:
                field, attributes = cls.compound_projection_map[projection]
                projected_attributes = [str(d[field][attribute]) for attribute in attributes]
                result.append(' | '.join(projected_attributes))
            else:
                field = cls.projection_map[projection][0]
                attribute = cls.projection_map[projection][1]
                result.append(d[field][attribute])

        return result

    @classmethod
    def _get_all_with_state(cls,
                            state,
                            computer=None,
                            user=None,
                            only_computer_user_pairs=False,
                            only_enabled=True,
                            limit=None):
        """
        Filter all calculations with a given state.

        Issue a warning if the state is not in the list of valid states.

        :param str state: The state to be used to filter (should be a string among
                those defined in aiida.common.datastructures.CalcJobState)
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
        # I assume that CalcJobState are strings. If this changes in the future,
        # update the filter below from dbattributes__tval to the correct field.
        from aiida.orm.computers import Computer
        from aiida.orm.querybuilder import QueryBuilder

        if state not in CalcJobState:
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
                raise Exception("{} is not a valid computer\n{}".format(computer, e))

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
        qb.append(cls, filters=calcfilter, tag='calc', with_computer='computer')
        qb.append(type="user", tag='user', filters=userfilter, with_node="calc")

        if only_computer_user_pairs:
            qb.add_projection("computer", "*")
            qb.add_projection("user", "*")
            returnresult = qb.distinct().all()
        else:
            qb.add_projection("calc", "*")
            if limit is not None:
                qb.limit(limit)
            returnresult = qb.all()
            returnresult = next(zip(*returnresult))
        return returnresult
