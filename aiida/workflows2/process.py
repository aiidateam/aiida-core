# -*- coding: utf-8 -*-

from abc import ABCMeta
import plum.process


class Process(plum.process.Process):
    __metaclass__ = ABCMeta

    def _on_process_starting(self, inputs):
        # Link and store the retrospective provenance for this process
        calc = self._create_db_record()
        for name, input in inputs.iteritems():
            calc._add_link_from(input, name)

        calc.store()
        self._current_calc = calc

    def _on_process_finished(self, outputs):
        from aiida.common.exceptions import ModificationNotAllowed

        # Check the output values
        for name, output in outputs.iteritems():
            if output._is_stored:
                raise ModificationNotAllowed(
                    "One of the values (for key '{}') of the "
                    "dictionary returned by the wrapped function "
                    "is already stored! Note that this node (and "
                    "any other side effect of the function) are "
                    "not going to be undone!".format(name))

        # Connect the outputs to the calculation that created them
        for name, output in outputs:
            output._add_link_from(self._current_calc, name)

    @staticmethod
    def _create_db_record(self):
        from aiida.orm.calculation import Calculation
        calc = Calculation()
        return calc


class FunctionProcess(Process):
    @staticmethod
    def build(func, output_name="value"):
        import inspect

        args, varargs, keywords, defaults = inspect.getargspec(func)

        def init(spec):
            for i in range(len(args)):
                if defaults and len(defaults) - len(args) + i >= 0:
                    spec.add_input(args[i], default=defaults[i])
                else:
                    spec.add_input(args[i])

            spec.add_output(output_name)

        return type(func.__name__, (FunctionProcess,),
                    {'_func': func,
                     '_init': staticmethod(init),
                     '_func_args': args,
                     '_output_name': output_name})

    def __init__(self):
        super(FunctionProcess, self).__init__()

    def _run(self, **kwargs):
        args = []
        for arg in self._func_args:
            args.append(kwargs.pop(arg))
        return {self._output_name: self._func(*args)}
