# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Class and decorators to generate processes out of simple python functions."""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import collections
import functools
import inspect

from six.moves import zip  # pylint: disable=unused-import

from aiida.common.lang import override
from aiida.manage.manager import get_manager

from .process import Process

__all__ = ('calcfunction', 'workfunction', 'FunctionProcess')


def calcfunction(function):
    """
    A decorator to turn a standard python function into a calcfunction.
    Example usage:

    >>> from aiida.orm import Int
    >>>
    >>> # Define the calcfunction
    >>> @calcfunction
    >>> def sum(a, b):
    >>>    return a + b
    >>> # Run it with some input
    >>> r = sum(Int(4), Int(5))
    >>> print(r)
    9
    >>> r.get_incoming().all() # doctest: +SKIP
    [Neighbor(link_type='', link_label='result',
    node=<CalcFunctionNode: uuid: ce0c63b3-1c84-4bb8-ba64-7b70a36adf34 (pk: 3567)>)]
    >>> r.get_incoming().get_node_by_label('result').get_incoming().all_nodes()
    [4, 5]

    """
    from aiida.orm import CalcFunctionNode
    return process_function(node_class=CalcFunctionNode)(function)


def workfunction(function):
    """
    A decorator to turn a standard python function into a workfunction.
    Example usage:

    >>> from aiida.orm import Int
    >>>
    >>> # Define the workfunction
    >>> @workfunction
    >>> def select(a, b):
    >>>    return a
    >>> # Run it with some input
    >>> r = select(Int(4), Int(5))
    >>> print(r)
    4
    >>> r.get_incoming().all() # doctest: +SKIP
    [Neighbor(link_type='', link_label='result',
    node=<WorkFunctionNode: uuid: ce0c63b3-1c84-4bb8-ba64-7b70a36adf34 (pk: 3567)>)]
    >>> r.get_incoming().get_node_by_label('result').get_incoming().all_nodes()
    [4, 5]

    """
    from aiida.orm import WorkFunctionNode
    return process_function(node_class=WorkFunctionNode)(function)


def process_function(node_class):
    """
    The base function decorator to create a FunctionProcess out of a normal python function.

    :param node_class: the ORM class to be used as the Node record for the FunctionProcess
    """

    @staticmethod
    @property
    def is_process_function():
        return True

    def decorator(function):
        """
        Turn the decorated function into a FunctionProcess.

        :param function: the actual decorated function that the FunctionProcess represents
        """
        process_class = FunctionProcess.build(function, node_class=node_class)

        def run_get_node(*args, **kwargs):
            """
            Run the FunctionProcess with the supplied inputs in a local runner.

            The function will have to create a new runner for the FunctionProcess instead of using the global runner,
            because otherwise if this workfunction were to call another one from within its scope, that would use
            the same runner and it would be blocking the event loop from continuing.

            :param args: input arguments to construct the FunctionProcess
            :param kwargs: input keyword arguments to construct the FunctionProcess
            :return: tuple of the outputs of the process and the calculation node
            """
            runner = get_manager().create_runner(with_persistence=False)
            inputs = process_class.create_inputs(*args, **kwargs)

            # Remove all the known inputs from the kwargs
            for port in process_class.spec().inputs:
                kwargs.pop(port, None)

            # If any kwargs remain, the spec should be dynamic, so we raise if it isn't
            if kwargs and not process_class.spec().inputs.dynamic:
                raise ValueError('{} does not support these kwargs: {}'.format(function.__name__, kwargs.keys()))

            process = process_class(inputs=inputs, runner=runner)
            result = process.execute()

            # Close the runner properly
            runner.close()

            store_provenance = inputs.get('metadata', {}).get('store_provenance', True)
            if not store_provenance:
                process.node._storable = False  # pylint: disable=protected-access
                process.node._unstorable_message = 'cannot store node because it was run with `store_provenance=False`'  # pylint: disable=protected-access

            return result, process.node

        def run_get_pk(*args, **kwargs):
            """Recreate the `run_get_pk` utility launcher."""
            result, node = run_get_node(*args, **kwargs)
            return result, node.pk

        @functools.wraps(function)
        def decorated_function(*args, **kwargs):
            """This wrapper function is the actual function that is called."""
            result, _ = run_get_node(*args, **kwargs)
            return result

        decorated_function.run = decorated_function
        decorated_function.run_get_pk = run_get_pk
        decorated_function.run_get_node = run_get_node
        decorated_function.is_process_function = is_process_function

        return decorated_function

    return decorator


class FunctionProcess(Process):
    """Function process class used for turning functions into a Process"""

    _func_args = None

    @staticmethod
    def _func(*_args, **_kwargs):
        """
        This is used internally to store the actual function that is being
        wrapped and will be replaced by the build method.
        """
        return {}

    @staticmethod
    def build(func, node_class):
        """
        Build a Process from the given function.

        All function arguments will be assigned as process inputs. If keyword arguments are specified then
        these will also become inputs.

        :param func: The function to build a process from
        :param node_class: Provide a custom node class to be used, has to be constructable with no arguments. It has to
            be a sub class of `ProcessNode` and the mixin :class:`~aiida.orm.utils.mixins.FunctionCalculationMixin`.
        :type node_class: :class:`aiida.orm.nodes.process.process.ProcessNode`
        :return: A Process class that represents the function
        :rtype: :class:`FunctionProcess`
        """
        from aiida import orm
        from aiida.orm import ProcessNode
        from aiida.orm.utils.mixins import FunctionCalculationMixin

        if not issubclass(node_class, ProcessNode) or not issubclass(node_class, FunctionCalculationMixin):
            raise TypeError('the node_class should be a sub class of `ProcessNode` and `FunctionCalculationMixin`')

        args, varargs, keywords, defaults = inspect.getargspec(func)  # pylint: disable=deprecated-method
        nargs = len(args)
        ndefaults = len(defaults) if defaults else 0
        first_default_pos = nargs - ndefaults

        if varargs is not None:
            raise ValueError('variadic arguments are not supported')

        def _define(cls, spec):
            """Define the spec dynamically"""
            super(FunctionProcess, cls).define(spec)

            for i, arg in enumerate(args):
                default = ()
                if i >= first_default_pos:
                    default = defaults[i - first_default_pos]

                # If the keyword was already specified, simply override the default
                if spec.has_input(arg):
                    spec.inputs[arg].default = default
                else:
                    # If the default is `None` make sure that the port also accepts a `NoneType`
                    # Note that we cannot use `None` because the validation will call `isinstance` which does not work
                    # when passing `None`, but it does work with `NoneType` which is returned by calling `type(None)`
                    if default is None:
                        valid_type = (orm.Data, type(None))
                    else:
                        valid_type = (orm.Data,)

                    spec.input(arg, valid_type=valid_type, default=default)

            # If the function support kwargs then allow dynamic inputs, otherwise disallow
            spec.inputs.dynamic = keywords is not None

            # Function processes return data types
            spec.outputs.valid_type = orm.Data

        return type(
            func.__name__, (FunctionProcess,), {
                '_func': staticmethod(func),
                Process.define.__name__: classmethod(_define),
                '_func_args': args,
                '_node_class': node_class
            })

    @classmethod
    def validate_inputs(cls, *args, **kwargs):  # pylint: disable=unused-argument
        """
        Validate the positional and keyword arguments passed in the function call.

        :raises TypeError: if more positional arguments are passed than the function defines
        """
        nargs = len(args)
        nparameters = len(cls._func_args)

        # If the spec is dynamic, i.e. the function signature includes `**kwargs` and the number of positional arguments
        # passed is larger than the number of explicitly defined parameters in the signature, the inputs are invalid and
        # we should raise. If we don't, some of the passed arguments, intended to be positional arguments, will be
        # misinterpreted as keyword arguments, but they won't have an explicit name to use for the link label, causing
        # the input link to be completely lost.
        if cls.spec().inputs.dynamic and nargs > nparameters:
            name = cls._func.__name__
            raise TypeError('{}() takes {} positional arguments but {} were given'.format(name, nparameters, nargs))

    @classmethod
    def create_inputs(cls, *args, **kwargs):
        """Create the input args for the FunctionProcess"""
        cls.validate_inputs(*args, **kwargs)

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
        return dict(list(zip(cls._func_args, args)))

    @classmethod
    def get_or_create_db_record(cls):
        return cls._node_class()

    def __init__(self, *args, **kwargs):
        if kwargs.get('enable_persistence', False):
            raise RuntimeError('Cannot persist a function process')
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
        """Execute the process."""
        result = super(FunctionProcess, self).execute()

        # FunctionProcesses can return a single value as output, and not a dictionary, so we should also return that
        if len(result) == 1 and self.SINGLE_OUTPUT_LINKNAME in result:
            return result[self.SINGLE_OUTPUT_LINKNAME]

        return result

    @override
    def _setup_db_record(self):
        """Set up the database record for the process."""
        super(FunctionProcess, self)._setup_db_record()
        self.node.store_source_info(self._func)

    @override
    def run(self):
        """Run the process"""
        from aiida.orm import Data
        from .exit_code import ExitCode

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

        if isinstance(result, Data):
            self.out(self.SINGLE_OUTPUT_LINKNAME, result)
        elif isinstance(result, collections.Mapping):
            for name, value in result.items():
                self.out(name, value)
        else:
            raise TypeError("Function process returned an output with unsupported type '{}'\n"
                            "Must be a Data type or a mapping of {{string: Data}}".format(result.__class__))

        return ExitCode()
