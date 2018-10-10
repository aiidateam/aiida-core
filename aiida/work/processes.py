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
from six.moves import zip, filter, range
from pika.exceptions import ConnectionClosed

import plumpy
from plumpy import ProcessState

from aiida.common import exceptions
from aiida.common.lang import override, protected
from aiida.common.links import LinkType
from aiida.common.log import LOG_LEVEL_REPORT
from aiida import orm
from aiida.orm.calculation.function import FunctionCalculation
from aiida.orm.calculation.work import WorkCalculation
from aiida.utils import serialize
from aiida.work.ports import InputPort, PortNamespace
from aiida.work.process_spec import ProcessSpec, ExitCode
from aiida.work.process_builder import ProcessBuilder
from . import utils

__all__ = ['Process', 'ProcessState', 'FunctionProcess']


@plumpy.auto_persist('_parent_pid', '_enable_persistence')
@six.add_metaclass(abc.ABCMeta)
class Process(plumpy.Process):
    """
    This class represents an AiiDA process which can be executed and will
    have full provenance saved in the database.
    """
    # pylint: disable=too-many-public-methods

    _spec_type = ProcessSpec
    _calc_class = WorkCalculation

    SINGLE_RETURN_LINKNAME = 'result'

    class SaveKeys(enum.Enum):
        """
        Keys used to identify things in the saved instance state bundle.
        """
        # pylint: disable=too-few-public-methods
        CALC_ID = 'calc_id'

    @classmethod
    def define(cls, spec):
        super(Process, cls).define(spec)
        spec.input('store_provenance', valid_type=bool, default=True, non_db=True)
        spec.input('description', valid_type=six.string_types[0], required=False, non_db=True)
        spec.input('label', valid_type=six.string_types[0], required=False, non_db=True)
        spec.inputs.valid_type = (orm.Data, orm.Calculation)
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
        return cls._calc_class()

    def __init__(self, inputs=None, logger=None, runner=None, parent_pid=None, enable_persistence=True):
        from .runners import get_runner

        self._runner = runner if runner is not None else get_runner()

        super(Process, self).__init__(
            inputs=self.spec().inputs.serialize(inputs),
            logger=logger,
            loop=self._runner.loop,
            communicator=self.runner.communicator)

        self._calc = None
        self._parent_pid = parent_pid
        self._enable_persistence = enable_persistence
        if self._enable_persistence and self.runner.persister is None:
            self.logger.warning('Disabling persistence, runner does not have a persister')
            self._enable_persistence = False

    def on_create(self):
        super(Process, self).on_create()
        # If parent PID hasn't been supplied try to get it from the stack
        if self._parent_pid is None and Process.current():
            current = Process.current()
            if isinstance(current, Process):
                self._parent_pid = current.pid
        self._pid = self._create_and_setup_db_record()

    def init(self):
        super(Process, self).init()
        if self._logger is None:
            self.set_logger(self._calc.logger)

    @property
    def calc(self):
        return self._calc

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

        if self.inputs.store_provenance:
            assert self.calc.is_stored

        out_state[self.SaveKeys.CALC_ID.value] = self.pid

    def get_provenance_inputs_iterator(self):
        return filter(lambda kv: not kv[0].startswith('_'), self.inputs.items())

    @override
    def load_instance_state(self, saved_state, load_context):
        from .runners import get_runner

        if 'runner' in load_context:
            self._runner = load_context.runner
        else:
            self._runner = get_runner()

        load_context = load_context.copyextend(loop=self._runner.loop, communicator=self._runner.communicator)
        super(Process, self).load_instance_state(saved_state, load_context)

        if self.SaveKeys.CALC_ID.value in saved_state:
            self._calc = orm.load_node(saved_state[self.SaveKeys.CALC_ID.value])
            self._pid = self.calc.pk
        else:
            self._pid = self._create_and_setup_db_record()

        self.calc.logger.info('Loaded process<{}> from saved state'.format(self.calc.pk))

    def kill(self, msg=None):
        """
        Kill the process and all the children calculations it called
        """
        self._calc.logger.debug('Request to kill Process<{}>'.format(self._calc.pk))

        had_been_terminated = self.has_terminated()

        result = super(Process, self).kill(msg)

        # Only kill children if we could be killed ourselves
        if result is not False and not had_been_terminated:
            killing = []
            for child in self.calc.called:
                try:
                    result = self.runner.controller.kill_process(child.pk, 'Killed by parent<{}>'.format(self.calc.pk))
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
            # In this case assume that output_port is the actual value and there
            # is just one return value
            value = output_port
            output_port = self.SINGLE_RETURN_LINKNAME

        if isinstance(value, orm.Node) and not value.is_stored:
            value.store()

        return super(Process, self).out(output_port, value)

    def out_many(self, out_dict):
        """
        Add all values given in ``out_dict`` to the outputs. The keys of the dictionary will be used as output names.
        """
        for key, value in out_dict.items():
            self.out(key, value)

    # region Process messages
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
            self.calc.seal()
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
        self.calc._set_exception(''.join(traceback.format_exception(exc_info[0], exc_info[1], None)))  # pylint: disable=protected-access
        self.report(''.join(traceback.format_exception(*exc_info)))

    @override
    def on_finish(self, result, successful):
        """
        Set the finish status on the orm.Calculation node
        """
        super(Process, self).on_finish(result, successful)

        if result is None or isinstance(result, int):
            self.calc._set_exit_status(result)  # pylint: disable=protected-access
        elif isinstance(result, ExitCode):
            self.calc._set_exit_status(result.status)  # pylint: disable=protected-access
            self.calc._set_exit_message(result.message)  # pylint: disable=protected-access
        else:
            raise ValueError('the result should be an integer, ExitCode or None, got {} {} {}'.format(
                type(result), result, self.pid))

    @override
    def on_paused(self, msg=None):
        """
        The Process was paused so set the paused attribute on the orm.Calculation node
        """
        super(Process, self).on_paused(msg)
        self._save_checkpoint()
        self.calc.pause()

    @override
    def on_playing(self):
        """
        The Process was unpaused so remove the paused attribute on the orm.Calculation node
        """
        super(Process, self).on_playing()
        self.calc.unpause()

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
        self.calc._set_process_status(status)  # pylint: disable=protected-access

    def run_process(self, process, *args, **inputs):
        with self.runner.child_runner() as runner:
            return runner.run(process, *args, **inputs)

    def submit(self, process, *args, **kwargs):
        return self.runner.submit(process, *args, **kwargs)

    @property
    def runner(self):
        return self._runner

    @protected
    def get_parent_calc(self):
        """
        Get the parent calculation node
        :return: the parent calculation node if there is one
        :rtype: :class:`aiida.orm.Calculation`
        """
        # Can't get it if we don't know our parent
        if self._parent_pid is None:
            return None

        return orm.load_node(pk=self._parent_pid)

    @protected
    def report(self, msg, *args, **kwargs):
        """
        Log a message to the logger, which should get saved to the
        database through the attached DbLogHandler. The class name and function
        name of the caller are prepended to the given message
        """
        message = '[{}|{}|{}]: {}'.format(self.calc.pk, self.__class__.__name__, inspect.stack()[1][3], msg)
        self.logger.log(LOG_LEVEL_REPORT, message, *args, **kwargs)

    def _create_and_setup_db_record(self):
        """
        Create and setup the database record for this process

        :return: the uuid of the process
        """
        self._calc = self.get_or_create_db_record()
        self._setup_db_record()
        if self.inputs.store_provenance:
            try:
                self.calc.store_all()
                if self.calc.is_finished_ok:
                    self._state = ProcessState.FINISHED
                    for name, value in self.calc.get_outputs_dict(link_type=LinkType.RETURN).items():
                        if name.endswith('_{pk}'.format(pk=value.pk)):
                            continue
                        self.out(name, value)
                    # This is needed for JobProcess. In that case, the outputs are
                    # returned regardless of whether they end in '_pk'
                    for name, value in self.calc.get_outputs_dict(link_type=LinkType.CREATE).items():
                        self.out(name, value)
            except exceptions.ModificationNotAllowed:
                # The calculation was already stored
                pass

        if self.calc.pk is not None:
            return self.calc.pk

        return uuid.UUID(self.calc.uuid)

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
        self.calc._set_process_state(state.LABEL)  # pylint: disable=protected-access

    def update_outputs(self):
        """Attach any new outputs to the node since the last time this was called"""
        # Link up any new outputs
        new_outputs = set(self.outputs.keys()) - set(self.calc.get_outputs_dict(link_type=LinkType.RETURN).keys())
        for label in new_outputs:
            value = self.outputs[label]
            # Try making us the creator
            try:
                value.add_link_from(self.calc, label, LinkType.CREATE)
            except ValueError:
                # Must have already been created...nae dramas
                pass

            value.store()

            if utils.is_work_calc_type(self.calc):
                value.add_link_from(self.calc, label, LinkType.RETURN)

    @property
    def process_class(self):
        """
        Return the class that represents this Process.

        For a standard Process or sub class of Process, this is the class itself. However, for legacy reasons,
        the Process class is a wrapper around another class. This function returns that original class, i.e. the
        class that really represents what was being executed.
        """
        return self.__class__

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
        assert not self.calc.is_sealed, 'orm.Calculation cannot be sealed when setting up the database record'

        # Store important process attributes in the node proxy
        self.calc._set_process_state(None)  # pylint: disable=protected-access
        self.calc._set_process_label(self.process_class.__name__)  # pylint: disable=protected-access
        self.calc._set_process_type(self.process_class)  # pylint: disable=protected-access

        parent_calc = self.get_parent_calc()

        if parent_calc:
            self.calc.add_link_from(parent_calc, 'CALL', link_type=LinkType.CALL)

        self._setup_db_inputs()
        self._add_description_and_label()

    def _setup_db_inputs(self):
        """
        Create the links that connect the inputs to the calculation node that represents this Process
        """
        parent_calc = self.get_parent_calc()

        for name, input_value in self._flat_inputs().items():

            if isinstance(input_value, orm.Calculation):
                input_value = utils.get_or_create_output_group(input_value)

            if not input_value.is_stored:
                # If the input isn't stored then assume our parent created it
                if parent_calc:
                    input_value.add_link_from(parent_calc, 'CREATE', link_type=LinkType.CREATE)
                if self.inputs.store_provenance:
                    input_value.store()

            self.calc.add_link_from(input_value, name)

    def _add_description_and_label(self):
        """Add the description and label to the calculation node"""
        if self.inputs:
            description = self.inputs.get('description', None)
            if description is not None:
                self._calc.description = description
            label = self.inputs.get('label', None)
            if label is not None:
                self._calc.label = label

    def _flat_inputs(self):
        """
        Return a flattened version of the parsed inputs dictionary. The eventual
        keys will be a concatenation of the nested keys

        :return: flat dictionary of parsed inputs
        """
        return dict(self._flatten_inputs(self.spec().inputs, self.inputs))

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
            k: v for k, v in process_instance.get_outputs(also_labels=True, link_type=LinkType.RETURN)
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
        else:
            namespace_list = [None]
            if namespace is not None:
                split_ns = namespace.split('.')
                namespace_list.extend(['.'.join(split_ns[:i]) for i in range(1, len(split_ns) + 1)])
            return namespace_list


class FunctionProcess(Process):
    """Function process class used for turning functions into a Process"""
    _func_args = None
    _calc_node_class = FunctionCalculation

    @staticmethod
    def _func(*_args, **_kwargs):
        """
        This is used internally to store the actual function that is being
        wrapped and will be replaced by the build method.
        """
        return {}

    @staticmethod
    def build(func, calc_node_class=None):
        """
        Build a Process from the given function.  All function arguments will
        be assigned as process inputs. If keyword arguments are specified then
        these will also become inputs.

        :param func: The function to build a process from
        :param calc_node_class: Provide a custom calculation class to be used,
            has to be constructable with no arguments
        :type calc_node_class: :class:`aiida.orm.calculation.Calculation`
        :return: A Process class that represents the function
        :rtype: :class:`FunctionProcess`
        """
        args, varargs, keywords, defaults = inspect.getargspec(func)  # pylint: disable=deprecated-method
        nargs = len(args)
        ndefaults = len(defaults) if defaults else 0
        first_default_pos = nargs - ndefaults

        if calc_node_class is None:
            calc_node_class = FunctionCalculation

        if varargs is not None:
            raise ValueError('variadic arguments are not supported')

        def _define(cls, spec):
            """Define the spec dynamically"""
            super(FunctionProcess, cls).define(spec)

            for i, arg in enumerate(args):
                default = ()
                if i >= first_default_pos:
                    default = defaults[i - first_default_pos]

                if spec.has_input(arg):
                    spec.inputs[arg].default = default
                else:
                    spec.input(arg, valid_type=orm.Data, default=default)

            # If the function support kwargs then allow dynamic inputs, otherwise disallow
            spec.inputs.dynamic = keywords is not None

            # Workfunctions return data types
            spec.outputs.valid_type = orm.Data

        return type(
            func.__name__, (FunctionProcess,), {
                '_func': staticmethod(func),
                Process.define.__name__: classmethod(_define),
                '_func_args': args,
                '_calc_node_class': calc_node_class
            })

    @classmethod
    def create_inputs(cls, *args, **kwargs):
        """Create the input args for the JobProcess"""
        ins = {}
        if kwargs:
            ins.update(kwargs)
        if args:
            ins.update(cls.args_to_dict(*args))
        return ins

    @classmethod
    def args_to_dict(cls, *args):
        """
        Create an input dictionary (i.e. label: value) from supplied args.

        :param args: The values to use
        :return: A label: value dictionary
        """
        return dict(zip(cls._func_args, args))

    @classmethod
    def get_or_create_db_record(cls):
        return cls._calc_node_class()

    def __init__(self, *args, **kwargs):
        if kwargs.get('enable_persistence', False):
            raise RuntimeError('Cannot persist a workfunction')
        super(FunctionProcess, self).__init__(enable_persistence=False, *args, **kwargs)

    @property
    def process_class(self):
        """
        Return the class that represents this Process, for the FunctionProcess this is the function itself.

        For a standard Process or sub class of Process, this is the class itself. However, for legacy reasons,
        the Process class is a wrapper around another class. This function returns that original class, i.e. the
        class that really represents what was being executed.
        """
        return self._func

    def execute(self):
        """Execute the process"""
        result = super(FunctionProcess, self).execute()
        # Create a special case for Process functions: They can return
        # a single value in which case you get this a not a dict
        if len(result) == 1 and self.SINGLE_RETURN_LINKNAME in result:
            return result[self.SINGLE_RETURN_LINKNAME]

        return result

    @override
    def _setup_db_record(self):
        """Set up the database record for the process"""
        super(FunctionProcess, self)._setup_db_record()
        self.calc.store_source_info(self._func)

    @override
    def run(self):
        """Run the process"""
        args = []

        # Split the inputs into positional and keyword arguments
        args = [None] * len(self._func_args)
        kwargs = {}
        for name, value in self.inputs.items():
            try:
                if self.spec().inputs[name].non_db:
                    # Don't consider non-database inputs
                    continue
            except KeyError:
                pass  # No port found

            # Check if it is a positional arg, if not then keyword
            try:
                args[self._func_args.index(name)] = value
            except ValueError:
                kwargs[name] = value

        result = self._func(*args, **kwargs)

        if result is None or isinstance(result, ExitCode):
            return result

        if isinstance(result, orm.Data):
            self.out(self.SINGLE_RETURN_LINKNAME, result)
        elif isinstance(result, collections.Mapping):
            for name, value in result.items():
                self.out(name, value)
        else:
            raise TypeError("Workfunction returned unsupported type '{}'\n"
                            "Must be a orm.Data type or a Mapping of {{string: orm.Data}}".format(result.__class__))

        return ExitCode()
