# -*- coding: utf-8 -*-

import inspect

import plum.process

import aiida.workflows2.util as util
from aiida.workflows2.execution_engine import TrackingExecutionEngine
from aiida.workflows2.util import load_class
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

    _spec_type = ProcessSpec

    @staticmethod
    def from_record(record):
        if record.process_class == Process.__class__.__name__:
            process_class = Process.__class__
        else:
            process_class = load_class(record.process_class)
        proc = process_class.create()
        proc._load_from_record(record)
        return proc

    def __init__(self):
        super(Process, self).__init__()
        self._current_calc = None
        self._state_storage = None

    def execute(self, inputs, exec_engine, state_storage):
        # TODO: Put state storage in a with(..)
        self._state_storage = state_storage
        self.run(inputs, exec_engine)
        self._state_storage = None

    def run(self, inputs=None, exec_engine=None):
        with util.ProcessStack(self) as stack:
            # Create the calculation node for the process (unstored)
            calc = self._create_db_record()
            assert(not calc.is_stored)

            if len(stack) > 1:
                # TODO: Call links need to work properly with fast-forwarding
                #calc.add_link_from(stack[-1]._current_calc, "CALL", LinkType.CALL)

                # if not exec_engine:
                #     exec_engine = stack[-2]._get_exec_engine().push(self)
                pass

            if self._can_fast_forward(calc, inputs):
                self._fast_forward()
            else:
                self._current_calc = calc
                super(Process, self).run(inputs, exec_engine)

    @classmethod
    def _create_default_exec_engine(cls):
        return TrackingExecutionEngine()

    # Messages #####################################################
    def _on_process_starting(self, inputs):
        """
        The process is starting with the given inputs
        :param inputs: A dictionary of inputs for each input port
        """

        # Link and store the retrospective provenance for this process
        for name, input in inputs.iteritems():
            # TODO: Need to have a discussion to see if we should automatically
            # store unstored inputs.  My feeling is yes.
            if not input.is_stored:
                input.store()
            self._current_calc.add_link_from(input, name)
        self._current_calc.store()

        super(Process, self)._on_process_starting(inputs)

    def _on_process_finialising(self):
        self._current_calc = None

    def _on_output_emitted(self, output_port, value, dynamic):
        """
        The process has emitted a value on the given output port.

        :param output_port: The output port name the value was emitted on
        :param value: The value emitted
        :param dynamic: Was the output port a dynamic one (i.e. not known
        beforehand?)
        """
        super(Process, self)._on_output_emitted(output_port, value, dynamic)

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

    def _can_fast_forward(self, calc_node, inputs):
        return False

    def _fast_forward(self):
        node = None  # Here we should find the old node
        for k, v in node.get_output_dict():
            self._out(k, v)

    def _load_from_stored_state(self, state_storage):
        pass


class FunctionProcess(Process):
    _func_args = None

    @staticmethod
    def _func(*args, **kwargs):
        """
        This is used internally to store the actual function that is being
        wrapped and will be replaced by the build method.
        """
        pass

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
        # TODO: Check that we're nto overwriting kwargs with args
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
