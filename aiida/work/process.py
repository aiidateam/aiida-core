# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################

import inspect
import collections
import uuid
from enum import Enum
import itertools

from plum.port import InputPort, Port, DynamicInputPort
import plum.process
from plum.process_monitor import MONITOR
import plum.process_monitor

import voluptuous
from abc import ABCMeta
from aiida.common.extendeddicts import FixedFieldsAttributeDict
import aiida.common.exceptions as exceptions
from aiida.common.lang import override, protected
from aiida.common.links import LinkType
from aiida.utils.calculation import add_source_info
from aiida.work.defaults import class_loader
import aiida.work.util
from aiida.work.util import PROCESS_LABEL_ATTR, get_or_create_output_group
from aiida.orm.calculation import Calculation
from aiida.orm.data.parameter import ParameterData
from aiida.orm.calculation.work import WorkCalculation
from aiida import LOG_LEVEL_REPORT



class DictSchema(object):
    def __init__(self, schema):
        self._schema = voluptuous.Schema(schema)

    def __call__(self, value):
        """
        Call this to validate the value against the schema.

        :param value: a regular dictionary or a ParameterData instance
        :return: tuple (success, msg).  success is True if the value is valid
            and False otherwise, in which case msg will contain information about
            the validation failure.
        :rtype: tuple
        """
        try:
            if isinstance(value, ParameterData):
                value = value.get_dict()
            self._schema(value)
            return True, None
        except voluptuous.Invalid as e:
            return False, str(e)

    def get_template(self):
        return self._get_template(self._schema.schema)

    def _get_template(self, dict):
        template = type(
            "{}Inputs".format(self.__class__.__name__),
            (FixedFieldsAttributeDict,),
            {'_valid_fields': dict.keys()})()

        for key, value in dict.iteritems():
            if isinstance(key, (voluptuous.Optional, voluptuous.Required)):
                if key.default is not voluptuous.UNDEFINED:
                    template[key.schema] = key.default
                else:
                    template[key.schema] = None
            if isinstance(value, collections.Mapping):
                template[key] = self._get_template(value)
        return template


class PortNamespace(collections.MutableMapping, Port):
    """
    A container for Ports. Effectively it maintains a dictionary whose members are
    either a Port or yet another PortNamespace. This allows for the nesting of ports
    """

    def __init__(self, namespace=None, help=None, required=True, validator=None, valid_type=None):
        super(PortNamespace, self).__init__(
            name=namespace, help=help, required=required, validator=validator, valid_type=valid_type
        )
        self._ports = {}

    @property
    def ports(self):
        return self._ports

    def __iter__(self):
        return self._ports.__iter__()

    def __len__(self):
        return len(self._ports)

    def __delitem__(self, key):
        del self._ports[key]

    def __getitem__(self, key):
        return self._ports[key]

    def __setitem__(self, key, value):
        self._ports[key] = value

    def validate(self, inputs):
        """
        Validate the namespace port itself and subsequently all the ports it contains

        :param inputs: a arbitrarily nested dictionary of parsed inputs
        """
        if inputs is None and self.required:
            return False, "required value was not provided for '{}'".format(self.name)

        for name, port in self._ports.iteritems():
            valid, message = port.validate(inputs.get(name, None))

            if not valid:
                return False, message

        return True, None


class ProcessSpec(plum.process.ProcessSpec):

    def __init__(self):
        super(ProcessSpec, self).__init__()
        self._fastforwardable = False
        self._inputs = PortNamespace()
        self._outputs = PortNamespace()

    def is_fastforwardable(self):
        return self._fastforwardable

    def fastforwardable(self):
        self._fastforwardable = True

    def get_inputs_template(self):
        """
        Get an object that represents a template of the known inputs and their
        defaults for the :class:`Process`.

        :return: An object with attributes that represent the known inputs for
            this process. Default values will be filled in.
        """
        template = type(
            "{}Inputs".format(self.__class__.__name__),
            (FixedFieldsAttributeDict,),
            {'_valid_fields': self.inputs.keys()})()

        # Now fill in any default values
        for name, value_spec in self.inputs.iteritems():
            if isinstance(value_spec.validator, DictSchema):
                template[name] = value_spec.validator.get_template()
            elif value_spec.default is not None:
                template[name] = value_spec.default
            else:
                template[name] = None

        return template

    def expose_inputs(self, process_class, namespace=None, exclude=(), include=None):
        """
        This method allows one to automatically add the inputs from another
        Process to this ProcessSpec. The optional namespace argument can be
        used to group the exposed inputs in a separated PortNamespace

        :param process_class: the Process class whose inputs to expose
        :param namespace: a namespace in which to place the exposed inputs
        :param exclude: list or tuple of input keys to exclude from being exposed
        """
        if exclude and include is not None:
            raise ValueError('exclude and include are mutually exclusive')

        if namespace:
            self._inputs[namespace] = PortNamespace(namespace)
            port_namespace = self._inputs[namespace]
        else:
            port_namespace = self._inputs

        for name, port in process_class.spec().inputs.iteritems():

            if name.startswith('_') or name == 'dynamic':
                continue

            if include is not None:
                if name in include:
                    port_namespace[name] = port
            else:
                if name not in exclude:
                    port_namespace[name] = port

class Process(plum.process.Process):
    """
    This class represents an AiiDA process which can be executed and will
    have full provenance saved in the database.
    """
    __metaclass__ = ABCMeta

    SINGLE_RETURN_LINKNAME = '_return'

    class SaveKeys(Enum):
        """
        Keys used to identify things in the saved instance state bundle.
        """
        CALC_ID = 'calc_id'
        PARENT_CALC_PID = 'parent_calc_pid'

    @classmethod
    def define(cls, spec):
        import aiida.orm
        super(Process, cls).define(spec)

        spec.input("_store_provenance", valid_type=bool, default=True, required=False)
        spec.input("_description", valid_type=basestring, required=False)
        spec.input("_label", valid_type=basestring, required=False)

        spec.dynamic_input(valid_type=(aiida.orm.Data, aiida.orm.Calculation))
        spec.dynamic_output(valid_type=aiida.orm.Data)

    @classmethod
    def get_inputs_template(cls):
        return cls.spec().get_inputs_template()

    @classmethod
    def _create_default_exec_engine(cls):
        from aiida.work.defaults import serial_engine
        return serial_engine

    @classmethod
    def create_db_record(cls):
        """
        Create a database calculation node that represents what happened in
        this process.
        :return:
        """
        from aiida.orm.calculation.work import WorkCalculation
        calc = WorkCalculation()
        return calc

    _spec_type = ProcessSpec

    def __init__(self):
        super(Process, self).__init__()
        self._calc = None
        self._parent_pid = None

    @property
    def calc(self):
        return self._calc

    @override
    def save_instance_state(self, bundle):
        super(Process, self).save_instance_state(bundle)

        if self.inputs._store_provenance:
            assert self.calc.is_stored

        bundle[self.SaveKeys.CALC_ID.value] = self.pid
        bundle.set_class_loader(class_loader)

    def run_after_queueing(self, wait_on):
        return self._run

    def get_provenance_inputs_iterator(self):
        return itertools.ifilter(lambda kv: not kv[0].startswith('_'),
                                 self.inputs.iteritems())

    @override
    def out(self, output_port, value=None):
        if value is None:
            # In this case assume that output_port is the actual value and there
            # is just one return value
            return super(Process, self).out(self.SINGLE_RETURN_LINKNAME,
                                            output_port)
        else:
            return super(Process, self).out(output_port, value)

    def out_many(self, **nodes):
        for name, value in nodes.items():
            self.out(name, value)

    @override
    def on_create(self, pid, inputs, saved_instance_state):
        from aiida.orm import load_node
        super(Process, self).on_create(pid, inputs, saved_instance_state)

        if saved_instance_state is None:
            # Get the parent from the top of the process stack
            try:
                self._parent_pid = aiida.work.util.ProcessStack.top().pid
            except IndexError:
                pass

            self._pid = self._create_and_setup_db_record()
        else:
            if self.SaveKeys.CALC_ID.value in saved_instance_state:
                self._calc = load_node(saved_instance_state[self.SaveKeys.CALC_ID.value])
                self._pid = self.calc.pk
            else:
                self._pid = self._create_and_setup_db_record()

            if self.SaveKeys.PARENT_CALC_PID.value in saved_instance_state:
                self._parent_pid = saved_instance_state[
                    self.SaveKeys.PARENT_CALC_PID.value]

        if self._logger is None:
            self.set_logger(self.calc.logger)

    @override
    def on_start(self):
        super(Process, self).on_start()
        aiida.work.util.ProcessStack.push(self)

    @override
    def on_finish(self):
        """
        Called when a Process enters the FINISHED state at which point
        we set the corresponding attribute of the workcalculation node
        """
        super(Process, self).on_finish()
        self.calc._set_attr(WorkCalculation.FINISHED_KEY, True)
        self.calc.seal()

    @override
    def _on_output_emitted(self, output_port, value, dynamic):
        """
        The process has emitted a value on the given output port.

        :param output_port: The output port name the value was emitted on
        :param value: The value emitted
        :param dynamic: Was the output port a dynamic one (i.e. not known
        beforehand?)
        """
        from aiida.orm import Data
        super(Process, self)._on_output_emitted(output_port, value, dynamic)
        assert isinstance(value, Data), \
            "Values outputted from process must be instances of AiiDA Data" \
            "types.  Got: {}".format(value.__class__)

        if not value.is_stored:
            value.add_link_from(self.calc, output_port, LinkType.CREATE)
            if self.inputs._store_provenance:
                value.store()
        value.add_link_from(self.calc, output_port, LinkType.RETURN)

    @override
    def do_run(self):
        # Exclude all private inputs
        ins = {k: v for k, v in self.inputs.iteritems() if not k.startswith('_')}
        return self._run(**ins)

    @protected
    def get_parent_calc(self):
        from aiida.orm import load_node
        # Can't get it if we don't know our parent
        if self._parent_pid is None:
            return None

        # First try and get the process from the registry in case it is running
        try:
            return MONITOR.get_process(self._parent_pid).calc
        except ValueError:
            pass

        # Ok, maybe the pid is actually a pk...
        try:
            return load_node(pk=self._parent_pid)
        except exceptions.NotExistent:
            pass

        # Out of options
        return None

    @protected
    def report(self, msg, *args, **kwargs):
        """
        Log a message to the logger, which should get saved to the
        database through the attached DbLogHandler. The class name and function
        name of the caller are prepended to the given message
        """
        message = '[{}|{}|{}]: {}'.format(self.calc.pk, self.__class__.__name__, inspect.stack()[1][3], msg)
        self.logger.log(LOG_LEVEL_REPORT, message, *args, **kwargs)

    def exposed_inputs(self, process_class, namespace=None, agglomerate=True):
        """
        Gather a dictionary of the inputs that were exposed for a given Process
        class under an optional namespace.

        :param process_class: Process class whose inputs to try and retrieve
        :param namespace: PortNamespace in which to look for the inputs
        """
        exposed_inputs = {}
        namespaces = [namespace]

        # If inputs are to be agglomerated, we prepend the lower lying namespace
        if agglomerate:
            namespaces.insert(0, None)

        for namespace in namespaces:

            # The namespace None indicates the base level namespace
            if namespace is None:
                inputs = self.inputs
                port_namespace = self.spec().inputs
            else:
                inputs = self.inputs[namespace]
                try:
                    port_namespace = self.spec().get_input(namespace)
                except KeyError:
                    raise ValueError('this process does not contain the "{}" input namespace'.format(namespace))

            for name, port in port_namespace.ports.iteritems():
                if name in inputs and name in process_class.spec().inputs:
                    exposed_inputs[name] = inputs[name]

        return exposed_inputs

    def _create_and_setup_db_record(self):
        self._calc = self.create_db_record()
        self._setup_db_record()
        if self.inputs._store_provenance:
            self.calc.store_all()

        if self.calc.pk is not None:
            return self.calc.pk
        else:
            return uuid.UUID(self.calc.uuid)

    def _setup_db_record(self):
        assert self.inputs is not None
        assert not self.calc.is_sealed, \
            "Calculation cannot be sealed when setting up the database record"

        # Save the name of this process
        self.calc._set_attr(PROCESS_LABEL_ATTR, self.__class__.__name__)

        parent_calc = self.get_parent_calc()

        for name, input_value in self._flat_inputs().iteritems():

            if isinstance(input_value, Calculation):
                input_value = get_or_create_output_group(input_value)

            # If the input isn't stored then assume our parent created it
            if not input_value.is_stored:
                if parent_calc:
                    input_value.add_link_from(parent_calc, 'CREATE', link_type=LinkType.CREATE)
                if self.inputs._store_provenance:
                    input_value.store()

            self.calc.add_link_from(input_value, name)

        if parent_calc:
            self.calc.add_link_from(parent_calc, 'CALL', link_type=LinkType.CALL)

        self._add_description_and_label()

    def _add_description_and_label(self):
        if self.raw_inputs:
            description = self.raw_inputs.get('_description', None)
            if description is not None:
                self._calc.description = description
            label = self.raw_inputs.get('_label', None)
            if label is not None:
                self._calc.label = label

    def _can_fast_forward(self, inputs):
        return False

    def _fast_forward(self):
        node = None  # Here we should find the old node
        for k, v in node.get_output_dict():
            self.out(k, v)

    def _flat_inputs(self):
        """
        Return a flattened version of the parsed inputs dictionary. The eventual
        keys will be a concatenation of the nested keys

        :return: flat dictionary of parsed inputs
        """
        return self._flatten_inputs(self.inputs)

    def _flatten_inputs(self, dictionary, parent_key='', separator='_'):
        """
        Function that will recursively flatten the inputs dictionary, omitting
        inputs whose key starts with an underscore as they are considered to be
        non storable.

        :param dictionary: nested dictionary of parsed inputs
        :param parent_key: the parent key with which to prefix the keys
        :param separator: character to use for the concatenation of keys
        """
        items = []
        for key, value in dictionary.iteritems():

            if key.startswith('_') or value is None:
                continue

            prefixed_key = parent_key + separator + key if parent_key else key

            if isinstance(value, collections.MutableMapping):
                items.extend(self._flatten_inputs(value, prefixed_key, separator=separator).iteritems())
            else:
                items.append((prefixed_key, value))

        return dict(items)


class FunctionProcess(Process):
    _func_args = None

    @staticmethod
    def _func(*args, **kwargs):
        """
        This is used internally to store the actual function that is being
        wrapped and will be replaced by the build method.
        """
        return {}

    @staticmethod
    def build(func, **kwargs):
        """
        Build a Process from the given function.  All function arguments will
        be assigned as process inputs.  If keyword arguments are specified then
        these will also become inputs.

        :param func: The function to build a process from
        :param kwargs: Optional keyword arguments that will become additional
            inputs to the process
        :return: A Process class that represents the function
        :rtype: :class:`Process`
        """
        import inspect
        from aiida.orm.data import Data

        args, varargs, keywords, defaults = inspect.getargspec(func)

        def _define(cls, spec):
            super(FunctionProcess, cls).define(spec)

            for i in range(len(args)):
                default = None
                if defaults and len(defaults) - len(args) + i >= 0:
                    default = defaults[i]
                spec.input(args[i], valid_type=Data, default=default)
                # Make sure to get rid of the argument from the keywords dict
                kwargs.pop(args[i], None)

            for k, v in kwargs.iteritems():
                spec.input(k)

            # If the function support kwargs then allow dynamic inputs,
            # otherwise disallow
            if keywords is not None:
                spec.dynamic_input()
            else:
                spec.no_dynamic_input()

            # We don't know what a function will return so keep it dynamic
            spec.dynamic_output(valid_type=Data)

        return type(func.__name__, (FunctionProcess,),
                    {'_func': staticmethod(func),
                     Process.define.__name__: classmethod(_define),
                     '_func_args': args})

    @classmethod
    def args_to_dict(cls, *args):
        """
        Create an input dictionary (i.e. label: value) from supplied args.

        :param args: The values to use
        :return: A label: value dictionary
        """
        assert (len(args) == len(cls._func_args))
        return dict(zip(cls._func_args, args))

    @override
    def _setup_db_record(self):
        super(FunctionProcess, self)._setup_db_record()
        add_source_info(self.calc, self._func)
        # Save the name of the function
        self.calc._set_attr(PROCESS_LABEL_ATTR, self._func.__name__)

    @override
    def _run(self, **kwargs):
        from aiida.orm.data import Data

        args = []
        for arg in self._func_args:
            args.append(kwargs.pop(arg))
        outs = self._func(*args, **kwargs)
        if outs is not None:
            if isinstance(outs, Data):
                self.out(self.SINGLE_RETURN_LINKNAME, outs)
            elif isinstance(outs, collections.Mapping):
                for name, value in outs.iteritems():
                    self.out(name, value)
            else:
                raise TypeError(
                    "Workfunction returned unsupported type '{}'\n"
                    "Must be a Data type or a Mapping of string => Data".
                    format(outs.__class__))


class _ProcessFinaliser(plum.process_monitor.ProcessMonitorListener):
    """
    Take care of finalising a process when it finishes either through successful
    completion or because of a failure caused by an exception.
    """
    def __init__(self):
        MONITOR.add_monitor_listener(self)

    @override
    def on_monitored_process_destroying(self, process):
        aiida.work.util.ProcessStack.pop(process)

    @override
    def on_monitored_process_failed(self, pid):
        from aiida.orm import load_node
        try:
            calc_node = load_node(pk=pid)
        except ValueError:
            pass
        else:
            calc_node.seal()
        aiida.work.util.ProcessStack.pop(pid=pid)


# Have a global singleton to take care of finalising all processes
_finaliser = _ProcessFinaliser()
