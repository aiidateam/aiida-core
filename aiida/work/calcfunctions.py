# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Function decorator that will turn a normal function into an AiiDA calcfunction."""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import
import functools
from . import manager
from . import processes

__all__ = ('calcfunction',)


def calcfunction(func):
    """
    A decorator to turn a standard python function into a calcfunction.
    Example usage:

    >>> from aiida.orm.data.int import Int
    >>>
    >>> # Define the calcfunction
    >>> @calcfunction
    >>> def sum(a, b):
    >>>    return a + b
    >>> # Run it with some input
    >>> r = sum(Int(4), Int(5))
    >>> print(r)
    9
    >>> r.get_inputs_dict() # doctest: +SKIP
    {u'result': <CalcFunctionNode: uuid: ce0c63b3-1c84-4bb8-ba64-7b70a36adf34 (pk: 3567)>}
    >>> r.get_inputs_dict()['result'].get_inputs()
    [4, 5]

    """
    from aiida.orm.node.process import CalcFunctionNode

    # Build the Process class with its ProcessSpec representing this function
    process_class = processes.FunctionProcess.build(func, node_class=CalcFunctionNode)

    def run_get_node(*args, **kwargs):
        """
        Run the FunctionProcess with the supplied inputs in a local runner.

        The function will have to create a new runner for the FunctionProcess instead of using the global runner,
        because otherwise if this calcfunction were to call another one from within its scope, that would use
        the same runner and it would be blocking the event loop from continuing.

        :param args: input arguments to construct the FunctionProcess
        :param kwargs: input keyword arguments to construct the FunctionProcess
        :return: tuple of the outputs of the process and the calculation node
        """
        runner = manager.AiiDAManager.create_runner(with_persistence=False)
        inputs = process_class.create_inputs(*args, **kwargs)

        # Remove all the known inputs from the kwargs
        for port in process_class.spec().inputs:
            kwargs.pop(port, None)

        # If any kwargs remain, the spec should be dynamic, so we raise if it isn't
        if kwargs and not process_class.spec().inputs.dynamic:
            raise ValueError('{} does not support these keyword arguments: {}'.format(func.__name__, kwargs.keys()))

        proc = process_class(inputs=inputs, runner=runner)
        return proc.execute(), proc.calc

    @functools.wraps(func)
    def wrapped_function(*args, **kwargs):
        """This wrapper function is the actual function that is called."""
        result, _ = run_get_node(*args, **kwargs)
        return result

    @staticmethod
    @property
    def is_calcfunction():
        return True

    wrapped_function.run_get_node = run_get_node
    wrapped_function.is_calcfunction = is_calcfunction

    return wrapped_function
