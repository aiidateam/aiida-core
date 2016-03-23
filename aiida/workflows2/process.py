# -*- coding: utf-8 -*-

from abc import ABCMeta
import plum.process

__copyright__ = u"Copyright (c), 2015, ECOLE POLYTECHNIQUE FEDERALE DE LAUSANNE (Theory and Simulation of Materials (THEOS) and National Centre for Computational Design and Discovery of Novel Materials (NCCR MARVEL)), Switzerland and ROBERT BOSCH LLC, USA. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file"
__version__ = "0.6.0"
__contributors__ = "Andrea Cepellotti, Giovanni Pizzi, Martin Uhrin"


class Process(plum.process.Process):
    __metaclass__ = ABCMeta

    def _on_process_starting(self, inputs):
        super(Process, self)._on_process_starting(inputs)

        # Link and store the retrospective provenance for this process
        calc = self._create_db_record()
        for name, input in inputs.iteritems():
            # TODO: Need to have a discussion to see if we should automatically
            # store unstored inputs.  My feeling is yes.
            if not input._is_stored:
                input.store()
            calc._add_link_from(input, name)

        calc.store()
        self._current_calc = calc

    def _on_process_finished(self, retval):
        super(Process, self)._on_process_finished(retval)
        self._current_calc = None

    def _on_output_emitted(self, output_port, value, dynamic):
        super(Process, self)._on_output_emitted(output_port, value, dynamic)

        if not value._is_stored:
            value.store()

        # If this isn't true then the function is just returning an existing
        # node directly.  If we ever have 'return' links an else statement
        # woudl be the place to create it
        if len(value.get_inputs()) == 0:
            value._add_link_from(self._current_calc, output_port)

    @staticmethod
    def _create_db_record():
        from aiida.orm.calculation import Calculation
        calc = Calculation()
        return calc


class FunctionProcess(Process):
    @staticmethod
    def build(func, **kwargs):
        import inspect

        args, varargs, keywords, defaults = inspect.getargspec(func)

        def init(spec):
            for i in range(len(args)):
                if defaults and len(defaults) - len(args) + i >= 0:
                    spec.add_input(args[i], default=defaults[i])
                else:
                    spec.add_input(args[i])
            for k, v in kwargs.iteritems():
                spec.add_input(k)
            # We don't know what a function will return so keep it dynamic
            spec.add_dynamic_output()

        return type(func.__name__, (FunctionProcess,),
                    {'_func': staticmethod(func),
                     '_init': staticmethod(init),
                     '_func_args': args})

    def __init__(self):
        super(FunctionProcess, self).__init__()

    def _run(self, **kwargs):
        args = []
        for arg in self._func_args:
            args.append(kwargs.pop(arg))
        outs = self._func(*args)
        for name, value in outs.iteritems():
            self._out(name, value)
