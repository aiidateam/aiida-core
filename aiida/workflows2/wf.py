# -*- coding: utf-8 -*-
"""
This file provides very simple workflows for testing purposes.
Do not delete, otherwise 'verdi developertest' will stop to work.
"""

from aiida.workflows2.process import FunctionProcess
from aiida.workflows2.defaults import execution_engine
import functools

__copyright__ = u"Copyright (c), This file is part of the AiiDA platform. For further information please visit http://www.aiida.net/. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file."
__version__ = "0.7.1.1"
__authors__ = "The AiiDA team."


def wf(func):
    @functools.wraps(func)
    def wrapped_function(*args, **kwargs):
        """
        This wrapper function is the actual function that is called.
        """
        # Do this here so that it doesn't enter as an input to the process
        run_async = kwargs.pop('__async', False)

        # Build up the Process repreresenting this function
        FuncProc = FunctionProcess.build(func, **kwargs)

        inputs = {}
        if kwargs:
            inputs.update(kwargs)
        if args:
            inputs.update(FuncProc.args_to_dict(*args))
        future = execution_engine.submit(FuncProc, inputs)

        if run_async:
            return future
        else:
            results = future.result()
            # Check if there is just one value returned
            if len(results) == 1 and FuncProc.SINGLE_RETURN_LINKNAME in results:
                return results[FuncProc.SINGLE_RETURN_LINKNAME]
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
