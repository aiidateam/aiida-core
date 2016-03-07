# -*- coding: utf-8 -*-
"""
This file provides very simple workflows for testing purposes.
Do not delete, otherwise 'verdi developertest' will stop to work.
"""

from aiida.orm import Calculation
from aiida.orm import Data

__copyright__ = u"Copyright (c), 2015, ECOLE POLYTECHNIQUE FEDERALE DE LAUSANNE (Theory and Simulation of Materials (THEOS) and National Centre for Computational Design and Discovery of Novel Materials (NCCR MARVEL)), Switzerland and ROBERT BOSCH LLC, USA. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file"
__version__ = "0.5.0"
__contributors__ = "Andrea Cepellotti, Giovanni Pizzi, Martin Uhrin"


def wf(func):
    import inspect
    import itertools
    import aiida.new_workflows.util as util

    def wrapped_function(*args, **kwargs):
        """
        This wrapper function is the actual function that is called.
        """
        in_dict = dict(
            itertools.chain(
                itertools.izip(inspect.getargspec(func)[0], args), kwargs))

        # Create the calculation (unstored)
        c = _create_calc(func, in_dict)

        try:
            stack = func._wf_stack
        except AttributeError:
            stack = []
            func._wf_stack = stack

        if stack:
            # TODO: This is where a call link would go from prent to this fn
            pass

        stack.append(func)
        # Run the wrapped function
        retval = func(*args, **kwargs)
        if isinstance(retval, Data):
            outputs = util.Outputs({'result': retval})
        elif isinstance(retval, util.Outputs):
            outputs = retval
        else:
            raise ValueError("AiiDA function must return an AiiDA data type "
                             "or an Outputs object.")
        stack.pop()

        _store_outputs(c, outputs)

        return outputs

    return wrapped_function


def aiidise(func):
    import inspect
    import itertools
    import aiida.new_workflows.util as util

    def wrapped_function(*args, **kwargs):
        in_dict = dict(
            itertools.chain(
                itertools.izip(inspect.getargspec(func)[0], args), kwargs))

        native_args = [util.to_native_type(arg) for arg in args]
        native_kwargs = {k: util.to_native_type(v) for k, v in kwargs.iteritems()}

        # Create the calculation (unstored)
        c = _create_calc(func, in_dict)

        # Run the wrapped function
        retval = util.to_db_type(func(*native_args, **native_kwargs))
        outputs = util.Outputs({'result': retval})

        _store_outputs(c, outputs)

        return retval

    return wrapped_function


def _create_calc(func, in_dict):
    # Create the calculation (unstored)
    c = Calculation()

    # Add data input nodes as links
    for k, v in in_dict.iteritems():
        c._add_link_from(v, label=k)

    _add_source_info(c, func)

    return c


def _add_source_info(calc, func):
    import inspect

    # Note: if you pass a lambda function, the name will be <lambda>; moreover
    # if you define a function f, and then do "h=f", h.__name__ will
    # still return 'f'!
    function_name = func.__name__

    # Try to get the source code
    source_code, first_line = inspect.getsourcelines(func)
    try:
        with open(inspect.getsourcefile(func)) as f:
            source = f.read()
    except IOError:
        source = None
    calc._set_attr("source_code", "".join(source_code))
    calc._set_attr("first_line_source_code", first_line)
    calc._set_attr("source_file", source)
    calc._set_attr("function_name", function_name)


def _store_outputs(calc, outputs):
    from aiida.common.exceptions import ModificationNotAllowed
    from django.db import transaction

    # Check the output values
    for k, v in outputs.iteritems():
        if v._is_stored:
            raise ModificationNotAllowed(
                "One of the values (for key '{}') of the "
                "dictionary returned by the wrapped function "
                "is already stored! Note that this node (and "
                "any other side effect of the function) are "
                "not going to be undone!".format(k))

    # Add link to output data nodes
    for k, v in outputs.iteritems():
        v._add_link_from(calc, label=k)

    with transaction.commit_on_success():
        # I call store_all for the Inline calculation;
        # this will store also the inputs, if needed.
        calc.store_all(with_transaction=False)
        # As c is already stored, I just call store (and not store_all)
        # on each output
        for v in outputs.itervalues():
            v.store(with_transaction=False)
