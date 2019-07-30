# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
from aiida.work.process import FunctionProcess
from aiida.work.defaults import serial_engine
import functools


def workfunction(func):
    """
    A decorator to turn a standard python function into a workfunction.
    Example usage:

    >>> from aiida.orm.data.base import Int
    >>> from aiida.work.workfunction import workfunction as wf
    >>>
    >>> # Define the workfunction
    >>> @wf
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
        # Do this here so that it doesn't enter as an input to the process
        return_pid = kwargs.pop('_return_pid', False)

        # Build up the Process representing this function
        FuncProc = FunctionProcess.build(func, **kwargs)

        inputs = {}
        if kwargs:
            inputs.update(kwargs)
        if args:
            inputs.update(FuncProc.args_to_dict(*args))
        future = serial_engine.submit(FuncProc, inputs)
        pid = future.pid

        results = future.result()
        # Check if there is just one value returned
        if len(results) == 1 and FuncProc.SINGLE_RETURN_LINKNAME in results:
            if return_pid:
                return results[FuncProc.SINGLE_RETURN_LINKNAME], pid
            else:
                return results[FuncProc.SINGLE_RETURN_LINKNAME]
        else:
            if return_pid:
                return results, pid
            else:
                return results

    wrapped_function._is_workfunction = True
    return wrapped_function
