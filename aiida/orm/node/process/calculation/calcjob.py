# -*- coding: utf-8 -*-
"""ORM class for CalcJobNode."""
from __future__ import absolute_import
from __future__ import print_function

from six.moves import range
from six.moves import zip

import copy
import datetime
import enum
import io
import six
import warnings

from aiida.common.datastructures import calc_states
from aiida.common.exceptions import ModificationNotAllowed, MissingPluginError
from aiida.common.links import LinkType
from aiida.common.lang import classproperty
from aiida.common.utils import str_timedelta
from aiida.plugins.loader import get_plugin_type_from_type_string
from aiida.orm.node.process import ProcessNode
from aiida.orm.mixins import Sealable
from aiida.common import timezone

from .calculation import CalculationNode

__all__ = ('CalcJobNode', 'CalculationResultManager')

SEALED_KEY = 'attributes.{}'.format(Sealable.SEALED_KEY)
CALCULATION_STATE_KEY = 'attributes.state'
SCHEDULER_STATE_KEY = 'attributes.scheduler_state'
PROCESS_STATE_KEY = 'attributes.{}'.format(ProcessNode.PROCESS_STATE_KEY)
EXIT_STATUS_KEY = 'attributes.{}'.format(ProcessNode.EXIT_STATUS_KEY)
DEPRECATION_DOCS_URL = 'http://aiida-core.readthedocs.io/en/latest/process/index.html#the-process-builder'

_input_subfolder = 'raw_input'


class CalcJobExitStatus(enum.Enum):
    """
    This enumeration maps specific calculation states to an integer. This integer can
    then be used to set the exit status of a CalcJobNode node. The values defined
    here map directly on the failed calculation states, but the idea is that sub classes
    of CalcJobNode can extend this enum with additional error codes
    """
    FINISHED = 0
    SUBMISSIONFAILED = 100
    RETRIEVALFAILED = 200
    PARSINGFAILED = 300
    FAILED = 400


class CalcJobNode(CalculationNode):
    """ORM class for all nodes representing the execution of a CalcJob."""
    # pylint: disable=abstract-method

    JOB_STATE_KEY = 'state'
    JOB_STATE_ATTRIBUTE_KEY = 'attributes.{}'.format(JOB_STATE_KEY)

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

    def __dir__(self):
        """
        Allow to list all valid attributes, adding also the use_* methods
        """
        return sorted(dir(type(self)) + list(['use_{}'.format(k) for k in self._use_methods.keys()]))

    def __getattr__(self, name):
        """
        Expand the methods with the use_* calls. Note that this method only gets called if 'name'
        is not already defined as a method. Returning one will then automatically raise the
        standard AttributeError exception.
        """
        if name == '_use_methods':
            raise AttributeError("'{0}' object has no attribute '{1}'".format(type(self), name))

        class UseMethod(object):
            """
            Generic class for the use_* methods. To know which use_* methods
            exist, use the ``dir()`` function. To get help on a specific method,
            for instance use_code, use::
              ``print use_code.__doc__``
            """

            def __init__(self, node, actual_name, data):
                self.node = node
                self.actual_name = actual_name
                self.data = data

                try:
                    self.__doc__ = data['docstring']
                except KeyError:
                    # Forgot to define the docstring! Use the default one
                    pass

            def __call__(self, parent_node, *args, **kwargs):
                # Not really needed, will be checked in get_linkname but I do anyway in order to raise
                # an exception as soon as possible, with the most intuitive caller function name
                additional_parameter = _parse_single_arg(
                    function_name='use_{}'.format(self.actual_name),
                    additional_parameter=self.data['additional_parameter'],
                    args=args, kwargs=kwargs)

                # Type check
                if not isinstance(parent_node, self.data['valid_types']):
                    if isinstance(self.data['valid_types'], collections.Iterable):
                        valid_types_string = ','.join([_.__name__ for _ in self.data['valid_types']])
                    else:
                        valid_types_string = self.data['valid_types'].__name__

                    raise TypeError(
                        'The given node is not of the valid type for use_{}.'
                        'Valid types are: {}, while you provided {}'.format(
                            self.actual_name, valid_types_string, parent_node.__class__.__name__))

                # Get actual link name
                actual_linkname = self.node.get_linkname(actual_name, *args, **kwargs)

                # Here I do the real job
                self.node._replace_link_from(parent_node, LinkType.INPUT_CALC, actual_linkname)

        prefix = 'use_'
        valid_use_methods = ['{}{}'.format(prefix, k) for k in self._use_methods.keys()]

        if name in valid_use_methods:
            actual_name = name[len(prefix):]
            return UseMethod(node=self, actual_name=actual_name, data=self._use_methods[actual_name])
        else:
            raise AttributeError("'{}' object has no attribute '{}'".format(self.__class__.__name__, name))

    @classproperty
    def _use_methods(cls):
        """
        Return the list of valid input nodes that can be set using the
        use_* method.

        For each key KEY of the return dictionary, the 'use_KEY' method is
        exposed.
        Each value must be a dictionary, defining the following keys:
        * valid_types: a class, or tuple of classes, that will be used to
          validate the parameter using the isinstance() method
        * additional_parameter: None, if no additional parameters can be passed
          to the use_KEY method beside the node, or the name of the additional
          parameter (a string)
        * linkname: the name of the link to create (a string if
          additional_parameter is None, or a callable if additional_parameter is
          a string. The value of the additional parameter will be passed to the
          callable, and it should return a string.
        * docstring: a docstring for the function

        .. note:: in subclasses, always extend the parent class, do not
          substitute it!
        """
        from aiida.orm.data.code import Code
        return {
            'code': {
                'valid_types': Code,
                'additional_parameter': None,
                'linkname': 'code',
                'docstring': 'Choose the code to use',
            },
        }

    def get_linkname(self, link, *args, **kwargs):
        """
        Return the linkname used for a given input link
        Pass as parameter "NAME" if you would call the use_NAME method.
        If the use_NAME method requires a further parameter, pass that
        parameter as the second parameter.
        """
        try:
            data = self._use_methods[link]
        except KeyError:
            raise ValueError("No '{}' link is defined for this calculation".format(link))

        # Raises if the wrong # of parameters is passed
        additional_parameter = _parse_single_arg(
            function_name='get_linkname',
            additional_parameter=data['additional_parameter'],
            args=args, kwargs=kwargs)

        if data['additional_parameter'] is not None:
            # Call the callable to get the proper linkname
            actual_linkname = data['linkname'](additional_parameter)
        else:
            actual_linkname = data['linkname']

        return actual_linkname

    def get_code(self):
        """
        Return the code for this calculation, or None if the code was not set.
        """
        from aiida.orm.data.code import Code
        from aiida.common.exceptions import NotExistent

        node =  self.get_incoming(node_class=Code)
        try:
            return node.get_node_by_label(self._use_methods['code']['linkname'])
        except NotExistent:
            return None


    @classproperty
    def exit_status_enum(cls):
        return CalcJobExitStatus

    @property
    def exit_status_label(self):
        """
        Return the label belonging to the exit status of the Calculation

        :returns: the exit status label
        """
        try:
            exit_status_enum = self.exit_status_enum(self.exit_status)
            exit_status_label = exit_status_enum.name
        except ValueError:
            exit_status_label = 'UNKNOWN'

        return exit_status_label

    _cacheable = True

    @classproperty
    def _updatable_attributes(cls):
        return super(CalcJobNode, cls)._updatable_attributes + (
            'job_id', 'scheduler_state', 'scheduler_lastchecktime', 'last_jobinfo', 'remote_workdir', 'retrieve_list',
            'retrieve_temporary_list', 'retrieve_singlefile_list', cls.JOB_STATE_KEY)

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

    @classmethod
    def process(cls):
        """
        Return the JobProcess class constructed based on this JobCalculatin class

        :return: JobProcess class
        """
        from aiida.work.job_processes import JobProcess
        return JobProcess.build(cls)

    @classmethod
    def get_builder(cls):
        """
        Return a JobProcessBuilder instance, tailored for this calculation class

        This builder is a mapping of the inputs of the CalcJobNode class, supports tab-completion, automatic
        validation when settings values as well as automated docstrings for each input

        :return: JobProcessBuilder instance
        """
        return cls.process().get_builder()

    def get_builder_restart(self):
        """
        Return a JobProcessBuilder instance, tailored for this calculation instance

        This builder is a mapping of the inputs of the CalcJobNode class, supports tab-completion, automatic
        validation when settings values as well as automated docstrings for each input.

        The fields of the builder will be pre-populated with all the inputs recorded for this instance as well as
        settings all the options that were explicitly set for this calculation instance.

        This builder can then directly be launched again to effectively run a duplicate calculation. But more useful
        is that it serves as a starting point to, after changing one or more inputs, launch a similar calculation by
        using this already completed calculation as a starting point.

        :return: JobProcessBuilder instance
        """
        from aiida.work.job_processes import JobProcess
        from aiida.work.ports import PortNamespace

        inputs = self.get_incoming()
        options = self.get_options(only_actually_set=True)
        builder = self.get_builder()

        for port_name, port in self.process().spec().inputs.items():
            if port_name == JobProcess.OPTIONS_INPUT_LABEL:
                setattr(builder, port_name, options)
            elif isinstance(port, PortNamespace):
                namespace = port_name + '_'
                sub = {entry.link_label[len(namespace):]: entry.node for entry in inputs if entry.link_label.startswith(namespace)}
                if sub:
                    setattr(builder, port_name, sub)
            else:
                if port_name in inputs.all_link_labels():
                    setattr(builder, port_name, inputs.get_node_by_label(port_name))

        return builder

    def _init_internal_params(self):
        """
        Define here internal parameters that should be defined right after the __init__
        This function is actually called by the __init__

        :note: if you inherit this function, ALWAYS remember to call super()._init_internal_params()
            as the first thing in your inherited function.
        """
        # By default, no output parser
        self._default_parser = None

        # Set default for the link to the retrieved folder (after calc is done)
        self._linkname_retrieved = 'retrieved'

        # Files in which the scheduler output and error will be stored.
        # If they are identical, outputs will be joined.
        self._SCHED_OUTPUT_FILE = '_scheduler-stdout.txt'
        self._SCHED_ERROR_FILE = '_scheduler-stderr.txt'

        # Files that should be shown by default, set it to None if you do not have a default file
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
        parent_dict = super(CalcJobNode, self)._set_defaults

        parent_dict.update({"parser_name": self._default_parser, "_linkname_retrieved": self._linkname_retrieved})

        return parent_dict

    def store(self, *args, **kwargs):
        """
        Override the store() method to store also the calculation in the NEW
        state as soon as this is stored for the first time.
        """
        super(CalcJobNode, self).store(*args, **kwargs)

        if self.get_state() is None:
            self._set_state(calc_states.NEW)

        return self

    def _add_outputs_from_cache(self, cache_node):
        self._set_state(calc_states.PARSING)
        super(CalcJobNode, self)._add_outputs_from_cache(cache_node=cache_node)
        self._set_state(cache_node.get_state())

    def _validate(self):
        """
        Verify if all the input nodes are present and valid.

        :raise: ValidationError: if invalid parameters are found.
        """
        from aiida.common.exceptions import MissingPluginError, ValidationError

        super(CalcJobNode, self)._validate()

        if self.get_computer() is None:
            raise ValidationError("You did not specify a computer")

        if self.get_state() not in calc_states:
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

        if not isinstance(self.get_option('withmpi', only_actually_set=False), bool):
            raise ValidationError("withmpi property must be boolean! It in instead {}"
                                  "".format(str(type(self.get_option('withmpi')))))

    def validate_incoming(self, source, link_type, link_label):
        """
        Validate adding a link of the given type from a given node to ourself.

        :param source: the node from which the link is coming
        :param link_type: the type of link
        :param link_label: link label
        :raise TypeError: if `source` is not a Node instance or `link_type` is not a `LinkType` enum
        :raise ValueError: if the proposed link is invalid
        """
        super(CalcJobNode, self).validate_incoming(source, link_type, link_label)

        state = self.get_state()
        valid_states = [calc_states.NEW]
        if state not in valid_states:
            raise ModificationNotAllowed('invalid link: CalcJobNode has to have state in {}, but is {}'.format(
                valid_states, state))

    def validate_outgoing(self, target, link_type, link_label):
        """
        Validate adding a link of the given type from ourself to a given node.

        :param target: the node to which the link is goming
        :param link_type: the type of link
        :param link_label: link label
        :raise TypeError: if `target` is not a Node instance or `link_type` is not a `LinkType` enum
        :raise ValueError: if the proposed link is invalid
        """
        super(CalcJobNode, self).validate_outgoing(target, link_type, link_label)

        state = self.get_state()
        valid_states = [calc_states.SUBMITTING, calc_states.RETRIEVING, calc_states.PARSING]

        if state not in valid_states:
            raise ModificationNotAllowed('invalid link: CalcJobNode has to have state in {}, but is {}'.format(
                valid_states, state))

    def _store_raw_input_folder(self, folder_path):
        """
        Copy the content of the folder internally, in a subfolder called
        'raw_input'

        :param folder_path: the path to the folder from which the content
               should be taken
        """
        # This function can be called only if the state is TOSUBMIT
        if self.get_state() != calc_states.TOSUBMIT:
            raise ModificationNotAllowed("The raw input folder can be stored only if the "
                                         "state is TOSUBMIT, it is instead {}".format(self.get_state()))

        # get subfolder and replace with copy
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

    @classproperty
    def options(cls):
        from aiida import orm

        return {
            'resources': {
                'attribute_key': 'jobresource_params',
                'valid_type': dict,
                'default': {},
                'help': 'Set the dictionary of resources to be used by the scheduler plugin, like the number of nodes, '
                        'cpus etc. This dictionary is scheduler-plugin dependent. Look at the documentation of the '
                        'scheduler for more details.'
            },
            'max_wallclock_seconds': {
                'attribute_key': 'max_wallclock_seconds',
                'valid_type': int,
                'non_db': True,
                'required': False,
                'help': 'Set the wallclock in seconds asked to the scheduler',
            },
            'custom_scheduler_commands': {
                'attribute_key': 'custom_scheduler_commands',
                'valid_type': six.string_types,
                'non_db': True,
                'required': False,
                'default': '',
                'help': 'Set a (possibly multiline) string with the commands that the user wants to manually set for the '
                        'scheduler. The difference of this option with respect to the `prepend_text` is the position in '
                        'the scheduler submission file where such text is inserted: with this option, the string is '
                        'inserted before any non-scheduler command',
            },
            'queue_name': {
                'attribute_key': 'queue_name',
                'valid_type': six.string_types,
                'non_db': True,
                'required': False,
                'help': 'Set the name of the queue on the remote computer',
            },
            'account': {
                'attribute_key': 'account',
                'valid_type': six.string_types,
                'non_db': True,
                'required': False,
                'help': 'Set the account to use in for the queue on the remote computer',
            },
            'qos': {
                'attribute_key': 'qos',
                'valid_type': six.string_types,
                'non_db': True,
                'required': False,
                'help': 'Set the quality of service to use in for the queue on the remote computer',
            },
            'computer': {
                'attribute_key': None,
                'valid_type': orm.Computer,
                'non_db': True,
                'required': False,
                'help': 'Set the computer to be used by the calculation',
            },
            'withmpi': {
                'attribute_key': 'withmpi',
                'valid_type': bool,
                'non_db': True,
                'required': False,
                'default': True,
                'help': 'Set the calculation to use mpi',
            },
            'mpirun_extra_params': {
                'attribute_key': 'mpirun_extra_params',
                'valid_type': (list, tuple),
                'non_db': True,
                'required': False,
                'default': [],
                'help': 'Set the extra params to pass to the mpirun (or equivalent) command after the one provided in '
                        'computer.mpirun_command. Example: mpirun -np 8 extra_params[0] extra_params[1] ... exec.x',
            },
            'import_sys_environment': {
                'attribute_key': 'import_sys_environment',
                'valid_type': bool,
                'non_db': True,
                'required': False,
                'default': True,
                'help': 'If set to true, the submission script will load the system environment variables',
            },
            'environment_variables': {
                'attribute_key': 'custom_environment_variables',
                'valid_type': dict,
                'non_db': True,
                'required': False,
                'default': {},
                'help': 'Set a dictionary of custom environment variables for this calculation',
            },
            'priority': {
                'attribute_key': 'priority',
                'valid_type': six.string_types[0],
                'non_db': True,
                'required': False,
                'help': 'Set the priority of the job to be queued',
            },
            'max_memory_kb': {
                'attribute_key': 'max_memory_kb',
                'valid_type': int,
                'non_db': True,
                'required': False,
                'help': 'Set the maximum memory (in KiloBytes) to be asked to the scheduler',
            },
            'prepend_text': {
                'attribute_key': 'prepend_text',
                'valid_type': six.string_types[0],
                'non_db': True,
                'required': False,
                'default': '',
                'help': 'Set the calculation-specific prepend text, which is going to be prepended in the scheduler-job '
                        'script, just before the code execution',
            },
            'append_text': {
                'attribute_key': 'append_text',
                'valid_type': six.string_types[0],
                'non_db': True,
                'required': False,
                'default': '',
                'help': 'Set the calculation-specific append text, which is going to be appended in the scheduler-job '
                        'script, just after the code execution',
            },
            'parser_name': {
                'attribute_key': 'parser',
                'valid_type': six.string_types[0],
                'non_db': True,
                'required': False,
                'help': 'Set a string for the output parser. Can be None if no output plugin is available or needed',
            }
        }

    def get_option(self, name, only_actually_set=False):
        """
        Retun the value of an option that was set for this CalcJobNode

        :param name: the option name
        :param only_actually_set: when False will return the default value even when option had not been explicitly set
        :return: the option value or None
        :raises: ValueError for unknown option
        """
        if name not in self.options:
            raise ValueError('unknown option {}'.format(name))

        option = self.options[name]
        attribute_key = option['attribute_key']
        default = option.get('default', None)

        attribute = self.get_attr(attribute_key, None)

        if attribute is None and only_actually_set is False and default is not None:
            attribute = default

        return attribute

    def set_option(self, name, value):
        """
        Set an option to the given value

        :param name: the option name
        :param value: the value to set
        :raises: ValueError for unknown option
        :raises: TypeError for values with invalid type
        """
        if name not in self.options:
            raise ValueError('unknown option {}'.format(name))

        option = self.options[name]
        valid_type = option['valid_type']
        attribute_key = option['attribute_key']

        if not isinstance(value, valid_type):
            raise TypeError('value is of invalid type {}'.format(type(value)))

        self._set_attr(attribute_key, value)

    def get_options(self, only_actually_set=False):
        """
        Return the dictionary of options set for this CalcJobNode

        :param only_actually_set: when False will return the default value even when option had not been explicitly set
        :return: dictionary of the options and their values
        """
        options = {}
        for name in self.options.keys():
            value = self.get_option(name, only_actually_set=only_actually_set)
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

    def set_queue_name(self, val):
        """
        Set the name of the queue on the remote computer.

        :param str val: the queue name
        """
        from aiida.common.warnings import AiidaDeprecationWarning as DeprecationWarning  # pylint: disable=redefined-builtin
        warnings.warn('explicit option getter/setter methods are deprecated, use get_option and set_option',
                      DeprecationWarning)
        if val is not None:
            self._set_attr('queue_name', six.text_type(val))

    def set_account(self, val):
        """
        Set the account on the remote computer.

        :param str val: the account name
        """
        from aiida.common.warnings import AiidaDeprecationWarning as DeprecationWarning  # pylint: disable=redefined-builtin
        warnings.warn('explicit option getter/setter methods are deprecated, use get_option and set_option',
                      DeprecationWarning)
        if val is not None:
            self._set_attr('account', six.text_type(val))

    def set_qos(self, val):
        """
        Set the quality of service on the remote computer.

        :param str val: the quality of service
        """
        from aiida.common.warnings import AiidaDeprecationWarning as DeprecationWarning  # pylint: disable=redefined-builtin
        warnings.warn('explicit option getter/setter methods are deprecated, use get_option and set_option',
                      DeprecationWarning)
        if val is not None:
            self._set_attr('qos', six.text_type(val))

    def set_import_sys_environment(self, val):
        """
        If set to true, the submission script will load the system
        environment variables.

        :param bool val: load the environment if True
        """
        from aiida.common.warnings import AiidaDeprecationWarning as DeprecationWarning  # pylint: disable=redefined-builtin
        warnings.warn('explicit option getter/setter methods are deprecated, use get_option and set_option',
                      DeprecationWarning)
        self._set_attr('import_sys_environment', bool(val))

    def get_import_sys_environment(self):
        """
        To check if it's loading the system environment
        on the submission script.

        :return: a boolean. If True the system environment will be load.
        """
        from aiida.common.warnings import AiidaDeprecationWarning as DeprecationWarning  # pylint: disable=redefined-builtin
        warnings.warn('explicit option getter/setter methods are deprecated, use get_option and set_option',
                      DeprecationWarning)
        return self.get_attr('import_sys_environment', True)

    def set_environment_variables(self, env_vars_dict):
        """
        Set a dictionary of custom environment variables for this calculation.

        Both keys and values must be strings.

        In the remote-computer submission script, it's going to export
        variables as ``export 'keys'='values'``
        """
        from aiida.common.warnings import AiidaDeprecationWarning as DeprecationWarning  # pylint: disable=redefined-builtin
        warnings.warn('explicit option getter/setter methods are deprecated, use get_option and set_option',
                      DeprecationWarning)
        if not isinstance(env_vars_dict, dict):
            raise ValueError("You have to pass a dictionary to set_environment_variables")

        for k, v in env_vars_dict.items():
            if not isinstance(k, six.string_types) or not isinstance(v, six.string_types):
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
        from aiida.common.warnings import AiidaDeprecationWarning as DeprecationWarning  # pylint: disable=redefined-builtin
        warnings.warn('explicit option getter/setter methods are deprecated, use get_option and set_option',
                      DeprecationWarning)
        return self.get_attr('custom_environment_variables', {})

    def set_priority(self, val):
        """
        Set the priority of the job to be queued.

        :param val: the values of priority as accepted by the cluster scheduler.
        """
        from aiida.common.warnings import AiidaDeprecationWarning as DeprecationWarning  # pylint: disable=redefined-builtin
        warnings.warn('explicit option getter/setter methods are deprecated, use get_option and set_option',
                      DeprecationWarning)
        self._set_attr('priority', six.text_type(val))

    def set_max_memory_kb(self, val):
        """
        Set the maximum memory (in KiloBytes) to be asked to the scheduler.

        :param val: an integer. Default=None
        """
        from aiida.common.warnings import AiidaDeprecationWarning as DeprecationWarning  # pylint: disable=redefined-builtin
        warnings.warn('explicit option getter/setter methods are deprecated, use get_option and set_option',
                      DeprecationWarning)
        self._set_attr('max_memory_kb', int(val))

    def get_max_memory_kb(self):
        """
        Get the memory (in KiloBytes) requested to the scheduler.

        :return: an integer
        """
        from aiida.common.warnings import AiidaDeprecationWarning as DeprecationWarning  # pylint: disable=redefined-builtin
        warnings.warn('explicit option getter/setter methods are deprecated, use get_option and set_option',
                      DeprecationWarning)
        return self.get_attr('max_memory_kb', None)

    def set_max_wallclock_seconds(self, val):
        """
        Set the wallclock in seconds asked to the scheduler.

        :param val: An integer. Default=None
        """
        from aiida.common.warnings import AiidaDeprecationWarning as DeprecationWarning  # pylint: disable=redefined-builtin
        warnings.warn('explicit option getter/setter methods are deprecated, use get_option and set_option',
                      DeprecationWarning)
        self._set_attr('max_wallclock_seconds', int(val))

    def get_max_wallclock_seconds(self):
        """
        Get the max wallclock time in seconds requested to the scheduler.

        :return: an integer
        :rtype: int
        """
        from aiida.common.warnings import AiidaDeprecationWarning as DeprecationWarning  # pylint: disable=redefined-builtin
        warnings.warn('explicit option getter/setter methods are deprecated, use get_option and set_option',
                      DeprecationWarning)
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
        from aiida.common.warnings import AiidaDeprecationWarning as DeprecationWarning  # pylint: disable=redefined-builtin
        warnings.warn('explicit option getter/setter methods are deprecated, use get_option and set_option',
                      DeprecationWarning)
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
        from aiida.common.warnings import AiidaDeprecationWarning as DeprecationWarning  # pylint: disable=redefined-builtin
        warnings.warn('explicit option getter/setter methods are deprecated, use get_option and set_option',
                      DeprecationWarning)
        self._set_attr('withmpi', val)

    def get_withmpi(self):
        """
        Get whether the job is set with mpi execution.

        :return: a boolean. Default=True.
        """
        from aiida.common.warnings import AiidaDeprecationWarning as DeprecationWarning  # pylint: disable=redefined-builtin
        warnings.warn('explicit option getter/setter methods are deprecated, use get_option and set_option',
                      DeprecationWarning)
        return self.get_attr('withmpi', True)

    def get_resources(self, full=False):
        """
        Returns the dictionary of the job resources set.

        :param full: if True, also add the default values, e.g.
            ``default_mpiprocs_per_machine``

        :return: a dictionary
        """
        from aiida.common.warnings import AiidaDeprecationWarning as DeprecationWarning  # pylint: disable=redefined-builtin
        warnings.warn('explicit option getter/setter methods are deprecated, use get_option and set_option',
                      DeprecationWarning)
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
        from aiida.common.warnings import AiidaDeprecationWarning as DeprecationWarning  # pylint: disable=redefined-builtin
        warnings.warn('explicit option getter/setter methods are deprecated, use get_option and set_option',
                      DeprecationWarning)
        return self.get_attr('queue_name', None)

    def get_account(self):
        """
        Get the account on the cluster.

        :return: a string or None.
        """
        from aiida.common.warnings import AiidaDeprecationWarning as DeprecationWarning  # pylint: disable=redefined-builtin
        warnings.warn('explicit option getter/setter methods are deprecated, use get_option and set_option',
                      DeprecationWarning)
        return self.get_attr('account', None)

    def get_qos(self):
        """
        Get the quality of service on the cluster.

        :return: a string or None.
        """
        from aiida.common.warnings import AiidaDeprecationWarning as DeprecationWarning  # pylint: disable=redefined-builtin
        warnings.warn('explicit option getter/setter methods are deprecated, use get_option and set_option',
                      DeprecationWarning)
        return self.get_attr('qos', None)

    def get_priority(self):
        """
        Get the priority, if set, of the job on the cluster.

        :return: a string or None
        """
        from aiida.common.warnings import AiidaDeprecationWarning as DeprecationWarning  # pylint: disable=redefined-builtin
        warnings.warn('explicit option getter/setter methods are deprecated, use get_option and set_option',
                      DeprecationWarning)
        return self.get_attr('priority', None)

    def get_prepend_text(self):
        """
        Get the calculation-specific prepend text,
        which is going to be prepended in the scheduler-job script, just before
        the code execution.
        """
        from aiida.common.warnings import AiidaDeprecationWarning as DeprecationWarning  # pylint: disable=redefined-builtin
        warnings.warn('explicit option getter/setter methods are deprecated, use get_option and set_option',
                      DeprecationWarning)
        return self.get_attr("prepend_text", "")

    def set_prepend_text(self, val):
        """
        Set the calculation-specific prepend text,
        which is going to be prepended in the scheduler-job script, just before
        the code execution.

        See also ``set_custom_scheduler_commands``

        :param val: a (possibly multiline) string
        """
        from aiida.common.warnings import AiidaDeprecationWarning as DeprecationWarning  # pylint: disable=redefined-builtin
        warnings.warn('explicit option getter/setter methods are deprecated, use get_option and set_option',
                      DeprecationWarning)
        self._set_attr("prepend_text", six.text_type(val))

    def get_append_text(self):
        """
        Get the calculation-specific append text,
        which is going to be appended in the scheduler-job script, just after
        the code execution.
        """
        from aiida.common.warnings import AiidaDeprecationWarning as DeprecationWarning  # pylint: disable=redefined-builtin
        warnings.warn('explicit option getter/setter methods are deprecated, use get_option and set_option',
                      DeprecationWarning)
        return self.get_attr("append_text", "")

    def set_append_text(self, val):
        """
        Set the calculation-specific append text,
        which is going to be appended in the scheduler-job script, just after
        the code execution.

        :param val: a (possibly multiline) string
        """
        from aiida.common.warnings import AiidaDeprecationWarning as DeprecationWarning  # pylint: disable=redefined-builtin
        warnings.warn('explicit option getter/setter methods are deprecated, use get_option and set_option',
                      DeprecationWarning)
        self._set_attr("append_text", six.text_type(val))

    def set_custom_scheduler_commands(self, val):
        """
        Set a (possibly multiline) string with the commands that the user
        wants to manually set for the scheduler.

        The difference of this method with respect to the set_prepend_text
        is the position in the scheduler submission file where such text is
        inserted: with this method, the string is inserted before any
        non-scheduler command.
        """
        from aiida.common.warnings import AiidaDeprecationWarning as DeprecationWarning  # pylint: disable=redefined-builtin
        warnings.warn('explicit option getter/setter methods are deprecated, use get_option and set_option',
                      DeprecationWarning)
        self._set_attr("custom_scheduler_commands", six.text_type(val))

    def get_custom_scheduler_commands(self):
        """
        Return a (possibly multiline) string with the commands that the user
        wants to manually set for the scheduler.
        See also the documentation of the corresponding
        ``set_`` method.

        :return: the custom scheduler command, or an empty string if no
          custom command was defined.
        """
        from aiida.common.warnings import AiidaDeprecationWarning as DeprecationWarning  # pylint: disable=redefined-builtin
        warnings.warn('explicit option getter/setter methods are deprecated, use get_option and set_option',
                      DeprecationWarning)
        return self.get_attr("custom_scheduler_commands", "")

    def get_mpirun_extra_params(self):
        """
        Return a list of strings, that are the extra params to pass to the
        mpirun (or equivalent) command after the one provided in
        computer.mpirun_command.
        Example: mpirun -np 8 extra_params[0] extra_params[1] ... exec.x

        Return an empty list if no parameters have been defined.
        """
        from aiida.common.warnings import AiidaDeprecationWarning as DeprecationWarning  # pylint: disable=redefined-builtin
        warnings.warn('explicit option getter/setter methods are deprecated, use get_option and set_option',
                      DeprecationWarning)
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
        from aiida.common.warnings import AiidaDeprecationWarning as DeprecationWarning  # pylint: disable=redefined-builtin
        warnings.warn('explicit option getter/setter methods are deprecated, use get_option and set_option',
                      DeprecationWarning)
        if extra_params is None:
            try:
                self._del_attr("mpirun_extra_params")
            except AttributeError:
                # it was not saved, yet
                pass
            return

        if not isinstance(extra_params, (list, tuple)):
            raise ValueError("You must pass a list of strings to set_mpirun_extra_params")
        for param in extra_params:
            if not isinstance(param, six.string_types):
                raise ValueError("You must pass a list of strings to set_mpirun_extra_params")

        self._set_attr("mpirun_extra_params", list(extra_params))

    def set_parser_name(self, parser):
        """
        Set a string for the output parser
        Can be None if no output plugin is available or needed.

        :param parser: a string identifying the module of the parser.
              Such module must be located within the folder 'aiida/parsers/plugins'
        """
        from aiida.common.warnings import AiidaDeprecationWarning as DeprecationWarning  # pylint: disable=redefined-builtin
        warnings.warn('explicit option getter/setter methods are deprecated, use get_option and set_option',
                      DeprecationWarning)
        self._set_attr('parser', parser)

    def get_parser_name(self):
        """
        Return a string locating the module that contains
        the output parser of this calculation, that will be searched
        in the 'aiida/parsers/plugins' directory. None if no parser is needed/set.

        :return: a string.
        """
        from aiida.common.warnings import AiidaDeprecationWarning as DeprecationWarning  # pylint: disable=redefined-builtin
        warnings.warn('explicit option getter/setter methods are deprecated, use get_option and set_option',
                      DeprecationWarning)

        return self.get_attr('parser', None)

    def _set_state(self, state):
        """
        Set the state of the calculation job.

        :param state: a string with the state from ``aiida.common.datastructures.calc_states``.
        :raise: ValueError if state is invalid
        """
        if state not in calc_states:
            raise ValueError("'{}' is not a valid calculation status".format(state))

        self._set_attr(self.JOB_STATE_KEY, state)

    def get_state(self):
        """
        Return the state of the calculation job.

        :return: the calculation job state
        """
        if not self.is_stored:
            return calc_states.NEW

        return self.get_attr(self.JOB_STATE_KEY, None)

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
            calc_states.TOSUBMIT, calc_states.SUBMITTING, calc_states.WITHSCHEDULER, calc_states.COMPUTED,
            calc_states.RETRIEVING, calc_states.PARSING
        ]

    @property
    def finished_ok(self):
        """
        Returns whether the Calculation has finished successfully, which means that it
        terminated nominally and had a zero exit status indicating a successful execution

        :return: True if the calculation has finished successfully, False otherwise
        :rtype: bool
        """
        return self.get_state() in [calc_states.FINISHED]

    @property
    def failed(self):
        """
        Returns whether the Calculation has failed, which means that it terminated nominally
        but it had a non-zero exit status

        :return: True if the calculation has failed, False otherwise
        :rtype: bool
        """
        return self.get_state() in [
            calc_states.SUBMISSIONFAILED, calc_states.RETRIEVALFAILED, calc_states.PARSINGFAILED, calc_states.FAILED
        ]

    def _set_remote_workdir(self, remote_workdir):
        if self.get_state() != calc_states.SUBMITTING:
            raise ModificationNotAllowed("Cannot set the remote workdir if you are not "
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
        if self.get_state() not in (calc_states.TOSUBMIT, calc_states.NEW):
            raise ModificationNotAllowed("Cannot set the retrieve_list for a calculation that is neither "
                                         "NEW nor TOSUBMIT (current state is {})".format(self.get_state()))

        # accept format of: [ 'remotename',
        #                     ['remotepath','localpath',0] ]
        # where the last number is used
        # to decide the localname, see CalcInfo or execmanager

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
        if self.get_state() not in (calc_states.TOSUBMIT, calc_states.NEW):
            raise ModificationNotAllowed('Cannot set the retrieve_temporary_list for a calculation that is neither '
                                         'NEW nor TOSUBMIT (current state is {})'.format(self.get_state()))

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
        if self.get_state() not in (calc_states.TOSUBMIT, calc_states.NEW):
            raise ModificationNotAllowed("Cannot set the retrieve_singlefile_list for a calculation that is neither "
                                         "NEW nor TOSUBMIT (current state is {})".format(self.get_state()))

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
        if self.get_state() != calc_states.SUBMITTING:
            raise ModificationNotAllowed("Cannot set the job id if you are not "
                                         "submitting the calculation (current state is "
                                         "{})".format(self.get_state()))

        return self._set_attr('job_id', six.text_type(job_id))

    def get_job_id(self):
        """
        Get the scheduler job id of the calculation.

        :return: a string
        """
        return self.get_attr('job_id', None)

    def _set_scheduler_state(self, state):
        # I don't do any test here on the possible valid values,
        # I just convert it to a string
        from aiida.common import timezone

        self._set_attr('scheduler_state', six.text_type(state))
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

    projection_map = {
        'pk': ('calculation', 'id'),
        'ctime': ('calculation', 'ctime'),
        'mtime': ('calculation', 'mtime'),
        'scheduler_state': ('calculation', SCHEDULER_STATE_KEY),
        'calculation_state': ('calculation', CALCULATION_STATE_KEY),
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
        'job_state': ('calculation', (CALCULATION_STATE_KEY, SCHEDULER_STATE_KEY))
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
            'calculation_state': 'Calculation state',
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
                calculation_filters['attributes.{}'.format(cls.JOB_STATE_KEY)] = {'in': states}

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
            calculation_class = get_plugin_type_from_type_string(calculation_type)
            module, class_name = calculation_class.rsplit('.', 1)

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

        try:
            if d['calculation'][CALCULATION_STATE_KEY] == calc_states.IMPORTED:
                d['calculation'][CALCULATION_STATE_KEY] = d['calculation']['attributes.state'] or "UNKNOWN"
        except KeyError:
            pass

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
        from aiida.orm.computers import Computer
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

    def _prepare_for_submission(self, tempfolder, inputdict):
        """
        This is the routine to be called when you want to create
        the input files and related stuff with a plugin.

        Args:
            tempfolder: a aiida.common.folders.Folder subclass where
                the plugin should put all its files.
            inputdict: A dictionary where
                each key is an input link name and each value an AiiDA
                node (with the Code!).
                The advantage of having this explicitly passed is that this
                allows to choose outside which nodes to use, and whether to
                use also unstored nodes, e.g. in a test_submit phase.

        TODO: document what it has to return (probably a CalcInfo object)
              and what is the behavior on the tempfolder
        """
        raise NotImplementedError

    def _get_authinfo(self):
        from aiida.common.exceptions import NotExistent

        computer = self.get_computer()
        if computer is None:
            raise NotExistent("No computer has been set for this calculation")

        return self.backend.authinfos.get(computer=computer, user=self.get_user())

    def _get_transport(self):
        """
        Return the transport for this calculation.
        """
        return self._get_authinfo().get_transport()

    def submit(self):
        """
        Creates a ContinueCalcJob and submits it with the current calculation node as the database
        record. This will ensure that even when this legacy entry point is called, that the calculation is
        taken through the Process layer. Preferably this legacy method should not be used at all but rather
        a JobProcess should be used.
        """
        import warnings
        from aiida.work.job_processes import ContinueCalcJob
        from aiida.work.launch import submit
        from aiida.common.warnings import AiidaDeprecationWarning as DeprecationWarning  # pylint: disable=redefined-builtin
        warnings.warn('directly creating and submitting calculations is deprecated, use the {}\nSee:{}'.format(
            'ProcessBuilder', DEPRECATION_DOCS_URL), DeprecationWarning)

        submit(ContinueCalcJob, _calc=self)

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

        outputs = self.get_outgoing()

        retrieved_node = None
        retrieved_linkname = self._get_linkname_retrieved()

        for entry in outputs:
            if entry.link_label == retrieved_linkname:
                if retrieved_node is None:
                    retrieved_node = entry.node
                else:
                    raise MultipleObjectsError("More than one output node "
                                               "with label '{}' for calc with pk= {}".format(
                        retrieved_linkname, self.pk))

        if retrieved_node is None:
            return None

        if not isinstance(retrieved_node, FolderData):
            raise TypeError("The retrieved node of calc with pk= {} is not of type FolderData".format(self.pk))

        return retrieved_node

    def kill(self):
        """
        Kill a calculation on the cluster.

        Can only be called if the calculation is in status WITHSCHEDULER.

        The command tries to run the kill command as provided by the scheduler,
        and raises an exception is something goes wrong.
        No changes of calculation status are done (they will be done later by
        the calculation manager).

        .. Note: Deprecated
        """
        raise NotImplementedError("deprecated method: to kill a calculation go through 'verdi calculation kill'")

    def _presubmit(self, folder):
        """
        Prepares the calculation folder with all inputs, ready to be copied to the cluster.

        :param folder: a SandboxFolder, empty in input, that will be filled with
          calculation input files and the scheduling script.

        :return calcinfo: the CalcInfo object containing the information
            needed by the daemon to handle operations.
        """
        import os

        from six.moves import StringIO as StringIO

        from aiida.common.exceptions import (NotExistent, PluginInternalError, ValidationError)
        from aiida.scheduler.datastructures import JobTemplate
        from aiida.common.utils import validate_list_of_string_tuples
        from aiida.orm import DataFactory
        from aiida.common.datastructures import CodeInfo, code_run_modes
        from aiida.orm.code import Code
        from aiida.orm.utils import load_node
        import aiida.common.json as json

        computer = self.get_computer()
        inputs = self.get_incoming(link_type=LinkType.INPUT_CALC)

        codes = [_ for _ in inputs.all_nodes() if isinstance(_, Code)]

        inputdict = {entry.link_label: entry.node for entry in inputs}

        calcinfo = self._prepare_for_submission(folder, inputdict)
        s = computer.get_scheduler()

        for code in codes:
            if code.is_local():
                if code.get_local_executable() in folder.get_content_list():
                    raise PluginInternalError("The plugin created a file {} that is also "
                                              "the executable name!".format(code.get_local_executable()))

        # I create the job template to pass to the scheduler
        job_tmpl = JobTemplate()
        job_tmpl.shebang = computer.get_shebang()
        # TODO: in the future, allow to customize the following variables
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
        retrieve_list = (calcinfo.retrieve_list if calcinfo.retrieve_list is not None else [])
        if (job_tmpl.sched_output_path is not None and job_tmpl.sched_output_path not in retrieve_list):
            retrieve_list.append(job_tmpl.sched_output_path)
        if not job_tmpl.sched_join_files:
            if (job_tmpl.sched_error_path is not None and job_tmpl.sched_error_path not in retrieve_list):
                retrieve_list.append(job_tmpl.sched_error_path)
        self._set_retrieve_list(retrieve_list)

        retrieve_singlefile_list = (calcinfo.retrieve_singlefile_list
                                    if calcinfo.retrieve_singlefile_list is not None else [])
        # a validation on the subclasses of retrieve_singlefile_list
        SinglefileData = DataFactory('singlefile')
        for _, subclassname, _ in retrieve_singlefile_list:
            FileSubclass = DataFactory(subclassname)
            if not issubclass(FileSubclass, SinglefileData):
                raise PluginInternalError("[presubmission of calc {}] "
                                          "retrieve_singlefile_list subclass problem: "
                                          "{} is not subclass of SinglefileData".format(self.pk, FileSubclass.__name__))
        self._set_retrieve_singlefile_list(retrieve_singlefile_list)

        # Handle the retrieve_temporary_list
        retrieve_temporary_list = (calcinfo.retrieve_temporary_list
                                   if calcinfo.retrieve_temporary_list is not None else [])
        self._set_retrieve_temporary_list(retrieve_temporary_list)

        # the if is done so that if the method returns None, this is
        # not added. This has two advantages:
        # - it does not add too many \n\n if most of the prepend_text are empty
        # - most importantly, skips the cases in which one of the methods
        #   would return None, in which case the join method would raise
        #   an exception
        job_tmpl.prepend_text = "\n\n".join(
            _ for _ in [computer.get_prepend_text()] + [code.get_prepend_text() for code in codes] +
            [calcinfo.prepend_text, self.get_option('prepend_text')] if _)

        job_tmpl.append_text = "\n\n".join(
            _ for _ in
            [self.get_option('append_text'), calcinfo.append_text,
             code.get_append_text(),
             computer.get_append_text()] if _)

        # Set resources, also with get_default_mpiprocs_per_machine
        resources = self.get_option('resources')
        def_cpus_machine = computer.get_default_mpiprocs_per_machine()
        if def_cpus_machine is not None:
            resources['default_mpiprocs_per_machine'] = def_cpus_machine
        job_tmpl.job_resource = s.create_job_resource(**resources)

        subst_dict = {'tot_num_mpiprocs': job_tmpl.job_resource.get_tot_num_mpiprocs()}

        for k, v in job_tmpl.job_resource.items():
            subst_dict[k] = v
        mpi_args = [arg.format(**subst_dict) for arg in computer.get_mpirun_command()]
        extra_mpirun_params = self.get_option('mpirun_extra_params')  # this is the same for all codes in the same calc

        # set the codes_info
        if not isinstance(calcinfo.codes_info, (list, tuple)):
            raise PluginInternalError("codes_info passed to CalcInfo must be a list of CalcInfo objects")

        codes_info = []
        for code_info in calcinfo.codes_info:

            if not isinstance(code_info, CodeInfo):
                raise PluginInternalError("Invalid codes_info, must be a list of CodeInfo objects")

            if code_info.code_uuid is None:
                raise PluginInternalError("CalcInfo should have "
                                          "the information of the code "
                                          "to be launched")
            this_code = load_node(code_info.code_uuid, sub_classes=(Code,))

            this_withmpi = code_info.withmpi  # to decide better how to set the default
            if this_withmpi is None:
                if len(calcinfo.codes_info) > 1:
                    raise PluginInternalError("For more than one code, it is "
                                              "necessary to set withmpi in "
                                              "codes_info")
                else:
                    this_withmpi = self.get_option('withmpi')

            if this_withmpi:
                this_argv = (mpi_args + extra_mpirun_params + [this_code.get_execname()] +
                             (code_info.cmdline_params if code_info.cmdline_params is not None else []))
            else:
                this_argv = [this_code.get_execname()] + (code_info.cmdline_params
                                                          if code_info.cmdline_params is not None else [])

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
                raise PluginInternalError("Need to set the order of the code execution (parallel or serial?)")
        else:
            job_tmpl.codes_run_mode = code_run_modes.SERIAL
        ########################################################################

        custom_sched_commands = self.get_option('custom_scheduler_commands')
        if custom_sched_commands:
            job_tmpl.custom_scheduler_commands = custom_sched_commands

        job_tmpl.import_sys_environment = self.get_option('import_sys_environment')

        job_tmpl.job_environment = self.get_option('environment_variables')

        queue_name = self.get_option('queue_name')
        account = self.get_option('account')
        qos = self.get_option('qos')
        if queue_name is not None:
            job_tmpl.queue_name = queue_name
        if account is not None:
            job_tmpl.account = account
        if qos is not None:
            job_tmpl.qos = qos
        priority = self.get_option('priority')
        if priority is not None:
            job_tmpl.priority = priority
        max_memory_kb = self.get_option('max_memory_kb')
        if max_memory_kb is not None:
            job_tmpl.max_memory_kb = max_memory_kb
        max_wallclock_seconds = self.get_option('max_wallclock_seconds')
        if max_wallclock_seconds is not None:
            job_tmpl.max_wallclock_seconds = max_wallclock_seconds
        max_memory_kb = self.get_option('max_memory_kb')
        if max_memory_kb is not None:
            job_tmpl.max_memory_kb = max_memory_kb

        # TODO: give possibility to use a different name??
        script_filename = '_aiidasubmit.sh'
        script_content = s.get_submit_script(job_tmpl)
        folder.create_file_from_filelike(StringIO(script_content), script_filename)

        subfolder = folder.get_subfolder('.aiida', create=True)
        subfolder.create_file_from_filelike(StringIO(json.dumps(job_tmpl)), 'job_tmpl.json')
        subfolder.create_file_from_filelike(StringIO(json.dumps(calcinfo)), 'calcinfo.json')

        if calcinfo.local_copy_list is None:
            calcinfo.local_copy_list = []

        if calcinfo.remote_copy_list is None:
            calcinfo.remote_copy_list = []

        # Some validation
        this_pk = self.pk if self.pk is not None else "[UNSTORED]"
        local_copy_list = calcinfo.local_copy_list
        try:
            validate_list_of_string_tuples(local_copy_list, tuple_length=2)
        except ValidationError as exc:
            raise PluginInternalError("[presubmission of calc {}] "
                                      "local_copy_list format problem: {}".format(this_pk, exc))

        remote_copy_list = calcinfo.remote_copy_list
        try:
            validate_list_of_string_tuples(remote_copy_list, tuple_length=3)
        except ValidationError as exc:
            raise PluginInternalError("[presubmission of calc {}] "
                                      "remote_copy_list format problem: {}".format(this_pk, exc))

        for (remote_computer_uuid, remote_abs_path, dest_rel_path) in remote_copy_list:
            try:
                remote_computer = self.backend.computers.get(uuid=remote_computer_uuid)
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
        Run a test submission by creating the files that would be generated for the real calculation in a local folder,
        without actually storing the calculation nor the input nodes. This functionality therefore also does not
        require any of the inputs nodes to be stored yet.

        :param folder: a Folder object, within which to create the calculation files. By default a folder
            will be created in the current working directory
        :param subfolder_name: the name of the subfolder to use within the directory of the ``folder`` object. By
            default a unique string will be generated based on the current datetime with the format ``yymmdd-``
            followed by an auto incrementing index
        """
        import os
        import errno
        from aiida.common import timezone

        from aiida.transport.plugins.local import LocalTransport
        from aiida.orm.computers import Computer
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

        # Find a new subfolder.
        # I do not user tempfile.mkdtemp, because it puts random characters
        # at the end of the directory name, therefore making difficult to
        # understand the order in which directories where stored
        counter = 0
        while True:
            counter += 1
            subfolder_path = os.path.join(folder.abspath, "{}-{:05d}".format(subfolder_basename, counter))
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

        subfolder = folder.get_subfolder(os.path.relpath(subfolder_path, folder.abspath), reset_limit=True)

        # I use the local transport where possible, to be as similar
        # as possible to a real submission
        t = LocalTransport()
        with t:
            t.chdir(subfolder.abspath)

            calcinfo, script_filename = self._presubmit(subfolder)

            code = self.get_code()

            if code.is_local():
                # Note: this will possibly overwrite files
                for f in code.get_folder_list():
                    t.put(code.get_abs_path(f), f)
                t.chmod(code.get_local_executable(), 0o755)  # rwxr-xr-x

            local_copy_list = calcinfo.local_copy_list
            remote_copy_list = calcinfo.remote_copy_list
            remote_symlink_list = calcinfo.remote_symlink_list

            for src_abs_path, dest_rel_path in local_copy_list:
                t.put(src_abs_path, dest_rel_path)

            if remote_copy_list:
                with io.open(os.path.join(subfolder.abspath, '_aiida_remote_copy_list.txt'), 'w', encoding='utf8') as f:
                    for (remote_computer_uuid, remote_abs_path, dest_rel_path) in remote_copy_list:
                        try:
                            remote_computer = self.backend.computers.get(uuid=remote_computer_uuid)
                        except NotExistent:
                            remote_computer = "[unknown]"
                        f.write(u"* I WOULD REMOTELY COPY "
                                "FILES/DIRS FROM COMPUTER {} (UUID {}) "
                                "FROM {} TO {}\n".format(remote_computer.name, remote_computer_uuid, remote_abs_path,
                                                         dest_rel_path))

            if remote_symlink_list:
                with io.open(
                        os.path.join(subfolder.abspath, '_aiida_remote_symlink_list.txt'), 'w', encoding='utf8') as f:
                    for (remote_computer_uuid, remote_abs_path, dest_rel_path) in remote_symlink_list:
                        try:
                            remote_computer = self.backend.computers.get(uuid=remote_computer_uuid)
                        except NotExistent:
                            remote_computer = "[unknown]"
                        f.write(u"* I WOULD PUT SYMBOLIC LINKS FOR "
                                "FILES/DIRS FROM COMPUTER {} (UUID {}) "
                                "FROM {} TO {}\n".format(remote_computer.name, remote_computer_uuid, remote_abs_path,
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
            outfile_content = retrieved_node.get_file_content(self._SCHED_OUTPUT_FILE)
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
            errfile_content = retrieved_node.get_file_content(self._SCHED_ERROR_FILE)
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


def _parse_single_arg(function_name, additional_parameter, args, kwargs):
    """
    Verifies that a single additional argument has been given (or no
    additional argument, if additional_parameter is None). Also
    verifies its name.
    :param function_name: the name of the caller function, used for
        the output messages
    :param additional_parameter: None if no additional parameters
        should be passed, or a string with the name of the parameter
        if one additional parameter should be passed.
    :return: None, if additional_parameter is None, or the value of
        the additional parameter
    :raise TypeError: on wrong number of inputs
    """
    # Here all the logic to check if the parameters are correct.
    if additional_parameter is not None:
        if len(args) == 1:
            if kwargs:
                raise TypeError("{}() received too many args".format(
                    function_name))
            additional_parameter_data = args[0]
        elif len(args) == 0:
            kwargs_copy = kwargs.copy()
            try:
                additional_parameter_data = kwargs_copy.pop(
                    additional_parameter)
            except KeyError:
                if kwargs_copy:
                    raise TypeError("{}() got an unexpected keyword "
                                    "argument '{}'".format(
                        function_name, kwargs_copy.keys()[0]))
                else:
                    raise TypeError("{}() requires more "
                                    "arguments".format(function_name))
            if kwargs_copy:
                raise TypeError("{}() got an unexpected keyword "
                                "argument '{}'".format(
                    function_name, kwargs_copy.keys()[0]))
        else:
            raise TypeError("{}() received too many args".format(
                function_name))
        return additional_parameter_data
    else:
        if kwargs:
            raise TypeError("{}() got an unexpected keyword "
                            "argument '{}'".format(
                function_name, kwargs.keys()[0]))
        if len(args) != 0:
            raise TypeError("{}() received too many args".format(
                function_name))

    return None


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
            raise AttributeError("Parser '{}' did not provide a result '{}'".format(self._parser.__class__.__name__,
                                                                                    name))

    def __getitem__(self, name):
        """
        interface to get to the parser results as a dictionary.

        :param name: name of the attribute to be asked to the parser results.
        """
        try:
            return self._parser.get_result(name)
        except AttributeError:
            raise KeyError("Parser '{}' did not provide a result '{}'".format(self._parser.__class__.__name__, name))
