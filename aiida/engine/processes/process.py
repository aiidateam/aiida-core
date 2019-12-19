# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""The AiiDA process class"""
import collections
import enum
import inspect
import uuid
import traceback

from pika.exceptions import ConnectionClosed

import plumpy
from plumpy import ProcessState
from kiwipy.communications import UnroutableError

from aiida import orm
from aiida.common import exceptions
from aiida.common.extendeddicts import AttributeDict
from aiida.common.lang import classproperty, override, protected
from aiida.common.links import LinkType
from aiida.common.log import LOG_LEVEL_REPORT

from .exit_code import ExitCode
from .builder import ProcessBuilder
from .ports import InputPort, OutputPort, PortNamespace, PORT_NAMESPACE_SEPARATOR
from .process_spec import ProcessSpec

__all__ = ('Process', 'ProcessState')


@plumpy.auto_persist('_parent_pid', '_enable_persistence')
class Process(plumpy.Process):
    """
    This class represents an AiiDA process which can be executed and will
    have full provenance saved in the database.
    """
    # pylint: disable=too-many-public-methods

    _node_class = orm.ProcessNode
    _spec_class = ProcessSpec

    SINGLE_OUTPUT_LINKNAME = 'result'

    class SaveKeys(enum.Enum):
        """
        Keys used to identify things in the saved instance state bundle.
        """
        # pylint: disable=too-few-public-methods
        CALC_ID = 'calc_id'

    @classmethod
    def define(cls, spec):
        # yapf: disable
        super().define(spec)
        spec.input_namespace(spec.metadata_key, required=False, non_db=True)
        spec.input('{}.store_provenance'.format(spec.metadata_key), valid_type=bool, default=True,
            help='If set to `False` provenance will not be stored in the database.')
        spec.input('{}.description'.format(spec.metadata_key), valid_type=str, required=False,
            help='Description to set on the process node.')
        spec.input('{}.label'.format(spec.metadata_key), valid_type=str, required=False,
            help='Label to set on the process node.')
        spec.input('{}.call_link_label'.format(spec.metadata_key), valid_type=str, default='CALL',
            help='The label to use for the `CALL` link if the process is called by another process.')
        spec.exit_code(1, 'ERROR_UNSPECIFIED', message='The process has failed with an unspecified error.')
        spec.exit_code(2, 'ERROR_LEGACY_FAILURE', message='The process failed with legacy failure mode.')
        spec.exit_code(10, 'ERROR_INVALID_OUTPUT', message='The process returned an invalid output.')
        spec.exit_code(11, 'ERROR_MISSING_OUTPUT', message='The process did not register a required output.')

    @classmethod
    def get_builder(cls):
        return ProcessBuilder(cls)

    @classmethod
    def get_or_create_db_record(cls):
        """
        Create a process node that represents what happened in this process.

        :return: A process node
        :rtype: :class:`aiida.orm.ProcessNode`
        """
        return cls._node_class()

    def __init__(self, inputs=None, logger=None, runner=None, parent_pid=None, enable_persistence=True):
        """ Process constructor.

        :param inputs: process inputs
        :type inputs: dict

        :param logger: aiida logger
        :type logger: :class:`logging.Logger`

        :param runner: process runner
        :type: :class:`aiida.engine.runners.Runner`

        :param parent_pid: id of parent process
        :type parent_pid: int

        :param enable_persistence: whether to persist this process
        :type enable_persistence: bool
        """
        from aiida.manage import manager

        self._runner = runner if runner is not None else manager.get_manager().get_runner()

        super().__init__(
            inputs=self.spec().inputs.serialize(inputs),
            logger=logger,
            loop=self._runner.loop,
            communicator=self.runner.communicator)

        self._node = None
        self._parent_pid = parent_pid
        self._enable_persistence = enable_persistence
        if self._enable_persistence and self.runner.persister is None:
            self.logger.warning('Disabling persistence, runner does not have a persister')
            self._enable_persistence = False

    def init(self):
        super().init()
        if self._logger is None:
            self.set_logger(self.node.logger)

    @classmethod
    def get_exit_statuses(cls, exit_code_labels):
        """Return the exit status (integers) for the given exit code labels.

        :param exit_code_labels: a list of strings that reference exit code labels of this process class
        :return: list of exit status integers that correspond to the given exit code labels
        :raises AttributeError: if at least one of the labels does not correspond to an existing exit code
        """
        exit_codes = cls.exit_codes
        return [getattr(exit_codes, label).status for label in exit_code_labels]

    @classproperty
    def exit_codes(cls):  # pylint: disable=no-self-argument
        """Return the namespace of exit codes defined for this WorkChain through its ProcessSpec.

        The namespace supports getitem and getattr operations with an ExitCode label to retrieve a specific code.
        Additionally, the namespace can also be called with either the exit code integer status to retrieve it.

        :returns: ExitCodesNamespace of ExitCode named tuples
        :rtype: :class:`aiida.engine.ExitCodesNamespace`
        """
        return cls.spec().exit_codes

    @classproperty
    def spec_metadata(cls):  # pylint: disable=no-self-argument
        """Return the metadata port namespace of the process specification of this process.

        :return: metadata dictionary
        :rtype: dict
        """
        return cls.spec().inputs['metadata']

    @property
    def node(self):
        """Return the ProcessNode used by this process to represent itself in the database.

        :return: instance of sub class of ProcessNode
        :rtype: :class:`aiida.orm.ProcessNode`
        """
        return self._node

    @property
    def uuid(self):
        """Return the UUID of the process which corresponds to the UUID of its associated `ProcessNode`.

        :return: the UUID associated to this process instance
        """
        return self.node.uuid

    @property
    def metadata(self):
        """Return the metadata that were specified when this process instance was launched.

        :return: metadata dictionary
        :rtype: dict
        """
        try:
            return self.inputs.metadata
        except AttributeError:
            return AttributeDict()

    def _save_checkpoint(self):
        """
        Save the current state in a chechpoint if persistence is enabled and the process state is not terminal

        If the persistence call excepts with a PersistenceError, it will be caught and a warning will be logged.
        """
        if self._enable_persistence and not self._state.is_terminal():
            try:
                self.runner.persister.save_checkpoint(self)
            except plumpy.PersistenceError:
                self.logger.exception('Exception trying to save checkpoint, this means you will '
                                      'not be able to restart in case of a crash until the next successful checkpoint.')

    @override
    def save_instance_state(self, out_state, save_context):
        """Save instance state.

        See documentation of :meth:`!plumpy.processes.Process.save_instance_state`.
        """
        super().save_instance_state(out_state, save_context)

        if self.metadata.store_provenance:
            assert self.node.is_stored

        out_state[self.SaveKeys.CALC_ID.value] = self.pid

    def get_provenance_inputs_iterator(self):
        """Get provenance input iterator.

        :rtype: filter
        """
        return filter(lambda kv: not kv[0].startswith('_'), self.inputs.items())

    @override
    def load_instance_state(self, saved_state, load_context):
        """Load instance state.

        :param saved_state: saved instance state

        :param load_context:
        :type load_context: :class:`!plumpy.persistence.LoadSaveContext`
        """
        from aiida.manage import manager

        if 'runner' in load_context:
            self._runner = load_context.runner
        else:
            self._runner = manager.get_manager().get_runner()

        load_context = load_context.copyextend(loop=self._runner.loop, communicator=self._runner.communicator)
        super().load_instance_state(saved_state, load_context)

        if self.SaveKeys.CALC_ID.value in saved_state:
            self._node = orm.load_node(saved_state[self.SaveKeys.CALC_ID.value])
            self._pid = self.node.pk
        else:
            self._pid = self._create_and_setup_db_record()

        self.node.logger.info('Loaded process<{}> from saved state'.format(self.node.pk))

    def kill(self, msg=None):
        """
        Kill the process and all the children calculations it called

        :param msg: message
        :type msg: str

        :rtype: bool
        """
        self.node.logger.info('Request to kill Process<{}>'.format(self.node.pk))

        had_been_terminated = self.has_terminated()

        result = super().kill(msg)

        # Only kill children if we could be killed ourselves
        if result is not False and not had_been_terminated:
            killing = []
            for child in self.node.called:
                try:
                    result = self.runner.controller.kill_process(child.pk, 'Killed by parent<{}>'.format(self.node.pk))
                    if isinstance(result, plumpy.Future):
                        killing.append(result)
                except ConnectionClosed:
                    self.logger.info('no connection available to kill child<%s>', child.pk)
                except UnroutableError:
                    self.logger.info('kill signal was unable to reach child<%s>', child.pk)

            if isinstance(result, plumpy.Future):
                # We ourselves are waiting to be killed so add it to the list
                killing.append(result)

            if killing:
                # We are waiting for things to be killed, so return the 'gathered' future
                result = plumpy.gather(killing)

        return result

    @override
    def out(self, output_port, value=None):
        """Attach output to output port.

        The name of the port will be used as the link label.

        :param output_port: name of output port
        :type output_port: str

        :param value: value to put inside output port
        """
        if value is None:
            # In this case assume that output_port is the actual value and there is just one return value
            value = output_port
            output_port = self.SINGLE_OUTPUT_LINKNAME

        return super().out(output_port, value)

    def out_many(self, out_dict):
        """Attach outputs to multiple output ports.

        Keys of the dictionary will be used as output port names, values as outputs.

        :param out_dict: output dictionary
        :type out_dict: dict
        """
        for key, value in out_dict.items():
            self.out(key, value)

    def on_create(self):
        """Called when a Process is created."""
        super().on_create()
        # If parent PID hasn't been supplied try to get it from the stack
        if self._parent_pid is None and Process.current():
            current = Process.current()
            if isinstance(current, Process):
                self._parent_pid = current.pid
        self._pid = self._create_and_setup_db_record()

    @override
    def on_entering(self, state):
        super().on_entering(state)
        # Update the node attributes every time we enter a new state

    def on_entered(self, from_state):
        # pylint: disable=cyclic-import
        from aiida.engine.utils import set_process_state_change_timestamp
        self.update_node_state(self._state)
        self._save_checkpoint()
        # Update the latest process state change timestamp
        set_process_state_change_timestamp(self)
        super().on_entered(from_state)

    @override
    def on_terminated(self):
        """Called when a Process enters a terminal state."""
        super().on_terminated()
        if self._enable_persistence:
            try:
                self.runner.persister.delete_checkpoint(self.pid)
            except BaseException:
                self.logger.exception('Failed to delete checkpoint')

        try:
            self.node.seal()
        except exceptions.ModificationNotAllowed:
            pass

    @override
    def on_except(self, exc_info):
        """
        Log the exception by calling the report method with formatted stack trace from exception info object
        and store the exception string as a node attribute

        :param exc_info: the sys.exc_info() object (type, value, traceback)
        """
        super().on_except(exc_info)
        self.node.set_exception(''.join(traceback.format_exception(exc_info[0], exc_info[1], None)))
        self.report(''.join(traceback.format_exception(*exc_info)))

    @override
    def on_finish(self, result, successful):
        """ Set the finish status on the process node.

        :param result: result of the process
        :type result: int or :class:`aiida.engine.ExitCode`

        :param successful: whether execution was successful
        :type successful: bool
        """
        super().on_finish(result, successful)

        if result is None:
            if not successful:
                result = self.exit_codes.ERROR_MISSING_OUTPUT  # pylint: disable=no-member
            else:
                result = ExitCode()

        if isinstance(result, int):
            self.node.set_exit_status(result)
        elif isinstance(result, ExitCode):
            self.node.set_exit_status(result.status)
            self.node.set_exit_message(result.message)
        else:
            raise ValueError('the result should be an integer, ExitCode or None, got {} {} {}'.format(
                type(result), result, self.pid))

    @override
    def on_paused(self, msg=None):
        """
        The Process was paused so set the paused attribute on the process node

        :param msg: message
        :type msg: str
        """
        super().on_paused(msg)
        self._save_checkpoint()
        self.node.pause()

    @override
    def on_playing(self):
        """
        The Process was unpaused so remove the paused attribute on the process node
        """
        super().on_playing()
        self.node.unpause()

    @override
    def on_output_emitting(self, output_port, value):
        """
        The process has emitted a value on the given output port.

        :param output_port: The output port name the value was emitted on
        :type output_port: str

        :param value: The value emitted
        """
        super().on_output_emitting(output_port, value)

        # Note that `PortNamespaces` should be able to receive non `Data` types such as a normal dictionary
        if isinstance(output_port, OutputPort) and not isinstance(value, orm.Data):
            raise TypeError('Processes can only return `orm.Data` instances as output, got {}'.format(value.__class__))

    def set_status(self, status):
        """
        The status of the Process is about to be changed, so we reflect this is in node's attribute proxy.

        :param status: the status message
        :type status: str
        """
        super().set_status(status)
        self.node.set_process_status(status)

    def submit(self, process, *args, **kwargs):
        """Submit process for execution.

        :param process: process
        :type process: :class:`aiida.engine.Process`

        """
        return self.runner.submit(process, *args, **kwargs)

    @property
    def runner(self):
        """Get process runner.

        :rtype: :class:`aiida.engine.runners.Runner`
        """
        return self._runner

    @protected
    def get_parent_calc(self):
        """
        Get the parent process node

        :return: the parent process node if there is one
        :rtype: :class:`aiida.orm.ProcessNode`
        """
        # Can't get it if we don't know our parent
        if self._parent_pid is None:
            return None

        return orm.load_node(pk=self._parent_pid)

    @classmethod
    def build_process_type(cls):
        """
        The process type.

        :return: string of the process type
        :rtype: str

        Note: This could be made into a property 'process_type' but in order to have it be a property of the class
        it would need to be defined in the metaclass, see https://bugs.python.org/issue20659
        """
        from aiida.plugins.entry_point import get_entry_point_string_from_class

        class_module = cls.__module__
        class_name = cls.__name__

        # If the process is a registered plugin the corresponding entry point will be used as process type
        process_type = get_entry_point_string_from_class(class_module, class_name)

        # If no entry point was found, default to fully qualified path name
        if process_type is None:
            return '{}.{}'.format(class_module, class_name)

        return process_type

    @protected
    def report(self, msg, *args, **kwargs):
        """Log a message to the logger, which should get saved to the database through the attached DbLogHandler.

        The pk, class name and function name of the caller are prepended to the given message

        :param msg: message to log
        :type msg: str

        :param args: args to pass to the log call
        :type args: list

        :param kwargs: kwargs to pass to the log call
        :type kwargs: dict
        """
        message = '[{}|{}|{}]: {}'.format(self.node.pk, self.__class__.__name__, inspect.stack()[1][3], msg)
        self.logger.log(LOG_LEVEL_REPORT, message, *args, **kwargs)

    def _create_and_setup_db_record(self):
        """
        Create and setup the database record for this process

        :return: the uuid of the process
        :rtype: :class:`!uuid.UUID`
        """
        self._node = self.get_or_create_db_record()
        self._setup_db_record()
        if self.metadata.store_provenance:
            try:
                self.node.store_all()
                if self.node.is_finished_ok:
                    self._state = ProcessState.FINISHED
                    for entry in self.node.get_outgoing(link_type=LinkType.RETURN):
                        if entry.link_label.endswith('_{pk}'.format(pk=entry.node.pk)):
                            continue
                        self.out(entry.link_label, entry.node)
                    # This is needed for CalcJob. In that case, the outputs are
                    # returned regardless of whether they end in '_pk'
                    for entry in self.node.get_outgoing(link_type=LinkType.CREATE):
                        self.out(entry.link_label, entry.node)
            except exceptions.ModificationNotAllowed:
                # The calculation was already stored
                pass
        else:
            # Cannot persist the process if were not storing provenance because that would require a stored node
            self._enable_persistence = False

        if self.node.pk is not None:
            return self.node.pk

        return uuid.UUID(self.node.uuid)

    @override
    def encode_input_args(self, inputs):
        """
        Encode input arguments such that they may be saved in a Bundle

        :param inputs: A mapping of the inputs as passed to the process
        :return: The encoded (serialized) inputs
        """
        from aiida.orm.utils import serialize
        return serialize.serialize(inputs)

    @override
    def decode_input_args(self, encoded):
        """
        Decode saved input arguments as they came from the saved instance state Bundle

        :param encoded: encoded (serialized) inputs
        :return: The decoded input args
        """
        from aiida.orm.utils import serialize
        return serialize.deserialize(encoded)

    def update_node_state(self, state):
        self.update_outputs()
        self.node.set_process_state(state.LABEL)

    def update_outputs(self):
        """Attach new outputs to the node since the last call.

        Does nothing, if self.metadata.store_provenance is False.
        """
        if self.metadata.store_provenance is False:
            return

        outputs_flat = self._flat_outputs()
        outputs_stored = self.node.get_outgoing(link_type=(LinkType.CREATE, LinkType.RETURN)).all_link_labels()
        outputs_new = set(outputs_flat.keys()) - set(outputs_stored)

        for link_label, output in outputs_flat.items():

            if link_label not in outputs_new:
                continue

            if isinstance(self.node, orm.CalculationNode):
                output.add_incoming(self.node, LinkType.CREATE, link_label)
            elif isinstance(self.node, orm.WorkflowNode):
                output.add_incoming(self.node, LinkType.RETURN, link_label)

            output.store()

    def _setup_db_record(self):
        """
        Create the database record for this process and the links with respect to its inputs

        This function will set various attributes on the node that serve as a proxy for attributes of the Process.
        This is essential as otherwise this information could only be introspected through the Process itself, which
        is only available to the interpreter that has it in memory. To make this data introspectable from any
        interpreter, for example for the command line interface, certain Process attributes are proxied through the
        calculation node.

        In addition, the parent calculation will be setup with a CALL link if applicable and all inputs will be
        linked up as well.
        """
        assert self.inputs is not None
        assert not self.node.is_sealed, 'process node cannot be sealed when setting up the database record'

        # Store important process attributes in the node proxy
        self.node.set_process_state(None)
        self.node.set_process_label(self.__class__.__name__)
        self.node.set_process_type(self.__class__.build_process_type())

        parent_calc = self.get_parent_calc()

        if parent_calc and self.metadata.store_provenance:

            if isinstance(parent_calc, orm.CalculationNode):
                raise exceptions.InvalidOperation('calling processes from a calculation type process is forbidden.')

            if isinstance(self.node, orm.CalculationNode):
                self.node.add_incoming(parent_calc, LinkType.CALL_CALC, self.metadata.call_link_label)

            elif isinstance(self.node, orm.WorkflowNode):
                self.node.add_incoming(parent_calc, LinkType.CALL_WORK, self.metadata.call_link_label)

        self._setup_metadata()
        self._setup_inputs()

    def _setup_metadata(self):
        """Store the metadata on the ProcessNode."""
        version_info = self.runner.plugin_version_provider.get_version_info(self)
        self.node.set_attribute_many(version_info)

        for name, metadata in self.metadata.items():
            if name in ['store_provenance', 'dry_run', 'call_link_label']:
                continue

            if name == 'label':
                self.node.label = metadata
            elif name == 'description':
                self.node.description = metadata
            elif name == 'computer':
                self.node.computer = metadata
            elif name == 'options':
                for option_name, option_value in metadata.items():
                    self.node.set_option(option_name, option_value)
            else:
                raise RuntimeError('unsupported metadata key: {}'.format(name))

    def _setup_inputs(self):
        """Create the links between the input nodes and the ProcessNode that represents this process."""
        for name, node in self._flat_inputs().items():

            # Certain processes allow to specify ports with `None` as acceptable values
            if node is None:
                continue

            # Special exception: set computer if node is a remote Code and our node does not yet have a computer set
            if isinstance(node, orm.Code) and not node.is_local() and not self.node.computer:
                self.node.computer = node.get_remote_computer()

            # Need this special case for tests that use ProcessNodes as classes
            if isinstance(self.node, orm.CalculationNode):
                self.node.add_incoming(node, LinkType.INPUT_CALC, name)

            elif isinstance(self.node, orm.WorkflowNode):
                self.node.add_incoming(node, LinkType.INPUT_WORK, name)

    def _flat_inputs(self):
        """
        Return a flattened version of the parsed inputs dictionary.

        The eventual keys will be a concatenation of the nested keys. Note that the `metadata` dictionary, if present,
        is not passed, as those are dealt with separately in `_setup_metadata`.

        :return: flat dictionary of parsed inputs
        :rtype: dict
        """
        inputs = {key: value for key, value in self.inputs.items() if key != self.spec().metadata_key}
        return dict(self._flatten_inputs(self.spec().inputs, inputs))

    def _flat_outputs(self):
        """
        Return a flattened version of the registered outputs dictionary.

        The eventual keys will be a concatenation of the nested keys.

        :return: flat dictionary of parsed outputs
        """
        return dict(self._flatten_outputs(self.spec().outputs, self.outputs))

    def _flatten_inputs(self, port, port_value, parent_name='', separator=PORT_NAMESPACE_SEPARATOR):
        """
        Function that will recursively flatten the inputs dictionary, omitting inputs for ports that
        are marked as being non database storable

        :param port: port against which to map the port value, can be InputPort or PortNamespace
        :type port: :class:`plumpy.ports.Port`

        :param port_value: value for the current port, can be a Mapping

        :param parent_name: the parent key with which to prefix the keys
        :type parent_name: str

        :param separator: character to use for the concatenation of keys
        :type separator: str

        :return: flat list of inputs
        :rtype: list
        """
        if (port is None and isinstance(port_value, orm.Node)) or (isinstance(port, InputPort) and not port.non_db):
            return [(parent_name, port_value)]

        if port is None and isinstance(port_value, collections.Mapping) or isinstance(port, PortNamespace):
            items = []
            for name, value in port_value.items():

                prefixed_key = parent_name + separator + name if parent_name else name

                try:
                    nested_port = port[name]
                except (KeyError, TypeError):
                    nested_port = None

                sub_items = self._flatten_inputs(
                    port=nested_port, port_value=value, parent_name=prefixed_key, separator=separator)
                items.extend(sub_items)
            return items

        assert (port is None) or (isinstance(port, InputPort) and port.non_db)
        return []

    def _flatten_outputs(self, port, port_value, parent_name='', separator=PORT_NAMESPACE_SEPARATOR):
        """
        Function that will recursively flatten the outputs dictionary.

        :param port: port against which to map the port value, can be OutputPort or PortNamespace
        :type port: :class:`plumpy.ports.Port`

        :param port_value: value for the current port, can be a Mapping
        :type parent_name: str

        :param parent_name: the parent key with which to prefix the keys
        :type parent_name: str

        :param separator: character to use for the concatenation of keys
        :type separator: str

        :return: flat list of outputs
        :rtype: list
        """
        if port is None and isinstance(port_value, orm.Node) or isinstance(port, OutputPort):
            return [(parent_name, port_value)]

        if (port is None and isinstance(port_value, collections.Mapping) or isinstance(port, PortNamespace)):
            items = []
            for name, value in port_value.items():

                prefixed_key = parent_name + separator + name if parent_name else name

                try:
                    nested_port = port[name]
                except (KeyError, TypeError):
                    nested_port = None

                sub_items = self._flatten_outputs(
                    port=nested_port, port_value=value, parent_name=prefixed_key, separator=separator)
                items.extend(sub_items)
            return items

        assert port is None, port
        return []

    def exposed_inputs(self, process_class, namespace=None, agglomerate=True):
        """
        Gather a dictionary of the inputs that were exposed for a given Process class under an optional namespace.

        :param process_class: Process class whose inputs to try and retrieve
        :type process_class: :class:`aiida.engine.Process`

        :param namespace: PortNamespace in which to look for the inputs
        :type namespace: str

        :param agglomerate: If set to true, all parent namespaces of the given ``namespace`` will also be
            searched for inputs. Inputs in lower-lying namespaces take precedence.
        :type agglomerate: bool

        :returns: exposed inputs
        :rtype: dict
        """
        exposed_inputs = {}

        namespace_list = self._get_namespace_list(namespace=namespace, agglomerate=agglomerate)
        for sub_namespace in namespace_list:

            # The sub_namespace None indicates the base level sub_namespace
            if sub_namespace is None:
                inputs = self.inputs
                port_namespace = self.spec().inputs
            else:
                inputs = self.inputs
                for part in sub_namespace.split('.'):
                    inputs = inputs[part]
                try:
                    port_namespace = self.spec().inputs.get_port(sub_namespace)
                except KeyError:
                    raise ValueError('this process does not contain the "{}" input namespace'.format(sub_namespace))

            # Get the list of ports that were exposed for the given Process class in the current sub_namespace
            exposed_inputs_list = self.spec()._exposed_inputs[sub_namespace][process_class]  # pylint: disable=protected-access

            for name in port_namespace.ports.keys():
                if name in inputs and name in exposed_inputs_list:
                    exposed_inputs[name] = inputs[name]

        return AttributeDict(exposed_inputs)

    def exposed_outputs(self, node, process_class, namespace=None, agglomerate=True):
        """Return the outputs which were exposed from the ``process_class`` and emitted by the specific ``node``

        :param node: process node whose outputs to try and retrieve
        :type node: :class:`aiida.orm.nodes.process.ProcessNode`

        :param namespace: Namespace in which to search for exposed outputs.
        :type namespace: str

        :param agglomerate: If set to true, all parent namespaces of the given ``namespace`` will also
            be searched for outputs. Outputs in lower-lying namespaces take precedence.
        :type agglomerate: bool

        :returns: exposed outputs
        :rtype: dict

        """
        namespace_separator = self.spec().namespace_separator

        output_key_map = {}
        # maps the exposed name to all outputs that belong to it
        top_namespace_map = collections.defaultdict(list)
        link_types = (LinkType.CREATE, LinkType.RETURN)
        process_outputs_dict = {
            entry.link_label: entry.node for entry in node.get_outgoing(link_type=link_types)
        }

        for port_name in process_outputs_dict:
            top_namespace = port_name.split(namespace_separator)[0]
            top_namespace_map[top_namespace].append(port_name)

        for port_namespace in self._get_namespace_list(namespace=namespace, agglomerate=agglomerate):
            # only the top-level key is stored in _exposed_outputs
            for top_name in top_namespace_map:
                if top_name in self.spec()._exposed_outputs[port_namespace][process_class]:  # pylint: disable=protected-access
                    output_key_map[top_name] = port_namespace

        result = {}

        for top_name, port_namespace in output_key_map.items():
            # collect all outputs belonging to the given top_name
            for port_name in top_namespace_map[top_name]:
                if port_namespace is None:
                    result[port_name] = process_outputs_dict[port_name]
                else:
                    result[port_namespace + namespace_separator + port_name] = process_outputs_dict[port_name]

        return AttributeDict(result)

    @staticmethod
    def _get_namespace_list(namespace=None, agglomerate=True):
        """Get the list of namespaces in a given namespace.

        :param namespace: name space
        :type namespace: str

        :param agglomerate: If set to true, all parent namespaces of the given ``namespace`` will also
            be searched.
        :type agglomerate: bool

        :returns: namespace list
        :rtype: list
        """
        if not agglomerate:
            return [namespace]

        namespace_list = [None]
        if namespace is not None:
            split_ns = namespace.split('.')
            namespace_list.extend(['.'.join(split_ns[:i]) for i in range(1, len(split_ns) + 1)])
        return namespace_list

    @classmethod
    def is_valid_cache(cls, node):
        """Check if the given node can be cached from.

        .. warning :: When overriding this method, make sure to call
            super().is_valid_cache(node) and respect its output. Otherwise,
            the 'invalidates_cache' keyword on exit codes will not work.

        This method allows extending the behavior of `ProcessNode.is_valid_cache`
        from `Process` sub-classes, for example in plug-ins.
        """
        try:
            return not cls.spec().exit_codes(node.exit_status).invalidates_cache
        except ValueError:
            return True


def get_query_string_from_process_type_string(process_type_string):  # pylint: disable=invalid-name
    """
    Take the process type string of a Node and create the queryable type string.

    :param process_type_string: the process type string
    :type process_type_string: str

    :return: string that can be used to query for subclasses of the process type using 'LIKE <string>'
    :rtype: str
    """
    if ':' in process_type_string:
        return process_type_string + '.'

    path = process_type_string.rsplit('.', 2)[0]
    return path + '.'
