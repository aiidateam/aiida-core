# -*- coding: utf-8 -*-

import collections
import plum.process
import plum.port as port
import voluptuous
from aiida.orm import load_node
from aiida.workflows2.execution_engine import execution_engine
import aiida.workflows2.util as util
from aiida.common.lang import override
from aiida.orm.data import Data
from aiida.common.links import LinkType
from aiida.utils.calculation import add_source_info
from aiida.common.extendeddicts import FixedFieldsAttributeDict
from abc import ABCMeta

__copyright__ = u"Copyright (c), 2015, ECOLE POLYTECHNIQUE FEDERALE DE LAUSANNE (Theory and Simulation of Materials (THEOS) and National Centre for Computational Design and Discovery of Novel Materials (NCCR MARVEL)), Switzerland and ROBERT BOSCH LLC, USA. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file"
__version__ = "0.6.0"
__contributors__ = "Andrea Cepellotti, Giovanni Pizzi, Martin Uhrin"


def run(process_class, *args, **inputs):
    """
    Synchronously (i.e. blocking) run a workfunction or Process.

    :param process_class: The process class or workfunction
    :param _attributes: Optional attributes (only for Processes)
    :param args: Positional arguments for a workfunction
    :param inputs: The list of inputs
    """
    if util.is_workfunction(process_class):
        return process_class(*args, **inputs)
    elif issubclass(process_class, Process):
        return execution_engine.run(process_class, inputs)


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

    KEY_CALC_PK = 'calc_pk'

    @classmethod
    def get_inputs_template(cls):
        return cls.spec().get_inputs_template()

    @classmethod
    def _create_default_exec_engine(cls):
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
        self.parent = None
        self._store_provenance = store_provenance

    @override
    def save_instance_state(self, bundle):
        super(Process, self).save_instance_state(bundle)
        if self._store_provenance:
            assert self._calc.is_stored
            bundle[self.KEY_CALC_PK] = self._calc.pk

    # Messages #####################################################
    @override
    def on_create(self, pid, inputs=None):
        super(Process, self).on_create(pid, inputs)

        # This fills out the parent
        util.ProcessStack.push(self)
        self._pid = self._create_and_setup_db_record()

    @override
    def on_recreate(self, pid, saved_instance_state):
        super(Process, self).on_recreate(pid, saved_instance_state)

        if self.KEY_CALC_PK in saved_instance_state:
            self._calc = load_node(saved_instance_state[self.KEY_CALC_PK])
            self._pid = self._calc.pk
        else:
            self._pid = self._create_and_setup_db_record()

    def _create_and_setup_db_record(self):
        self._calc = self.create_db_record()
        self._setup_db_record()
        if self._store_provenance:
            assert self._calc.is_stored
            return self._calc.pk
        else:
            return self._calc.uuid

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
        super(Process, self)._on_output_emitted(output_port, value, dynamic)
        assert isinstance(value, Data), \
            "Values outputted from process must be instances of AiiDA Data" \
            "types.  Got: {}".format(value.__class__)

        if not value.is_stored:
            if self._store_provenance:
                value.store()
            value.add_link_from(self._calc, output_port,
                                LinkType.CREATE)
        value.add_link_from(self._calc, output_port, LinkType.RETURN)

    #################################################################

    def _setup_db_record(self):
        assert self.inputs is not None

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
                if self._store_provenance:
                    input.store()
                # If the input isn't stored then assume our parent created it
                if self._parent:
                    input.add_link_from(self._parent.calc, "CREATE",
                                        link_type=LinkType.CREATE)

            self.calc.add_link_from(input, name)

        if self._parent:
            self.calc.add_link_from(self._parent.calc, "CALL",
                                    link_type=LinkType.CALL)

        if self._store_provenance:
            self.calc.store_all()

    def _can_fast_forward(self, inputs):
        return False

    def _fast_forward(self):
        node = None  # Here we should find the old node
        for k, v in node.get_output_dict():
            self.out(k, v)

    @property
    def calc(self):
        return self._calc

    @property
    def _parent(self):
        return self.parent

    @_parent.setter
    def _parent(self, parent):
        self.parent = parent


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
        """
        import inspect

        args, varargs, keywords, defaults = inspect.getargspec(func)

        def _define(spec):
            for i in range(len(args)):
                default = None
                if defaults and len(defaults) - len(args) + i >= 0:
                    default = defaults[i]
                spec.input(args[i], default=default)
                # Make sure to get rid of the argument from the keywords dict
                kwargs.pop(args[i], None)

            for k, v in kwargs.iteritems():
                spec.input(k)
            # We don't know what a function will return so keep it dynamic
            spec.dynamic_output()

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

    @classmethod
    def create_db_record(cls):
        calc = super(FunctionProcess, cls).create_db_record()
        add_source_info(calc, cls._func)
        return calc

    def _run(self, **kwargs):
        args = []
        for arg in self._func_args:
            args.append(kwargs.pop(arg))
        outs = self._func(*args)
        for name, value in outs.iteritems():
            self.out(name, value)
