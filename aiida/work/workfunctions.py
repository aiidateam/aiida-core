# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""
This file provides very simple workflows for testing purposes.
Do not delete, otherwise 'verdi developertest' will stop to work.
"""

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
    {u'_return': <WorkCalculation: uuid: ce0c63b3-1c84-4bb8-ba64-7b70a36adf34 (pk: 3567)>}
    >>> r.get_inputs_dict()['_return'].get_inputs()
    [4, 5]

    """

    @functools.wraps(func)
    def wrapped_function(*args, **kwargs):
        """
        This wrapper function is the actual function that is called.
        """
        # Build up the Process representing this function
        wf_class = processes.FunctionProcess.build(func, calc_node_class=calc_node_class, **kwargs)
        inputs = wf_class.create_inputs(*args, **kwargs)
        # Have to create a new runner for the workfunction instead of using
        # the global because otherwise a workfunction that calls another from
        # within its scope would be blocking the event loop
        runner = runners.Runner(rmq_config=None, rmq_submit=False, enable_persistence=False)
        return wf_class(inputs=inputs, runner=runner).execute()

    def run_get_node(*args, **kwargs):
        # Build up the Process representing this function
        wf_class = processes.FunctionProcess.build(func, calc_node_class=calc_node_class, **kwargs)
        inputs = wf_class.create_inputs(*args, **kwargs)
        proc = wf_class(inputs=inputs)
        return proc.execute(), proc.calc

    wrapped_function.run_get_node = run_get_node

    wrapped_function._original = func
    wrapped_function._is_workfunction = True

    return wrapped_function
