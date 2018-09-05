# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Function decorator that will turn a normal function into an AiiDA workfunction."""
from __future__ import absolute_import
import functools
from . import processes
from . import runners

__all__ = ['workfunction']


def workfunction(func, calc_node_class=None):
    """
    A decorator to turn a standard python function into a workfunction.
    Example usage:

    >>> from aiida.orm.data.int import Int
    >>>
    >>> # Define the workfunction
    >>> @workfunction
    >>> def sum(a, b):
    >>>    return a + b
    >>> # Run it with some input
    >>> r = sum(Int(4), Int(5))
    >>> print(r)
    9
    >>> r.get_inputs_dict() # doctest: +SKIP
    {u'result': <FunctionCalculation: uuid: ce0c63b3-1c84-4bb8-ba64-7b70a36adf34 (pk: 3567)>}
    >>> r.get_inputs_dict()['result'].get_inputs()
    [4, 5]

    """
    # Build the Process class with its ProcessSpec representing this function
    process_class = processes.FunctionProcess.build(func, calc_node_class=calc_node_class)

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
        runner = runners.Runner(rmq_config=None, rmq_submit=False, enable_persistence=False)
        inputs = process_class.create_inputs(*args, **kwargs)

        # Remove all the known inputs from the kwargs
        for port in process_class.spec().inputs:
            kwargs.pop(port, None)

        # If any kwargs remain, the spec should be dynamic, so we raise if it isn't
        if kwargs and not process_class.spec().inputs.dynamic:
            raise ValueError('{} does not support keyword arguments'.format(func.__name__))

        proc = process_class(inputs=inputs, runner=runner)
        return proc.execute(), proc.calc

    @functools.wraps(func)
    def wrapped_function(*args, **kwargs):
        """
        This wrapper function is the actual function that is called.
        """
        result, _ = run_get_node(*args, **kwargs)
        return result

    @staticmethod
    @property
    def is_workfunction():
        return True

    wrapped_function.run_get_node = run_get_node
    wrapped_function.is_workfunction = is_workfunction

    return wrapped_function
