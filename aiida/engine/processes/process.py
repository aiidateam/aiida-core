# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""The AiiDA process class"""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import abc
import collections
import enum
import inspect
import uuid
import traceback

import six
from six.moves import filter, range
from pika.exceptions import ConnectionClosed

import plumpy
from plumpy import ProcessState

from aiida.common import exceptions
from aiida.common.extendeddicts import AttributeDict
from aiida.common.lang import classproperty, override, protected
from aiida.common.links import LinkType
from aiida.common.log import LOG_LEVEL_REPORT
from aiida import orm
from aiida.orm import ProcessNode, CalculationNode, WorkflowNode
from aiida.orm.utils import serialize

from .. import utils
from .exit_code import ExitCode
from .builder import ProcessBuilder
from .ports import InputPort, PortNamespace
from .process_spec import ProcessSpec

__all__ = ('Process', 'ProcessState')


@plumpy.auto_persist('_parent_pid', '_enable_persistence')
@six.add_metaclass(abc.ABCMeta)
class Process(plumpy.Process):
    """
    This class represents an AiiDA process which can be executed and will
    have full provenance saved in the database.
    """
    # pylint: disable=too-many-public-methods

    _node_class = ProcessNode
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
        super(Process, cls).define(spec)
        spec.input_namespace(spec.metadata_key, required=False, non_db=True)
        spec.input_namespace('{}.{}'.format(spec.metadata_key, spec.options_key), required=False)
        spec.input('{}.store_provenance'.format(spec.metadata_key), valid_type=bool, default=True)
        spec.input('{}.description'.format(spec.metadata_key), valid_type=six.string_types[0], required=False)
        spec.input('{}.label'.format(spec.metadata_key), valid_type=six.string_types[0], required=False)
        spec.inputs.valid_type = (orm.Data,)
        spec.outputs.valid_type = (orm.Data,)

    @classmethod
    def get_builder(cls):
        return ProcessBuilder(cls)

    @classmethod
    def get_or_create_db_record(cls):
        """
        Create a database calculation node that represents what happened in
        this process.
        :return: A calculation
        """
        return cls._node_class()

    def __init__(self, inputs=None, logger=None, runner=None, parent_pid=None, enable_persistence=True):
        from aiida.manage import manager

        self._runner = runner if runner is not None else manager.get_manager().get_runner()

        super(Process, self).__init__(
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
        super(Process, self).init()
        if self._logger is None:
            self.set_logger(self.node.logger)

    @classproperty
    def exit_codes(self):
        """
        Return the namespace of exit codes defined for this WorkChain through its ProcessSpec.
        The namespace supports getitem and getattr operations with an ExitCode label to retrieve a specific code.
        Additionally, the namespace can also be called with either the exit code integer status to retrieve it.

        :returns: ExitCodesNamespace of ExitCode named tuples
        """
        return self.spec().exit_codes

    @property
    def node(self):
        """Return the ProcessNode used by this process to represent itself in the database.

        :return: instance of sub class of ProcessNode
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
        """Return the metadata passed when launching this process.

        :return: metadata dictionary
        """
        try:
            return self.inputs.metadata
        except AttributeError:
            return AttributeDict()

    @property
    def options(self):
        """Return the options of the metadata passed when launching this process.

        :return: options dictionary
        """
        try:
            return self.metadata.options
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
                self.logger.exception("Exception trying to save checkpoint, this means you will "
                                      "not be able to restart in case of a crash until the next successful checkpoint.")

    @override
    def save_instance_state(self, out_state, save_context):
        super(Process, self).save_instance_state(out_state, save_context)

        if self.metadata.store_provenance:
            assert self.node.is_stored

        out_state[self.SaveKeys.CALC_ID.value] = self.pid

    def get_provenance_inputs_iterator(self):
        return filter(lambda kv: not kv[0].startswith('_'), self.inputs.items())

    @override
    def load_instance_state(self, saved_state, load_context):
        from aiida.manage import manager

        if 'runner' in load_context:
            self._runner = load_context.runner
        else:
            self._runner = manager.get_manager().get_runner()

        load_context = load_context.copyextend(loop=self._runner.loop, communicator=self._runner.communicator)
        super(Process, self).load_instance_state(saved_state, load_context)

        if self.SaveKeys.CALC_ID.value in saved_state:
            self._node = orm.load_node(saved_state[self.SaveKeys.CALC_ID.value])
            self._pid = self.node.pk
        else:
            self._pid = self._create_and_setup_db_record()

        self.node.logger.info('Loaded process<{}> from saved state'.format(self.node.pk))

    def kill(self, msg=None):
        """
        Kill the process and all the children calculations it called
        """
        self.node.logger.debug('Request to kill Process<{}>'.format(self.node.pk))

        had_been_terminated = self.has_terminated()

        result = super(Process, self).kill(msg)

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

            if isinstance(result, plumpy.Future):
                # We ourselves are waiting to be killed so add it to the list
                killing.append(result)

            if killing:
                # We are waiting for things to be killed, so return the 'gathered' future
                result = plumpy.gather(result)

        return result

    @override
    def out(self, output_port, value=None):
        if value is None:
            # In this case assume that output_port is the actual value and there is just one return value
            value = output_port
            output_port = self.SINGLE_OUTPUT_LINKNAME

        return super(Process, self).out(output_port, value)

    def out_many(self, out_dict):
        """
        Add all values given in ``out_dict`` to the outputs. The keys of the dictionary will be used as output names.
        """
        for key, value in out_dict.items():
            self.out(key, value)

    # region Process event hooks
    def on_create(self):
        super(Process, self).on_create()
        # If parent PID hasn't been supplied try to get it from the stack
        if self._parent_pid is None and Process.current():
            current = Process.current()
            if isinstance(current, Process):
                self._parent_pid = current.pid
        self._pid = self._create_and_setup_db_record()

    @override
    def on_entering(self, state):
        super(Process, self).on_entering(state)
        # Update the node attributes every time we enter a new state

    def on_entered(self, from_state):
        self.update_node_state(self._state)
        self._save_checkpoint()
        # Update the latest process state change timestamp
        utils.set_process_state_change_timestamp(self)
        super(Process, self).on_entered(from_state)

    @override
    def on_terminated(self):
        """
        Called when a Process enters a terminal state.
        """
        super(Process, self).on_terminated()
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

        :param exc_info: the sys.exc_info() object
        """
        super(Process, self).on_except(exc_info)
        self.node.set_exception(''.join(traceback.format_exception(exc_info[0], exc_info[1], None)))
        self.report(''.join(traceback.format_exception(*exc_info)))

    @override
    def on_finish(self, result, successful):
        """
        Set the finish status on the process node
        """
        super(Process, self).on_finish(result, successful)

        if result is None or isinstance(result, int):
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
        """
        super(Process, self).on_paused(msg)
        self._save_checkpoint()
        self.node.pause()

    @override
    def on_playing(self):
        """
        The Process was unpaused so remove the paused attribute on the process node
        """
        super(Process, self).on_playing()
        self.node.unpause()

    @override
    def on_output_emitting(self, output_port, value):
        """
        The process has emitted a value on the given output port.

        :param output_port: The output port name the value was emitted on
        :param value: The value emitted
        """
        super(Process, self).on_output_emitting(output_port, value)

        if not isinstance(value, orm.Data):
            raise TypeError('Values output from process must be instances of AiiDA orm.Data types, got {}'.format(
                value.__class__))

    # end region

    def set_status(self, status):
        """
        The status of the Process is about to be changed, so we reflect this is in node's attribute proxy.

        :param status: the status message
        """
        super(Process, self).set_status(status)
        self.node.set_process_status(status)

    def submit(self, process, *args, **kwargs):
        return self.runner.submit(process, *args, **kwargs)

    @property
    def runner(self):
        return self._runner

    @protected
    def get_parent_calc(self):
        """
        Get the parent process node

        :return: the parent process node if there is one
        :rtype: :class:`aiida.orm.nodes.process.process.ProcessNode`
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
        :param args: args to pass to the log call
        :param kwargs: kwargs to pass to the log call
        """
        message = '[{}|{}|{}]: {}'.format(self.node.pk, self.__class__.__name__, inspect.stack()[1][3], msg)
        self.logger.log(LOG_LEVEL_REPORT, message, *args, **kwargs)

    def _create_and_setup_db_record(self):
        """
        Create and setup the database record for this process

        :return: the uuid of the process
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

        if self.node.pk is not None:
            return self.node.pk

        return uuid.UUID(self.node.uuid)

    @override
    def encode_input_args(self, inputs):
        """
        Encode input arguments such that they may be saved in a Bundle

        :param inputs: A mapping of the inputs as passed to the process
        :return: The encoded inputs
        """
        return serialize.serialize(inputs)

    @override
    def decode_input_args(self, encoded):
        """
        Decode saved input arguments as they came from the saved instance state Bundle

        :param encoded:
        :return: The decoded input args
        """
        return serialize.deserialize(encoded)

    def update_node_state(self, state):
        self.update_outputs()
        self.node.set_process_state(state.LABEL)

    def update_outputs(self):
        """Attach any new outputs to the node since the last time this was called, if store provenance is True."""
        if self.metadata.store_provenance is False:
            return

        outputs_stored = self.node.get_outgoing(link_type=(LinkType.CREATE, LinkType.RETURN)).all_link_labels()
        outputs_new = set(self.outputs.keys()) - set(outputs_stored)

        for link_label in outputs_new:

            output = self.outputs[link_label]

            if isinstance(self.node, CalculationNode):
                output.add_incoming(self.node, LinkType.CREATE, link_label)
            elif isinstance(self.node, WorkflowNode):
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

            if isinstance(parent_calc, CalculationNode):
                raise exceptions.InvalidOperation('calling processes from a calculation type process is forbidden.')

            if isinstance(self.node, CalculationNode):
                self.node.add_incoming(parent_calc, LinkType.CALL_CALC, 'CALL_CALC')

            elif isinstance(self.node, WorkflowNode):
                self.node.add_incoming(parent_calc, LinkType.CALL_WORK, 'CALL_WORK')

        self._setup_metadata()
        self._setup_inputs()

    def _setup_metadata(self):
        """Store the metadata on the ProcessNode."""
        for name, metadata in self.metadata.items():
            if name == 'store_provenance':
                continue
            elif name == 'label':
                self.node.label = metadata
            elif name == 'description':
                self.node.description = metadata
            elif name == 'options':
                for option_name, option_value in metadata.items():
                    self.node.set_option(option_name, option_value)
            else:
                raise RuntimeError('unsupported metadata key: {}'.format(name))

    def _setup_inputs(self):
        """Create the links between the input nodes and the ProcessNode that represents this process."""
        from aiida.orm import Code

        for name, node in self._flat_inputs().items():

            # Certain processes allow to specify ports with `None` as acceptable values
            if node is None:
                continue

            # Special exception: set computer if node is a remote Code and our node does not yet have a computer set
            if isinstance(node, Code) and not node.is_local() and not self.node.computer:
                self.node.computer = node.get_remote_computer()

            # Need this special case for tests that use ProcessNodes as classes
            if isinstance(self.node, ProcessNode) and not isinstance(self.node, (CalculationNode, WorkflowNode)):
                self.node.add_incoming(node, LinkType.INPUT_WORK, name)

            elif isinstance(self.node, CalculationNode):
                self.node.add_incoming(node, LinkType.INPUT_CALC, name)

            elif isinstance(self.node, WorkflowNode):
                self.node.add_incoming(node, LinkType.INPUT_WORK, name)

    def _flat_inputs(self):
        """
        Return a flattened version of the parsed inputs dictionary.

        The eventual keys will be a concatenation of the nested keys. Note that the `metadata` dictionary, if present,
        is not passed, as those are dealt with separately in `_setup_metadata`.

        :return: flat dictionary of parsed inputs
        """
        inputs = {key: value for key, value in self.inputs.items() if key != self.spec().metadata_key}
        return dict(self._flatten_inputs(self.spec().inputs, inputs))

    def _flatten_inputs(self, port, port_value, parent_name='', separator='_'):
        """
        Function that will recursively flatten the inputs dictionary, omitting inputs for ports that
        are marked as being non database storable

        :param port: port against which to map the port value, can be InputPort or PortNamespace
        :param port_value: value for the current port, can be a Mapping
        :param parent_name: the parent key with which to prefix the keys
        :param separator: character to use for the concatenation of keys
        """
        if ((port is None and isinstance(port_value, orm.Node)) or
            (isinstance(port, InputPort) and not getattr(port, 'non_db', False))):
            return [(parent_name, port_value)]

        if (port is None and isinstance(port_value, collections.Mapping) or isinstance(port, PortNamespace)):
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

    def exposed_inputs(self, process_class, namespace=None, agglomerate=True):
        """
        Gather a dictionary of the inputs that were exposed for a given Process class under an optional namespace.

        :param process_class: Process class whose inputs to try and retrieve

        :param namespace: PortNamespace in which to look for the inputs
        :type namespace: str

        :param agglomerate: If set to true, all parent namespaces of the given ``namespace`` will also be
            searched for inputs. Inputs in lower-lying namespaces take precedence.
        :type agglomerate: bool
        """
        exposed_inputs = {}

        namespace_list = self._get_namespace_list(namespace=namespace, agglomerate=agglomerate)
        for nspace in namespace_list:

            # The nspace None indicates the base level nspace
            if nspace is None:
                inputs = self.inputs
                port_nspace = self.spec().inputs
            else:
                inputs = self.inputs
                for part in nspace.split('.'):
                    inputs = inputs[part]
                try:
                    port_nspace = self.spec().inputs.get_port(nspace)
                except KeyError:
                    raise ValueError('this process does not contain the "{}" input nspace'.format(nspace))

            # Get the list of ports that were exposed for the given Process class in the current nspace
            exposed_inputs_list = self.spec()._exposed_inputs[nspace][process_class]  # pylint: disable=protected-access

            for name in port_nspace.ports.keys():
                if name in inputs and name in exposed_inputs_list:
                    exposed_inputs[name] = inputs[name]

        return exposed_inputs

    def exposed_outputs(self, process_instance, process_class, namespace=None, agglomerate=True):
        """
        Gather the outputs which were exposed from the ``process_class`` and emitted by the specific
        ``process_instance`` in a dictionary.

        :param namespace: Namespace in which to search for exposed outputs.
        :type namespace: str

        :param agglomerate: If set to true, all parent namespaces of the given ``namespace`` will also
            be searched for outputs. Outputs in lower-lying namespaces take precedence.
        :type agglomerate: bool
        """
        namespace_separator = self.spec().namespace_separator

        output_key_map = {}
        # maps the exposed name to all outputs that belong to it
        top_namespace_map = collections.defaultdict(list)
        process_outputs_dict = {
            entry.link_label: entry.node for entry in process_instance.get_outgoing(link_type=LinkType.RETURN)
        }

        for port_name in process_outputs_dict:
            top_namespace = port_name.split(namespace_separator)[0]
            top_namespace_map[top_namespace].append(port_name)

        for nspace in self._get_namespace_list(namespace=namespace, agglomerate=agglomerate):
            # only the top-level key is stored in _exposed_outputs
            for top_name in top_namespace_map:
                if top_name in self.spec()._exposed_outputs[nspace][process_class]:  # pylint: disable=protected-access
                    output_key_map[top_name] = nspace

        result = {}

        for top_name, nspace in output_key_map.items():
            # collect all outputs belonging to the given top_name
            for port_name in top_namespace_map[top_name]:
                if nspace is None:
                    result[port_name] = process_outputs_dict[port_name]
                else:
                    result[nspace + namespace_separator + port_name] = process_outputs_dict[port_name]
        return result

    @staticmethod
    def _get_namespace_list(namespace=None, agglomerate=True):
        """Get the list of namespaces in a given namespace"""
        if not agglomerate:
            return [namespace]

        namespace_list = [None]
        if namespace is not None:
            split_ns = namespace.split('.')
            namespace_list.extend(['.'.join(split_ns[:i]) for i in range(1, len(split_ns) + 1)])
        return namespace_list


def get_query_string_from_process_type_string(process_type_string):  # pylint: disable=invalid-name
    """
    Take the process type string of a Node and create the queryable type string.

    :param process_type_string: the process type string
    :return: string that can be used to query for subclasses of the process type using 'LIKE <string>'
    """
    if ":" in process_type_string:
        return process_type_string + "."

    path = process_type_string.rsplit('.', 2)[0]
    return path + "."
