# -*- coding: utf-8 -*-

import plum.process
import plum.persistence.persistence_mixin
import plum.port as port

import aiida.workflows2.util as util
from aiida.workflows2.execution_engine import execution_engine
from aiida.common.links import LinkType
from aiida.utils.calculation import add_source_info
from abc import ABCMeta

__copyright__ = u"Copyright (c), 2015, ECOLE POLYTECHNIQUE FEDERALE DE LAUSANNE (Theory and Simulation of Materials (THEOS) and National Centre for Computational Design and Discovery of Novel Materials (NCCR MARVEL)), Switzerland and ROBERT BOSCH LLC, USA. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file"
__version__ = "0.6.0"
__contributors__ = "Andrea Cepellotti, Giovanni Pizzi, Martin Uhrin"


class ProcessSpec(plum.process.ProcessSpec):
    def __init__(self):
        super(ProcessSpec, self).__init__()
        self._fastforwardable = False

    def is_fastforwardable(self):
        return self._fastforwardable

    def fastforwardable(self):
        self._fastforwardable = True


class Process(plum.process.Process):
    """
    This class represents an AiiDA process which can be executed and will
    have full provenance saved in the database.
    """
    __metaclass__ = ABCMeta

    @classmethod
    def _create_default_exec_engine(cls):
        return execution_engine

    class RunningData(object):
        def __init__(self, inputs):
            self.inputs = inputs
            self.current_calc = None
            self.parent = None

    _spec_type = ProcessSpec

    def __init__(self, create_output_links=True):
        super(Process, self).__init__()
        self._running_data = None
        self._create_output_links = create_output_links

    @property
    def current_calculation_node(self):
        return self._current_calc

    # Messages #####################################################
    def on_start(self, inputs, exec_engine):
        """
        The process is starting with the given inputs
        :param inputs: A dictionary of inputs for each input port
        """
        super(Process, self).on_start(inputs, exec_engine)
        util.ProcessStack.push(self)
        self._running_data = self.RunningData(inputs)
        self._setup_db_record(inputs)

    def on_finalise(self):
        super(Process, self).on_finalise()
        util.ProcessStack.push(self)
        self._running_data = None

    def _on_output_emitted(self, output_port, value, dynamic):
        """
        The process has emitted a value on the given output port.

        :param output_port: The output port name the value was emitted on
        :param value: The value emitted
        :param dynamic: Was the output port a dynamic one (i.e. not known
        beforehand?)
        """
        super(Process, self)._on_output_emitted(output_port, value, dynamic)

        if self._create_output_links:
            if value.is_stored:
                link_type = LinkType.RETURN
            else:
                value.store()
                link_type = LinkType.CREATE

            value.add_link_from(self._current_calc, output_port, link_type)
    #################################################################

    def _create_db_record(self):
        """
        Create a database calculation node that represents what happened in
        this process.
        :return:
        """
        from aiida.orm.calculation.process import ProcessCalculation
        calc = ProcessCalculation()
        return calc

    def _setup_db_record(self, inputs):
        # Link and store the retrospective provenance for this process
        calc = self._create_db_record()  # (unstored)
        assert (not calc.is_stored)

        # First get a dictionary of all the inputs to link, this is needed to
        # deal with things like input groups
        to_link = {}
        for name, input in inputs.iteritems():
            if isinstance(self.spec().get_input(name), port.InputGroupPort):
                to_link.update(
                    {"{}_{}".format(name, k): v for k, v in input.iteritems()})
            else:
                to_link[name] = input

        for name, input in to_link.iteritems():
            if not input.is_stored:
                input.store()
                # If the input isn't stored then assume our parent created it
                if self._parent:
                    input.add_link_from(self._parent._current_calc, "CREATE",
                                        link_type=LinkType.CREATE)

            calc.add_link_from(input, name)

        if self._parent:
            calc.add_link_from(self._parent._current_calc, "CALL", LinkType.CALL)

        self._current_calc = calc
        self._current_calc.store()

    def _can_fast_forward(self, inputs):
        return False

    def _fast_forward(self):
        node = None  # Here we should find the old node
        for k, v in node.get_output_dict():
            self._out(k, v)

    @property
    def _inputs(self):
        assert self._running_data, "Process not running"
        return self._running_data.inputs

    @property
    def _current_calc(self):
        assert self._running_data, "Process not running"
        return self._running_data.current_calc

    @_current_calc.setter
    def _current_calc(self, calc_node):
        assert self._running_data, "Process not running"
        self._running_data.current_calc = calc_node

    @property
    def _parent(self):
        assert self._running_data, "Process not running"
        return self._running_data.parent

    @_parent.setter
    def _parent(self, parent):
        assert self._running_data, "Process not running"
        self._running_data.parent = parent


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
        assert(len(args) == len(cls._func_args))
        return dict(zip(cls._func_args, args))

    def __init__(self):
        super(FunctionProcess, self).__init__()

    def __call__(self, *args, **kwargs):
        """
        Call the function process, this way the object can be used as a
        function.  It will translate the arguments into process inputs and
        run the process.

        :param args: Function arguments
        :param kwargs: Keyword arguments
        :return:
        """
        assert(len(args) == len(self._func_args))
        inputs = kwargs
        # Add all the non-keyword arguments as inputs
        # TODO: Check that we're not overwriting kwargs with args
        for name, value in zip(self._func_args, args):
            inputs[name] = value
        # Now get the superclass to deal with the keyword args and run
        return super(FunctionProcess, self).__call__(**inputs)

    def _run(self, **kwargs):
        args = []
        for arg in self._func_args:
            args.append(kwargs.pop(arg))
        outs = self._func(*args)
        for name, value in outs.iteritems():
            self._out(name, value)

    def _create_db_record(self):
        calc = super(FunctionProcess, self)._create_db_record()
        add_source_info(calc, self._func)
        return calc
