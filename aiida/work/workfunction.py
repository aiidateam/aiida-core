## -*- coding: utf-8 -*-
"""
This file provides very simple workflows for testing purposes.
Do not delete, otherwise 'verdi developertest' will stop to work.
"""

from aiida.work.process import FunctionProcess
from aiida.work.defaults import serial_engine
import functools

__copyright__ = u"Copyright (c), This file is part of the AiiDA platform. For further information please visit http://www.aiida.net/. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file."
__version__ = "0.7.0"
__authors__ = "The AiiDA team."


def workfunction(func):
    @functools.wraps(func)
    def wrapped_function(*args, **kwargs):
        """
        This wrapper function is the actual function that is called.
        """
        # Do this here so that it doesn't enter as an input to the process
        run_async = kwargs.pop('__async', False)
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

        if run_async:
            if return_pid:
                return future, pid
            else:
                return future
        else:
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

# def aiidise(func):
#     import inspect
#     import itertools
#
#     def wrapped_function(*args, **kwargs):
#         in_dict = dict(
#             itertools.chain(
#                 itertools.izip(inspect.getargspec(func)[0], args), kwargs))
#
#         native_args = [util.to_native_type(arg) for arg in args]
#         native_kwargs = {k: util.to_native_type(v) for k, v in kwargs.iteritems()}
#
#         # Create the calculation (unstored)
#         calc = Calculation()
#         util.save_calc(calc, func, in_dict)
#
#         # Run the wrapped function
#         retval = util.to_db_type(func(*native_args, **native_kwargs))
#
#         retval.add_link_from(calc, 'result')
#
#         return retval
#
#     return wrapped_function
