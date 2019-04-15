# -*- coding: utf-8 -*-

import collections
import uuid

import plum.port as port
import plum.process

import aiida.workflows2.util as util
import voluptuous
from abc import ABCMeta
from aiida.common.extendeddicts import FixedFieldsAttributeDict
import aiida.common.exceptions as exceptions
from aiida.common.lang import override, protected
from aiida.common.links import LinkType
from aiida.utils.calculation import add_source_info

__copyright__ = u"Copyright (c), This file is part of the AiiDA platform. For further information please visit http://www.aiida.net/. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file."
__version__ = "0.7.1.1"
__authors__ = "The AiiDA team."


class DictSchema(object):
    def __init__(self, schema):
        self._schema = voluptuous.Schema(schema)

    def __call__(self, value):
        """
        Call this to validate the value against the chema
        :return: tuple (success, msg).  success is True if the value is valid
        and False otherwise, in which case msg will contain information about
        the validation failure.
        """
        try:
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


class ProcessSpec(plum.process.ProcessSpec):
    def __init__(self):
        super(ProcessSpec, self).__init__()
        self._fastforwardable = False

    def is_fastforwardable(self):
        return self._fastforwardable

    def fastforwardable(self):
        self._fastforwardable = True

    def get_inputs_template(self):
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


class Process(plum.process.Process):
    """
    This class represents an AiiDA process which can be executed and will
    have full provenance saved in the database.
    """
    __metaclass__ = ABCMeta

    PROCESS_LABEL_ATTR = '_process_label'

    KEY_CALC_ID = 'calc_id'
    KEY_PARENT_CALC_PID = 'parent_calc_pid'

    @classmethod
    def _define(cls, spec):
        from aiida.orm import Data

        spec.dynamic_input(valid_type=Data)
        spec.dynamic_output(valid_type=Data)

    @classmethod
    def get_inputs_template(cls):
        return cls.spec().get_inputs_template()

    @classmethod
    def _create_default_exec_engine(cls):
        from aiida.workflows2.defaults import execution_engine
        return execution_engine

    @classmethod
    def create_db_record(cls):
        """
        Create a database calculation node that represents what happened in
        this process.
        :return:
        """
        from aiida.orm.calculation.process import ProcessCalculation
        calc = ProcessCalculation()
        return calc

    _spec_type = ProcessSpec

    def __init__(self, store_provenance=True):
        super(Process, self).__init__()
        self._calc = None
        self._parent_pid = None
        self._store_provenance = store_provenance

    @override
    def save_instance_state(self, bundle):
        super(Process, self).save_instance_state(bundle)

        bundle[self._INPUTS] = self._convert_to_ids(self.inputs)
        if self._store_provenance:
            assert self._calc.is_stored

        bundle[self.KEY_CALC_ID] = self.pid

    def _convert_to_ids(self, nodes):
        from aiida.orm import Node

        input_ids = {}
        for label, node in nodes.iteritems():
            if node is None:
                continue
            elif isinstance(node, Node):
                if node.is_stored:
                    input_ids[label] = node.pk
                else:
                    # Try using the UUID, but there's probably no chance of
                    # being abel to recover the node from this if not stored
                    # (for the time being)
                    input_ids[label] = node.uuid
            elif isinstance(node, collections.Mapping):
                input_ids[label] = self._convert_to_ids(node)
        return input_ids

    def _load_nodes_from(self, pks_mapping):
        """
        Take a dictionary of of {label: pk} or nested dictionary i.e.
        {label: {label: pk}} and convert to the equivalent dictionary but
        with nodes instead of the ids.

        :param pks_mapping: The dictionary of node pks.
        :return: A dictionary with the loaded nodes.
        """
        from aiida.orm import load_node

        nodes = {}
        for label, pk in pks_mapping.iteritems():
            if isinstance(pk, collections.Mapping):
                nodes[label] = self._load_nodes_from(pk)
            else:
                nodes[label] = load_node(pk=pk)
        return nodes

    # Messages #####################################################
    @override
    def on_create(self, pid, inputs=None):
        super(Process, self).on_create(pid, inputs)

        # Get the parent from the top of the process stack
        try:
            self._parent_pid = util.ProcessStack.top().pid
        except IndexError:
            pass

        self._pid = self._create_and_setup_db_record()

    @override
    def on_recreate(self, pid, saved_instance_state):
        from aiida.orm import load_node

        # Replace the node pks for real nodes
        saved_instance_state[self._INPUTS] = \
            self._load_nodes_from(saved_instance_state[self._INPUTS])
        super(Process, self).on_recreate(pid, saved_instance_state)

        if self.KEY_CALC_ID in saved_instance_state:
            self._calc = load_node(saved_instance_state[self.KEY_CALC_ID])
            self._pid = self._calc.pk
        else:
            self._pid = self._create_and_setup_db_record()

        if self.KEY_PARENT_CALC_PID in saved_instance_state:
            self._parent_pid = saved_instance_state[self.KEY_PARENT_CALC_PID]

    @override
    def on_start(self):
        super(Process, self).on_start()
        util.ProcessStack.push(self)

    @override
    def on_restart(self):
        super(Process, self).on_restart()
        util.ProcessStack.push(self)

    @override
    def on_fail(self, exception):
        super(Process, self).on_fail(exception)
        self.calc.seal()

    @override
    def on_finish(self, retval):
        super(Process, self).on_finish(retval)
        self.calc.seal()

    @override
    def on_stop(self):
        super(Process, self).on_stop()
        util.ProcessStack.pop()

    @override
    def _on_output_emitted(self, output_port, value, dynamic):
        """
        The process has emitted a value on the given output port.

        :param output_port: The output port name the value was emitted on
        :param value: The value emitted
        :param dynamic: Was the output port a dynamic one (i.e. not known
        beforehand?)
        """
        from aiida.orm.data import Data

        super(Process, self)._on_output_emitted(output_port, value, dynamic)
        assert isinstance(value, Data), \
            "Values outputted from process must be instances of AiiDA Data" \
            "types.  Got: {}".format(value.__class__)

        if not value.is_stored:
            value.add_link_from(self._calc, output_port, LinkType.CREATE)
            if self._store_provenance:
                value.store()
        value.add_link_from(self._calc, output_port, LinkType.RETURN)

    #################################################################

    def _create_and_setup_db_record(self):
        self._calc = self.create_db_record()
        self._setup_db_record()
        if self._store_provenance:
            self._calc.store_all()

        if self._calc.pk is not None:
            return self._calc.pk
        else:
            return uuid.UUID(self._calc.uuid)

    def _setup_db_record(self):
        assert self.inputs is not None
        assert not self.calc.is_sealed,\
            "Calculation cannot be sealed when setting up the database record"

        # Save the name of this process
        self.calc._set_attr(self.PROCESS_LABEL_ATTR, self.__class__.__name__)

        parent_calc = self.get_parent_calc()

        # First get a dictionary of all the inputs to link, this is needed to
        # deal with things like input groups
        to_link = {}
        for name, input in self.inputs.iteritems():
            if self.spec().has_input(name):
                if isinstance(self.spec().get_input(name), port.InputGroupPort):
                    to_link.update(
                        {"{}_{}".format(name, k): v for k, v in
                         input.iteritems()})
                else:
                    to_link[name] = input
            else:
                # It's not in the spec, so we better support dynamic inputs
                assert self.spec().has_dynamic_input()
                to_link[name] = input

        for name, input in to_link.iteritems():
            if not input.is_stored:
                # If the input isn't stored then assume our parent created it
                if parent_calc:
                    input.add_link_from(parent_calc, "CREATE",
                                        link_type=LinkType.CREATE)
                if self._store_provenance:
                    input.store()

            self.calc.add_link_from(input, name)

        if parent_calc:
            self.calc.add_link_from(parent_calc, "CALL",
                                    link_type=LinkType.CALL)

    def _can_fast_forward(self, inputs):
        return False

    def _fast_forward(self):
        node = None  # Here we should find the old node
        for k, v in node.get_output_dict():
            self.out(k, v)

    @protected
    def get_parent_calc(self):
        # Can't get it if we don't know our parent
        if self._parent_pid is None:
            return None

        parent_calc = None
        # First try and get the process from the registry in case it is running
        if self.process_registry is not None:
            try:
                parent_process =\
                    self.process_registry.get_running_process(self._parent_pid)
                return parent_process.calc
            except ValueError:
                pass

        # Ok, maybe the pid is actually a pk...
        try:
            from aiida.orm import load_node
            return load_node(pk=self._parent_pid)
        except exceptions.NotExistent:
            pass

        # Out of options
        return None

    @property
    def calc(self):
        return self._calc


class FunctionProcess(Process):
    SINGLE_RETURN_LINKNAME = '_return'
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
        """
        import inspect
        from aiida.orm.data import Data

        args, varargs, keywords, defaults = inspect.getargspec(func)

        def _define(spec):
            for i in range(len(args)):
                default = None
                if defaults and len(defaults) - len(args) + i >= 0:
                    default = defaults[i]
                spec.input(args[i], valid_type=Data, default=default)
                # Make sure to get rid of the argument from the keywords dict
                kwargs.pop(args[i], None)

            for k, v in kwargs.iteritems():
                spec.input(k)
            # We don't know what a function will return so keep it dynamic
            spec.dynamic_output(valid_type=Data)

        return type(func.__name__, (FunctionProcess,),
                    {'_func': staticmethod(func),
                     '_define': staticmethod(_define),
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
        self.calc._set_attr(self.PROCESS_LABEL_ATTR, self._func.__name__)

    def _run(self, **kwargs):
        from aiida.orm.data import Data

        args = []
        for arg in self._func_args:
            args.append(kwargs.pop(arg))
        outs = self._func(*args)
        if isinstance(outs, Data):
            self.out(self.SINGLE_RETURN_LINKNAME, outs)
        elif isinstance(outs, collections.Mapping):
            for name, value in outs.iteritems():
                self.out(name, value)
        else:
            raise TypeError(
                "TypeError: Workfunction returned unsupported type '{}'\n"
                "Must be a Data type or a Mapping of string: Data".
                format(outs.__class__))

